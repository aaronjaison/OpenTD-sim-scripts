"""Main desktop window; all widget updates stay on the Tk thread."""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from queue import Empty
import webbrowser
from .connections import Connections
from .graphics import theme, input_form, draw_chart
from .layout import ScrollableFrame
from .test_queue import TestQueue
from backend.config import from_fields


class Application:
    def __init__(self, root, connections=None):
        self.root, self.connections = root, connections or Connections()
        self.folder, self.samples = None, []
        root.title("OpenTD · Thermal Trial Workbench")
        root.geometry("1120x820")
        root.minsize(900, 760)
        theme(root)
        body = ttk.Frame(root, padding=20)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="ORBIT / Thermal Workbench", style="Title.TLabel").pack(anchor="w")
        ttk.Label(body, text="Configure  /  Queue  /  Explore").pack(anchor="w", pady=(0, 12))
        tabs = ttk.Notebook(body)
        tabs.pack(fill="both", expand=True)
        self.preview = ScrollableFrame(tabs)
        tabs.add(self.preview.frame, text="Thermal preview")
        self._preview(self.preview.body)
        from .opentd_panel import OpenTDPanel
        self.opentd = OpenTDPanel(tabs, self.connections.output)
        tabs.add(self.opentd.frame, text="OpenTD automation")
        self.status = tk.StringVar(root, "Ready · preview uses a single uniform-temperature body")
        ttk.Label(body, textvariable=self.status, wraplength=1020).pack(anchor="w", pady=(10, 0))
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.timer = root.after(75, self.poll)

    def _preview(self, parent):
        # CAD selection records provenance; physical properties remain explicit inputs.
        source = ttk.Frame(parent)
        source.pack(fill="x")
        self.model = tk.StringVar(parent)
        ttk.Button(source, text="Choose CAD file…", command=self.choose_model).pack(side="left")
        ttk.Entry(source, textvariable=self.model).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Label(parent, text="Optional .SLDPRT / .SLDASM reference. Geometry is not meshed; enter effective properties below.").pack(anchor="w", pady=5)
        form = ttk.Frame(parent)
        form.pack(fill="x")
        self.values = input_form(form)
        ttk.Label(parent, text="Equation names: t (s), T (K), ambient (K), pi. Functions: sin, cos, exp, sqrt, abs, min, max.").pack(anchor="w", pady=(10, 2))
        ttk.Label(parent, text="Energy balance: m·cp·dT/dt = Q − h·A·(T−Ta) − ε·σ·A·(T⁴−Ta⁴). Use smaller steps to check convergence.").pack(anchor="w")
        buttons = ttk.Frame(parent)
        buttons.pack(fill="x", pady=10)
        self.run_button = ttk.Button(buttons, text="Load saved / run preview", command=self.run)
        self.run_button.pack(side="left")
        self.cancel_button = ttk.Button(buttons, text="Cancel", command=self.connections.cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=8)
        self.open_button = ttk.Button(buttons, text="Open results folder", command=self.open_results, state="disabled")
        self.open_button.pack(side="left")
        ttk.Button(buttons, text="Queue test", command=self.run).pack(side="left", padx=8)
        ttk.Button(buttons, text="Re-run entirely", command=lambda: self.run(True)).pack(side="left")
        self.jobs = TestQueue(parent)
        self.canvas = tk.Canvas(parent, width=760, height=320, bg="#101c2e", highlightthickness=0)
        self.canvas.pack(pady=4)
        draw_chart(self.canvas, [])

    def choose_model(self):
        path = filedialog.askopenfilename(filetypes=[("SolidWorks files", "*.SLDPRT *.SLDASM *.sldprt *.sldasm")])
        if path:
            self.model.set(path)

    def run(self, force=False):
        try:
            fields = {key: value.get() for key, value in self.values.items()}
            fields = {**fields, "model": self.model.get()}
            from_fields(fields)
            self.enqueue(fields, force)
        except (ValueError, OSError) as error:
            messagebox.showerror("Check trial inputs", str(error), parent=self.root)

    def enqueue(self, fields, force):
        self.jobs.add(f"{fields['model'] or 'Manual body'} · {fields['heat']} W"
                      + (" · fresh" if force else " · reuse"),
                      lambda: self.start_preview(fields, force),
                      lambda: self.enqueue(fields, True))

    def start_preview(self, fields, force):
        self.connections.run(fields, force)
        self.run_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.status.set("Loading saved results or running preview…")

    def poll(self):
        # Drain completed events before enabling another trial.
        try:
            while True:
                kind, payload = self.connections.controller.events.get_nowait()
                self.handle_event(kind, payload)
        except Empty:
            pass
        self.jobs.pump()
        self.timer = self.root.after(75, self.poll)

    def handle_event(self, kind, payload):
        if kind == "progress":
            self.status.set(payload)
            return
        self.jobs.finish(kind)
        self.run_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        if kind == "done":
            self.samples, self.folder = payload
            draw_chart(self.canvas, self.samples)
            self.open_button.configure(state="normal")
            self.status.set(f"Results: {len(self.samples):,} samples · Final {self.samples[-1].temperature_k:.2f} K · {self.folder.name}")
        else:
            self.status.set(payload)
            if kind == "error":
                messagebox.showerror("Trial failed", payload, parent=self.root)

    def open_results(self):
        webbrowser.open(self.folder.as_uri())

    def close(self):
        # A live solver process cannot safely be terminated by closing its UI.
        if self.opentd.busy:
            messagebox.showinfo("OpenTD is running", "Wait for the OpenTD operation to finish before closing.", parent=self.root)
            return
        self.jobs.clear()
        self.connections.cancel()
        self.opentd.close()
        self.root.after_cancel(self.timer)
        self.root.destroy()
