"""Reusable Tkinter layout and plotting primitives."""
import tkinter as tk
from tkinter import ttk
from backend.config import TrialConfig
from backend.plotting import coordinates

# All editable thermal inputs carry explicit SI units.
FIELDS = [("mass", "Mass (kg)"), ("specific_heat", "Specific heat (J/kg/K)"),
          ("area", "Surface area (m²)"), ("convection", "Convection (W/m²/K)"),
          ("emissivity", "Emissivity (0–1)"), ("initial", "Initial temperature (K)"),
          ("ambient", "Ambient temperature (K)"), ("duration", "Duration (s)"),
          ("step", "Time step (s)"), ("heat", "Heat input Q(t,T) (W)")]


def theme(root):
    """Apply a readable desktop theme without extra dependencies."""
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background="#edf2f7")
    style.configure("TLabel", background="#edf2f7", foreground="#16283e", font=("Segoe UI", 10))
    style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
    style.configure("TButton", padding=(12, 7), font=("Segoe UI", 10))
    style.configure("TNotebook.Tab", padding=(14, 7))
    root.configure(background="#edf2f7")


def input_form(parent):
    """Create a two-column form and return its independent StringVars."""
    defaults = TrialConfig()
    values = {}
    for index, (key, label) in enumerate(FIELDS):
        row, column = divmod(index, 2)
        ttk.Label(parent, text=label).grid(row=row*2, column=column, sticky="w", padx=8, pady=(8, 2))
        values[key] = tk.StringVar(parent, value=str(getattr(defaults, key)))
        ttk.Entry(parent, textvariable=values[key], width=28).grid(
            row=row*2+1, column=column, sticky="ew", padx=8)
    parent.columnconfigure((0, 1), weight=1)
    return values


def draw_chart(canvas, samples):
    """Draw temperature history with labels; bound drawing work to 1,002 points."""
    canvas.delete("all")
    if not samples:
        canvas.create_text(380, 145, text="Run a trial to see temperature over time",
                           fill="#b4c5d8", font=("Segoe UI", 14))
        return
    stride = max(1, (len(samples) + 998)//1000)
    full_coordinates = coordinates(samples)
    points = full_coordinates[::stride]
    if points[-1] != full_coordinates[-1]:
        points = [*points, full_coordinates[-1]]
    canvas.create_line(60, 35, 60, 275, 730, 275, fill="#61748c")
    if len(points) > 1:
        canvas.create_line(*[v for point in points for v in point], fill="#55d6be", width=2)
    x, y = points[-1]
    canvas.create_oval(x-3, y-3, x+3, y+3, fill="#55d6be", outline="")
    for x, y, text in [(62, 18, "Temperature (K)"), (680, 303, f"{samples[-1].time_s:g} s"),
                        (62, 303, f"{samples[0].time_s:g} s"),
                        (40, 45, f"{max(s.temperature_k for s in samples):.1f}"),
                        (40, 270, f"{min(s.temperature_k for s in samples):.1f}")]:
        canvas.create_text(x, y, text=text, fill="#e8eff7", font=("Segoe UI", 10))
