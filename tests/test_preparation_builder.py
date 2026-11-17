"""Meshed-input gating, cleanup on failure and prepared-copy publication."""
from types import SimpleNamespace as NS
from unittest.mock import Mock
from pathlib import Path
import json
import pytest
from backend.preparation import geometry as g,builder as b


def test_inspect_mesh(tmp_path,monkeypatch):
    source=tmp_path/'mesh.dwg';source.write_bytes(b'model')
    obj=NS(Handle='h',TypeName='Rectangle',Layer='Shell',Comment='part')
    d=Mock()
    for kind in g.GETTERS:getattr(d,'Get'+kind).return_value=[]
    d.GetRectangles.return_value=[obj]
    d.GetNodes.return_value=[NS(Submodel='MAIN',Id=1,NodeType='DIFFUSION'),NS(Submodel='SPACE',Id=1,NodeType='BOUNDARY')]
    d.GetHeatLoads.return_value=[];d.GetOrbits.return_value=[NS(Name='orbit')]
    monkeypatch.setattr(g.open_td_api,'connect',lambda _:d)
    cat=g.inspect_mesh(source,tmp_path)
    assert cat.nodes==('MAIN.1',) and cat.orbits==('orbit',) and cat.fingerprint
    d.GetRectangles.return_value=[]
    with pytest.raises(ValueError,match='geometry only'):g.inspect_mesh(source,tmp_path)
    d.GetRectangles.return_value=[obj];d.GetNodes.return_value=[]
    with pytest.raises(ValueError):g.inspect_mesh(source,tmp_path)
    assert d.Quit.call_count==3


def test_build_publish_and_failure(tmp_path,monkeypatch):
    source=tmp_path/'source.dwg';source.write_bytes(b'model')
    catalog=g.MeshCatalog(str(source),(('a','Rectangle','Shell',''),),('MAIN.1',),0)
    d=Mock();d.GetNodes.return_value=[NS(Submodel='MAIN',Id=1,NodeType='DIFFUSION'),NS(Submodel='SPACE',Id=1,NodeType='BOUNDARY')]
    monkeypatch.setattr(b,'inspect_mesh',lambda *_:catalog)
    monkeypatch.setattr(b,'validate',lambda *_:None)
    monkeypatch.setattr(b.open_td_api,'connect',lambda _:d)
    monkeypatch.setattr(b.open_td_api,'load_api',Mock())
    for name in ('databases','assign','loads_and_contacts','case_and_environment'):monkeypatch.setattr(b,name,Mock())
    monkeypatch.setattr(b,'entities',lambda _:{'a':Mock()})
    recipe={'source':str(source),'mesh':str(source),'case':'Base','parts':[]}
    result=b.build(recipe,tmp_path)
    assert Path(result.drawing).read_bytes()==b'model' and source.read_bytes()==b'model'
    assert json.loads(Path(result.report).read_text())['status'].startswith('Model authored')
    monkeypatch.setattr(b,'entities',lambda _:{})
    with pytest.raises(ValueError,match='changed'):b.build(recipe,tmp_path)
    assert d.Quit.call_count==2
