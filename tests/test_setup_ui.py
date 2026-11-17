"""Real Tk wizard target selection, queue integration and stale-discovery handling."""
from unittest.mock import Mock, patch
import pytest
from backend.setup_wizard import SetupCatalog, SetupResult
from backend.sim_settings import SimulationSettings
from frontend.setup_dialog import SetupDialog
from frontend.opentd_panel import OpenTDPanel


@pytest.fixture
def panel(root, tmp_path):
    p = OpenTDPanel(root, tmp_path)
    source = tmp_path / "model.dwg"; source.touch()
    p.values["drawing"].set(str(source)); p.values["case"].set("Case")
    yield p
    p.close()


def catalog(panel):
    return SetupCatalog(panel.values["drawing"].get(), "Case", "", {
        "nodes": ["MAIN.1", "MAIN.2"], "loads": [("h", "Battery", "LOAD")], "optics": ["VED"],
        "settings": SimulationSettings(selected=("duration",))})


def test_controller_and_queue(panel):
    ctl = panel.setup
    with patch("frontend.setup_controller.messagebox.showerror") as err:
        ctl.open(); assert err.call_count == 1
        panel.simulation.enabled.set(True)
        ctl.open(); assert err.call_count == 2
        panel.simulation.selected["duration"].set(True)
        panel.simulation.selected["period"].set(True)
        panel.simulation.orbital.set(True)
        ctl.open(); assert err.call_count == 3
        panel.simulation.selected["period"].set(False)
        panel.values["case"].set("")
        ctl.open(); assert err.call_count == 4
    panel.values["case"].set("Case")
    result = catalog(panel)
    with patch("frontend.opentd_panel.Thread") as thread:
        ctl.open()
        operation = thread.call_args.kwargs["args"][0]
        with patch("frontend.setup_controller.inspect_setup", return_value=result): panel.work(operation)
        panel.poll()
    assert ctl.dialog is not None
    ctl.accept(result)  # replace an open wizard, retaining a single active dialog
    result = SetupResult(panel.values["drawing"].get(), "Case", "", "connections.json")
    panel.values["node"].set("All nodes")
    panel.events.put(("done", result)); panel.poll()
    assert panel.values["node"].get() == "All nodes"
    assert "Case" in panel.cases.display.get()
    assert "Connected copy" in panel.status.get()
    ctl.dialog.window.destroy()
    ctl.accept(catalog(panel))
    changed = SetupResult("new.dwg", "Case", "", "report", "old.dwg")
    assert "Drawing changed" in ctl.accept(changed)
    changed = SetupResult("new.dwg", "Case", "", "report", panel.values["drawing"].get())
    assert "Connected copy" in ctl.accept(changed)
    panel.values["drawing"].set("changed.dwg")
    assert "ignored" in ctl.accept(catalog_result := SetupCatalog("old.dwg", "Case", "", {}))


def test_dialog_validations_and_submission(root):
    cat = SetupCatalog("model.dwg", "Case", "G", {"nodes": ["MAIN.1"], "loads": [("h", "Battery", "LOAD")], "optics": ["VED"]})
    settings = SimulationSettings(selected=("initial", "heat", "emissivity"))
    submitted = Mock()
    dialog = SetupDialog(root, cat, settings, "out", submitted)
    with patch("frontend.setup_dialog.messagebox.showerror") as err:
        dialog.create(); assert "nodes" in err.call_args.args[1]
        dialog.nodes.selection_set(0)
        dialog.create(); assert "heat load" in err.call_args.args[1]
        dialog.heat.current(0)
        dialog.create(); assert "coating" in err.call_args.args[1]
        dialog.coating.current(0); dialog.volume.set("bad")
        dialog.create(); assert err.call_count == 4
    dialog.volume.set("0.00002")
    dialog.create()
    with patch("frontend.setup_dialog.prepare_setup", return_value="prepared") as prepare:
        assert submitted.call_args.args[0]() == "prepared"
        assert prepare.call_args.args[-5:] == (("MAIN.1",), "h", 2e-5, "VED", "")
    dialog = SetupDialog(root, cat, SimulationSettings(selected=("duration",)), "out", submitted)
    dialog.volume.set("ignored")
    dialog.create()
    with patch("frontend.setup_dialog.prepare_setup") as prepare:
        submitted.call_args.args[0]()
        assert prepare.call_args.args[-3] == 0


def test_selected_form_values(panel):
    form = panel.simulation
    form.enabled.set(True); form.toggle()
    form.selected["duration"].set(True)
    form.values["initial"].set("ignored invalid text")
    form.refresh()
    assert form.read().parameters() == {"SIM_DURATION_S": "3300"}
    assert str(form.entries["initial"]["state"]) == "disabled"
