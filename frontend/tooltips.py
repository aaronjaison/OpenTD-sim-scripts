"""Delayed label-hover explanations with deterministic widget cleanup."""
import tkinter as tk


class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.window = widget, text, None
        self.timer = None
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<Destroy>", self.hide, add="+")

    def schedule(self, *_):
        self.hide()
        self.timer = self.widget.after(2000, self.show)

    def show(self, *_):
        self.timer = None
        if self.window is not None:
            return
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        x = min(self.widget.winfo_rootx(), max(0, self.widget.winfo_screenwidth()-380))
        y = min(self.widget.winfo_rooty()+self.widget.winfo_height()+6,
                max(0, self.widget.winfo_screenheight()-110))
        self.window.geometry(f"+{x}+{y}")
        tk.Label(self.window, text=self.text, wraplength=350, justify="left", padx=12, pady=9,
                 bg="#203047", fg="#e6edf7", font=("Segoe UI", 10)).pack()

    def hide(self, *_):
        if self.timer is not None:
            self.widget.after_cancel(self.timer)
            self.timer = None
        if self.window is not None:
            self.window.destroy()
            self.window = None
