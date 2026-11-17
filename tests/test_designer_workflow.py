"""Isolated native sessions, source preservation, failure receipts and UI dispatch."""
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from backend.designer import workflow as w, probe, status, session
from frontend.opentd_panel import OpenTDPanel


def test_probe(tmp_path):
    p=tmp_path/'receipt.json'
    assert "GetMethod('FetchLicense')" in probe.script(p)
    for data, message in [({'licensed':False,'bodies':5},'license'),({'licensed':True,'bodies':0},'no bodies')]:
        p.write_text(json.dumps(data))
        with pytest.raises(RuntimeError,match=message):probe.verify(p)
    p.write_text('{"licensed":true,"bodies":787}')
    assert probe.verify(p)['bodies']==787


def test_mesh_status(tmp_path,monkeypatch):
    folder=tmp_path/'out';folder.mkdir();native=tmp_path/'native';native.mkdir()
    op=native/'Output.op';op.write_text('incomplete')
    monkeypatch.setattr(status.time,'monotonic',Mock(side_effect=[0,1,3]))
    monkeypatch.setattr(status.time,'sleep',Mock())
    with pytest.raises(TimeoutError):status.wait_mesh(folder,lambda:[native],2)
    status.time.monotonic.side_effect=None;status.time.monotonic.return_value=0
    op.write_text('{"discriminator":"ErrorOperationOutput","Completed":false}')
    with pytest.raises(RuntimeError,match='geometry'):status.wait_mesh(folder,lambda:[native])
    assert json.loads((folder/'mesh-error.json').read_text())['Completed'] is False
    op.write_text('{}');mesh=folder/'femodel.xml';mesh.write_text('partial')
    status.time.sleep.side_effect=lambda _:mesh.write_text('<mesh/>')
    assert status.wait_mesh(folder,lambda:[native])==mesh


def test_session(monkeypatch,tmp_path):
    connection=Mock();connection.connect_ex.return_value=0
    monkeypatch.setattr(session.socket,'socket',Mock(return_value=Mock(__enter__=Mock(return_value=connection),__exit__=Mock(return_value=False))))
    with pytest.raises(RuntimeError,match='already open'):session.launch('source')
    connection.connect_ex.return_value=1
    monkeypatch.setattr(session,'LAUNCHER',tmp_path/'launcher.exe')
    with pytest.raises(RuntimeError,match='not found'):session.launch('source')
    session.LAUNCHER.touch()
    with patch.object(session.subprocess,'Popen') as start:
        session.launch('source');assert start.call_args.args[0][-1]=='source'
    class RPCError(Exception):pass
    client=Mock();client.grpc.RpcError=RPCError
    client.call.side_effect=[RPCError(),{}, {'isComplete':False},{},{'isComplete':True,'name':'other'}, {}, {'isComplete':True,'name':'SOURCE'}]
    monkeypatch.setattr(session.time,'sleep',Mock())
    assert session.ready(client, 'source')['isComplete']
    monkeypatch.setattr(session.time,'monotonic',Mock(side_effect=[0,400]))
    with pytest.raises(TimeoutError):session.ready(client, 'source')
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path));assert session.session_root()==tmp_path/'Temp'/'Discovery'


def test_workflow(tmp_path,monkeypatch):
    source=tmp_path/'a.SLDASM';source.write_bytes(b'CAD')
    for path in (tmp_path/'missing.sldasm',tmp_path/'bad.txt'):
        path.touch()
        if path.suffix=='.sldasm':path.unlink()
        with pytest.raises(ValueError):w.run(path,tmp_path/'out')
    client=Mock();monkeypatch.setattr(w,'DesignerRPC',Mock(return_value=client))
    monkeypatch.setattr(w,'launch',Mock());monkeypatch.setattr(w,'ready',Mock())
    monkeypatch.setattr(w,'session_root',lambda:tmp_path/'sessions')
    def audit(p):p.with_suffix('.json').write_text('{"licensed":true,"bodies":787}')
    client.script.side_effect=audit
    def mesh(folder,sessions):
        assert sessions()==set()
        return folder/'femodel.xml'
    monkeypatch.setattr(w,'wait_mesh',mesh)
    assert 'Mesh exported' in w.run(source,tmp_path/'out')
    receipt=json.loads(next((tmp_path/'out').glob('*/receipt.json')).read_text())
    assert receipt['source_unchanged'] and receipt['bodies']==787
    client.close.assert_called_once()
    client.script.side_effect=RuntimeError('native failure')
    with pytest.raises(RuntimeError,match='native'):w.run(source,tmp_path/'out')
    assert client.close.call_count==2


def test_ui_action(root,tmp_path):
    panel=OpenTDPanel(root,tmp_path);panel.preparation.open();dialog=panel.preparation.dialog
    with patch('tkinter.messagebox.showerror') as error:
        dialog.import_mesh();error.assert_called_once()
    source=tmp_path/'a.sldasm';source.touch();dialog.source.set(str(source))
    with patch.object(panel,'load_nodes') as submit,patch('backend.designer.workflow.run',return_value='mesh') as run:
        dialog.import_mesh();assert submit.call_args.args[0]()=='mesh'
        run.call_args.args[2]('progress');assert panel.events.get_nowait()==('progress','progress')
    panel.close()
