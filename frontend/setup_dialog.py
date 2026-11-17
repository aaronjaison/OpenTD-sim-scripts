"""Explicit target selection and connection review for a prepared-copy wizard."""
import tkinter as tk
from tkinter import ttk, messagebox
from backend.sim_settings import SYMBOLS
from backend.setup_wizard import prepare_setup
from .tooltips import Tooltip
from .setup_optics import add_optical_help


class SetupDialog:
    def __init__(self, parent, catalog, settings, output, submit):
        self.catalog, self.settings, self.output, self.submit = catalog, settings, output, submit
        self.window = tk.Toplevel(parent)
        self.window.title("Connect simulation settings")
        params = settings.parameters()
        height = 300 + sum(extra for key, extra in (("initial", 230), ("heat", 130), ("emissivity", 175)) if SYMBOLS[key] in params)
        self.window.geometry(f"760x{height}")
        body = ttk.Frame(self.window, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Connect settings in a new DWG copy", style="Title.TLabel").pack(anchor="w")
        ttk.Label(body, text="Case: " + catalog.case + "   Group: " + (catalog.group or "default")).pack(anchor="w", pady=6)
        ttk.Label(body, text="Selected overrides: " + ", ".join(params), wraplength=710).pack(anchor="w")
        ttk.Label(body, text="Timing connects to the selected case. Node/load edits affect this copied model. "
                  "Emissivity affects every face using the selected coating. Review targets before creating.", wraplength=710).pack(anchor="w", pady=10)
        main = body
        body = ttk.Frame(main)
        if SYMBOLS["initial"] in params:
            body.pack(fill="both", expand=True)
        ttk.Label(body, text="Initial temperature: select nodes (all objects sharing each ID are connected)").pack(anchor="w")
        row = ttk.Frame(body)
        row.pack(fill="both", expand=True)
        self.nodes = tk.Listbox(row, selectmode="extended", exportselection=False, height=8,
            bg="#111e30", fg="#e6edf7", selectbackground="#28516c", selectforeground="#ffffff")
        self.nodes.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(row, command=self.nodes.yview)
        scrollbar.pack(side="right", fill="y")
        self.nodes.configure(yscrollcommand=scrollbar.set)
        for node in catalog.targets["nodes"]:
            self.nodes.insert("end", node)
        if SYMBOLS["initial"] not in params:
            self.nodes.configure(state="disabled")
        body = ttk.Frame(main)
        if SYMBOLS["heat"] in params:
            body.pack(fill="x")
        ttk.Label(body, text="Battery heating: existing constant heat load").pack(anchor="w", pady=(10, 2))
        self.loads = {f"{name} [{handle}, {kind}]": handle for handle, name, kind in catalog.targets["loads"]}
        self.heat = ttk.Combobox(body, values=list(self.loads), state="readonly")
        self.heat.pack(fill="x")
        if SYMBOLS["heat"] not in params:
            self.heat.configure(state="disabled")
        self.volume = tk.StringVar(body, "")
        ttk.Label(body, text="Heated volume in m³ (required only for a W total-power load)").pack(anchor="w", pady=(6, 2))
        ttk.Entry(body, textvariable=self.volume).pack(fill="x")
        Tooltip(self.heat, "Select one existing battery load. Its existing value expression is replaced. For total power: W = W/m³ × the volume represented by that load. No extra load is added.")
        body = ttk.Frame(main)
        if SYMBOLS["emissivity"] in params:
            body.pack(fill="x")
        ttk.Label(body, text="Fixed emissivity: existing VED optical coating").pack(anchor="w", pady=(10, 2))
        self.coating = ttk.Combobox(body, values=catalog.targets["optics"], state="readonly")
        self.coating.pack(fill="x")
        if SYMBOLS["emissivity"] not in params:
            self.coating.configure(state="disabled")
        else:
            add_optical_help(self, body)
        body = main
        ttk.Label(body, text="Boundary/time-varying nodes and nonconstant heat loads are excluded. "
                  "Orbital connections remain model-author settings. Existing restart blocks initial-temperature setup.", wraplength=710).pack(anchor="w", pady=10)
        buttons = ttk.Frame(body)
        buttons.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Create connected copy", command=self.create).pack(side="left")
        ttk.Button(buttons, text="Cancel", command=self.window.destroy).pack(side="right")

    def create(self):
        params = self.settings.parameters()
        nodes = tuple(self.nodes.get(i) for i in self.nodes.curselection())
        heat = self.loads.get(self.heat.get(), "")
        coating = self.coating.get()
        try:
            if SYMBOLS["initial"] in params and not nodes:
                raise ValueError("Select the nodes whose initial temperature should change.")
            if SYMBOLS["heat"] in params and not heat:
                raise ValueError("Select the existing battery heat load.")
            if SYMBOLS["emissivity"] in params and not coating:
                raise ValueError("Select the VED coating.")
            volume = float(self.volume.get() or 0) if SYMBOLS["heat"] in params else 0
        except ValueError as error:
            messagebox.showerror("Check connection targets", str(error), parent=self.window)
            return
        catalog, settings, output = self.catalog, self.settings, self.output
        self.submit(lambda: prepare_setup(catalog.drawing, catalog.case, catalog.group,
            settings, output, nodes, heat, volume, coating, catalog.targets.get("optical_database", "")))
        self.window.destroy()
