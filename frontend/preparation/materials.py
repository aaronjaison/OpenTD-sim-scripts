"""Explicit component-to-thermal-entity material and optical assignments."""
import tkinter as tk
from tkinter import ttk, messagebox
from .forms import fields, listbox, remove_selected


class MaterialsPage:
    def __init__(self, parent):
        self.parts, self.handles = [], []
        ttk.Label(parent, text="Select mesh entities, enter measured material data, then assign a named component.", wraplength=800).pack(anchor="w")
        self.geometry = listbox(parent, 6)
        row = ttk.Frame(parent); row.pack(fill="x")
        self.values = fields(row, [
            ("name", "Component name", "", "Unique label: letters, digits, underscores; start with a letter."),
            ("density", "Density · kg/m³", "", "Measured bulk density. No material properties are guessed from CAD labels."),
            ("conductivity", "Conductivity · W/m/K", "", "Isotropic, constant conductivity. Advanced anisotropy needs model-author preparation."),
            ("cp", "Specific heat · J/kg/K", "", "Constant specific heat for this baseline model."),
            ("thickness", "Shell thickness · m", "", "Required for shells. Leave blank for solids or radiation-only skins; solids use their existing volume."),
            ("alpha", "Solar absorptivity", "", "0..1, opaque diffuse coating; solar reflection = 1 - absorption."),
            ("epsilon", "IR emissivity", "", "0..1, constant opaque diffuse IR coating, independent of solar absorption.")])
        self.skin = tk.BooleanVar(parent, False)
        ttk.Checkbutton(parent, text="Radiation-only skin: no extra shell mass/conduction", variable=self.skin).pack(anchor="w", pady=4)
        buttons = ttk.Frame(parent); buttons.pack(fill="x")
        ttk.Button(buttons, text="Assign selected entities", command=self.add).pack(side="left")
        ttk.Button(buttons, text="Remove assignment", command=lambda: remove_selected(self.assigned, self.parts)).pack(side="right")
        self.assigned = listbox(parent, 4)

    def populate(self, catalog):
        self.handles = [e[0] for e in catalog.entities]
        self.geometry.delete(0, "end")
        for handle, kind, layer, comment in catalog.entities:
            self.geometry.insert("end", f"{handle} | {kind} | {layer} | {comment}")

    def refresh(self):
        self.assigned.delete(0, "end")
        for part in self.parts:
            self.assigned.insert("end", f"{part['name']}: {len(part['handles'])} entities")

    def add(self):
        try:
            handles = [self.handles[i] for i in self.geometry.curselection()]
            if not handles:
                raise ValueError("Select thermal mesh entities first.")
            if set(handles) & {h for part in self.parts for h in part["handles"]}:
                raise ValueError("Remove the previous assignment before assigning those entities again.")
            part = {k: (v.get().strip() if k == "name" else float(v.get() or (0 if k == "thickness" else ""))) for k, v in self.values.items()}
            self.parts.append(dict(part, handles=handles, skin=self.skin.get()))
            self.refresh()
        except ValueError as error:
            messagebox.showerror("Check material assignment", str(error), parent=self.geometry)
