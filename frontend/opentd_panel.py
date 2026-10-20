"""Prepared-case controls and background OpenTD operations."""
from queue import Queue, Empty
from threading import Thread
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
from backend.open_td_api import diagnostics
from backend.opentd_trials import OpenTDRequest, run_prepared


class OpenTDPanel:
    def __init__(self, parent, output):
        self.output, self.events, self.busy = output, Queue(), False
        self.frame = ttk.Frame(parent, padding=18)
        ttk.Label(self.frame, text="Run a prepared Thermal Desktop case", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.frame, text="Import/mesh your SolidWorks geometry in Thermal Desktop first. This runs a separate DWG copy.\nKeep referenced meshes, materials and assemblies available at their original paths.", wraplength=950).pack(anchor="w", pady=12)
        self.values = {}
        for key, label in [("drawing", "Prepared drawing (.dwg)"), ("case", "Exact case name"),
                           ("group", "Case group (optional)"), ("node", "Result node (e.g. MAIN.1)")]:
            ttk.Label(self.frame, text=label).pack(anchor="w", pady=(8, 2))
            value = tk.StringVar(self.frame)
            self.values[key] = value
            ttk.Entry(self.frame, textvariable=value, width=90).pack(fill="x")
        ttk.Button(self.frame, text="Choose drawing…", command=self.choose).pack(anchor="w", pady=8)
        ttk.Label(self.frame, text="Case symbol overrides: one NAME=expression per line (Thermal Desktop syntax)").pack(anchor="w")
        self.overrides = tk.Text(self.frame, height=7, font=("Consolas", 11))
        self.overrides.pack(fill="x", pady=6)
        controls = ttk.Frame(self.frame)
        controls.pack(fill="x", pady=10)
        self.check_button = ttk.Button(controls, text="Check OpenTD installation", command=self.check)
        self.check_button.pack(side="left")
        self.run_button = ttk.Button(controls, text="Run prepared case", command=self.run)
        self.run_button.pack(side="left", padx=8)
        self.open_button = ttk.Button(controls, text="Open results", command=self.open_results, state="disabled")
        self.open_button.pack(side="left")
        self.status = tk.StringVar(self.frame, "OpenTD 2026 R1 / .NET 8 · Requires installed and licensed AutoCAD, Thermal Desktop and SINDA.")
        ttk.Label(self.frame, textvariable=self.status, wraplength=950).pack(anchor="w", pady=12)
        self.timer = self.frame.after(100, self.poll)

    def choose(self):
        path = filedialog.askopenfilename(filetypes=[("Thermal Desktop drawing", "*.dwg")])
        if path:
            self.values["drawing"].set(path)

    def check(self):
        self.start(diagnostics)

    def run(self):
        try:
            request = OpenTDRequest(**{key: value.get() for key, value in self.values.items()},
                                    overrides=self.overrides.get("1.0", "end")).validate()
            self.start(lambda: run_prepared(request, self.output,
                       lambda text: self.events.put(("progress", text))))
        except ValueError as error:
            messagebox.showerror("Check OpenTD inputs", str(error), parent=self.frame)

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
                self.run_button.configure(state="normal")
                self.check_button.configure(state="normal")
                if kind == "done" and isinstance(value, tuple):
                    _, self.folder = value
                    self.open_button.configure(state="normal")
                    self.status.set(f"OpenTD results saved: {self.folder}")
                else:
                    self.status.set(value)
        except Empty:
            pass
        self.timer = self.frame.after(100, self.poll)

    def open_results(self):
        webbrowser.open(self.folder.as_uri())

    def close(self):
        self.frame.after_cancel(self.timer)
