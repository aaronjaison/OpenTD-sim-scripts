"""Scrollable panels keep controls usable on smaller Windows displays."""
import tkinter as tk
from tkinter import ttk


class ScrollableFrame:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.canvas = tk.Canvas(self.frame, highlightthickness=0, background="#edf2f7")
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = ttk.Frame(self.canvas, padding=10)
        self.window = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", self.update_region)
        self.canvas.bind("<Configure>", self.update_width)

    def update_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_width(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)
