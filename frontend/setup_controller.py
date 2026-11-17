"""Queue wizard inspection/preparation without running vendor calls on Tk."""
from pathlib import Path
from tkinter import ttk, messagebox
from backend.setup_targets import SUPPORTED
from backend.sim_settings import SYMBOLS
from backend.node_catalog import validate_drawing
from backend.case_catalog import CaseCatalog
from backend.setup_wizard import inspect_setup, SetupCatalog
from .setup_dialog import SetupDialog
from .tooltips import Tooltip


class SetupController:
    def __init__(self, panel, parent):
        self.panel, self.dialog = panel, None
        button = ttk.Button(parent, text="Connect settings…", command=self.open)
        button.pack(anchor="w", pady=6)
        Tooltip(button, "First check Customize simulation and the individual settings to change, then connect them to existing model targets in a new drawing copy.")

    def open(self):
        panel = self.panel
        try:
            source = str(validate_drawing(panel.values["drawing"].get()))
            self.settings = panel.simulation.read()
            if self.settings is None:
                raise ValueError("Enable Customize simulation and check the settings to connect.")
            if set(self.settings.parameters()) - {SYMBOLS[n] for n in SUPPORTED}:
                raise ValueError("The wizard connects basic settings only; uncheck orbital overrides.")
            case, group = panel.values["case"].get().strip(), panel.values["group"].get()
            if not case:
                raise ValueError("Choose an existing case first.")
        except ValueError as error:
            messagebox.showerror("Connect settings", str(error), parent=panel.frame)
            return
        settings = self.settings
        def inspect():
            result = inspect_setup(source, case, group, panel.output, SYMBOLS["emissivity"] in settings.parameters())
            return SetupCatalog(result.drawing, result.case, result.group, dict(result.targets, settings=settings))
        panel.load_nodes(inspect)

    def accept(self, result):
        panel = self.panel
        if isinstance(result, SetupCatalog):
            if Path(panel.values["drawing"].get()).resolve() != Path(result.drawing):
                return "Drawing changed; ignored old setup inspection."
            if self.dialog is not None and self.dialog.window.winfo_exists():
                self.dialog.window.destroy()
            self.dialog = SetupDialog(panel.frame, result, result.targets["settings"], panel.output, panel.load_nodes)
            return "Select targets and create the connected drawing copy."
        if result.source and Path(panel.values["drawing"].get()).resolve() != Path(result.source):
            return f"Drawing changed; connected copy saved at {result.drawing}."
        selected_node = panel.values["node"].get()
        panel.values["drawing"].set(result.drawing)
        panel.cases.accept(CaseCatalog(str(Path(result.drawing).resolve()), ((result.case, result.group),)))
        panel.values["node"].set(selected_node)
        return f"Connected copy selected. Review {result.report}. Use Re-run entirely to verify the model."

    def close(self):
        if self.dialog is not None and self.dialog.window.winfo_exists():
            self.dialog.window.destroy()
