"""Prepared-case controls and background OpenTD operations."""
from queue import Queue, Empty
from threading import Thread
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
from .layout import ScrollableFrame
from .sim_form import SimulationForm
from .tooltips import Tooltip
from .test_queue import TestQueue
from .node_picker import NodePicker, NodeCatalog
from backend.reuse import reuse_or_run
from backend.open_td_api import diagnostics
from backend.opentd_trials import OpenTDRequest, run_prepared


class OpenTDPanel:
    def __init__(self, parent, output):
        self.output, self.events, self.busy = output, Queue(), False
        self.container = ScrollableFrame(parent)
        self.frame = self.container.frame
        body = self.container.body
        ttk.Label(body, text="MISSION / Thermal Desktop", style="Title.TLabel").pack(anchor="w")
        ttk.Label(body, text="Import/mesh your SolidWorks geometry in Thermal Desktop first. This runs a separate DWG copy.\nKeep referenced meshes, materials and assemblies available at their original paths.", wraplength=950).pack(anchor="w", pady=12)
        self.values = {}
        for key, label in [("drawing", "Prepared drawing (.dwg)"), ("case", "Exact case name"),
                           ("group", "Case group (optional)"), ("node", "Result node")]:
            ttk.Label(body, text=label).pack(anchor="w", pady=(8, 2))
            value = tk.StringVar(self.frame)
            self.values[key] = value
            if key == "node":
                self.nodes = NodePicker(body, self.values["drawing"], value, self.load_nodes, output)
            else:
                entry = ttk.Entry(body, textvariable=value, width=90)
                entry.pack(fill="x")
                Tooltip(entry, {"drawing": "Prepared Thermal Desktop DWG. Runs use a copy; external references must remain accessible.",
                    "case": "Exact name of an existing case set in the drawing.",
                    "group": "Case-set group; leave blank for the default group."}[key])
        ttk.Button(body, text="Choose drawing…", command=self.choose).pack(anchor="w", pady=8)
        self.simulation = SimulationForm(body)
        ttk.Label(body, text="Advanced symbol overrides: one NAME=expression per line (Thermal Desktop syntax)").pack(anchor="w")
        self.overrides = tk.Text(body, height=3, font=("Consolas", 10), bg="#111e30", fg="#e6edf7", insertbackground="#7dd3fc", relief="flat")
        self.overrides.pack(fill="x", pady=6)
        controls = ttk.Frame(body)
        controls.pack(fill="x", pady=10)
        self.check_button = ttk.Button(controls, text="Check OpenTD installation", command=self.check)
        self.check_button.pack(side="left")
        self.run_button = ttk.Button(controls, text="Load saved / run case", command=self.run)
        self.run_button.pack(side="left", padx=8)
        self.open_button = ttk.Button(controls, text="Open results", command=self.open_results, state="disabled")
        self.open_button.pack(side="left")
        ttk.Button(controls, text="Queue test", command=self.run).pack(side="left", padx=8)
        ttk.Button(controls, text="Re-run entirely", command=lambda: self.run(True)).pack(side="left")
        self.jobs = TestQueue(body)
        self.status = tk.StringVar(self.frame, "OpenTD 2026 R1 / AutoCAD 2024 default · Requires installed and licensed AutoCAD, Thermal Desktop and SINDA.")
        ttk.Label(body, textvariable=self.status, wraplength=950).pack(anchor="w", pady=12)
        Tooltip(self.overrides, "Optional NAME=expression overrides. Do not duplicate enabled simulation parameters. Symbols must already control the intended model properties.")
        Tooltip(self.run_button, "Load matching saved results, or run a new case if none exist.")
        Tooltip(self.check_button, "Check the installed OpenTD runtime without launching a simulation.")
        self.timer = self.frame.after(100, self.poll)

    def choose(self):
        path = filedialog.askopenfilename(filetypes=[("Thermal Desktop drawing", "*.dwg")])
        if path:
            self.values["drawing"].set(path)

    def load_nodes(self, operation):
        self.jobs.add("Load available result nodes", lambda: self.start(operation))

    def check(self):
        if not self.busy:
            self.jobs.add("Installation check", lambda: self.start(diagnostics))

    def run(self, force=False):
        try:
            request = OpenTDRequest(**{key: value.get() for key, value in self.values.items()},
                                    overrides=self.overrides.get("1.0", "end"), settings=self.simulation.read()).validate()
            self.enqueue(request, force)
        except ValueError as error:
            messagebox.showerror("Check OpenTD inputs", str(error), parent=self.frame)

    def enqueue(self, request, force):
        progress = lambda text: self.events.put(("progress", text))
        operation = lambda: reuse_or_run(request, self.output,
            lambda: run_prepared(request, self.output, progress), progress, force)
        self.jobs.add(f"{request.case} · {request.node}" + (" · fresh" if force else " · reuse"),
                      lambda: self.start(operation), lambda: self.enqueue(request, True))

    def start(self, operation):
        if self.busy:
            return
        self.busy = True
        self.run_button.configure(state="disabled")
        self.check_button.configure(state="disabled")
        self.status.set("Working…")
        Thread(target=self.work, args=(operation,), daemon=True).start()

    def work(self, operation):
        try:
            self.events.put(("done", operation()))
        except Exception as error:
            self.events.put(("error", str(error)))

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "progress":
                    self.status.set(value)
                    continue
                self.busy = False
                self.jobs.finish(kind)
                self.run_button.configure(state="normal")
                self.check_button.configure(state="normal")
                if kind == "done" and isinstance(value, NodeCatalog):
                    self.status.set(self.nodes.accept(value))
                elif kind == "done" and isinstance(value, tuple):
                    _, self.folder = value
                    self.open_button.configure(state="normal")
                    self.status.set(f"OpenTD results saved: {self.folder}")
                else:
                    self.status.set(value)
        except Empty:
            pass
        self.jobs.pump()
        self.timer = self.frame.after(100, self.poll)

    def open_results(self):
        webbrowser.open(self.folder.as_uri())

    def close(self):
        self.nodes.close()
        self.frame.after_cancel(self.timer)
