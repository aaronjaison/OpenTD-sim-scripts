"""Lazy OpenTD 2026/.NET 8 connection; preview needs no licensed dependencies."""
import importlib
import os
from pathlib import Path
import sys


def find_install():
    """Prefer an explicit installation, otherwise discover installed Ansys versions."""
    explicit = os.environ.get("OPENTD_HOME")
    if explicit:
        return Path(explicit)
    candidates = sorted(Path("C:/Program Files/ANSYS Inc").glob("v*/CRTech/Thermal Desktop/OpenTD.dll"))
    if not candidates:
        raise RuntimeError("OpenTD not found. Set OPENTD_HOME to the folder containing OpenTD.dll.")
    return candidates[-1].parent


def assembly_directory():
    """Select the vendor .NET Framework build for AutoCAD 2024 by default."""
    root = find_install()
    if os.environ.get("OPENTD_RUNTIME", "netfx") == "netfx":
        return root / "InstallUtils" / "gac"
    return root


def load_api():
    """Load the Windows Desktop runtime before importing pythonnet's clr module."""
    root = find_install()
    try:
        pythonnet = importlib.import_module("pythonnet")
        runtime = os.environ.get("OPENTD_RUNTIME", "netfx")
        if runtime == "netfx":
            pythonnet.load("netfx")
        elif runtime == "coreclr":
            pythonnet.load("coreclr", runtime_config=str(Path(__file__).with_name("opentd.runtimeconfig.json")))
        else:
            raise ValueError("OPENTD_RUNTIME must be netfx or coreclr.")
        clr = importlib.import_module("clr")
        # This dependency ships beside TD Designer in the 2026 R1 installation.
        dependencies = root.parent / "TD Designer" / "RemoteExporter"
        for directory in (assembly_directory(), root, dependencies):
            if str(directory) not in sys.path:
                sys.path.append(str(directory))
        protobuf = dependencies / "Google.Protobuf.dll"
        if protobuf.is_file():
            clr.AddReference(str(protobuf))
        clr.AddReference(str(assembly_directory() / "OpenTD.dll"))
        return importlib.import_module("OpenTD")
    except Exception as error:
        raise RuntimeError(f"Cannot load OpenTD from {root}. Install pythonnet and the matching .NET runtime. {error}") from error


def connect(drawing, api=None):
    """Open an isolated drawing in a NEW TD process, never attach to user work."""
    api = api or load_api()
    desktop = api.ThermalDesktop()
    acad = os.environ.get("OPENTD_ACAD", "C:/Program Files/Autodesk/AutoCAD 2024/acad.exe")
    desktop.ConnectConfig.AcadExePathname = api.Utility.RootedPathname(acad)
    desktop.ConnectConfig.Type = api.TdConnectConfig.Types.START_NEW_TD
    desktop.ConnectConfig.DwgPathname = api.Utility.RootedPathname(str(Path(drawing).resolve()))
    desktop.ConnectConfig.StartTimeout.DelayMs = 500
    desktop.ConnectConfig.StartTimeout.NumberOfTries = 120
    desktop.Connect()
    return desktop


def diagnostics():
    """Construct an API object without starting AutoCAD or consuming a solver run."""
    api = load_api()
    desktop = api.ThermalDesktop()
    return f"OpenTD loaded: {desktop.GetType().Assembly.FullName}. Live runs need AutoCAD, TD and SINDA licenses."


def read_temperatures(filename, node):
    """Read one SINDA temperature series from a save file using the vendor reader."""
    load_api()
    clr = importlib.import_module("clr")
    system = importlib.import_module("System")
    assembly = clr.AddReference(str(assembly_directory() / "OpenTD.Results.dll"))
    # Direct type construction avoids optional plotting dependencies in Results.
    dataset = system.Activator.CreateInstance(assembly.GetType("OpenTD.Results.Dataset.SaveFile"),
                                             system.Array[system.Object]([str(filename)]))
    try:
        dataset.Units.SetToSI()
        times = list(dataset.GetTimes())
        submodel, identifier = node.rsplit(".", 1)
        data = dataset.GetData(system.Array[system.String]([f"{submodel}.T{identifier}"]))
        temperatures = list(data[0])
        return times, temperatures
    finally:
        dataset.Close()
