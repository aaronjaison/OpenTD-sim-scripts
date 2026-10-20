"""Shared real-Tk fixture; tests never need a licensed solver."""
import tkinter as tk
import pytest


@pytest.fixture
def root():
    window = tk.Tk()
    window.withdraw()
    yield window
    try:
        window.destroy()
    except tk.TclError:
        pass
