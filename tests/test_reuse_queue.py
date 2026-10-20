"""Verify reuse, forced reruns, source changes and FIFO snapshots."""
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock
import json
import os
import pytest
from backend.config import TrialConfig
from backend.reuse import identity, reuse_or_run, read_samples
from backend.main_processes import run_trial
from backend.opentd_trials import OpenTDRequest
from threading import Event
from frontend.test_queue import TestQueue


def test_reuse_force_and_config(tmp_path):
    config = TrialConfig(duration=2)
    progress = Mock()
    operation = Mock(side_effect=lambda: run_trial(config, tmp_path, Event(), progress))
    first = reuse_or_run(config, tmp_path, operation, progress)
    assert reuse_or_run(config, tmp_path, operation, progress) == first
    assert operation.call_count == 1
    fresh = reuse_or_run(config, tmp_path, operation, progress, True)
    assert fresh[1] != first[1]
    assert reuse_or_run(config, tmp_path, operation, progress) == fresh
    reuse_or_run(replace(config, heat="30"), tmp_path, operation, progress)
    assert operation.call_count == 3


def test_files_and_legacy(tmp_path):
    source = tmp_path / "part.SLDPRT"
    source.write_text("first")
    config = TrialConfig(model=str(source), duration=2)
    progress = Mock()
    operation = lambda: run_trial(config, tmp_path, Event(), progress)
    first = reuse_or_run(config, tmp_path, operation, progress)
    (first[1] / "reuse.json").unlink()
    assert reuse_or_run(config, tmp_path, operation, progress) == first
    os.utime(source, (2000000000, 2000000000))
    second = reuse_or_run(config, tmp_path, operation, progress)
    assert second[1] != first[1]
    source.write_text("changed")
    assert reuse_or_run(config, tmp_path, operation, progress)[1] != second[1]
    drawing = tmp_path / "model.dwg"
    drawing.touch()
    assert len(identity(OpenTDRequest(str(drawing), "Case", "MAIN.1"))["files"]) == 1


@pytest.mark.parametrize("damage", ["receipt", "missing", "csv", "empty", "nan", "key"])
def test_corrupt_cache_runs_again(tmp_path, damage):
    config = TrialConfig(duration=2)
    operation = lambda: run_trial(config, tmp_path, Event(), lambda _: None)
    _, folder = reuse_or_run(config, tmp_path, operation, lambda _: None)
    if damage == "receipt":
        (folder / "reuse.json").write_text("bad json")
    elif damage == "missing":
        (folder / "report.md").unlink()
    else:
        text = {"csv": "time_s,temperature_k,heat_w\nwrong,2,3\n",
                "empty": "time_s,temperature_k,heat_w\n",
                "nan": "time_s,temperature_k,heat_w\n0,nan,\n",
                "key": "other\n1\n"}[damage]
        (folder / "results.csv").write_text(text)
    assert reuse_or_run(config, tmp_path, operation, lambda _: None)[1] != folder


def test_blank_heat_and_queue(root, tmp_path):
    (tmp_path / "results.csv").write_text("time_s,temperature_k,heat_w\n0,300,\n")
    assert read_samples(tmp_path)[0].heat_w is None
    jobs = TestQueue(root)
    first, second, third = Mock(), Mock(), Mock()
    jobs.add("first", first)
    jobs.add("second", second)
    jobs.add("third", third)
    first.assert_called_once()
    second.assert_not_called()
    jobs.finish("done")
    jobs.pump()
    second.assert_called_once()
    jobs.clear()
    jobs.finish("error")
    jobs.finish("error")
    jobs.pump()
    third.assert_not_called()
    assert jobs.items.get(0).startswith("done")
    assert jobs.items.get(2).startswith("Removed")


def test_live_results_reuse_without_launch(tmp_path):
    from dataclasses import asdict
    from backend.results_interp import save_results
    from backend.solver import Sample
    drawing = tmp_path / "live.dwg"
    drawing.write_bytes(b"drawing")
    database = tmp_path / "TdThermo.tdp"
    database.write_bytes(b"materials")
    request = OpenTDRequest(str(drawing), "Case", "MAIN.1")
    samples = [Sample(0, 318.15, None)]
    def run():
        folder = save_results(TrialConfig(model=str(drawing)), samples, tmp_path,
                              "OpenTD prepared-case result", configuration=asdict(request))
        return samples, folder
    launch = Mock(side_effect=run)
    original = reuse_or_run(request, tmp_path, launch, Mock())
    assert reuse_or_run(request, tmp_path, launch, Mock()) == original
    assert launch.call_count == 1
    database.write_bytes(b"changed materials")
    assert reuse_or_run(request, tmp_path, launch, Mock())[1] != original[1]
    assert launch.call_count == 2
