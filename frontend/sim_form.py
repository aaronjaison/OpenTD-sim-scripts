"""Compact, opt-in simulation settings for a prepared model."""
import tkinter as tk
from tkinter import ttk
from backend.sim_settings import FIELDS, SimulationSettings
from .tooltips import Tooltip


class SimulationForm:
    def __init__(self, parent):
        container = ttk.Frame(parent)
        container.pack(fill="x")
        self.enabled = tk.BooleanVar(parent, False)
        self.orbital = tk.BooleanVar(parent, False)
        toggle = ttk.Checkbutton(container, text="Customize simulation", variable=self.enabled, command=self.toggle)
        toggle.pack(anchor="w", pady=6)
        Tooltip(toggle, "Enable named SIM_* parameter overrides. Your DWG must follow the preparation guide; otherwise its existing case settings are preserved.")
        self.body = ttk.Frame(container)
        self.values = {}
        for index, (name, (label, help_text, default)) in enumerate(FIELDS.items()):
            row, column = divmod(index, 3)
            cell = ttk.Frame(self.body, padding=(0, 4, 12, 4))
            cell.grid(row=row, column=column, sticky="ew")
            caption = ttk.Label(cell, text=label + " ⓘ")
            caption.pack(anchor="w")
            value = tk.StringVar(parent, str(default))
            self.values[name] = value
            entry = ttk.Entry(cell, textvariable=value, width=22)
            entry.pack(fill="x")
            Tooltip(caption, help_text)
        orbital = ttk.Checkbutton(self.body, text="Apply orbital parameters + recalculate RadCAD", variable=self.orbital)
        orbital.grid(row=4, column=0, columnspan=3, sticky="w", pady=6)
        Tooltip(orbital, "Requires a prepared orbit/attitude and solar, albedo and Earth IR radiation tasks linked to the documented orbital symbols.")
        self.body.columnconfigure((0, 1, 2), weight=1)

    def toggle(self):
        if self.enabled.get():
            self.body.pack(fill="x", pady=6)
        else:
            self.body.pack_forget()

    def read(self):
        if not self.enabled.get():
            return None
        settings = SimulationSettings(**{key: float(value.get()) for key, value in self.values.items()},
                                      orbital=self.orbital.get())
        settings.parameters()
        return settings
