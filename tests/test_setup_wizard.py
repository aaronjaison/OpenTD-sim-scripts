"""Isolated preparation, failure cleanup, optical copies and connection receipts."""
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock
import json
import pytest
from backend import setup_wizard as w
from backend.sim_settings import SimulationSettings


class NetList(list):
    def Add(self, value): self.append(value)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    source = tmp_path / "model.dwg"; source.write_bytes(b"original")
    optics = tmp_path / "source.rco"; optics.write_bytes(b"optical")
    (tmp_path / "TdThermo.tdp").write_bytes(b"material")
    case = Mock(OpticOverride=0, OpticFilename=str(optics), SymbolNames=NetList(["SIM_DURATION_S"]), SymbolValues=NetList(["5"]))
    d = Mock(); d.GetCaseSet.return_value = case; d.GetOpticalPropDBPathname.return_value = str(optics)
    d.GetSymbols.return_value = [NS(Name="SIM_DURATION_S", Value="5", Update=Mock())]
    monkeypatch.setattr(w.open_td_api, "connect", Mock(return_value=d))
    monkeypatch.setattr(w.open_td_api, "load_api", Mock())
    monkeypatch.setattr(w, "catalog", lambda *_: {"nodes": [], "loads": [], "optics": []})
    monkeypatch.setattr(w, "connect_targets", Mock(return_value=[("control", "timendExp", "SIM_DURATION_S")]))
    monkeypatch.setattr(w, "verify_targets", Mock())
    return source, optics, case, d


def test_prepare_and_inspect(setup, tmp_path):
    source, optics, case, d = setup
    cat = w.inspect_setup(str(source), "Case", "", tmp_path, optical_database=str(optics))
    assert cat.targets["optical_database"] == str(optics)
    assert cat.targets["nodes"] == [] and optics.read_bytes() == b"optical"
    case.OpticOverride = 0
    result = w.prepare_setup(source, "Case", "G", SimulationSettings(duration=100, selected=("duration",)), tmp_path)
    record = json.loads(Path(result.report).read_text())
    assert record["parameters"] == {"SIM_DURATION_S": "100"}
    assert case.SymbolValues == ["100"] and source.read_bytes() == b"original"
    assert Path(result.drawing).with_name("TdThermo.tdp").read_bytes() == b"material"
    w.verify_targets.assert_called_once()
    assert d.Quit.call_count == 2
    w.inspect_setup(source, "Case", "", tmp_path, include_optics=False)
    case.OpticOverride = 1; case.OpticFilename = str(optics)
    result = w.prepare_setup(source, "Case", "", SimulationSettings(selected=("emissivity",)), tmp_path, coating="VED", optical_database=str(optics))
    assert Path(result.drawing).with_name("setup-optics.rco").read_bytes() == b"optical"
    assert case.CalculateRadiation == 1
    assert d.CreateSymbol.call_count == 1


def test_failures_close_and_dont_publish(setup, tmp_path, monkeypatch):
    source, optics, case, d = setup
    with pytest.raises(ValueError, match="basic"):
        w.prepare_setup(source, "Case", "", SimulationSettings(orbital=True), tmp_path)
    d.GetCaseSet.side_effect = RuntimeError("unavailable")
    with pytest.raises(RuntimeError): w.inspect_setup(source, "Case", "", tmp_path)
    with pytest.raises(RuntimeError): w.prepare_setup(source, "Case", "", SimulationSettings(selected=("duration",)), tmp_path)
    assert d.Quit.call_count == 2
    d.GetCaseSet.side_effect = None
    monkeypatch.setattr(w, "verify_targets", Mock(side_effect=RuntimeError("readback")))
    with pytest.raises(RuntimeError): w.prepare_setup(source, "Case", "", SimulationSettings(selected=("duration",)), tmp_path)
    assert not list(tmp_path.glob("opentd-setup-*/connections.json"))


def test_optical_paths(setup, tmp_path):
    _, optics, case, d = setup
    case.OpticOverride = 1
    case.OpticFilename = "relative.rco"
    with pytest.raises(ValueError, match="absolute"): w.local_optics(d, case, tmp_path / "new.dwg")
    case.OpticFilename = str(tmp_path / "missing.rco")
    with pytest.raises(ValueError, match="Missing"): w.local_optics(d, case, tmp_path / "new.dwg")
