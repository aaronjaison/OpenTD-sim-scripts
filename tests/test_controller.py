"""Verify worker outcomes, cancellation and publication ordering."""
from threading import Event
from unittest.mock import Mock, patch
import pytest
from backend.config import TrialConfig
from backend.con_interpreter import Controller
from backend.main_processes import run_trial
from backend.solver import Cancelled
from frontend.connections import Connections


def test_end_to_end(tmp_path):
    controller=Controller()
    assert not controller.busy
    controller.start(TrialConfig(duration=2),tmp_path)
    controller.worker.join(10)
    assert not controller.busy
    events=[]
    while not controller.events.empty():events.append(controller.events.get())
    assert events[-1][0]=='done'
    assert (events[-1][1][1]/'report.md').is_file()
    assert any(kind=='progress' for kind,_ in events)


@pytest.mark.parametrize('error,kind',[(ValueError('bad'),'error'),(Cancelled('stop'),'cancelled')])
def test_worker_errors(error,kind):
    controller=Controller(runner=Mock(side_effect=error))
    controller._work(TrialConfig(),'output')
    assert controller.events.get()==(kind,str(error))


def test_busy_cancel_and_connections(tmp_path):
    controller=Controller();controller.worker=Mock()
    controller.worker.is_alive.return_value=True
    with pytest.raises(ValueError):controller.start(TrialConfig(),tmp_path)
    controller.cancel();assert controller.cancelled.is_set()
    bridge=Connections(tmp_path,Mock())
    bridge.run({'mass':'2'})
    assert bridge.controller.start.call_args.args[0].mass==2
    bridge.cancel();bridge.controller.cancel.assert_called_once()
    assert Connections().output.name=='output'


def test_cancel_after_solve(tmp_path):
    event=Event()
    def solve(*args):event.set();return []
    with patch('backend.main_processes.solve',solve):
        with pytest.raises(Cancelled):run_trial(TrialConfig(),tmp_path,event,lambda _:None)
    assert not list(tmp_path.iterdir())
