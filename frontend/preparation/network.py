"""Guided explicit nodal powers and measured node-to-node contact conductances."""
import tkinter as tk
from tkinter import ttk, messagebox
from .forms import listbox, remove_selected


class NetworkPage:
    def __init__(self, parent):
        self.loads, self.contacts = [], []
        ttk.Label(parent, text="Add real thermal connections; touching CAD faces do not prove thermal contact. "
                  "These are point-to-point conductors in W/K, not automatic face stitching.", wraplength=800).pack(anchor="w", pady=8)
        self.from_node = ttk.Combobox(parent, state="readonly")
        self.to_node = ttk.Combobox(parent, state="readonly")
        self.load_node = ttk.Combobox(parent, state="readonly")
        self.conductance = tk.StringVar(parent, "")
        self.power = tk.StringVar(parent, "")
        for label, widget in (("Contact: from node", self.from_node), ("Contact: to node", self.to_node)):
            ttk.Label(parent, text=label).pack(anchor="w"); widget.pack(fill="x", pady=3)
        ttk.Label(parent, text="Total conductance for this link · W/K").pack(anchor="w")
        ttk.Entry(parent, textvariable=self.conductance).pack(fill="x")
        ttk.Button(parent, text="Add conductor", command=self.contact).pack(anchor="w", pady=5)
        self.contact_list = listbox(parent, 4)
        ttk.Button(parent, text="Remove conductor", command=lambda: remove_selected(self.contact_list, self.contacts)).pack(anchor="w")
        ttk.Label(parent, text="Heat input: selected node").pack(anchor="w", pady=(12, 0))
        self.load_node.pack(fill="x")
        ttk.Label(parent, text="Constant power at this node · W (split total battery power across nodes)").pack(anchor="w")
        ttk.Entry(parent, textvariable=self.power).pack(fill="x")
        ttk.Button(parent, text="Add heat load", command=self.load).pack(anchor="w", pady=5)
        self.load_list = listbox(parent, 4)
        ttk.Button(parent, text="Remove heat load", command=lambda: remove_selected(self.load_list, self.loads)).pack(anchor="w")

    def populate(self, nodes):
        for widget in (self.from_node, self.to_node, self.load_node):
            widget.configure(values=nodes)

    def refresh(self):
        self.contact_list.delete(0, "end"); self.load_list.delete(0, "end")
        for link in self.contacts:
            self.contact_list.insert("end", f"{link['from']} -> {link['to']}: {link['conductance']} W/K")
        for load in self.loads:
            self.load_list.insert("end", f"{load['node']}: {load['watts']} W")

    def contact(self):
        try:
            self.contacts.append({"from": self.from_node.get(), "to": self.to_node.get(), "conductance": float(self.conductance.get())})
            self.refresh()
        except ValueError as error:
            messagebox.showerror("Check conductance", str(error), parent=self.contact_list)

    def load(self):
        try:
            self.loads.append({"node": self.load_node.get(), "watts": float(self.power.get())})
            self.refresh()
        except ValueError as error:
            messagebox.showerror("Check heat power", str(error), parent=self.load_list)
