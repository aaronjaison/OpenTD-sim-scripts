"""Simulation contract validation, vendor application and compact GUI behavior."""
from dataclasses import replace
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import pytest
from backend.sim_settings import SimulationSettings, SYMBOLS, apply_settings
from backend.opentd_trials import OpenTDRequest, run_prepared
from frontend.sim_form import SimulationForm
from frontend.tooltips import Tooltip
from tkinter import ttk


@pytest.mark.parametrize("change", [{"initial": float("nan")}, {"initial": 0}, {"heat": -1},
    {"emissivity": 2}, {"cycles": 1.5}, {"cycles": -1}, {"cycles": 1}, {"altitude": -1},
    {"inclination": 181}, {"beta": 91}, {"output": 4000}, {"max_step": 4000},
    {"cycles": 1e308, "period": 1e308, "orbital": True}])
def test_bad_settings(change):
    with pytest.raises(ValueError): replace(SimulationSettings(), **change).parameters()


def test_parameters_and_application():
    settings = SimulationSettings(cycles=5, orbital=True)
    params = settings.parameters()
    assert float(params["SIM_DURATION_S"]) == 27000
    desktop = Mock()
    desktop.GetSymbols.return_value = [NS(Name=name) for name in SYMBOLS.values()]
    case = Mock(RadiationTasks=[object()])
    assert apply_settings(desktop, case, settings) == params
    assert case.Transient == 1 and case.SteadyState == 0 and case.CalculateRadiation == 1
    assert len(apply_settings(desktop, case, SimulationSettings())) == 6
    case.RadiationTasks = []
    with pytest.raises(ValueError, match="RadCAD"): apply_settings(desktop, case, settings)
    desktop.GetSymbols.return_value = []
    with pytest.raises(ValueError, match="SIM_INITIAL_K"): apply_settings(desktop, case, settings)


def test_request_settings(tmp_path):
    drawing = tmp_path / "model.dwg"
    drawing.touch()
    request = OpenTDRequest(str(drawing), "Case", "MAIN.1", settings=SimulationSettings())
    assert request.validate() == request
    with pytest.raises(ValueError, match="conflict"):
        replace(request, overrides="sim_initial_k=280").validate()


def test_form_and_tooltip(root):
    form = SimulationForm(root)
    assert form.read() is None
    form.enabled.set(True)
    form.toggle()
    assert form.read() == SimulationSettings()
    form.values["heat"].set("60000")
    assert form.read().heat == 60000
    form.values["duration"].set("bad")
    with pytest.raises(ValueError): form.read()
    form.enabled.set(False)
    form.toggle()
    widget = ttk.Entry(root)
    tip = Tooltip(widget, "Explanation")
    tip.show()
    window = tip.window
    tip.show()
    assert tip.window is window
    tip.hide()
    tip.hide()
    assert tip.window is None


def test_live_settings_forwarding(tmp_path, monkeypatch):
    from backend import opentd_trials as trials
    from pathlib import Path
    class NetList(list):
        def Add(self, item): self.append(item)
    drawing = tmp_path / "model.dwg"
    drawing.touch()
    case = Mock(SymbolNames=NetList(), SymbolValues=NetList(), SymbolComments=NetList())
    case.Run.side_effect = lambda: (Path(case.UserDirectory) / "trial.sav").touch()
    desktop = Mock()
    desktop.GetCaseSet.return_value = case
    desktop.GetSymbols.return_value = [NS(Name=name) for name in SYMBOLS.values()]
    monkeypatch.setattr(trials.open_td_api, "connect", lambda _: desktop)
    monkeypatch.setattr(trials, "prepare_toolchain", Mock())
    monkeypatch.setattr(trials.open_td_api, "read_temperatures", lambda *_: ([0], [293]))
    request = OpenTDRequest(str(drawing), "Case", "MAIN.1", settings=SimulationSettings())
    _, folder = run_prepared(request, tmp_path, Mock())
    assert "SIM_OUTPUT_S" in case.SymbolNames
    assert case.Transient == 1
    assert 'SIM_INITIAL_K' in (folder / 'config.json').read_text()
