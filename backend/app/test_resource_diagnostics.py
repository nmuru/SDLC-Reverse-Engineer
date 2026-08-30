import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.resource_diagnostics import ResourceDiagnostics


class ResourceDiagnosticsTests(unittest.TestCase):
    def test_disabled_monitor_creates_no_file(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            monitor = ResourceDiagnostics(False, temporary_dir, run_id="test")
            monitor.start()
            monitor.sample()
            monitor.stop()
            self.assertEqual(list(Path(temporary_dir).iterdir()), [])

    def test_enabled_monitor_records_structured_events(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            monitor = ResourceDiagnostics(
                True,
                temporary_dir,
                sample_interval_seconds=0.25,
                run_id="test-run",
            )
            monitor.start()
            monitor.phase_start("features", "Features", batch_index=0)
            monitor.sample()
            monitor.phase_end("features", "Features", batch_index=0)
            monitor.run_event("analysis_completed", completed_phase_count=1)
            monitor.stop()

            files = list(Path(temporary_dir).glob("resource-diagnostics-*.jsonl"))
            self.assertEqual(len(files), 1)

            records = [json.loads(line) for line in files[0].read_text().splitlines()]
            events = [record["event"] for record in records]
            self.assertIn("monitor_started", events)
            self.assertIn("sample", events)
            self.assertIn("phase_started", events)
            self.assertIn("phase_finished", events)
            self.assertIn("analysis_completed", events)
            self.assertIn("monitor_stopped", events)

            sample = next(record for record in records if record["event"] == "sample")
            self.assertIn("rss_mb", sample["process"])
            self.assertIn("cpu_percent", sample["process"])
            self.assertIn("total_ram_mb", sample["system"])
            self.assertIn("available_ram_mb", sample["system"])
            self.assertEqual(sample["run_id"], "test-run")

    def test_monitor_failure_does_not_break_pipeline(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            monitor = ResourceDiagnostics(True, temporary_dir, run_id="test")
            monitor.start()
            with patch.object(monitor, "_write_record", side_effect=OSError("disk full")):
                monitor.sample()
            monitor.stop()


if __name__ == "__main__":
    unittest.main()
