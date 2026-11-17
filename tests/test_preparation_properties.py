"""Private database seeding, shell/solid/skin assignment and supported limits."""
from types import SimpleNamespace as NS
from unittest.mock import Mock
import sys
import pytest
from preparation_fakes import Dim, NetList
from backend.preparation.properties import assign, databases


def shell():
    return NS(TopMaterial='',BotMaterial='',TopBotMaterial='',TopThickness=Dim(),BotThickness=Dim(),
        UseTopMaterialStack=0,UseBotMaterialStack=0,UseTopMLI=0,UseBotMLI=0,AnalysisGroups=NetList(),Update=Mock())


def test_materials_and_variants(tmp_path,monkeypatch):
    d=Mock();d.CreateThermoProps.return_value=NS(Density=Dim(),Conductivity=Dim(),SpecificHeat=Dim(),Update=Mock())
    d.CreateOpticalProps.return_value=Mock()
    active=NS(BOTH='both');outside=NS(OUTSIDE='outside')
    api=NS(UnitsData=Mock,RadCAD=NS(AnalysisGroupSurfaceInfo=lambda g,a:(g,a),RcEntityData=NS(Active=active),
           FdSolid=NS(AnalysisGroupSolidInfo=lambda g,a,f:(g,a,f),RcFdSolidData=NS(Active=outside))))
    array=Mock();array.__getitem__=Mock(return_value=lambda values:values)
    monkeypatch.setitem(sys.modules,'System',NS(Array=array,Int32=int))
    s=shell();s.TopThicknessExp=NS(Value="old");s.DensityMult=2;s.DensityMultExp=NS(Value="old");s.GenerateCCDataExp=NS(Value="0")
    solid=NS(ThermoMaterial='',GenerateCondCapExp=NS(Value='0'),OutsideOpticalProperties=['',''],InsideOpticalProperties=['',''],AnalysisGroups=NetList(),Update=Mock())
    volume=NS(ThermoMaterial='',Update=Mock())
    part={'name':'Shell','handles':['a','b','c'],'density':2700,'conductivity':205,'cp':900,'thickness':.001,'alpha':.2,'epsilon':.8,'skin':False}
    assign(d,api,{'a':s,'b':solid,'c':volume},[part],'GROUP')
    assert s.TopThicknessExp.Value=='' and s.DensityMult==1 and s.DensityMultExp.Value=='' and s.GenerateCCDataExp.Value==''
    assert s.TopThickness.GetValueSI()==.001 and s.BotThickness.GetValueSI()==0
    assert solid.OutsideOpticalProperties==['PREP_Shell']*2
    for field in ('UseTopMaterialStack','UseBotMaterialStack','UseTopMLI','UseBotMLI'):
        setattr(s,field,1)
        with pytest.raises(ValueError,match='Layer'):assign(d,api,{'a':s},[dict(part,handles=['a'])],'G')
        setattr(s,field,0)
    with pytest.raises(ValueError,match='skins'):assign(d,api,{'b':solid},[dict(part,handles=['b'],skin=True)],'G')
    with pytest.raises(ValueError,match='exterior'):assign(d,api,{'c':volume},[dict(part,handles=['c'])],'G')
    assign(d,api,{'a':s},[dict(part,handles=['a'],skin=True)],'G')
    assert s.GenerateCCData==0
    assign(d,api,{'fresh':shell()},[dict(part,handles=['fresh'])],'G')
    old=tmp_path/'old.tdp';old.write_bytes(b'original')
    d.GetThermoPropDBPathname.return_value=str(old);d.GetOpticalPropDBPathname.return_value=str(tmp_path/'missing.rco')
    databases(d,tmp_path)
    assert (tmp_path/'prep-materials.tdp').read_bytes()==b'original'
    assert 'UNICODE' in (tmp_path/'prep-optics.rco').read_text(encoding='utf-8-sig')
