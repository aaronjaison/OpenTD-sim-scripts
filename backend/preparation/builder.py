"""Build a reviewable thermal model in a new folder, never overwrite CAD inputs."""
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
from .. import open_td_api
from ..setup_wizard import isolated_copy, SetupResult
from .geometry import inspect_mesh, entities
from .project import validate, save_recipe
from .properties import assign, databases
from .environment import case_and_environment, loads_and_contacts


def build(recipe, output):
    mesh = inspect_mesh(recipe["mesh"], output)
    validate(recipe, mesh)
    drawing = isolated_copy(recipe["mesh"], output)
    desktop = open_td_api.connect(drawing)
    try:
        api = open_td_api.load_api()
        objects = entities(desktop)
        if set(objects) != {e[0] for e in mesh.entities}:
            raise ValueError("Mesh changed during preparation; inspect it again.")
        databases(desktop, drawing.parent)
        desktop.RadiationAnalysisGroupManager.CreateOrUpdate("PREP_RADIATION", "Guided preparation surfaces")
        assign(desktop, api, objects, recipe["parts"], "PREP_RADIATION")
        # Use one physical endpoint for each shared ID; reject conflicting duplicates.
        nodes = {}
        for node in desktop.GetNodes():
            if str(node.NodeType) != "DIFFUSION":
                continue
            key = f"{node.Submodel}.{node.Id}"
            nodes[key] = node
        loads_and_contacts(desktop, api, recipe, nodes)
        case_and_environment(desktop, api, recipe, nodes, drawing.parent)
        desktop.SaveAs(str(drawing))
        report = drawing.with_name("preparation.json")
        save_recipe(drawing.with_name("project.json"), recipe)
        evidence = {"source": recipe["source"], "mesh": mesh.drawing, "drawing": str(drawing),
                    "case": recipe["case"], "recipe": recipe, "mesh_catalog": asdict(mesh),
                    "source_sha256": hashlib.sha256(Path(recipe["source"]).read_bytes()).hexdigest(),
                    "mesh_sha256": hashlib.sha256(Path(mesh.drawing).read_bytes()).hexdigest(),
                    "status": "Model authored; baseline solve, contact/mesh review and convergence checks still required.",
                    "meshing": "User-supplied TD mesh; no automatic SolidWorks tessellation or contact inference.",
                    "existing_heat_loads_retained": mesh.heat_loads}
        report.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        return SetupResult(str(drawing), recipe["case"], "", str(report), recipe["mesh"])
    finally:
        desktop.Quit()
