"""Warm both original cooking model options without desktop capture or input.

The upstream --check-model-only path loads and exercises the real inference
kernels using synthetic arrays, then exits before creating a game adapter.
Pass --executable to validate the same path inside the portable program.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback


ROOT = Path(__file__).resolve().parents[1]
MODELS = ("resnet18", "resnet101")


def worker_command(model: str, directory: Path, executable: Path | None) -> list[str]:
    command = [str(executable)] if executable else [sys.executable, str(ROOT / "main.py")]
    command += [
        "--worker", "--games", "1", "--output", str(directory / "runs"),
        "--control-file", str(directory / "stop"), "--model", model,
        "--check-model-only",
    ]
    return command


def logs(directory: Path) -> str:
    sections = []
    for name in ("process-output.log", "launcher.log"):
        path = directory / name
        if path.is_file():
            content = path.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                sections.append(f"{name}:\n{content[-12000:]}")
    return "\n".join(sections)


def check_one(model: str, expected: dict, directory: Path, *,
              executable: Path | None, timeout: float) -> dict:
    import win32job

    directory.mkdir()
    job = win32job.CreateJobObject(None, "")
    settings = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
    settings["BasicLimitInformation"]["LimitFlags"] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, settings)
    process = None
    try:
        with (directory / "process-output.log").open("wb") as output:
            process = subprocess.Popen(
                worker_command(model, directory, executable), cwd=ROOT,
                stdout=output, stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
                     "LOCALAPPDATA": str(directory / "user-data")},
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            win32job.AssignProcessToJobObject(job, int(process._handle))
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(f"{model} model warmup exceeded {timeout:g} seconds.\n{logs(directory)}") from exc
        if code != 0:
            raise RuntimeError(f"{model} model worker exited with code {code}.\n{logs(directory)}")
        report_path = directory / "model-check.json"
        if not report_path.is_file():
            raise RuntimeError(f"{model} worker produced no model-check.json.\n{logs(directory)}")
        checked = json.loads(report_path.read_text(encoding="utf-8"))
        required = {
            "passed": True, "model": model, "loaded_architecture": model,
            "sha256": expected["sha256"], "warmup_completed": True,
            "game_inputs_sent": 0,
        }
        for field, expected_value in required.items():
            if checked.get(field) != expected_value:
                raise ValueError(f"{model}: {field} was {checked.get(field)!r}; expected {expected_value!r}")
        if checked.get('torch_imported') is not False:
            raise ValueError(f'{model} unexpectedly imported PyTorch')
        checked["manifest_verified"] = True
        return checked
    finally:
        # Own the complete worker tree, including any venv launcher descendants.
        job.Close()
        if process is not None and process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def check_models(*, executable: Path | None, timeout: float) -> dict:
    if sys.platform != "win32":
        raise ValueError("Cooking runtime verification requires Windows.")
    manifest = json.loads((ROOT / "upstream" / "cooking" / "models-manifest.json").read_text(encoding="utf-8"))
    report = {
        "mode": "packaged" if executable else "source",
        "models": [], "game_inputs_sent": 0,
        "capture": "synthetic arrays only",
    }
    if executable:
        report["executable"] = str(executable)
    with tempfile.TemporaryDirectory(prefix="holodori-model-check-") as temporary:
        directory = Path(temporary).resolve()
        for model in MODELS:
            expected = manifest["files"][f"models/inference/point-classifier-{model}.onnx"]
            report["models"].append(check_one(
                model, expected, directory / model, executable=executable, timeout=timeout))
    report["passed"] = True
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, help="Verify the built EXE instead of the source entry point.")
    parser.add_argument("--report", type=Path, help="Also save the complete JSON verification report.")
    parser.add_argument("--timeout", type=float, default=180,
                        help="Maximum seconds for each model, up to 180 (default: 180).")
    args = parser.parse_args()
    if args.executable and not args.executable.is_file():
        parser.error(f"Executable does not exist: {args.executable}")
    if not 0 < args.timeout <= 180:
        parser.error("--timeout must be greater than 0 and at most 180 seconds")
    try:
        result = check_models(executable=args.executable.resolve() if args.executable else None,
                              timeout=args.timeout)
    except Exception:
        result = {"passed": False, "error": traceback.format_exc(), "game_inputs_sent": 0}
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
