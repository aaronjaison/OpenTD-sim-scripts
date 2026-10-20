"""Run a prepared Thermal Desktop case in a dedicated working directory."""
from dataclasses import asdict, dataclass
from pathlib import Path
import math
import re
import shutil
import tempfile
from . import open_td_api
from .config import TrialConfig
from .results_interp import save_results
from .solver import Sample


@dataclass(frozen=True)
class OpenTDRequest:
    drawing: str
    case: str
    node: str
    group: str = ""
    overrides: str = ""

    def validate(self):
        path = Path(self.drawing)
        if path.suffix.lower() != ".dwg" or not path.is_file():
            raise ValueError("Select a prepared Thermal Desktop .dwg file.")
        if not self.case.strip() or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*\.\d+", self.node):
            raise ValueError("Enter the exact case name and a node such as MAIN.1.")
        parse_overrides(self.overrides)
        return self


def parse_overrides(text):
    """Validate one unique symbol=expression override per line."""
    result = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        name, separator, expression = line.partition("=")
        name, expression = name.strip(), expression.strip()
        if not separator or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) or not expression:
            raise ValueError("Use one SYMBOL=expression per line.")
        if name.casefold() in {key.casefold() for key in result}:
            raise ValueError(f"Duplicate symbol: {name}")
        result[name] = expression
    return result


def run_prepared(request, output, progress):
    """Preserve the source drawing; only run an isolated copy and read fresh results."""
    request.validate()
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="opentd-work-", dir=root))
    drawing = work / Path(request.drawing).name
    shutil.copy2(request.drawing, drawing)
    progress("Starting Thermal Desktop with a separate drawing copy…")
    desktop = open_td_api.connect(drawing)
    case = desktop.GetCaseSet(request.case, request.group)
    # Direct all generated solver artifacts to the trial directory.
    case.UseUserDirectory = 1
    case.UserDirectory = str(work.resolve())
    case.SindaFilenames = "trial"
    case.SaveTemp = 1
    case.RunSinda = 1
    case.RunSindaShowPlot = 0
    for name, expression in parse_overrides(request.overrides).items():
        names = list(case.SymbolNames)
        if name in names:
            case.SymbolValues[names.index(name)] = expression
        else:
            case.SymbolNames.Add(name)
            case.SymbolValues.Add(expression)
            case.SymbolComments.Add("Thermal Trial Workbench override")
    case.Update()
    desktop.SaveAs(str(drawing.resolve()))
    progress("Running prepared OpenTD case; wait for the licensed solver…")
    case.Run()
    saves = list(work.rglob("*.sav"))
    if len(saves) != 1:
        raise RuntimeError(f"Expected one fresh SINDA .sav result, found {len(saves)}. Inspect {work}.")
    times, temperatures = open_td_api.read_temperatures(saves[0], request.node)
    if not times or len(times) != len(temperatures):
        raise ValueError("OpenTD returned missing or mismatched time/temperature data.")
    if any(not math.isfinite(x) for x in times + temperatures):
        raise ValueError("OpenTD results contain nonfinite values.")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("OpenTD result times must be strictly increasing.")
    samples = [Sample(t, temperature, None) for t, temperature in zip(times, temperatures)]
    metadata = {"drawing": str(Path(request.drawing).resolve()), "case": request.case,
                "node": request.node, "overrides": parse_overrides(request.overrides),
                "solver_directory": str(work), "heat_w": "Not extracted; CSV column is blank.",
                "model_description": "The prepared Thermal Desktop drawing defines physics; temperatures are exported in SI units."}
    config = TrialConfig(model=request.drawing)
    folder = save_results(config, samples, root, "OpenTD prepared-case result", metadata, asdict(request))
    return samples, folder
