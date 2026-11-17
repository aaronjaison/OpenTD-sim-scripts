"""Choose an existing case and its exact group from the prepared drawing."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from backend.case_catalog import CaseCatalog, discover_cases
from backend.node_catalog import validate_drawing


class CasePicker:
    def __init__(self, parent, values, submit, output):
        self.values, self.submit, self.output = values, submit, output
        self.cases = ()
        self.display = tk.StringVar(parent)
        row = ttk.Frame(parent)
        row.pack(fill="x")
        self.combo = ttk.Combobox(row, textvariable=self.display, state="readonly")
        self.combo.pack(side="left", fill="x", expand=True)
        self.combo.bind("<<ComboboxSelected>>", self.select)
        ttk.Button(row, text="Load case names", command=self.load).pack(side="left", padx=(8, 0))
        self.trace = values["drawing"].trace_add("write", self.changed)

    def changed(self, *_):
        self.cases = ()
        self.combo.configure(values=())
        self.display.set("")
        self.values["case"].set("")
        self.values["group"].set("")

    def load(self):
        try:
            drawing = str(validate_drawing(self.values["drawing"].get()))
        except ValueError as error:
            messagebox.showerror("Choose drawing", str(error), parent=self.combo)
            return
        self.submit(lambda: discover_cases(drawing, self.output))

    def accept(self, catalog):
        if str(Path(self.values["drawing"].get()).resolve()) != catalog.drawing:
            return "Drawing changed; ignored the previous case list."
        old = (self.values["case"].get(), self.values["group"].get())
        self.cases = catalog.cases
        self.combo.configure(values=tuple(f"{name}  [group: {group or '(default)'}]" for name, group in self.cases))
        if self.cases:
            self.combo.current(self.cases.index(old) if old in self.cases else 0)
            self.select()
        else:
            self.changed()
        return f"Loaded {len(self.cases)} case sets."

    def select(self, *_):
        index = self.combo.current()
        if index >= 0:
            name, group = self.cases[index]
            self.values["case"].set(name)
            self.values["group"].set(group)

    def close(self):
        self.values["drawing"].trace_remove("write", self.trace)
