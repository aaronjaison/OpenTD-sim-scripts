"""Small labeled SI forms and editable lists used by preparation stages."""
import tkinter as tk
from tkinter import ttk
from ..tooltips import Tooltip


def fields(parent, definitions):
    result = {}
    for row, (key, label, value, help_text) in enumerate(definitions):
        caption = ttk.Label(parent, text=label + " ⓘ")
        caption.grid(row=row, column=0, sticky="w", padx=4, pady=5)
        Tooltip(caption, help_text)
        result[key] = tk.StringVar(parent, str(value))
        ttk.Entry(parent, textvariable=result[key], width=32).grid(row=row, column=1, sticky="ew", padx=4, pady=5)
    parent.columnconfigure(1, weight=1)
    return result


def listbox(parent, height=7):
    row = ttk.Frame(parent)
    row.pack(fill="both", expand=True, pady=6)
    box = tk.Listbox(row, height=height, selectmode="extended", exportselection=False,
                     bg="#111e30", fg="#e6edf7", selectbackground="#28516c")
    bar = ttk.Scrollbar(row, command=box.yview)
    box.configure(yscrollcommand=bar.set)
    box.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    return box


def remove_selected(box, items):
    for index in reversed(box.curselection()):
        del items[index]
        box.delete(index)
