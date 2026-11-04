"""Rebind this VED study's packaged databases without changing its source drawing."""
import argparse
from pathlib import Path
import shutil
import tempfile
from .open_td_api import connect

CASES = tuple(f"VED_e{n:03d}" for n in (30, 40, 50, 60, 70, 80))


def prepare(bundle):
    """Create a local runnable copy after extracting or moving the study bundle."""
    root = Path(bundle).resolve()
    model = root / "model"
    files = [model / name for name in ("Recreated_VED_Sweep.dwg", "Materials.tdp", "Optics.rco",
                                       *[case + ".rco" for case in CASES])]
    if any(not path.is_file() for path in files):
        raise ValueError("Bundle must contain the DWG, Materials.tdp, Optics.rco and all six case .rco files in model/.")
    folder = Path(tempfile.mkdtemp(prefix="prepared-", dir=root))
    drawing = folder / files[0].name
    shutil.copy2(files[0], drawing)
    desktop = connect(drawing)
    try:
        desktop.OpenThermoPropDB(str(model / "Materials.tdp"))
        desktop.OpenOpticalPropDB(str(model / "Optics.rco"))
        for name in CASES:
            case = desktop.GetCaseSet(name, "")
            case.OpticOverride = 1
            case.OpticFilename = str(model / (name + ".rco"))
            case.ThermoOverride = 0
            case.UseUserDirectory = 1
            target = folder / name
            target.mkdir()
            case.UserDirectory = str(target)
            case.RunSinda = 1
            case.SaveTemp = 1
            case.Update()
        desktop.SaveAs(str(drawing))
    finally:
        desktop.Quit()
    return drawing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Extracted study folder containing model/")
    print(prepare(parser.parse_args().bundle))


if __name__ == "__main__":
    main()
