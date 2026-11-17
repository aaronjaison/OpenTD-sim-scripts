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


def test_single_dwg_workflow(ui, root):
    from tkinter import ttk
    assert ui.opentd.frame.winfo_manager() == "pack"
    assert not any(isinstance(child, ttk.Notebook) for child in root.winfo_children())
    assert set(ui.opentd.values) == {"drawing", "case", "group", "node"}
    ui.opentd.busy = True
    with patch('frontend.interface.messagebox.showinfo') as info:
        ui.close()
        info.assert_called_once()
    ui.opentd.busy = False


def test_plot_sampling(root):
    import tkinter as tk
    from frontend.graphics import input_form
    canvas = tk.Canvas(root)
    assert len(input_form(root)) == 10
    draw_chart(canvas, [])
    rows = [Sample(i, 293+i/100, 0) for i in range(2003)]
    draw_chart(canvas, rows)
    assert canvas.find_all()
    draw_chart(canvas, [Sample(0, 318.15, None)])
    assert any(canvas.type(item) == "oval" for item in canvas.find_all())


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
    instance.opentd.container.update_width(SimpleNamespace(width=900))
    instance.opentd.container.update_region()
    assert float(instance.opentd.container.canvas.itemcget(instance.opentd.container.window,'width'))==900
    instance.close()
