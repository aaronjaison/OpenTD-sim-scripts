"""Exercise queued UI snapshots, retry selection and serial advancement."""
from unittest.mock import Mock, patch
from frontend.interface import Application
from frontend.connections import Connections
from frontend.opentd_panel import OpenTDPanel
from frontend.test_queue import TestQueue


def test_preview_queue_snapshots(root, tmp_path):
    ui = Application(root, Connections(tmp_path))
    ui.values["duration"].set("2")
    ui.values["heat"].set("10")
    ui.run()
    ui.values["heat"].set("40")
    ui.run()
    ui.connections.controller.worker.join(10)
    ui.poll()
    assert ui.samples[-1].heat_w == 10
    ui.connections.controller.worker.join(10)
    ui.poll()
    assert ui.samples[-1].heat_w == 40
    first_folder = ui.folder
    ui.jobs.items.selection_set(1)
    ui.jobs.rerun_selected()
    ui.connections.controller.worker.join(10)
    ui.poll()
    assert ui.folder != first_folder
    assert ui.samples[-1].heat_w == 40
    ui.close()


def test_queue_selection(root):
    queue = TestQueue(root)
    queue.rerun_selected()
    queue.add("check", Mock())
    queue.items.selection_set(0)
    queue.rerun_selected()
    retry = Mock()
    queue.add("trial", Mock(), retry)
    queue.items.selection_clear(0, "end")
    queue.items.selection_set(1)
    queue.rerun_selected()
    retry.assert_called_once()


def test_live_queue_after_check(root, tmp_path):
    panel = OpenTDPanel(root, tmp_path)
    drawing = tmp_path / "test.dwg"
    drawing.touch()
    for key, value in {"drawing": str(drawing), "case": "Case", "node": "MAIN.1"}.items():
        panel.values[key].set(value)
    with patch("frontend.opentd_panel.Thread") as thread:
        panel.check()
        panel.start(Mock())
        panel.run(True)
        assert len(panel.jobs.pending) == 1
        panel.events.put(("done", "installed"))
        panel.poll()
        assert thread.call_count == 2
        panel.jobs.items.selection_set(1)
        panel.jobs.rerun_selected()
        assert len(panel.jobs.pending) == 1
    panel.close()


def test_queued_missing_input_continues(root):
    queue = TestQueue(root)
    queue.add("deleted source", Mock(side_effect=ValueError("File missing")))
    assert "File missing" in queue.items.get(0)
    next_job = Mock()
    queue.add("next", next_job)
    next_job.assert_called_once()
