"""Portable preparation recipes and strict SI input/coverage validation."""
import json
import math
from pathlib import Path
import re


def source_file(path):
    source = Path(path)
    if source.suffix.lower() not in (".sldasm", ".sldprt", ".dwg") or not source.is_file():
        raise ValueError("Choose an existing SolidWorks assembly/part or DWG source.")
    return str(source.resolve())


def number(value, label, minimum=0, maximum=math.inf, positive=False):
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum or (positive and result == 0):
        raise ValueError(f"Check {label}: must be finite, within {minimum}..{maximum}" + (", and positive." if positive else "."))
    return result


def validate(recipe, catalog):
    source_file(recipe["source"])
    if Path(recipe["mesh"]).resolve() != Path(catalog.drawing):
        raise ValueError("Mesh changed; inspect the selected thermal DWG again.")
    if recipe.get("mesh_sha256", catalog.fingerprint) != catalog.fingerprint:
        raise ValueError("Mesh file changed; inspect again and review component mappings.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,39}", recipe["case"]):
        raise ValueError("Case name: start with a letter; use up to 40 letters, digits or underscores.")
    used, labels = set(), set()
    types = {e[0]: e[1].lower() for e in catalog.entities}
    for part in recipe["parts"]:
        label = part["name"]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,30}", label) or label in labels:
            raise ValueError("Component names must be unique identifiers up to 31 characters.")
        labels.add(label)
        handles = part["handles"]
        if not handles or len(set(handles)) != len(handles) or used.intersection(handles):
            raise ValueError("Assign each thermal entity to exactly one component.")
        used.update(handles)
        for field in ("density", "conductivity", "cp"):
            number(part[field], field, positive=True)
        surface = any(not any(word in types.get(h, "") for word in ("solid", "tet", "brick", "wedge", "pyramid")) for h in handles)
        number(part["thickness"], "shell thickness", positive=surface and not part["skin"])
        for field in ("alpha", "epsilon"):
            number(part[field], field, maximum=1)
    if used != {e[0] for e in catalog.entities}:
        raise ValueError("Assign materials to every inspected thermal entity; remove stale or extra assignments.")
    nodes = set(catalog.nodes)
    for load in recipe["loads"]:
        if load["node"] not in nodes:
            raise ValueError("Heat load requires a diffusion node from this mesh.")
        number(load["watts"], "heat power")
    pairs = set()
    for link in recipe["contacts"]:
        a, b = link["from"], link["to"]
        pair = tuple(sorted((a, b)))
        if a == b or not {a, b} <= nodes or pair in pairs:
            raise ValueError("Contact endpoints must be different mesh nodes; duplicate pairs are not allowed.")
        pairs.add(pair)
        number(link["conductance"], "conductance W/K", positive=True)
    env = recipe["environment"]
    for field in ("initial", "space", "duration", "output", "max_step"):
        number(env[field], field, positive=True)
    if max(float(env["output"]), float(env["max_step"])) > float(env["duration"]):
        raise ValueError("Output interval and maximum step must not exceed duration.")
    if env["mode"] not in ("Deep space", "Existing orbit"):
        raise ValueError("Choose Deep space or Existing orbit.")
    if env["mode"] == "Existing orbit" and env["orbit"] not in catalog.orbits:
        raise ValueError("Select an existing, validated orbit/attitude by name.")
    return recipe


def save_recipe(path, recipe):
    # Drafts are deliberately allowed before the mesh and assignments are complete.
    Path(path).write_text(json.dumps({"schema": 1, "recipe": recipe}, indent=2), encoding="utf-8")


def load_recipe(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("recipe"), dict):
        raise ValueError("Unsupported preparation project format.")
    return data["recipe"]
