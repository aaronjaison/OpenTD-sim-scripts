"""Verify all-node statistics, exports, invalid histories and atomic publication."""
from dataclasses import replace, asdict
from pathlib import Path
from unittest.mock import Mock
import csv
import json
import pytest
from backend import opentd_trials as trials
from backend.node_results import ALL_NODES, summarize, mean_samples, write_node_files
from backend.results_interp import save_results
from backend.config import TrialConfig
from backend.reuse import reuse_or_run


def test_statistics_and_report(tmp_path):
    times = [0, 2, 5]
    histories = {"MAIN.1": [300, 310, 320], "MAIN.2": [280, 300, 310]}
    summary = summarize(times, histories)
    assert summary == [(0, 290, 280, 300, 2), (2, 305, 300, 310, 2), (5, 315, 310, 320, 2)]
    folder = save_results(TrialConfig(), mean_samples(summary), tmp_path,
        artifacts=lambda folder: write_node_files(folder, times, histories, summary))
    with (folder / "nodes.csv").open() as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == ["time_s", "MAIN.1_temperature_k", "MAIN.2_temperature_k"]
    assert rows[-1] == ["5", "320", "310"]
    assert "including boundary nodes" in (folder / "report.md").read_text()
    assert "315.0" in (folder / "node_summary.csv").read_text()
    assert summarize([0], {"BOUND.1": [293]}) == [(0, 293, 293, 293, 1)]


@pytest.mark.parametrize("times,histories", [([], {}), ([0], {}),
    ([float("nan")], {"A.1": [3]}), ([1, 0], {"A.1": [3, 4]}),
    ([0, 0], {"A.1": [3, 4]}), ([0, 1], {"A.1": [3]}),
    ([0], {"A.1": [float("inf")]})])
def test_invalid_history(times, histories):
    with pytest.raises(ValueError):
        summarize(times, histories)


def test_all_node_trial_and_reuse(tmp_path, monkeypatch):
    source = tmp_path / "model.dwg"
    source.touch()
    request = trials.OpenTDRequest(str(source), "Case", ALL_NODES)
    assert request.validate() == request
    case = Mock()
    case.Run.side_effect = lambda: (Path(case.UserDirectory) / "trial.sav").touch()
    desktop = Mock()
    desktop.GetCaseSet.return_value = case
    monkeypatch.setattr(trials, "prepare_toolchain", Mock())
    monkeypatch.setattr(trials.open_td_api, "connect", Mock(return_value=desktop))
    reader = Mock(return_value=([0, 1], {"A.1": [280, 290], "B.2": [300, 320]}))
    monkeypatch.setattr(trials.open_td_api, "read_all_temperatures", reader)
    operation = Mock(side_effect=lambda: trials.run_prepared(request, tmp_path, Mock()))
    samples, folder = reuse_or_run(request, tmp_path, operation, Mock())
    assert [s.temperature_k for s in samples] == [290, 305]
    case.Run.assert_called_once()
    details = json.loads((folder / "config.json").read_text())
    assert details["metadata"]["node_count"] == 2
    assert details["config"]["node"] == ALL_NODES
    assert "mean temperature" in details["engine"]
    assert reuse_or_run(request, tmp_path, operation, Mock())[1] == folder
    assert operation.call_count == 1
    (folder / "nodes.csv").unlink()
    assert reuse_or_run(request, tmp_path, operation, Mock())[1] != folder
    assert operation.call_count == 2


def test_artifact_failure_does_not_publish(tmp_path):
    samples = mean_samples(summarize([0], {"A.1": [300]}))
    with pytest.raises(OSError):
        save_results(TrialConfig(), samples, tmp_path, artifacts=Mock(side_effect=OSError("disk full")))
    assert not list(tmp_path.glob("*/report.md"))
    assert not list(tmp_path.glob(".pending-*"))
