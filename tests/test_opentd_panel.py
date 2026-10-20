"""Exercise OpenTD UI operations and queue handling without licenses."""
from unittest.mock import patch,Mock
import pytest
from frontend.opentd_panel import OpenTDPanel


@pytest.fixture
def panel(root,tmp_path):
    instance=OpenTDPanel(root,tmp_path)
    yield instance
    instance.close()


def test_choose_check_and_events(panel,tmp_path):
    with patch('frontend.opentd_panel.filedialog.askopenfilename',side_effect=['model.dwg','']):
        panel.choose();panel.choose()
    assert panel.values['drawing'].get()=='model.dwg'
    with patch('frontend.opentd_panel.Thread') as thread,patch('frontend.opentd_panel.diagnostics',return_value='available'):
        panel.check()
        thread.return_value.start.assert_called_once()
        panel.check();thread.return_value.start.assert_called_once()
        operation=thread.call_args.kwargs['args'][0]
        panel.work(operation)
    panel.poll();assert panel.status.get()=='available' and not panel.busy
    panel.work(Mock(side_effect=ValueError('failed')))
    panel.poll();assert panel.status.get()=='failed'
    panel.events.put(('progress','solving'));panel.poll();assert panel.status.get()=='solving'
    panel.events.put(('done',([],tmp_path)));panel.poll()
    assert panel.folder==tmp_path
    with patch('frontend.opentd_panel.webbrowser.open') as opened:
        panel.open_results();opened.assert_called_once_with(tmp_path.as_uri())


def test_run_validation_and_worker(panel,tmp_path):
    with patch('frontend.opentd_panel.messagebox.showerror') as error:
        panel.run();error.assert_called_once()
    drawing=tmp_path/'model.dwg';drawing.touch()
    for name,value in [('drawing',str(drawing)),('case','Case'),('node','MAIN.1')]:
        panel.values[name].set(value)
    with patch('frontend.opentd_panel.Thread') as thread:
        panel.run()
        operation=thread.call_args.kwargs['args'][0]
        def runner(request,output,progress):
            progress('solving')
            assert request.node=='MAIN.1'
            return [],tmp_path
        with patch('frontend.opentd_panel.run_prepared',runner):panel.work(operation)
    panel.poll();assert panel.folder==tmp_path
