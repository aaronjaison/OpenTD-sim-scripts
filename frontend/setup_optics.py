"""Recover a missing optical catalog explicitly instead of showing a silent blank."""
from tkinter import ttk, filedialog
from backend.setup_wizard import inspect_setup, SetupCatalog


def add_optical_help(dialog, parent):
    empty = not dialog.catalog.targets["optics"]
    text = ("No coatings found in this case's optical database. Select the model's actual .rco file below, "
            "or restore/create and assign its coating in Thermal Desktop, then reopen the wizard.") if empty else (
            "Choose the coating already assigned to the intended faces. You can load a different model database below.")
    ttk.Label(parent, text=text, wraplength=710).pack(anchor="w", pady=6)
    ttk.Button(parent, text="Load optical database…", command=lambda: choose_database(dialog)).pack(anchor="w")
    ttk.Label(parent, text="Loading a database does not assign coatings to surfaces. Keep the model's material names consistent.",
              wraplength=710).pack(anchor="w", pady=4)


def choose_database(dialog):
    path = filedialog.askopenfilename(parent=dialog.window, title="Choose this model's optical database",
                                     filetypes=[("RadCAD optical database", "*.rco")])
    if not path:
        return
    catalog, settings, output = dialog.catalog, dialog.settings, dialog.output
    def inspect():
        result = inspect_setup(catalog.drawing, catalog.case, catalog.group, output, optical_database=path)
        return SetupCatalog(result.drawing, result.case, result.group, dict(result.targets, settings=settings))
    dialog.submit(inspect)
    dialog.window.destroy()
