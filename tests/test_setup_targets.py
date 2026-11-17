"""Target validation, shared identities, expression units and persisted readback."""
from types import SimpleNamespace as NS
from unittest.mock import Mock
import pytest
from backend.setup_targets import catalog, connect_targets, verify_targets, eligible_heat
from backend.sim_settings import SimulationSettings, apply_settings


@pytest.fixture
def model():
    def exp(value=""): return NS(Value=value, unitsType="unit")
    nodes = [NS(Submodel="MAIN", Id=1, Handle=h, NodeType="DIFFUSION", UseVersusTime=0,
                InitialTempExp=exp(), Update=Mock()) for h in ("a", "b")]
    loads = [NS(Handle="h", Name="battery", Type="LOAD", HeatLoadTransientType="CONSTANT_HEAT_LOAD",
                ValueExp=exp(), Update=Mock())]
    optic = NS(Name="VED", VarIrEmis=0, TempIrEmis=0, UseWaveLengthDepProps=0, emisExp=exp(), Update=Mock())
    control = NS(**{k: exp() for k in ("timendExp", "outputExp", "dtimehExp")})
    case = NS(SindaControl=control, UseRestartFile=0, RestartCase=0)
    desktop = Mock()
    desktop.GetNodes.return_value = nodes
    desktop.GetHeatLoads.return_value = loads
    desktop.GetOpticalPropss.return_value = [optic]
    desktop.GetOpticalProps.return_value = optic
    desktop.GetNode.side_effect = lambda handle: next(n for n in nodes if n.Handle == handle)
    desktop.GetHeatLoad.return_value = loads[0]
    api = NS(UnitsData=Mock, ExpressionData=lambda value, units: exp(value))
    return desktop, case, api, nodes, loads, optic


def test_connections_and_catalog(model):
    d, c, api, nodes, loads, optic = model
    assert catalog(d) == {"nodes": ["MAIN.1"], "loads": [("h", "battery", "LOAD")], "optics": ["VED"]}
    assert catalog(d, False)["optics"] == []
    records = connect_targets(d, c, api, SimulationSettings().parameters(), ("MAIN.1",), "h", 2e-5, "VED")
    verify_targets(d, c, records)
    assert len(records) == 7 and all(n.UserOverride for n in nodes)
    assert loads[0].ValueExp.Value.startswith("SIM_BATTERY_QVOL*")
    loads[0].Type = "VOLUME"
    connect_targets(d, c, api, {"SIM_BATTERY_QVOL": "2"}, (), "h", 0, "")
    assert loads[0].ValueExp.Value == "SIM_BATTERY_QVOL"
    loads[0].HeatLoadTransientType = "TIME_VARY_HEAT_LOAD"
    assert not eligible_heat(loads[0])
    loads[0].HeatLoadTransientType = "CONSTANT_HEAT_LOAD"
    loads[0].Type = "FLUX"
    assert not eligible_heat(loads[0])
    verify_targets(d, c, [])
    c.SindaControl.timendExp.Value = "wrong"
    with pytest.raises(RuntimeError, match="persist"):
        verify_targets(d, c, [("control", "timendExp", "SIM_DURATION_S")])


@pytest.mark.parametrize("change", ["restart", "restart_case", "empty", "missing", "boundary", "time"])
def test_initial_rejections(model, change):
    d, c, api, nodes, _, _ = model
    ids = ("MAIN.1",)
    if change == "restart": c.UseRestartFile = 1
    if change == "restart_case": c.RestartCase = 1
    if change == "empty": ids = ()
    if change == "missing": ids = ("MAIN.2",)
    if change == "boundary": nodes[1].NodeType = "BOUNDARY"
    if change == "time": nodes[1].UseVersusTime = 1
    with pytest.raises(ValueError): connect_targets(d, c, api, {"SIM_INITIAL_K": "293"}, ids, "", 0, "")


@pytest.mark.parametrize("volume", [0, -1, float("nan"), float("inf")])
def test_bad_volume(model, volume):
    d, c, api, *_ = model
    with pytest.raises(ValueError): connect_targets(d, c, api, {"SIM_BATTERY_QVOL": "1"}, (), "h", volume, "")


def test_heat_and_optical_rejections(model):
    d, c, api, _, _, optic = model
    with pytest.raises(ValueError): connect_targets(d, c, api, {"SIM_BATTERY_QVOL": "1"}, (), "bad", 1, "")
    for name in ("", "bad"):
        with pytest.raises(ValueError): connect_targets(d, c, api, {"SIM_VED_EPS": ".5"}, (), "", 0, name)
    for field in ("VarIrEmis", "TempIrEmis", "UseWaveLengthDepProps"):
        setattr(optic, field, 1)
        with pytest.raises(ValueError): connect_targets(d, c, api, {"SIM_VED_EPS": ".5"}, (), "", 0, "VED")
        setattr(optic, field, 0)


def test_partial_settings():
    s = SimulationSettings(duration=90, initial=float("nan"), heat=-1, selected=("duration",))
    assert s.parameters() == {"SIM_DURATION_S": "90"}
    d = Mock(); d.GetSymbols.return_value = [NS(Name="SIM_DURATION_S")]
    assert apply_settings(d, Mock(), s) == s.parameters()
    for selected in ((), ("bad",), ("heat", "heat")):
        with pytest.raises(ValueError): SimulationSettings(selected=selected).parameters()
    with pytest.raises(ValueError): SimulationSettings(selected=("period",)).parameters()
    with pytest.raises(ValueError): SimulationSettings(cycles=2, orbital=True, selected=("cycles",)).parameters()
    s = SimulationSettings(cycles=2, orbital=True, selected=("cycles", "period"))
    assert s.parameters()["SIM_DURATION_S"] == "10800"
