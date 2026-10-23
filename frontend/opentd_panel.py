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
from .case_picker import CasePicker, CaseCatalog
from backend.reuse import reuse_or_run
from backend.open_td_api import diagnostics
from backend.opentd_trials import OpenTDRequest, run_prepared


class OpenTDPanel:
    def __init__(self, parent, output):
        self.output, self.events, self.busy = output, Queue(), False
        self.container = ScrollableFrame(parent)
        self.frame = self.container.frame
        body = self.container.body
        ttk.Label(body, text="ORBIT / Thermal Workbench", style="Title.TLabel").pack(anchor="w")
        ttk.Label(body, text="01  Choose DWG     /     02  Set simulation     /     03  Queue tests", wraplength=950).pack(anchor="w", pady=12)
        self.values = {key: tk.StringVar(self.frame) for key in ("drawing", "case", "group", "node")}
        for key, label in [("drawing", "Prepared drawing (.dwg)"), ("case", "Exact case name"),
                           ("group", "Case group (optional)"), ("node", "Result node")]:
            caption = ttk.Label(body, text=label)
            caption.pack(anchor="w", pady=(8, 2))
            value = self.values[key]
            Tooltip(caption, {"drawing": "Prepared DWG; runs use a copy.", "case": "Load existing case sets from this drawing; selecting one also sets its group.", "group": "Group of the selected case; blank means default.", "node": "Select one result node or All nodes for all saved temperatures and their mean."}[key])
            if key == "node":
                self.nodes = NodePicker(body, self.values["drawing"], value, self.load_nodes, output)
            elif key == "case":
                self.cases = CasePicker(body, self.values, self.load_nodes, output)
            else:
                row = ttk.Frame(body)
                row.pack(fill="x")
                entry = ttk.Entry(row, textvariable=value, width=90)
                entry.pack(side="left", fill="x", expand=True)
                if key == "drawing":
                    ttk.Button(row, text="Choose DWG…", command=self.choose).pack(side="left", padx=(8, 0))
        self.simulation = SimulationForm(body)
        advanced = ttk.Label(body, text="Advanced symbol overrides ⓘ")
        advanced.pack(anchor="w")
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
        ttk.Button(controls, text="Add to queue", command=self.run).pack(side="left", padx=8)
        ttk.Button(controls, text="Re-run entirely", command=lambda: self.run(True)).pack(side="left")
        self.jobs = TestQueue(body)
        self.status = tk.StringVar(self.frame, "OpenTD 2026 R1 / AutoCAD 2024 default · Requires installed and licensed AutoCAD, Thermal Desktop and SINDA.")
        ttk.Label(body, textvariable=self.status, wraplength=950).pack(anchor="w", pady=12)
        Tooltip(advanced, "Optional NAME=expression overrides. Do not duplicate enabled simulation parameters. Symbols must already control the intended model properties.")
        self.timer = self.frame.after(100, self.poll)

    def choose(self):
        path = filedialog.askopenfilename(filetypes=[("Thermal Desktop drawing", "*.dwg")])
        if path:
            self.values["drawing"].set(path)

    def load_nodes(self, operation):
        self.jobs.add("Inspect drawing", lambda: self.start(operation))

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
                elif kind == "done" and isinstance(value, CaseCatalog):
                    self.status.set(self.cases.accept(value))
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
        self.cases.close()
        self.frame.after_cancel(self.timer)
