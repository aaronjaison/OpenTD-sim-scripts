"""Explicit baseline case, SI timing, nodal loading and boundaries."""
from types import SimpleNamespace as NS
from unittest.mock import Mock
import pytest
from preparation_fakes import vendor
from backend.preparation.environment import case_and_environment, loads_and_contacts


def test_case_and_loads(tmp_path):
    d,c,n,api=vendor()
    recipe={'case':'Baseline','environment':{'duration':10,'output':1,'max_step':.1,'initial':293,'space':3,'mode':'Deep space','orbit':''},'loads':[{'node':'MAIN.1','watts':2}], 'contacts':[{'from':'MAIN.1','to':'MAIN.2','conductance':.5}]}
    assert case_and_environment(d,api,recipe,{'MAIN.1':n},tmp_path) is c
    assert c.SindaControl.timendExp.Value=='SIM_DURATION_S'
    assert n.InitialTemp.GetValueSI()==293
    loads_and_contacts(d,api,recipe,{'MAIN.1':n,'MAIN.2':Mock()})
    assert d.CreateHeatLoad.return_value.Value==2
    assert d.CreateConductor.return_value.Value==.5
    symbol=NS(Name='SIM_DURATION_S',Value='',Update=Mock());d.GetSymbols.return_value=[symbol]
    recipe['environment'].update(mode='Existing orbit',orbit='orbit')
    case_and_environment(d,api,recipe,{},tmp_path)
    assert len(c.RadiationTasks)==3 and symbol.Value=='10'
    d.GetCaseSets.return_value=[NS(Name='Other',GroupName=''),NS(Name='Baseline',GroupName='G')]
    case_and_environment(d,api,recipe,{},tmp_path)
    d.GetCaseSets.return_value=[NS(Name='Baseline',GroupName='')]
    with pytest.raises(ValueError,match='new case'):case_and_environment(d,api,recipe,{},tmp_path)
    d.GetCaseSets.return_value=[]
    n.Submodel='PREP_SPACE'
    with pytest.raises(ValueError,match='PREP_SPACE'):case_and_environment(d,api,recipe,{},tmp_path)
    loads_and_contacts(d,api,{'loads':[],'contacts':[]},{})
