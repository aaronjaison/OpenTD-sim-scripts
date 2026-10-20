"""Exercise actual Tk widgets, events and lifecycle without a running mainloop."""
from unittest.mock import Mock,patch
from pathlib import Path
import runpy
import pytest
from backend.solver import Sample
from frontend.interface import Application
from frontend.graphics import draw_chart
from frontend.connections import Connections


@pytest.fixture
def ui(root,tmp_path):
    instance=Application(root,Connections(tmp_path))
    yield instance
    if root.winfo_exists():instance.close()


def test_gui_preview_run(ui,root):
    ui.values['duration'].set('2')
    ui.run()
    ui.connections.controller.worker.join(10)
    ui.poll()
    assert ui.folder.is_dir()
    assert ui.samples[-1].time_s==2
    assert 'Results: 3 samples' in ui.status.get()
    assert ui.canvas.find_all()
    with patch('frontend.interface.webbrowser.open') as opened:
        ui.open_results();opened.assert_called_once_with(ui.folder.as_uri())


def test_selection_errors_and_events(ui):
    with patch('frontend.interface.filedialog.askopenfilename',side_effect=['part.SLDPRT','']):
        ui.choose_model();ui.choose_model()
    assert ui.model.get()=='part.SLDPRT'
    with patch('frontend.interface.messagebox.showerror') as error:
        ui.run();error.assert_called_once()
        ui.handle_event('error','failed');assert error.call_count==2
    ui.handle_event('cancelled','cancelled');assert ui.status.get()=='cancelled'
    ui.handle_event('progress','50%');assert ui.status.get()=='50%'
    ui.opentd.busy=True
    with patch('frontend.interface.messagebox.showinfo') as info:
        ui.close();info.assert_called_once()
    ui.opentd.busy=False


def test_plot_sampling(ui):
    rows=[Sample(i,293+i/100,0) for i in range(2003)]
    draw_chart(ui.canvas,rows)
    assert ui.canvas.find_all()
    draw_chart(ui.canvas,[Sample(0,318.15,None)])
    assert any(ui.canvas.type(item)=="oval" for item in ui.canvas.find_all())


def test_entrypoints():
    import app
    with patch.object(app.tk,'Tk') as factory,patch.object(app,'Application') as window:
        app.main();window.assert_called_once_with(factory.return_value)
        factory.return_value.mainloop.assert_called_once()
    with patch('tkinter.Tk') as factory,patch('frontend.interface.Application'):
        runpy.run_module('app',run_name='__main__')
        factory.return_value.mainloop.assert_called_once()


def test_scrolling_and_default_connections(root):
    from types import SimpleNamespace
    instance=Application(root)
    instance.preview.update_width(SimpleNamespace(width=900))
    instance.preview.update_region()
    assert float(instance.preview.canvas.itemcget(instance.preview.window,'width'))==900
    instance.close()
