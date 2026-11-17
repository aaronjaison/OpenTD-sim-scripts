"""Enumerate supported thermal geometry without treating CAD solids as a mesh."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
from ..setup_wizard import isolated_copy
from .. import open_td_api

GETTERS = ("Rectangles", "Cylinders", "Disks", "Cones", "Spheres", "Polygons", "MeshFDs",
           "SolidBricks", "SolidCones", "SolidCylinders", "SolidEllipsoids", "SolidSpheres",
           "LinearTris", "LinearQuads", "LinearTets", "LinearBricks", "LinearWedges", "LinearPyramids",
           "QuadraticTris", "QuadraticQuads", "QuadraticTets", "QuadraticBricks", "QuadraticWedges", "QuadraticPyramids")


@dataclass(frozen=True)
class MeshCatalog:
    drawing: str
    entities: tuple
    nodes: tuple
    heat_loads: int
    orbits: tuple = ()
    fingerprint: str = ""


def entities(desktop):
    result = {}
    for kind in GETTERS:
        for obj in getattr(desktop, "Get" + kind)():
            result[str(obj.Handle)] = obj
    return result


def inspect_mesh(drawing, output):
    copy = isolated_copy(drawing, output)
    desktop = open_td_api.connect(copy)
    try:
        objects = entities(desktop)
        nodes = tuple(sorted({f"{n.Submodel}.{n.Id}" for n in desktop.GetNodes()
                              if str(n.NodeType) == "DIFFUSION"}))
        if not objects or not nodes:
            raise ValueError("This is geometry only, or has no supported thermal mesh. Import/mesh it in TD Designer, legacy TD Direct or Thermal Desktop, save the thermal DWG, then inspect again.")
        catalog = tuple((handle, str(obj.TypeName), str(obj.Layer), str(obj.Comment)) for handle, obj in objects.items())
        return MeshCatalog(str(Path(drawing).resolve()), catalog, nodes, len(desktop.GetHeatLoads()), tuple(str(o.Name) for o in desktop.GetOrbits()), hashlib.sha256(Path(drawing).read_bytes()).hexdigest())
    finally:
        desktop.Quit()
