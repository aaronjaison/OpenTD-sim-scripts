"""Inspect available thermal nodes without running or modifying the source model."""
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile
from . import open_td_api


@dataclass(frozen=True)
class NodeCatalog:
    drawing: str
    nodes: tuple[str, ...]


def validate_drawing(drawing):
    path = Path(drawing)
    if path.suffix.lower() != ".dwg" or not path.is_file():
        raise ValueError("Choose an existing Thermal Desktop .dwg before loading nodes.")
    return path.resolve()


def discover_nodes(drawing, output):
    """Use a separate copy/process; shared-temperature IDs appear only once."""
    source = validate_drawing(drawing)
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="opentd-nodes-", dir=root))
    copy = work / source.name
    shutil.copy2(source, copy)
    desktop = open_td_api.connect(copy)
    try:
        nodes = {(str(node.Submodel), int(node.Id)) for node in desktop.GetNodes()}
        ordered = sorted(nodes, key=lambda node: (node[0].casefold(), node[0], node[1]))
        return NodeCatalog(str(source), tuple(f"{submodel}.{identifier}" for submodel, identifier in ordered))
    finally:
        # Only the inspection instance is closed; user's open drawings are untouched.
        desktop.Quit()
