"""Failure diagnostics retain actionable guidance, request snapshots and traceback."""
from unittest.mock import patch
import pytest
from frontend.errors import capture_failure, show_failure
from frontend.sim_form import SimulationForm
from tkinter import ttk


@pytest.mark.parametrize("message, expected", [
    ("DWG is missing prepared-model symbols: SIM_DURATION_S", "create AND connect"),
    ("Orbital runs require prepared RadCAD radiation tasks.", "Disable orbital"),
    ("Error loading Edge Contactor[MAIN][1]::318", "zero total length"),
    ("Edge conductance failed", "zero total length"),
    ("Unexpected Edge failure", "case messages"),
    ("", "RuntimeError"),
])
def test_failure_report(tmp_path, message, expected):
    try:
        raise RuntimeError(message)
    except RuntimeError as error:
        failure = capture_failure(error, tmp_path, {"case": "Case Set 0", "heat": 12000})
    assert expected in failure.details
    log, = (tmp_path / "errors").glob("*.txt")
    text = log.read_text(encoding="utf-8")
    assert "Traceback" in text and "Case Set 0" in text and "12000" in text
    with patch("frontend.errors.messagebox.showerror") as dialog:
        assert show_failure(failure, None) == failure.message
        dialog.assert_called_once_with("Test failed", failure.details, parent=None)


def test_unwritable_log_still_reports_error(tmp_path):
    with patch("frontend.errors.Path.mkdir", side_effect=OSError("disk full")):
        failure = capture_failure(ValueError("bad case"), tmp_path, None)
    assert "bad case" in failure.details and "Could not save diagnostic log: disk full" in failure.details


def test_settings_expand_in_place(root):
    form = SimulationForm(root)
    following = ttk.Label(root, text="Queue")
    following.pack()
    form.enabled.set(True)
    form.toggle()
    assert root.pack_slaves().index(form.body.master) < root.pack_slaves().index(following)
    form.enabled.set(False)
    form.toggle()
    form.enabled.set(True)
    form.toggle()
    assert root.pack_slaves().index(form.body.master) < root.pack_slaves().index(following)
