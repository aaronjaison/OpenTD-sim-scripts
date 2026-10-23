"""Main-thread FIFO controls; each job retains its submitted configuration."""
from collections import deque
import tkinter as tk
from tkinter import ttk


class TestQueue:
    __test__ = False

    def __init__(self, parent):
        self.pending = deque()
        self.active = None
        self.reruns = {}
        self.items = tk.Listbox(parent, height=3, exportselection=False, bg="#111e30", fg="#dbe7f5", selectbackground="#28506b", relief="flat", highlightthickness=0)
        self.items.pack(fill="x", pady=5)
        ttk.Button(parent, text="Re-run selected test entirely", command=self.rerun_selected).pack(anchor="w")
        ttk.Button(parent, text="Remove waiting tests", command=self.clear).pack(anchor="w")

    def add(self, label, operation, rerun=None):
        index = self.items.size()
        self.reruns[index] = rerun
        self.items.insert("end", f"Waiting · {label}")
        self.pending.append((index, label, operation))
        self.pump()

    def rerun_selected(self):
        selected = self.items.curselection()
        if selected and self.reruns[selected[0]] is not None:
            self.reruns[selected[0]]()

    def pump(self):
        if self.active is not None or not self.pending:
            return
        index, label, operation = self.pending.popleft()
        self.active = (index, label)
        self.replace(index, f"Running · {label}")
        try:
            operation()
        except (ValueError, OSError) as error:
            self.finish(f"Failed: {error}")

    def replace(self, index, text):
        self.items.delete(index)
        self.items.insert(index, text)

    def finish(self, status):
        if self.active is not None:
            index, label = self.active
            self.replace(index, f"{status} · {label}")
            self.active = None

    def clear(self):
        while self.pending:
            index, label, _ = self.pending.popleft()
            self.replace(index, f"Removed · {label}")
