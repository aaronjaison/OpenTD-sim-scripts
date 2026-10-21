"""Result-node dropdown with asynchronous discovery and stale-result protection."""
from pathlib import Path
from backend.node_results import ALL_NODES
from tkinter import ttk, messagebox
from backend.node_catalog import NodeCatalog, discover_nodes, validate_drawing


class NodePicker:
    def __init__(self, parent, drawing, selected, submit, output):
        self.drawing, self.selected = drawing, selected
        self.submit, self.output = submit, output
        self.combo = ttk.Combobox(parent, textvariable=selected, width=90, values=(ALL_NODES,))
        self.combo.pack(fill="x")
        ttk.Button(parent, text="Load available nodes", command=self.load).pack(anchor="w", pady=5)
        ttk.Label(parent, text="Loads nodes from a separate drawing copy without solving. Choose All nodes for every saved node and its mean over time.").pack(anchor="w")
        self.trace = drawing.trace_add("write", self.changed)

    def changed(self, *_):
        # Never offer a previous drawing's node IDs after the source changes.
        self.combo.configure(values=(ALL_NODES,))
        self.selected.set("")

    def load(self):
        try:
            drawing = str(validate_drawing(self.drawing.get()))
        except ValueError as error:
            messagebox.showerror("Choose drawing", str(error), parent=self.combo)
            return
        self.submit(lambda: discover_nodes(drawing, self.output))

    def accept(self, catalog):
        """Called only by the Tk event loop after the worker completes."""
        if str(Path(self.drawing.get()).resolve()) != catalog.drawing:
            return "Drawing changed; ignored the previous drawing's node list."
        self.combo.configure(values=(ALL_NODES, *catalog.nodes))
        if self.selected.get() not in (ALL_NODES, *catalog.nodes):
            self.selected.set(catalog.nodes[0] if catalog.nodes else "")
        return (f"Loaded {len(catalog.nodes)} available result nodes."
                if catalog.nodes else "No thermal nodes found in this drawing.")

    def close(self):
        self.drawing.trace_remove("write", self.trace)
