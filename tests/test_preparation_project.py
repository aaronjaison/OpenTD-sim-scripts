"""SI recipe validation, mapping coverage, stale mesh and editable draft storage."""
from copy import deepcopy
from dataclasses import replace
import json
import pytest
from backend.preparation.geometry import MeshCatalog
from backend.preparation.project import validate, source_file, number, save_recipe, load_recipe


@pytest.fixture
def recipe(tmp_path):
    source=tmp_path/'raw.SLDASM';source.touch()
    mesh=tmp_path/'mesh.dwg';mesh.touch()
    cat=MeshCatalog(str(mesh), (("a","Rectangle","body",""),), ("MAIN.1","MAIN.2"), 0, ("orbit",))
    r={"source":str(source),"mesh":str(mesh),"case":"Baseline", "parts":[{"name":"Shell","handles":["a"],"density":2700,"conductivity":205,"cp":900,"thickness":.001,"alpha":.2,"epsilon":.8,"skin":False}],"loads":[{"node":"MAIN.1","watts":1}],"contacts":[{"from":"MAIN.1","to":"MAIN.2","conductance":.5}],"environment":{"initial":293,"space":3,"duration":10,"output":1,"max_step":.1,"mode":"Deep space","orbit":""}}
    return r,cat


def test_valid_recipe_and_storage(recipe,tmp_path):
    r,cat=recipe
    assert validate(r,cat) is r
    r['environment'].update(mode='Existing orbit',orbit='orbit');validate(r,cat)
    skin=deepcopy(r);skin["parts"][0].update(thickness=0,skin=True);validate(skin,cat)
    solid=replace(cat,entities=(("a","SolidBrick","body",""),));skin["parts"][0]["skin"]=False;validate(skin,solid)
    path=tmp_path/'project.json';save_recipe(path,r);assert load_recipe(path)==r
    path.write_text('{"schema":2,"recipe":{}}')
    with pytest.raises(ValueError):load_recipe(path)
    path.write_text('{"schema":1,"recipe":[]}')
    with pytest.raises(ValueError):load_recipe(path)
    with pytest.raises(ValueError):source_file(tmp_path/'missing.dwg')
    bad=tmp_path/'model.exe';bad.touch()
    with pytest.raises(ValueError):source_file(bad)
    for value in (-1,float('nan'),float('inf'),0):
        with pytest.raises(ValueError):number(value,'input',positive=True)
    with pytest.raises(ValueError):number(-1,'input')


@pytest.mark.parametrize('kind',['mesh','hash','case','name','duplicate','empty','repeat_handle','overlap','unassigned','extra','density','alpha','load_node','power','self','contact_node','duplicate_contact','conductance','duration','output','mode','orbit'])
def test_bad_recipe(recipe,kind):
    r,cat=recipe;r=deepcopy(r)
    part=r['parts'][0];env=r['environment']
    if kind=='mesh':r['mesh']='other.dwg'
    if kind=='hash':r['mesh_sha256']='stale'
    if kind=='case':r['case']='bad case'
    if kind=='name':part['name']='1bad'
    if kind=='duplicate':r['parts'].append(deepcopy(part))
    if kind=='empty':part['handles']=[]
    if kind=='repeat_handle':part['handles']=['a','a']
    if kind=='overlap':r['parts'].append(dict(part,name='Other'))
    if kind=='unassigned':r['parts']=[]
    if kind=='extra':part['handles']=['b']
    if kind=='density':part['density']=0
    if kind=='alpha':part['alpha']=2
    if kind=='load_node':r['loads'][0]['node']='SPACE.1'
    if kind=='power':r['loads'][0]['watts']=-1
    if kind=='self':r['contacts'][0]['to']='MAIN.1'
    if kind=='contact_node':r['contacts'][0]['to']='SPACE.1'
    if kind=='duplicate_contact':r['contacts']*=2
    if kind=='conductance':r['contacts'][0]['conductance']=0
    if kind=='duration':env['duration']=0
    if kind=='output':env['output']=20
    if kind=='mode':env['mode']='other'
    if kind=='orbit':env.update(mode='Existing orbit',orbit='missing')
    with pytest.raises(ValueError):validate(r,cat)
