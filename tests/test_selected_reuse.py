"""Persisted cache identities normalize the immutable selected-setting snapshot."""
from dataclasses import asdict, replace
from unittest.mock import Mock
from backend.reuse import reuse_or_run
from backend.opentd_trials import OpenTDRequest
from backend.sim_settings import SimulationSettings
from backend.config import TrialConfig
from backend.results_interp import save_results
from backend.solver import Sample


def test_selected_override_reuses_and_changed_selection_does_not(tmp_path):
    drawing = tmp_path / "model.dwg"
    drawing.write_bytes(b"drawing")
    request = OpenTDRequest(str(drawing), "Case", "MAIN.1", settings=SimulationSettings(selected=("duration",)))
    samples = [Sample(0, 300, None)]
    def run():
        folder = save_results(TrialConfig(model=str(drawing)), samples, tmp_path,
                              "OpenTD prepared-case result", configuration=asdict(request))
        return samples, folder
    operation = Mock(side_effect=run)
    first = reuse_or_run(request, tmp_path, operation, Mock())
    assert reuse_or_run(request, tmp_path, operation, Mock()) == first
    assert operation.call_count == 1
    changed = replace(request, settings=replace(request.settings, selected=("output",)))
    assert reuse_or_run(changed, tmp_path, operation, Mock())[1] != first[1]
    assert operation.call_count == 2
