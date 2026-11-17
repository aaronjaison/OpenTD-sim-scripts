"""Serialize preparation with existing inspection/test jobs and select built models."""
from dataclasses import dataclass, replace
from pathlib import Path
from tkinter import ttk
from backend.preparation.geometry import inspect_mesh, MeshCatalog
from backend.preparation.builder import build
from backend.node_catalog import validate_drawing
from .dialog import PreparationDialog


@dataclass(frozen=True)
class ModelReady:
    result: object
    previous: str


class PreparationController:
    def __init__(self, panel, parent):
        self.panel, self.dialog = panel, None
        ttk.Button(parent, text="Prepare model…", command=self.open).pack(anchor="w", pady=6)

    def open(self):
        if self.dialog is not None and self.dialog.window.winfo_exists():
            self.dialog.window.lift()
            return
        self.dialog = PreparationDialog(self.panel.frame, self.scan, self.build)

    def scan(self, mesh):
        source = str(validate_drawing(mesh))
        self.panel.load_nodes(lambda: inspect_mesh(source, self.panel.output))

    def build(self, recipe):
        previous = self.panel.values["drawing"].get()
        self.panel.load_nodes(lambda: ModelReady(build(recipe, self.panel.output), previous))

    def accept(self, value):
        if isinstance(value, MeshCatalog):
            if self.dialog is None or not self.dialog.window.winfo_exists():
                return "Preparation window closed; mesh inspection ignored."
            return self.dialog.accept(value)
        if self.panel.values["drawing"].get() != value.previous:
            return f"Drawing changed; prepared model saved at {value.result.drawing}."
        self.panel.setup.accept(replace(value.result, source=""))
        self.panel.values["node"].set("All nodes")
        if self.dialog is not None and self.dialog.window.winfo_exists():
            self.dialog.status.set(f"Model built. Review {value.result.report}; run the selected case with customization OFF for its baseline.")
        self.panel.simulation.enabled.set(False); self.panel.simulation.toggle()
        return f"Prepared model selected. Review {value.result.report}, then Re-run entirely."

    def close(self):
        if self.dialog is not None and self.dialog.window.winfo_exists():
            self.dialog.window.destroy()
