"""Use one Tcl interpreter with independent top-level test windows."""
import tkinter as tk
import pytest


@pytest.fixture(scope="session")
def tk_session():
    window = tk.Tk()
    window.withdraw()
    yield window
    window.destroy()


@pytest.fixture
def root(tk_session):
    window = tk.Toplevel(tk_session)
    window.withdraw()
    yield window
    if window.winfo_exists():
        window.destroy()
