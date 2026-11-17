"""Explicit baseline boundary, solver settings and existing orbit selection."""
from tkinter import ttk
from .forms import fields


class EnvironmentPage:
    def __init__(self, parent):
        ttk.Label(parent, text="Start with a deep-space baseline or select a validated orbit/attitude in the mesh DWG. "
                  "Orbit creation and CAD meshing use the vendor tools; this screen does not infer pointing.", wraplength=800).pack(anchor="w", pady=8)
        self.mode = ttk.Combobox(parent, values=("Deep space", "Existing orbit"), state="readonly")
        self.mode.set("Deep space"); self.mode.pack(fill="x", pady=6)
        ttk.Label(parent, text="Existing orbit name (required for orbital mode)").pack(anchor="w")
        self.orbit = ttk.Combobox(parent, state="readonly"); self.orbit.pack(fill="x", pady=6)
        body = ttk.Frame(parent); body.pack(fill="x")
        self.values = fields(body, [
            ("initial", "Initial temperature · K", 293, "Starting temperature of diffusion nodes; existing boundary nodes stay unchanged."),
            ("space", "Space boundary · K", 3, "Radiation sink temperature. A new PREP_SPACE boundary is created."),
            ("duration", "Duration · s", 3300, "Transient end time, starting at zero."),
            ("output", "Save interval · s", 10, "Saved-result interval, independent of integration step."),
            ("max_step", "Maximum solver step · s", 1, "Upper step control for the baseline automatic transient solver.")])
        ttk.Label(parent, text="Deep space adds radiation exchange and emission, without solar/albedo/Earth-IR heating. "
                  "Orbital mode additionally uses the selected orbit's existing environment and attitude. "
                  "Neither mode implies thermal equilibrium.", wraplength=800).pack(anchor="w", pady=12)

    def read(self):
        return dict({key: float(value.get()) for key, value in self.values.items()}, mode=self.mode.get(), orbit=self.orbit.get())

    def restore(self, values):
        for key, value in self.values.items(): value.set(values[key])
        self.mode.set(values["mode"]); self.orbit.set(values["orbit"])
