"""Keep actionable failure details visible and preserve technical diagnostics."""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import traceback
from tkinter import messagebox


@dataclass(frozen=True)
class Failure:
    message: str
    details: str


def capture_failure(error, output, context):
    """Called in the worker while its traceback is still available."""
    message = str(error) or type(error).__name__
    advice = "Check the diagnostic log and the Thermal Desktop case messages before retrying."
    if "missing prepared-model symbols" in message:
        advice = ("This drawing is not prepared for Customize simulation. To use its existing "
                  "case settings, turn Customize simulation off. To apply these inputs, have the "
                  "model author create AND connect the SIM_* symbols described in DWG_PREPARATION.md. "
                  "Q_BAT and EMIS do not replace those bindings. Turning customization off does not "
                  "fix other model errors.")
    elif "RadCAD radiation tasks" in message:
        advice = "Disable orbital recalculation or prepare the orbit and RadCAD tasks described in DWG_PREPARATION.md."
    elif "Edge" in message and ("Contactor" in message or "conductance" in message):
        advice = "Repair the referenced edge contactor in Thermal Desktop; its selected edges have zero total length."
    details = f"{message}\n\n{advice}"
    try:
        folder = Path(output) / "errors"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = folder / f"error-{stamp}.txt"
        path.write_text(f"{details}\n\nQueued request: {context!r}\n\n{traceback.format_exc()}", encoding="utf-8")
        details += f"\n\nDiagnostic log: {path.resolve()}"
    except OSError as failure:
        details += f"\n\nCould not save diagnostic log: {failure}"
    return Failure(message, details)


def show_failure(failure, parent):
    """Display on the UI thread, then allow remaining queued tests to continue."""
    messagebox.showerror("Test failed", failure.details, parent=parent)
    return failure.message
