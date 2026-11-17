"""Inspect and prepare isolated model copies with a verifiable connection report."""
from dataclasses import dataclass
from pathlib import Path
import json
import shutil
import tempfile
from . import open_td_api
from .node_catalog import validate_drawing
from .setup_targets import catalog, connect_targets, verify_targets, SUPPORTED
from .sim_settings import SYMBOLS


@dataclass(frozen=True)
class SetupCatalog:
    drawing: str
    case: str
    group: str
    targets: dict


@dataclass(frozen=True)
class SetupResult:
    drawing: str
    case: str
    group: str
    report: str
    source: str = ""


def isolated_copy(drawing, output):
    source = validate_drawing(drawing)
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="opentd-setup-", dir=root)).resolve()
    copy = folder / source.name
    shutil.copy2(source, copy)
    for name in ("TdThermo.tdp", "RcOptics.rco"):
        sidecar = source.with_name(name)
        if sidecar.is_file():
            shutil.copy2(sidecar, folder / name)
    return copy


def local_optics(desktop, case, drawing, optical_database=""):
    source = Path(optical_database or (case.OpticFilename if case.OpticOverride else desktop.GetOpticalPropDBPathname()))
    if not source.is_absolute():
        raise ValueError("Optical database path must be absolute; resolve it in Thermal Desktop first.")
    if not source.is_file():
        raise ValueError(f"Missing optical database: {source}")
    target = drawing.with_name("setup-optics.rco")
    shutil.copy2(source, target)
    desktop.OpenOpticalPropDB(str(target))
    case.OpticOverride = 1
    case.OpticFilename = str(target)


def inspect_setup(drawing, case_name, group, output, include_optics=True, optical_database=""):
    copy = isolated_copy(drawing, output)
    desktop = open_td_api.connect(copy)
    try:
        case = desktop.GetCaseSet(case_name, group)
        if include_optics:
            local_optics(desktop, case, copy, optical_database)
        targets = catalog(desktop, include_optics)
        targets["optical_database"] = optical_database
        return SetupCatalog(str(Path(drawing).resolve()), case_name, group, targets)
    finally:
        desktop.Quit()


def prepare_setup(drawing, case_name, group, settings, output, nodes=(), heat="", volume=0, coating="", optical_database=""):
    parameters = settings.parameters()
    if set(parameters) - {SYMBOLS[name] for name in SUPPORTED}:
        raise ValueError("The wizard connects basic settings only. Orbital connections require model-author preparation.")
    copy = isolated_copy(drawing, output)
    desktop = open_td_api.connect(copy)
    try:
        api = open_td_api.load_api()
        case = desktop.GetCaseSet(case_name, group)
        if SYMBOLS["emissivity"] in parameters:
            local_optics(desktop, case, copy, optical_database)
        available = {str(s.Name): s for s in desktop.GetSymbols()}
        for name, value in parameters.items():
            symbol = available.get(name)
            if symbol is None:
                symbol = desktop.CreateSymbol(name, value)
            else:
                symbol.Value = value
                symbol.Update()
            # Existing case-local overrides must not hide the setup value.
            if name in list(case.SymbolNames):
                case.SymbolValues[list(case.SymbolNames).index(name)] = value
        records = connect_targets(desktop, case, api, parameters, nodes, heat, volume, coating)
        case.SteadyState, case.Transient = 0, 1
        if SYMBOLS["emissivity"] in parameters:
            case.CalculateRadiation = 1
            case.RadiationTaskDbOption = api.CaseSetData.RadiationTaskDbOptions.RECALCULATE
        case.Update()
        desktop.SaveAs(str(copy))
        case = desktop.GetCaseSet(case_name, group)
        verify_targets(desktop, case, records)
        report = copy.with_name("connections.json")
        report.write_text(json.dumps({"source": str(Path(drawing).resolve()), "drawing": str(copy),
            "case": case_name, "group": group, "parameters": parameters, "connections": records,
            "scope": "Node/load changes apply to this copied model; the coating is shared by all faces assigned to it.",
            "verification": "API readback of expressions after SaveAs; validate generated solver deck before design use."}, indent=2), encoding="utf-8")
        return SetupResult(str(copy), case_name, group, str(report), str(Path(drawing).resolve()))
    finally:
        desktop.Quit()
