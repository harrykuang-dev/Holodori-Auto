"""Update the four upstream gitlinks without modifying their source files.

Only the Python standard library and Git are required.  ``--check`` fetches
remote commits but never changes a checkout, index, or the lock file.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Sequence


MODULES = {
    "high_low": ("app_locale.py", "APP_VERSION"),
    "fishing": ("gui.py", "APP_VERSION"),
    "jump_rope": ("batch_session.py", "APP_VERSION"),
    "cooking": ("gui.py", "VERSION"),
}
LOCK_NAME = "upstream-lock.json"
SCHEMA_VERSION = 1


class SyncError(RuntimeError):
    """An operation was refused or Git could not complete it."""


def git(root: Path, *args: str) -> str:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True,
        encoding="utf-8", errors="replace", env=env, check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SyncError(f"git {' '.join(args)} failed in {root}: {detail}")
    return result.stdout.strip()


@dataclass(frozen=True)
class Module:
    name: str
    path: str
    repository: str
    branch: str


def module_config(root: Path, name: str) -> Module:
    path = f"upstream/{name}"
    prefix = f"submodule.{path}"
    configured_path = git(root, "config", "--file", ".gitmodules", "--get", f"{prefix}.path")
    if configured_path != path:
        raise SyncError(f"Unexpected submodule path for {name}: {configured_path!r}")
    repository = git(root, "config", "--file", ".gitmodules", "--get", f"{prefix}.url")
    branch = git(root, "config", "--file", ".gitmodules", "--get", f"{prefix}.branch")
    git(root, "check-ref-format", "--branch", branch)
    if not repository:
        raise SyncError(f"No upstream repository configured for {name}")
    child = root / path
    if not (child / ".git").exists():
        raise SyncError(f"{path} is not initialized; run git submodule update --init --recursive")
    actual = Path(git(child, "rev-parse", "--show-toplevel")).resolve()
    if actual != child.resolve():
        raise SyncError(f"{path} is not a separate initialized Git checkout")
    return Module(name, path, repository, branch)


def index_commit(root: Path, module: Module) -> str:
    entries = git(root, "ls-files", "--stage", "--", module.path).splitlines()
    if len(entries) != 1:
        raise SyncError(f"{module.path} does not have one resolved gitlink in the index")
    metadata, path = entries[0].split("\t", 1)
    mode, commit, stage = metadata.split()
    if mode != "160000" or stage != "0" or path != module.path:
        raise SyncError(f"{module.path} is not a resolved gitlink in the index")
    return commit


def checkout_commit(root: Path, module: Module) -> str:
    return git(root / module.path, "rev-parse", "HEAD")


def checkout_branch(root: Path, module: Module) -> str | None:
    try:
        return git(root / module.path, "symbolic-ref", "--quiet", "--short", "HEAD")
    except SyncError:
        return None


def read_version(root: Path, module: Module, commit: str) -> str | None:
    filename, constant = MODULES[module.name]
    try:
        source = git(root / module.path, "show", f"{commit}:{filename}")
        tree = ast.parse(source, filename=filename)
    except (SyncError, SyntaxError):
        return None
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            targets, value = statement.targets, statement.value
        elif isinstance(statement, ast.AnnAssign):
            targets, value = [statement.target], statement.value
        else:
            continue
        if value is None or not any(isinstance(item, ast.Name) and item.id == constant for item in targets):
            continue
        try:
            literal = ast.literal_eval(value)
        except (ValueError, TypeError):
            return None
        return literal if isinstance(literal, str) else None
    return None


def lock_entry(root: Path, module: Module, commit: str) -> dict:
    return {
        "path": module.path,
        "repository": module.repository,
        "branch": module.branch,
        "commit": commit,
        "version": read_version(root, module, commit),
    }


def read_lock(root: Path) -> dict:
    try:
        lock = json.loads((root / LOCK_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SyncError(f"Cannot read {LOCK_NAME}: {exc}; use --write-lock for the initial lock") from exc
    if not isinstance(lock, dict) or lock.get("schema_version") != SCHEMA_VERSION:
        raise SyncError(f"Unsupported {LOCK_NAME} schema")
    entries = lock.get("modules")
    if not isinstance(entries, dict) or set(entries) != set(MODULES):
        raise SyncError(f"{LOCK_NAME} must contain exactly: {', '.join(MODULES)}")
    for name, entry in entries.items():
        if not isinstance(entry, dict) or not re.fullmatch(r"[0-9a-f]{40,64}", str(entry.get("commit", ""))):
            raise SyncError(f"Invalid locked commit for {name}")
    return lock


def write_lock(root: Path, lock: dict) -> None:
    destination = root / LOCK_NAME
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=root,
                                         prefix=LOCK_NAME + ".", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(lock, indent=2, ensure_ascii=False) + "\n")
        temporary.replace(destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def verify_lock(root: Path, modules: list[Module], lock: dict) -> None:
    for module in modules:
        entry = lock["modules"][module.name]
        pin = index_commit(root, module)
        actual = checkout_commit(root, module)
        expected = lock_entry(root, module, pin)
        if entry != expected:
            raise SyncError(f"{LOCK_NAME} does not match the index pin or metadata for {module.name}")
        if actual != pin:
            raise SyncError(f"{module.path} checkout differs from its index pin; stage an intended update or restore the pinned checkout")


def ensure_clean_for_update(root: Path, selected: list[Module]) -> None:
    protected = [".gitmodules", LOCK_NAME, *(item.path for item in selected)]
    status = git(root, "status", "--porcelain", "--untracked-files=no", "--", *protected)
    if status:
        raise SyncError("Refusing to overwrite edits to .gitmodules, the lock file, or selected gitlinks; commit or restore those edits first")
    for module in selected:
        status = git(root / module.path, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none")
        if status:
            raise SyncError(f"Refusing to update dirty submodule {module.path}; commit, stash, or remove its local changes first")


def fetch_target(root: Path, module: Module) -> str:
    child = root / module.path
    if git(child, "remote", "get-url", "origin") != module.repository:
        raise SyncError(f"{module.path} origin differs from .gitmodules; run git submodule sync first")
    ref = f"refs/remotes/origin/{module.branch}"
    git(child, "fetch", "--no-tags", "--", "origin", f"+refs/heads/{module.branch}:{ref}")
    return git(child, "rev-parse", "--verify", f"{ref}^{{commit}}")


def synchronize(root: Path, selected_names: Sequence[str], *, check: bool = False,
                verify: bool = False, initial_lock: bool = False) -> dict:
    root = root.resolve()
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise SyncError("Run the tool from the Holodori-Auto repository root")
    modules = [module_config(root, name) for name in MODULES]
    selected = [module for module in modules if module.name in selected_names]
    if initial_lock:
        if (root / LOCK_NAME).exists():
            raise SyncError(f"{LOCK_NAME} already exists; initial lock creation never overwrites an existing lock")
        entries = {}
        for module in modules:
            commit = checkout_commit(root, module)
            if commit != index_commit(root, module):
                raise SyncError(f"Stage the intended gitlink for {module.name} before creating the initial lock")
            entries[module.name] = lock_entry(root, module, commit)
        write_lock(root, {"schema_version": SCHEMA_VERSION, "modules": entries})
        return {"mode": "write-lock", "changed": True, "modules": entries}
    lock = read_lock(root)
    if verify:
        verify_lock(root, modules, lock)
        return {"mode": "verify", "changed": False, "modules": lock["modules"]}
    if not check:
        ensure_clean_for_update(root, selected)
        verify_lock(root, modules, lock)
    plans = []
    for module in selected:
        current = checkout_commit(root, module)
        target = fetch_target(root, module)
        plans.append({
            "name": module.name, "path": module.path,
            "before": current, "after": target, "changed": current != target,
            "before_version": read_version(root, module, current),
            "after_version": read_version(root, module, target),
        })
    changes = [plan for plan in plans if plan["changed"]]
    if not check and changes:
        changed_checkouts = []
        try:
            for plan in changes:
                module = next(item for item in selected if item.name == plan["name"])
                previous_branch = checkout_branch(root, module)
                git(root / module.path, "checkout", "--no-overwrite-ignore", "--detach", plan["after"])
                changed_checkouts.append((module, plan["before"], previous_branch))
                lock["modules"][module.name] = lock_entry(root, module, plan["after"])
            write_lock(root, lock)
        except Exception:
            for module, previous, previous_branch in reversed(changed_checkouts):
                if previous_branch:
                    git(root / module.path, "checkout", "--no-overwrite-ignore", previous_branch)
                else:
                    git(root / module.path, "checkout", "--no-overwrite-ignore", "--detach", previous)
            raise
    return {"mode": "check" if check else "update", "changed": bool(changes), "modules": plans}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fetch and report; do not change worktrees, the index, or the lock")
    mode.add_argument("--verify", action="store_true", help="verify all checkout/index pins against the lock without network access")
    mode.add_argument("--write-lock", action="store_true", help="create the initial lock from the current index/checkout; no network")
    parser.add_argument("--module", action="append", choices=list(MODULES), dest="modules", help="only check/update this module; repeatable")
    parser.add_argument("--json", action="store_true", help="print a machine-readable report")
    args = parser.parse_args(argv)
    if args.modules and (args.verify or args.write_lock):
        parser.error("--module applies to checking or updating; lock verification/creation always covers all modules")
    try:
        report = synchronize(Path(__file__).resolve().parents[1], args.modules or list(MODULES),
                             check=args.check, verify=args.verify, initial_lock=args.write_lock)
    except (SyncError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.verify:
        print("All four upstream commits, versions, and gitlink pins match the lock.")
    elif args.write_lock:
        print(f"Created {LOCK_NAME} from the four pinned checkouts.")
    else:
        for item in report["modules"]:
            result = f"{item['before'][:12]} -> {item['after'][:12]}" if item["changed"] else f"current ({item['before'][:12]})"
            print(f"{item['name']}: {result}")
        if report["changed"] and not args.check:
            print("Updated checkouts and lock. Review, then git add upstream upstream-lock.json before --verify.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
