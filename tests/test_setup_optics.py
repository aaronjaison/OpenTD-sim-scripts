"""Empty optical catalog recovery preserves settings and the explicitly chosen file."""
from unittest.mock import Mock, patch
from types import SimpleNamespace as NS
from backend.setup_wizard import SetupCatalog
from backend.sim_settings import SimulationSettings
from frontend.setup_optics import add_optical_help, choose_database
from frontend.setup_dialog import SetupDialog


def test_empty_state_and_load(root):
    cat = SetupCatalog("model.dwg", "Case", "", {"nodes": [], "loads": [], "optics": []})
    settings = SimulationSettings(selected=("emissivity",))
    submit = Mock()
    dialog = SetupDialog(root, cat, settings, "out", submit)
    assert not dialog.coating["values"]
    with patch("frontend.setup_optics.filedialog.askopenfilename", return_value=""):
        choose_database(dialog)
    submit.assert_not_called()
    with patch("frontend.setup_optics.filedialog.askopenfilename", return_value="chosen.rco"):
        choose_database(dialog)
    result = SetupCatalog("model.dwg", "Case", "", {"optics": ["VED"], "optical_database": "chosen.rco"})
    with patch("frontend.setup_optics.inspect_setup", return_value=result) as inspect:
        new = submit.call_args.args[0]()
        inspect.assert_called_once_with("model.dwg", "Case", "", "out", optical_database="chosen.rco")
        assert new.targets["settings"] == settings
        assert new.targets["optical_database"] == "chosen.rco"


def test_optical_database_reaches_preparation(root):
    cat = SetupCatalog("model.dwg", "Case", "", {"nodes": [], "loads": [], "optics": ["VED"], "optical_database": "chosen.rco"})
    submit = Mock()
    dialog = SetupDialog(root, cat, SimulationSettings(selected=("emissivity",)), "out", submit)
    dialog.coating.current(0)
    dialog.create()
    with patch("frontend.setup_dialog.prepare_setup") as prepare:
        submit.call_args.args[0]()
        assert prepare.call_args.args[-1] == "chosen.rco"
