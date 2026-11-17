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
        Tooltip(toggle, "Enable named SIM_* parameter overrides. Check only the values to change. Use Connect settings to prepare missing connections.")
        self.body = ttk.Frame(container)
        self.values, self.selected, self.entries = {}, {}, {}
        for index, (name, (label, help_text, default)) in enumerate(FIELDS.items()):
            row, column = divmod(index, 3)
            cell = ttk.Frame(self.body, padding=(0, 4, 12, 4))
            cell.grid(row=row, column=column, sticky="ew")
            self.selected[name] = tk.BooleanVar(parent, False)
            caption = ttk.Checkbutton(cell, text=label + " ⓘ", variable=self.selected[name], command=self.refresh)
            caption.pack(anchor="w")
            value = tk.StringVar(parent, str(default))
            self.values[name] = value
            entry = ttk.Entry(cell, textvariable=value, width=22)
            entry.pack(fill="x")
            self.entries[name] = entry
            entry.configure(state="disabled")
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

    def refresh(self):
        for name, entry in self.entries.items():
            entry.configure(state="normal" if self.selected[name].get() else "disabled")

    def read(self):
        if not self.enabled.get():
            return None
        names = tuple(key for key in FIELDS if self.selected[key].get())
        settings = SimulationSettings(**{key: float(self.values[key].get()) for key in names}, selected=names,
                                      orbital=self.orbital.get())
        settings.parameters()
        return settings
