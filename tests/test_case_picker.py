"""Case discovery, group selection, delayed help and wheel behavior."""
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import pytest
from backend import case_catalog as catalog
from frontend.opentd_panel import OpenTDPanel
from frontend.tooltips import Tooltip
from frontend.layout import ScrollableFrame
from tkinter import ttk


def test_discovery(tmp_path, monkeypatch):
    source = tmp_path / "model.dwg"
    source.write_bytes(b"source")
    desktop = Mock()
    desktop.GetCaseSets.return_value = [NS(Name="Case", GroupName="B"), NS(Name="Case", GroupName="")]
    monkeypatch.setattr(catalog.open_td_api, "connect", lambda _: desktop)
    result = catalog.discover_cases(str(source), tmp_path)
    assert result.cases == (("Case", ""), ("Case", "B"))
    desktop.GetCaseSets.side_effect = ValueError("failed")
    with pytest.raises(ValueError): catalog.discover_cases(str(source), tmp_path)
    assert desktop.Quit.call_count == 2
    assert source.read_bytes() == b"source"


def test_case_picker(root, tmp_path):
    panel = OpenTDPanel(root, tmp_path)
    picker = panel.cases
    picker.select()
    with patch("frontend.case_picker.messagebox.showerror") as error:
        picker.load()
        error.assert_called_once()
    source = tmp_path / "model.dwg"
    source.touch()
    panel.values["drawing"].set(str(source))
    result = catalog.CaseCatalog(str(source.resolve()), (("Case", ""), ("Case", "Group")))
    with patch("frontend.opentd_panel.Thread") as thread:
        picker.load()
        with patch("frontend.case_picker.discover_cases", return_value=result):
            panel.work(thread.call_args.kwargs["args"][0])
    panel.poll()
    assert panel.values["case"].get() == "Case"
    picker.combo.current(1)
    picker.select()
    assert panel.values["group"].get() == "Group"
    picker.accept(result)
    assert picker.combo.current() == 1
    panel.values["drawing"].set(str(tmp_path / "other.dwg"))
    assert "ignored" in picker.accept(result)
    assert not picker.cases and not panel.values["case"].get()
    panel.values["drawing"].set(str(source))
    assert picker.accept(catalog.CaseCatalog(str(source.resolve()), ())) == "Loaded 0 case sets."
    panel.close()


def test_delayed_hover(root):
    widget = ttk.Label(root, text="Name")
    tip = Tooltip(widget, "help")
    assert not widget.bind("<FocusIn>")
    with patch.object(widget, "after", return_value="timer") as after, patch.object(widget, "after_cancel") as cancel:
        tip.schedule()
        assert tip.window is None
        after.assert_called_once_with(2000, tip.show)
        tip.schedule()
        cancel.assert_called_once_with("timer")
        tip.hide()
        assert tip.timer is None
    tip.show()
    assert tip.window is not None
    tip.hide()


def test_mouse_wheel(root):
    panel = ScrollableFrame(root)
    event = NS(x_root=10, y_root=10, delta=-120)
    with patch.object(panel.frame, "winfo_containing", return_value=panel.body), patch.object(panel.canvas, "yview_scroll") as scroll:
        assert panel.wheel(event) == "break"
        scroll.assert_called_with(1, "units")
        event.delta = 240
        panel.wheel(event)
        scroll.assert_called_with(-2, "units")
        event.delta = 0
        assert panel.wheel(event) is None
    with patch.object(panel.frame, "winfo_containing", return_value=None):
        panel.wheel(event)
    with patch.object(panel.frame, "winfo_containing", return_value=root):
        panel.wheel(event)
    panel.cleanup(NS(widget=root))
    panel.frame.destroy()
