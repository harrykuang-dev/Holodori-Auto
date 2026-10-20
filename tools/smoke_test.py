"""Exercise all original embedded interfaces without starting game automation.

Global shortcut listeners are replaced through the integration's smoke mode.
Settings are redirected to a unique temporary LOCALAPPDATA directory. Pass
--executable to exercise the packaged child runtimes with the same host checks.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    "high_low": {"strategy": 1},
    "fishing": {
        "target_mode": "count", "target_amount": "7", "target": "7", "diagnostics": True,
    },
    "jump_rope": {
        "target": "3", "timing": 0.65, "diagnostics": True,
    },
    "cooking": {
        "model": "resnet101", "games": "3", "developer_mode": True,
    },
}
SHARED_SETTINGS = {"language": "English", "start_key": "Alt+F7", "stop_key": "Ctrl+Alt+F10"}


@contextmanager
def isolated_data(directory: Path):
    previous = os.environ.get("LOCALAPPDATA")
    os.environ["LOCALAPPDATA"] = str(directory)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = previous


def exercise(*, executable: Path | None, timeout: float, screenshot: Path | None) -> dict:
    import tkinter as tk
    import win32gui
    import win32job

    sys.path.insert(0, str(ROOT))
    from holodori.app import HolodoriApp, PROJECT_URL
    from holodori.runtime import LANGUAGES, dpi_awareness

    report = {"mode": "packaged" if executable else "source", "modules": [], "errors": []}
    if executable:
        report["executable"] = str(executable)
    dpi_awareness()
    with tempfile.TemporaryDirectory(prefix="holodori-smoke-") as temporary:
        directory = Path(temporary)
        with isolated_data(directory / "user-data"):
            root = tk.Tk()
            callback_errors = []
            root.report_callback_exception = lambda kind, error, tb: callback_errors.append(
                "".join(traceback.format_exception(kind, error, tb)))
            kwargs = {"smoke": True, "session_dir": directory}
            if executable:
                kwargs["child_executable"] = executable
            app = HolodoriApp(root, **kwargs)
            processes = []
            closed = False

            def pump_until(predicate, description):
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    try:
                        root.update()
                    except tk.TclError:
                        if predicate():
                            return
                        raise
                    if callback_errors:
                        raise AssertionError("Host callback failed: " + callback_errors[-1])
                    if app.last_error:
                        raise AssertionError(f"{description}: {app.last_error}")
                    if app.last_status.get("errors"):
                        raise AssertionError("Child callback failed: " + "\n".join(app.last_status["errors"]))
                    if predicate():
                        return
                    time.sleep(0.01)
                startup = ""
                if app.channel and (app.channel / "startup.txt").is_file():
                    startup = (app.channel / "startup.txt").read_text(encoding="utf-8", errors="replace")[-8000:]
                raise AssertionError(f"Timed out waiting for {description}; status={app.last_status!r}\n{startup}")

            def live_count():
                return win32job.QueryInformationJobObject(
                    app.job, win32job.JobObjectBasicAccountingInformation)["ActiveProcesses"]

            def ready(module):
                pump_until(lambda: app.active == module and app.ready and app.process is not None
                           and app.process.poll() is None, module + " ready")
                # A venv executable can redirect through an additional native
                # Python launcher. Track feature sessions by their Popen handle;
                # the Windows job also owns any legitimate worker descendants.
                assert live_count() >= 1, "The isolated child is outside the host job"
                assert sum(process.poll() is None for process in processes) <= 1, "Previous feature session remains alive"
                assert not app.last_status.get("busy"), f"{module} started an automation unexpectedly"
                assert app.last_status.get("module") == module
                if not processes or processes[-1] is not app.process:
                    processes.append(app.process)

            def request(action, **extra):
                app.request(action, **extra)
                number = app.sequence
                pump_until(lambda: app.last_status.get("request") == number
                           and app.last_status.get("state") == "ready", action + " acknowledgement")

            def shared_settings_match(expected):
                return app.pending_settings is None and app.settings == expected and all(
                    app.last_status.get(key) == value for key, value in expected.items())

            def assert_shared(module, expected=SHARED_SETTINGS):
                pump_until(lambda: shared_settings_match(expected), module + " shared preferences")
                assert app.last_status.get("shared_controls_hidden") is True, f"{module} duplicate shared controls remain visible"
                assert app.last_status.get("language_selector_hidden") is True, f"{module} original language selector remains visible"
                assert app.last_status.get('embedded_chrome_hidden') is True, f'{module} repeated heading or version remains visible'
                assert app.last_status.get('instructions'), f'{module} instruction text missing'
                assert app.last_status.get('display_status'), f'{module} status text missing'
                root.update_idletasks()
                assert app.navigation.winfo_y() < app.intro.winfo_y() < app.shared_card.winfo_y() < app.body.winfo_y(), 'Shared layout order differs'
                assert app.instructions.cget('text') == app.last_status['instructions']
                assert app.status.cget('text') == app.last_status['display_status']
                assert app.version_label.cget('text') == 'v1.0.0'
                assert root.title() == 'Holodori-Auto', f'{module} changed the Tk window title'
                window = win32gui.GetAncestor(root.winfo_id(), 2)
                assert win32gui.GetWindowText(window) == 'Holodori-Auto', f'{module} changed the native window title'
                assert not app.note.cget('text'), 'Unexpected component version in host footer'
                assert not app.last_status.get("capture_active"), f"{module} shortcut capture remains active"
                assert not app.last_status.get("busy"), f"{module} started an automation unexpectedly"

            def begin_capture(target):
                app.begin_capture(target)
                pump_until(lambda: app.capture_target == target and app.capture_ready
                           and app.last_status.get("capture_active") is True,
                           target + " shortcut capture and child listener suspension")

            def capture_shortcut(target, event, expected):
                begin_capture(target)
                app.capture_key(event)
                pump_until(lambda: shared_settings_match(expected) and app.capture_target is None
                           and not app.last_status.get("capture_active"), target + " shortcut acceptance")

            try:
                ready("high_low")
                with patch('holodori.app.webbrowser.open', return_value=True) as browser:
                    app.version_label.event_generate('<Button-1>')
                    root.update()
                    browser.assert_called_once_with(PROJECT_URL)
                report['version_link'] = PROJECT_URL
                # Use the host's actual capture methods with synthetic Tk events;
                # no native keyboard/game input is sent, and smoke listeners are inert.
                initial = dict(app.settings)
                begin_capture("start")
                app.capture_key(SimpleNamespace(keysym="Alt_L", state=0, keycode=18))
                assert app.capture_target == "start" and app.capture_ready
                assert app.last_status.get("capture_active") is True
                assert app.settings == initial, "A modifier-only press changed the shortcut"
                app.capture_key(SimpleNamespace(keysym="F7", state=0x8, keycode=118))
                numlock_settings = dict(initial, start_key="F7")
                pump_until(lambda: shared_settings_match(numlock_settings)
                           and not app.last_status.get("capture_active"), "Num Lock without Alt")
                assert app.settings["start_key"] == "F7", "Num Lock was interpreted as Alt"

                alt_settings = dict(numlock_settings, start_key="Alt+F7")
                capture_shortcut("start", SimpleNamespace(keysym="F7", state=0x20008, keycode=118), alt_settings)
                shortcut_settings = dict(alt_settings, stop_key="Ctrl+Alt+F10")
                capture_shortcut("stop", SimpleNamespace(keysym="F10", state=0x20004, keycode=121), shortcut_settings)

                before_cancel = dict(app.settings)
                begin_capture("stop")
                app.capture_key(SimpleNamespace(keysym="Escape", state=0, keycode=27))
                pump_until(lambda: app.capture_target is None and not app.last_status.get("capture_active"),
                           "Escape capture cancellation")
                assert shared_settings_match(before_cancel), "Cancelled capture changed shared preferences"

                app.language.set("English")
                app.change_language()
                assert_shared("high_low")
                preferences = directory / "user-data" / "HolodoriAuto" / "settings.json"
                assert json.loads(preferences.read_text(encoding="utf-8")) == SHARED_SETTINGS
                report["shared_preferences"] = {
                    **SHARED_SETTINGS, "modifier_only_ignored": True, "num_lock_not_alt": True,
                    "escape_cancelled": True, "persisted": True,
                }
                for index, module in enumerate(FIELDS):
                    if index:
                        previous = app.process
                        app.select(module)
                        ready(module)
                        assert previous.poll() == 0, f"Previous child did not close cleanly: {previous.poll()}"
                    assert_shared(module)
                    for language in LANGUAGES:
                        app.language.set(language)
                        app.change_language()
                        assert_shared(module, dict(SHARED_SETTINGS, language=language))
                    app.language.set(SHARED_SETTINGS['language'])
                    app.change_language()
                    assert_shared(module)
                    fields = FIELDS[module]
                    request("set_fields", fields=fields)
                    snapshot = app.last_status["snapshot"]
                    for key, expected in fields.items():
                        assert snapshot.get(key) == expected, f"{module}.{key}: {snapshot.get(key)!r} != {expected!r}"
                    app.request("dialog")
                    number = app.sequence
                    pump_until(lambda: app.last_status.get("request") == number
                               and app.last_status.get("dialog_checked"), module + " original dialog")
                    assert app.process.poll() is None
                    root.geometry(f"{max(app.px(420), root.minsize()[0])}x{max(app.px(760), root.minsize()[1])}")
                    request("snapshot")
                    root.iconify()
                    root.update()
                    root.deiconify()
                    root.update()
                    root.lift()
                    request("snapshot")
                    assert_shared(module)
                    report["modules"].append({
                        "id": module, "pid": app.process.pid, "fields": fields,
                        "dialog_checked": True, "resize_and_restore": True,
                        "native_job_processes": live_count(),
                        "shared_preferences_applied": True, "shared_controls_hidden": True,
                        "window_title": "Holodori-Auto", "languages_checked": len(LANGUAGES),
                    })

                # Revisiting each page verifies the actual process replacement and restore contract.
                for module, fields in FIELDS.items():
                    previous = app.process
                    app.select(module)
                    ready(module)
                    if app.process is not previous:
                        assert previous.poll() == 0
                    request("snapshot")
                    assert_shared(module)
                    for key, expected in fields.items():
                        actual = app.last_status["snapshot"].get(key)
                        assert actual == expected, f"Restored {module}.{key}: {actual!r} != {expected!r}"

                # Leave the first feature visible in optional review screenshots.
                app.select("high_low")
                ready("high_low")
                assert_shared("high_low")
                root.update_idletasks()
                heights = {'language': app.language_choice.winfo_height(),
                           **{kind: field.winfo_height() for kind, field in app.shortcut_frames.items()}}
                assert len(set(heights.values())) == 1, f'Shared control heights differ: {heights}'
                report['shared_control_heights'] = heights
                if screenshot:
                    from PIL import ImageGrab
                    settled = time.monotonic() + 0.6
                    pump_until(lambda: time.monotonic() >= settled, "final child painting")
                    screenshot.parent.mkdir(parents=True, exist_ok=True)
                    left, top = root.winfo_rootx(), root.winfo_rooty()
                    ImageGrab.grab(bbox=(left, top, left + root.winfo_width(), top + root.winfo_height())).save(screenshot)
                    report["screenshot"] = str(screenshot)

                last = app.process
                app.close()
                pump_until(lambda: app.process is None, "graceful host shutdown")
                closed = True
                assert last.poll() == 0
                assert all(process.poll() == 0 for process in processes), "A child exited abnormally or remains alive"
                assert not callback_errors
                report.update(passed=True, child_launches=len(processes), settings_restored=True,
                              graceful_shutdown=True, game_automation_started=False)
            finally:
                if not closed:
                    try:
                        app.job.Close()
                    except Exception:
                        pass
                    for process in processes:
                        try:
                            process.wait(timeout=5)
                        except Exception:
                            pass
                    try:
                        root.destroy()
                    except tk.TclError:
                        pass
                    if app.stream:
                        app.stream.close()
                        app.stream = None
                    app.temporary.cleanup()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, help="Use the built EXE for the isolated feature processes.")
    parser.add_argument("--timeout", type=float, default=45, help="Maximum seconds for each asynchronous UI step.")
    parser.add_argument("--screenshot", type=Path, help="Save a PNG of the embedded application after verification.")
    parser.add_argument("--report", type=Path, help="Also save the JSON verification report.")
    args = parser.parse_args()
    if args.executable and not args.executable.is_file():
        parser.error(f"Executable does not exist: {args.executable}")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        result = exercise(executable=args.executable.resolve() if args.executable else None,
                          timeout=args.timeout, screenshot=args.screenshot.resolve() if args.screenshot else None)
    except Exception:
        result = {"passed": False, "error": traceback.format_exc(), "game_automation_started": False}
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
