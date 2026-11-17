"""Preparation jobs serialize through the workbench and guard stale results."""
from unittest.mock import Mock,patch
from dataclasses import replace
from pathlib import Path
from backend.preparation.geometry import MeshCatalog
from backend.setup_wizard import SetupResult
from frontend.preparation.controller import ModelReady
from frontend.opentd_panel import OpenTDPanel


def test_controller_events(root,tmp_path):
    p=OpenTDPanel(root,tmp_path);ctl=p.preparation
    cat=MeshCatalog(str(tmp_path/'mesh.dwg'),(('a','Rectangle','Shell',''),),('MAIN.1',),0)
    assert 'closed' in ctl.accept(cat)
    ctl.open();original=ctl.dialog;ctl.open();assert ctl.dialog is original
    Path(cat.drawing).touch();ctl.dialog.mesh.set(cat.drawing)
    with patch('frontend.opentd_panel.Thread') as thread:
        ctl.scan(cat.drawing)
        with patch('frontend.preparation.controller.inspect_mesh',return_value=cat):
            p.work(thread.call_args.kwargs['args'][0])
        p.poll()
    assert ctl.dialog.catalog==cat
    result=SetupResult(str(tmp_path/'prepared.dwg'),'Base','','report',cat.drawing)
    p.values['drawing'].set('before')
    with patch('frontend.opentd_panel.Thread') as thread:
        ctl.build({'mesh':cat.drawing})
        with patch('frontend.preparation.controller.build',return_value=result):
            p.work(thread.call_args.kwargs['args'][0])
        p.poll()
    assert p.values['drawing'].get()==result.drawing and p.values['node'].get()=='All nodes'
    assert not p.simulation.enabled.get()
    assert 'changed' in ctl.accept(ModelReady(result,'old'))
    ctl.dialog.window.destroy()
    assert 'Prepared model' in ctl.accept(ModelReady(result,result.drawing))
    assert 'closed' in ctl.accept(cat)
    ctl.open()
    p.close()
