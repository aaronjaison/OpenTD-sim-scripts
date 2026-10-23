"""Scrollable panels keep controls usable on smaller Windows displays."""
import tkinter as tk
from tkinter import ttk


class ScrollableFrame:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.canvas = tk.Canvas(self.frame, highlightthickness=0, background="#0b1220")
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = ttk.Frame(self.canvas, padding=10)
        self.window = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.top = self.frame.winfo_toplevel()
        self.wheel_binding = self.top.bind("<MouseWheel>", self.wheel, add="+")
        self.frame.bind("<Destroy>", self.cleanup, add="+")
        self.body.bind("<Configure>", self.update_region)
        self.canvas.bind("<Configure>", self.update_width)

    def update_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_width(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)

    def wheel(self, event):
        # Only scroll this panel when the pointer is over it or its descendants.
        target = self.frame.winfo_containing(event.x_root, event.y_root)
        if target is None or not str(target).startswith(str(self.frame) + "."):
            return
        if event.delta:
            steps = -max(1, abs(int(event.delta)) // 120) * (1 if event.delta > 0 else -1)
            self.canvas.yview_scroll(steps, "units")
            return "break"

    def cleanup(self, event):
        if event.widget == self.frame:
            self.top.unbind("<MouseWheel>", self.wheel_binding)
