# OpenTD Thermal Trial Workbench

A working Python/Tkinter prototype for repeatable thermal trials, with an optional adapter for prepared Thermal Desktop cases.

## Start

On Windows, install Python 3.11 or newer with Tcl/Tk. From this checkout:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test,opentd]"
.\.venv\Scripts\python.exe app.py
```

The thermal preview itself uses only the Python standard library. `pythonnet` is needed only for OpenTD. For this development computer, a ready-to-run environment exists in the separate `working-prototype` worktree; launch its `.venv/Scripts/pythonw.exe` with `app.py` as the argument, or run the command above from that worktree.

## Working prototype workflow

1. Open **Thermal preview**. Optionally select a `.SLDPRT` or `.SLDASM` source reference.
2. Enter mass, specific heat, area, convection, emissivity and temperatures in the displayed SI units.
3. Enter a heat-input equation, duration and time step; select **Run thermal preview**.
4. Inspect the temperature graph, then select **Open results folder**.
5. Change an input and rerun. Each attempt gets its own timestamped folder and per-source trial number.

The default trial produces 601 samples and a final temperature of approximately **303.754314 K**. It uses a 1 kg body, specific heat 900 J/kg/K, 0.1 m² area, 10 W/m²/K convection, emissivity 0.8, initial/ambient temperature 293.15 K, and 25 W heating for 600 s.

The preview solves a single uniform-temperature body:

```text
m * cp * dT/dt = Q(t,T) - h*A*(T-Ta) - emissivity*sigma*A*(T^4-Ta^4)
```

This is a lumped thermal estimate. **Selecting a SolidWorks file records its source; it does not import geometry, determine mass/area, mesh an assembly, or solve spatial temperature gradients.** Enter effective properties yourself. Automatic CAD-to-thermal-model conversion is outside this prototype.

Equations support `t` (seconds), `T` (kelvin), `ambient` (kelvin), `pi`, `+ - * / **`, parentheses, and `sin`, `cos`, `exp`, `sqrt`, `abs`, `min`, `max`. Examples: `25`, `25 + 10*sin(2*pi*t/120)`, `max(0, 50 - 0.5*(T-ambient))`. Expressions are interpreted through a restricted arithmetic tree, never Python `eval`. Limits: 500 characters, 100 syntax nodes, powers from -16 to 16, and finite results with magnitude at most 1e12.

The solver uses fixed-step RK4 with at most 100,000 steps. It includes the exact end time even when duration is not divisible by the step. Temperatures outside 0–10,000 K fail the trial. Reduce the step and compare results to establish convergence; the preview does not implement adaptive error control. Cancel interrupts calculation before publication; publication already in progress may finish.

## Saved results

`output/<UTC timestamp>_<source name>_<source identity>_trial-0001/` contains:

- `report.md`: source, UTC timestamp, trial number, numerical summary, input record and embedded plot.
- `results.csv`: full-precision time, temperature and heat input.
- `temperature.svg`: portable temperature graph.
- `config.json`: immutable input snapshot and engine metadata.

Reports are published only after all four files are written. `.trials/` reserves attempt numbers across concurrent processes; failed publication can leave a gap. Source identity uses the source path, so equal basenames in different folders remain separate. Previous reports are never overwritten. Generated outputs and virtual environments are not committed.

## OpenTD automation

The **OpenTD automation** tab is for a **prepared Thermal Desktop `.dwg`**, an exact case name/group and a result node such as `MAIN.1`. Prepare/import/mesh the SolidWorks geometry and define your thermal network in Thermal Desktop first. Case symbol overrides accept one `NAME=expression` per line in Thermal Desktop syntax; these are separate from the preview inputs.

The adapter copies the drawing to a unique `output/opentd-work-*` folder, starts a **new** Thermal Desktop process, applies case-local overrides, directs solver outputs there and runs the case. It reads one fresh SINDA `.sav` file through the vendor SaveFile reader in SI units, then exports the selected node's temperature. Heat input is not extracted for live results, so that CSV column is blank. The prepared drawing controls physics; `config.json` records the live case, group, node and overrides instead of preview parameters. Referenced mesh/material/include files must remain accessible; copying the DWG does not copy or rewrite those references. The launched TD instance and raw solver files remain available for inspection. The UI blocks closing while a live operation is running; live solver cancellation is not implemented.

Prerequisites: compatible AutoCAD, licensed Thermal Desktop and SINDA, the required compiler/toolchain, Python `pythonnet`, and the matching .NET runtime. This machine has AutoCAD 2024 and TD 2026 R1. The default adapter uses the vendor .NET Framework assembly in `InstallUtils/gac`.

Optional environment settings before launch:

```powershell
$env:OPENTD_HOME = 'C:\Program Files\ANSYS Inc\v261\CRTech\Thermal Desktop'
$env:OPENTD_ACAD = 'C:\Program Files\Autodesk\AutoCAD 2024\acad.exe'
$env:OPENTD_RUNTIME = 'netfx'
```

For a compatible AutoCAD 2025+ installation, select `OPENTD_RUNTIME=coreclr`, set the matching AutoCAD executable, and install .NET 8 Windows Desktop Runtime. Restart the workbench when changing runtime; pythonnet cannot switch an initialized CLR in place.

**Integration status:** real OpenTD 26.1 .NET Framework and .NET 8 assemblies were loaded and real API objects constructed on this computer. The supplied Thermal Desktop drawing connected successfully and its case/nodes were retrieved. Its case reached the model-check stage, which reported 80 duplicate node IDs; how to handle those requires a physical-model decision. A licensed SINDA solve and vendor result extraction have not yet been verified end to end. Adapter contract doubles do not establish licensed solver correctness. The standalone thermal preview is verified end to end, including a run linked to the supplied SolidWorks assembly.

Older drawings may display version-backup/default-change dialogs in AutoCAD, which block OpenTD until handled. If startup times out, inspect that newly launched AutoCAD window before retrying; do not repeatedly launch more instances.

Vendor references: [OpenTD Python guide](https://developer.synopsys.com/docs/opentd-2025-r2/getting-started/appendix-B-using-opentd-with-python.md), [ThermalDesktop API](https://developer.synopsys.com/docs/opentd-net8-reference-2025-r2/class_open_t_d_1_1_thermal_desktop.xhtml).

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests include analytic adiabatic heating, Newton cooling, time-varying heat integration, radiation step convergence, expression rejection, cancellation, atomic report publication, real Tk widgets, and OpenTD adapter error/success contracts. Pytest enforces **100% statement and branch coverage** of all application modules, with no source exclusions. GUI tests require a working Tk display. All Python files remain below 150 lines.

## Layout

The requested frontend/backend separation is preserved. `frontend/interface.py` calls graphics helpers and `frontend/connections.py`; the controller queues worker events; `backend/main_processes.py` coordinates the local solver and result export. `backend/opentd_trials.py` coordinates the live path through `backend/open_td_api.py`. See `AGENT_INSTRUCTIONS.MD` for the full file map.
