"""Real Tk material maps, contact/load forms and preparation draft roundtrips."""
import json
from pathlib import Path
from unittest.mock import Mock,patch
import pytest
from backend.preparation.geometry import MeshCatalog
from frontend.preparation.dialog import PreparationDialog
from frontend.preparation.forms import remove_selected


@pytest.fixture
def ui(root,tmp_path):
    dialog=PreparationDialog(root,Mock(),Mock())
    source=tmp_path/'raw.sldprt';source.touch();mesh=tmp_path/'mesh.dwg';mesh.touch()
    dialog.source.set(str(source));dialog.mesh.set(str(mesh))
    cat=MeshCatalog(str(mesh),(('a','Rectangle','Shell',''),),('MAIN.1','MAIN.2'),0,('orbit',),'hash')
    yield dialog,cat
    if dialog.window.winfo_exists():dialog.window.destroy()


def test_assignments_and_network(ui):
    dialog,cat=ui;m=dialog.materials;n=dialog.network
    assert 'Inspected' in dialog.accept(cat)
    with patch('frontend.preparation.materials.messagebox.showerror') as error:
        m.add();assert error.call_count==1
        m.geometry.selection_set(0);m.add();assert error.call_count==2
        values={'name':'Shell','density':2700,'conductivity':205,'cp':900,'thickness':.001,'alpha':.2,'epsilon':.8}
        for key,value in values.items():m.values[key].set(value)
        m.add();assert len(m.parts)==1
        m.add();assert error.call_count==3
    n.from_node.set('MAIN.1');n.to_node.set('MAIN.2');n.load_node.set('MAIN.1')
    with patch('frontend.preparation.network.messagebox.showerror') as error:
        n.contact();n.load();assert error.call_count==2
    n.conductance.set('.5');n.power.set('2');n.contact();n.load()
    assert len(n.loads)==len(n.contacts)==1
    recipe=dialog.recipe();assert recipe['parts'][0]['handles']==['a']
    dialog.build();dialog.submit.assert_called_once()
    m.assigned.selection_set(0);remove_selected(m.assigned,m.parts);assert not m.parts
    remove_selected(m.assigned,m.parts)
    with patch('frontend.preparation.dialog.messagebox.showerror') as error:
        dialog.build();assert error.call_count==1
    assert 'ignored' in dialog.accept(MeshCatalog('different.dwg',(),(),0))
    dialog.materials.parts=[values]
    dialog.accept(MeshCatalog(cat.drawing,cat.entities,cat.nodes,0,(),'newhash'))
    assert not dialog.materials.parts and not dialog.network.loads


def test_sources_and_drafts(ui,tmp_path):
    dialog,cat=ui
    with patch('frontend.preparation.dialog.messagebox.showerror') as error:
        dialog.build();assert error.call_count==1
        dialog.source.set('missing.sldprt');dialog.scan();assert error.call_count==2
    source=tmp_path/'raw.sldprt';dialog.source.set(str(source));dialog.scan()
    dialog.inspect.assert_called_once_with(cat.drawing)
    with patch('frontend.preparation.dialog.filedialog.askopenfilename',side_effect=['','chosen.dwg']):
        dialog.choose(dialog.mesh,[]);dialog.choose(dialog.mesh,[])
    assert dialog.mesh.get()=='chosen.dwg';dialog.mesh.set(cat.drawing)
    path=tmp_path/'project.json'
    with patch('frontend.preparation.dialog.filedialog.asksaveasfilename',side_effect=['',str(path)]):
        dialog.save();dialog.save()
    dialog.source.set('changed');dialog.environment.values['initial'].set('99')
    with patch('frontend.preparation.dialog.filedialog.askopenfilename',side_effect=['',str(path)]):
        dialog.load();dialog.load()
    assert dialog.source.get()==str(source) and dialog.environment.values['initial'].get()=='293.0'
    dialog.accept(cat)
    with patch('frontend.preparation.dialog.filedialog.asksaveasfilename',return_value=str(path)),patch('frontend.preparation.dialog.save_recipe',side_effect=OSError('disk')),patch('frontend.preparation.dialog.messagebox.showerror') as err:
        dialog.save();assert err.call_count==1
    path.write_text('{"schema":1,"recipe":{}}')
    with patch('frontend.preparation.dialog.filedialog.askopenfilename',return_value=str(path)),patch('frontend.preparation.dialog.messagebox.showerror') as err:
        dialog.load();assert err.call_count==1
