"""Read case names and groups from an isolated drawing inspection."""
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile
from .node_catalog import validate_drawing
from . import open_td_api


@dataclass(frozen=True)
class CaseCatalog:
    drawing: str
    cases: tuple[tuple[str, str], ...]


def discover_cases(drawing, output):
    source = validate_drawing(drawing)
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="opentd-cases-", dir=root))
    copy = work / source.name
    shutil.copy2(source, copy)
    desktop = open_td_api.connect(copy)
    try:
        cases = {(str(case.Name), str(case.GroupName)) for case in desktop.GetCaseSets()}
        return CaseCatalog(str(source), tuple(sorted(cases)))
    finally:
        desktop.Quit()
