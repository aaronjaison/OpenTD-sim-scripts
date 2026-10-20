"""Verify validation and compare integration with independent analytic solutions."""
from dataclasses import replace
import math
from threading import Event
import pytest
from backend.config import TrialConfig, from_fields
from backend.solver import solve, Cancelled


@pytest.mark.parametrize("field,value", [("mass",0),("specific_heat",-1),("initial",0),
    ("ambient",0),("duration",-1),("step",0),("area",-1),("convection",-1),
    ("emissivity",1.1),("emissivity",-0.1),("mass",math.nan),("step",math.inf),
    ("step",601),("step",0.000001)])
def test_invalid_parameters(field,value):
    with pytest.raises(ValueError):
        replace(TrialConfig(),**{field:value}).validate()


def test_models_and_conversion(tmp_path):
    model=tmp_path/'part.SLDPRT';model.write_bytes(b'CAD reference')
    assert from_fields({'model':str(model),'mass':'2','heat':'10'}).mass == 2
    assembly=tmp_path/'part.SLDASM';assembly.touch()
    TrialConfig(model=str(assembly)).validate()
    for path in [tmp_path/'missing.SLDPRT',tmp_path/'bad.txt']:
        with pytest.raises(ValueError):TrialConfig(model=str(path)).validate()
    with pytest.raises(ValueError):from_fields({'mass':'bad'})


def test_adiabatic_heating_and_partial_step():
    config=TrialConfig(mass=2,specific_heat=100,area=0,heat='20',duration=10,step=3)
    rows=solve(config,Event(),lambda _:None)
    assert [s.time_s for s in rows] == [0,3,6,9,10]
    assert rows[-1].temperature_k == pytest.approx(config.initial+1)


def test_convection_matches_closed_form():
    config=TrialConfig(initial=350,ambient=290,emissivity=0,heat='0',duration=120)
    rows=solve(config,Event(),lambda _:None)
    expected=290+60*math.exp(-config.convection*config.area*120/(config.mass*config.specific_heat))
    assert rows[-1].temperature_k == pytest.approx(expected,abs=1e-8)


def test_variable_heat_and_radiation_convergence():
    config=TrialConfig(area=0,heat='2*t',duration=10,step=0.5)
    assert solve(config,Event(),lambda _:None)[-1].temperature_k == pytest.approx(config.initial+100/900)
    radiating=TrialConfig(initial=400,heat='0',convection=0,step=4)
    coarse=solve(radiating,Event(),lambda _:None)
    fine=solve(replace(radiating,step=0.5),Event(),lambda _:None)
    assert fine[-1].temperature_k < 400
    assert coarse[-1].temperature_k == pytest.approx(fine[-1].temperature_k,abs=1e-5)


def test_cancel_and_unstable_steps():
    event=Event();event.set()
    with pytest.raises(Cancelled):solve(TrialConfig(),event,lambda _:None)
    for config in [TrialConfig(mass=1e-12,heat='-100'),TrialConfig(initial=10001),
                   TrialConfig(mass=1e-300,specific_heat=1e-300)]:
        with pytest.raises((ValueError,ZeroDivisionError)):
            solve(config,Event(),lambda _:None)


def test_large_run_progress_is_bounded():
    events=[]
    solve(TrialConfig(duration=1000),Event(),events.append)
    assert len(events)==100
