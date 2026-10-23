"""Exercise queued UI snapshots, retry selection and serial advancement."""
from unittest.mock import Mock, patch
from frontend.interface import Application
from frontend.connections import Connections
from frontend.opentd_panel import OpenTDPanel
from frontend.test_queue import TestQueue


def test_dwg_queue_snapshots(root, tmp_path):
    from backend.solver import Sample
    ui = Application(root, Connections(tmp_path))
    panel = ui.opentd
    drawing = tmp_path / "model.dwg"
    drawing.touch()
    for key, value in {"drawing": str(drawing), "case": "Case", "node": "MAIN.1"}.items():
        panel.values[key].set(value)
    panel.simulation.enabled.set(True)
    panel.simulation.values["heat"].set("12000")
    with patch("frontend.opentd_panel.Thread") as thread:
        panel.run()
        first = thread.call_args.kwargs["args"][0]
        panel.simulation.values["heat"].set("60000")
        panel.run()
        assert len(panel.jobs.pending) == 1
        captured = []
        def runner(request, output, progress):
            captured.append(request.settings.heat)
            return [Sample(0, 300, None)], tmp_path
        with patch("frontend.opentd_panel.run_prepared", runner):
            panel.work(first)
            panel.poll()
            second = thread.call_args.kwargs["args"][0]
            panel.work(second)
            panel.poll()
        assert captured == [12000, 60000]
        panel.jobs.items.selection_set(0)
        panel.jobs.rerun_selected()
        with patch("frontend.opentd_panel.run_prepared", runner):
            panel.work(thread.call_args.kwargs["args"][0])
            panel.poll()
        assert captured[-1] == 12000
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
