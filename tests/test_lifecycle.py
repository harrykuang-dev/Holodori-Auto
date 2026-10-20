"""Module process ownership tests without native windows or game input."""
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from holodori.app import HolodoriApp
from holodori.channel import write_json
from holodori.modules import MODULES


class FakeProcess:
    def __init__(self, code=None):
        self.code = code
        self._handle = 123
        self.terminated = False

    def poll(self):
        return self.code

    def terminate(self):
        self.terminated = True
        self.code = -15


class FakeJob:
    def __init__(self, active=0):
        self.active = active
        self.closed = False

    def Close(self):
        self.closed = True


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.job_api = SimpleNamespace(
            JobObjectExtendedLimitInformation=9,
            JobObjectBasicAccountingInformation=1,
            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE=0x2000,
            CreateJobObject=mock.Mock(side_effect=lambda *_: FakeJob()),
            SetInformationJobObject=mock.Mock(),
            AssignProcessToJobObject=mock.Mock(),
            TerminateJobObject=mock.Mock(),
        )
        self.job_api.QueryInformationJobObject = mock.Mock(side_effect=self.query_job)
        self.addCleanup(mock.patch.stopall)
        mock.patch.dict("sys.modules", win32job=self.job_api).start()
        self.app = HolodoriApp.__new__(HolodoriApp)
        self.app.root = mock.Mock()
        self.app.root.winfo_id.return_value = 100
        self.app.smoke = True
        self.app.child_executable = None
        self.app.temporary = mock.Mock()
        self.app.session_dir = Path(self.temporary.name)
        self.app.channel = self.app.session_dir / "active"
        self.app.channel.mkdir()
        (self.app.channel / "startup.txt").write_text("", encoding="utf-8")
        self.app.process = self.app.stream = self.app.job = None
        self.app.active = "cooking"
        self.app.pending = None
        self.app.ready = False
        self.app.closing = False
        self.app.waiting_switch = False
        self.app.last_status = {}
        self.app.last_error = None
        self.app.sequence = 0
        self.app.snapshots = {}
        self.app.source_versions = {}
        self.app._session_draining = False
        self.app._job_termination_requested = False
        self.app._cleanup_error_reported = False
        self.app._finished_status = {}
        self.app._finished_code = None
        self.app._startup_error = None
        self.app.language = mock.Mock(get=mock.Mock(return_value="English"))
        self.app.note = self.app.progress = self.app.placeholder = self.app.reload = mock.Mock()
        self.app.buttons = {module.id: mock.Mock() for module in MODULES}
        self.app.container = None
        self.app.body = mock.Mock()
        self.app.px = lambda number: number

    def query_job(self, job, information):
        if information == self.job_api.JobObjectExtendedLimitInformation:
            return {"BasicLimitInformation": {"LimitFlags": 0}}
        return {"ActiveProcesses": job.active}

    def test_switch_waits_for_surviving_workers_to_exit(self):
        job = self.app.job = FakeJob(active=2)
        self.app.process = FakeProcess(code=1)
        self.app.stream = io.StringIO()
        self.app.pending = "fishing"
        self.app.waiting_switch = True
        self.app.launch = mock.Mock()
        write_json(self.app.channel / "status.json", {"snapshot": {"games": "7"}})

        self.app.poll()
        self.job_api.TerminateJobObject.assert_called_once_with(job, 1)
        self.app.launch.assert_not_called()
        self.assertIs(self.app.job, job)
        self.assertIsNone(self.app.process)
        self.assertEqual(self.app.snapshots["cooking"], {"games": "7"})

        self.app.poll()
        self.job_api.TerminateJobObject.assert_called_once()
        self.app.launch.assert_not_called()
        job.active = 0
        self.app.poll()
        self.assertTrue(job.closed)
        self.assertIsNone(self.app.job)
        self.app.launch.assert_called_once_with("fishing")

    def test_selection_between_gui_exit_and_poll_cannot_start_overlap(self):
        self.app.process = FakeProcess(code=0)
        self.app.job = FakeJob(active=1)
        self.app.launch = mock.Mock()
        self.app.select("jump_rope")
        self.app.launch.assert_not_called()
        self.assertEqual(self.app.pending, "jump_rope")

    def test_host_close_waits_for_residual_workers(self):
        job = self.app.job = FakeJob(active=1)
        self.app.process = FakeProcess(code=0)
        self.app.close()
        self.app.poll()
        self.app.root.destroy.assert_not_called()
        self.app.temporary.cleanup.assert_not_called()
        job.active = 0
        self.app.poll()
        self.app.root.destroy.assert_called_once()
        self.app.temporary.cleanup.assert_called_once()

    def test_failed_cleanup_is_reported_and_blocks_replacement(self):
        class JobError(Exception):
            pass

        self.app.job = FakeJob(active=1)
        self.app._session_draining = True
        self.app.pending = "fishing"
        self.app.launch = mock.Mock()
        self.job_api.TerminateJobObject.side_effect = JobError("native job failure")
        self.app.poll()
        self.app.poll()
        self.assertIn("native job failure", self.app.last_error)
        self.app.launch.assert_not_called()
        self.assertIsNotNone(self.app.job)

    def test_job_assignment_error_stops_child_and_releases_resources(self):
        class NativeError(Exception):
            pass

        process = FakeProcess()
        self.job_api.AssignProcessToJobObject.side_effect = NativeError("assignment failed")
        with mock.patch("holodori.app.tk.Frame") as frame, mock.patch(
            "holodori.app.subprocess.Popen", return_value=process
        ), mock.patch("holodori.app.subprocess.CREATE_NO_WINDOW", 0, create=True):
            frame.return_value.winfo_id.return_value = 100
            self.app.launch("fishing")
        self.assertTrue(process.terminated)
        self.assertIs(self.app.process, process)
        self.assertIn("assignment failed", self.app.last_error)
        stream = self.app.stream
        self.app.poll()
        self.assertIsNone(self.app.process)
        self.assertIsNone(self.app.job)
        self.assertTrue(stream.closed)

    def test_popen_error_closes_stream_and_job_without_losing_retry(self):
        with mock.patch("holodori.app.tk.Frame") as frame, mock.patch(
            "holodori.app.subprocess.Popen", side_effect=OSError("missing executable")
        ), mock.patch("holodori.app.subprocess.CREATE_NO_WINDOW", 0, create=True):
            frame.return_value.winfo_id.return_value = 100
            self.app.launch("high_low")
        self.assertIsNone(self.app.process)
        self.assertIsNone(self.app.stream)
        self.assertIn("missing executable", self.app.last_error)
        self.app.poll()
        self.assertIsNone(self.app.job)
        self.app.launch = mock.Mock()
        self.app.retry()
        self.app.launch.assert_called_once_with("high_low")


if __name__ == "__main__":
    unittest.main()
