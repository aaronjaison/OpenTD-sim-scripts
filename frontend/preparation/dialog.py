"""Five-stage preparation project: source, material map, network, environment, review."""
import copy
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from backend.preparation.project import source_file, save_recipe, load_recipe, validate
from .materials import MaterialsPage
from .network import NetworkPage
from .environment import EnvironmentPage
from ..layout import ScrollableFrame


class PreparationDialog:
    def __init__(self, parent, inspect, submit):
        self.inspect, self.submit, self.catalog = inspect, submit, None
        self.fingerprint = ""
        self.window = tk.Toplevel(parent); self.window.title("Prepare a thermal model")
        self.window.geometry("1000x820")
        self.source, self.mesh, self.case = (tk.StringVar(self.window, v) for v in ("", "", "ORBIT_Base"))
        book = ttk.Notebook(self.window); book.pack(fill="both", expand=True, padx=12, pady=12)
        pages = []
        for name in ("1 Source / mesh", "2 Materials", "3 Contacts / heat", "4 Environment", "5 Build / review"):
            scroll = ScrollableFrame(book); book.add(scroll.frame, text=name); pages.append(scroll.body)
        self.source_page(pages[0])
        self.materials = MaterialsPage(pages[1]); self.network = NetworkPage(pages[2])
        self.environment = EnvironmentPage(pages[3])
        self.status = tk.StringVar(self.window, "Select the source CAD and an inspected thermal mesh before building.")
        ttk.Label(pages[4], textvariable=self.status, wraplength=900).pack(anchor="w", pady=12)
        ttk.Label(pages[4], text="Review every material, shell thickness, exposed coating, node contact and heat input. "
                  "Existing heat loads/conductors in the mesh remain active. The output is a new transient case and private property files. "
                  "Run a baseline and convergence checks before engineering use.", wraplength=900).pack(anchor="w", pady=12)
        ttk.Button(pages[4], text="Build prepared model copy", command=self.build).pack(anchor="w")
        row = ttk.Frame(self.window); row.pack(fill="x", padx=12, pady=8)
        ttk.Button(row, text="Save project draft…", command=self.save).pack(side="left")
        ttk.Button(row, text="Load project draft…", command=self.load).pack(side="left", padx=8)
        ttk.Button(row, text="Close", command=self.window.destroy).pack(side="right")

    def source_page(self, page):
        ttk.Label(page, text="Start with SolidWorks (.SLDASM/.SLDPRT) or a DWG. Keep assembly references together. "
                  "This version guides the CAD/meshing handoff; it does not automatically mesh raw CAD.", wraplength=900).pack(anchor="w", pady=12)
        for label, var, filters in (("Source CAD", self.source, [("Supported CAD", "*.sldasm *.sldprt *.dwg")]),
                                    ("Thermal mesh DWG", self.mesh, [("Thermal Desktop DWG", "*.dwg")])):
            ttk.Label(page, text=label).pack(anchor="w", pady=(8, 2))
            row = ttk.Frame(page); row.pack(fill="x")
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
            ttk.Button(row, text="Choose…", command=lambda v=var, f=filters: self.choose(v, f)).pack(side="left", padx=8)
        ttk.Label(page, text="CAD handoff: in TD Direct/SpaceClaim, import the SolidWorks assembly (or raw DWG), "
                  "simplify unwanted small features, verify model units, create a thermal surface/solid mesh, "
                  "retain component/layer names and save its Thermal Desktop DWG. Return here and select that DWG. "
                  "A DWG already containing thermal entities can be used directly. Plain CAD solids are blocked.", wraplength=900).pack(anchor="w", pady=16)
        ttk.Label(page, text="TD Direct/SpaceClaim and CAD translators may need separate installation/licensing. "
                  "This wizard does not install software or fabricate a mesh.", wraplength=900).pack(anchor="w", pady=8)
        ttk.Label(page, text="New case name").pack(anchor="w")
        ttk.Entry(page, textvariable=self.case).pack(fill="x", pady=4)
        ttk.Button(page, text="Inspect thermal mesh", command=self.scan).pack(anchor="w", pady=12)

    def choose(self, variable, filters):
        path = filedialog.askopenfilename(parent=self.window, filetypes=filters)
        if path: variable.set(path)

    def recipe(self):
        return {"source": self.source.get(), "mesh": self.mesh.get(), "case": self.case.get(),
                "mesh_sha256": self.fingerprint, "parts": copy.deepcopy(self.materials.parts), "loads": copy.deepcopy(self.network.loads),
                "contacts": copy.deepcopy(self.network.contacts), "environment": self.environment.read()}

    def scan(self):
        try:
            source_file(self.source.get())
            self.inspect(self.mesh.get())
        except ValueError as error:
            messagebox.showerror("Check preparation source", str(error), parent=self.window)

    def accept(self, catalog):
        if catalog.drawing != str(Path(self.mesh.get()).resolve()):
            return "Mesh changed; ignored previous inspection."
        if self.fingerprint and self.fingerprint != catalog.fingerprint:
            self.materials.parts = []; self.materials.refresh()
            self.network.loads, self.network.contacts = [], []; self.network.refresh()
        self.fingerprint = catalog.fingerprint
        self.catalog = catalog
        self.materials.populate(catalog); self.network.populate(catalog.nodes)
        self.environment.orbit.configure(values=catalog.orbits)
        text = f"Inspected {len(catalog.entities)} thermal entities and {len(catalog.nodes)} diffusion node IDs. Existing heat loads retained: {catalog.heat_loads}."
        self.status.set(text)
        return text

    def build(self):
        try:
            if self.catalog is None:
                raise ValueError("Inspect the thermal mesh before building.")
            recipe = validate(self.recipe(), self.catalog)
            self.submit(recipe)
        except ValueError as error:
            messagebox.showerror("Check preparation", str(error), parent=self.window)

    def save(self):
        path = filedialog.asksaveasfilename(parent=self.window, defaultextension=".json", filetypes=[("Preparation project", "*.json")])
        if path:
            try: save_recipe(path, self.recipe())
            except (ValueError, OSError) as error: messagebox.showerror("Save project", str(error), parent=self.window)

    def load(self):
        path = filedialog.askopenfilename(parent=self.window, filetypes=[("Preparation project", "*.json")])
        if not path: return
        try:
            recipe = load_recipe(path)
            self.environment.restore(recipe["environment"])
            self.source.set(recipe["source"]); self.mesh.set(recipe["mesh"]); self.case.set(recipe["case"])
            self.materials.parts = recipe["parts"]; self.materials.refresh()
            self.network.loads, self.network.contacts = recipe["loads"], recipe["contacts"]; self.network.refresh()
            self.fingerprint = recipe.get("mesh_sha256", "")
            self.catalog = None
            self.status.set("Project loaded. Inspect the mesh again before building.")
        except (ValueError, KeyError, OSError) as error:
            messagebox.showerror("Load project", str(error), parent=self.window)
