# OpenTD Thermal Trial Workbench

A working Python/Tkinter prototype for repeatable thermal trials, with a unified prepared-DWG workflow.

## Start

On Windows, install Python 3.11 or newer with Tcl/Tk. From this checkout:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test,opentd]"
.\.venv\Scripts\python.exe app.py
```

The thermal preview itself uses only the Python standard library. `pythonnet` is needed only for OpenTD. For this development computer, a ready-to-run environment exists in the separate `working-prototype` worktree; launch its `.venv/Scripts/pythonw.exe` with `app.py` as the argument, or run the command above from that worktree.

## Working prototype workflow

1. Choose a prepared `.dwg` file in the single main window.
2. Enter its case name/group and select a result node or **All nodes**.
3. Enable **Customize simulation** for a DWG following [the preparation contract](DWG_PREPARATION.md), then enter the settings.
4. Select **Add to queue**. Change the file/settings and add further tests while the queue runs.
5. Open results when complete. Matching results load by default; use **Re-run entirely** for a fresh attempt.

The previous standalone preview tab has been removed. Its lumped solver remains available as a backend utility for tests and numerical experiments; it does not parse SolidWorks geometry or replace the prepared DWG simulation.

## Saved results

`output/<UTC timestamp>_<source name>_<source identity>_trial-0001/` contains:

- `report.md`: source, UTC timestamp, trial number, numerical summary, input record and embedded plot.
- `results.csv`: full-precision time, temperature and heat input.
- `temperature.svg`: portable temperature graph.
- `config.json`: immutable input snapshot and engine metadata.

Reports are published only after all four files are written. `.trials/` reserves attempt numbers across concurrent processes; failed publication can leave a gap. Source identity uses the source path, so equal basenames in different folders remain separate. Previous reports are never overwritten. Generated outputs and virtual environments are not committed.

## OpenTD automation

The main screen is for a **prepared Thermal Desktop `.dwg`**, an exact case name/group and a result node such as `MAIN.1`. Prepare/import/mesh the SolidWorks geometry and define your thermal network in Thermal Desktop first. Case symbol overrides accept one `NAME=expression` per line in Thermal Desktop syntax; these are separate from the preview inputs.

The adapter copies the drawing to a unique `output/opentd-work-*` folder, starts a **new** Thermal Desktop process, applies case-local overrides, directs solver outputs there and runs the case. It reads one fresh SINDA `.sav` file through the vendor SaveFile reader in SI units, then exports the selected node's temperature. Heat input is not extracted for live results, so that CSV column is blank. The prepared drawing controls physics; `config.json` records the live case, group, node and overrides instead of preview parameters. Adjacent default material databases `TdThermo.tdp` and `RcOptics.rco` are copied when present. Other referenced mesh/material/include files must remain accessible; their references are not rewritten. The launched TD instance and raw solver files remain available for inspection. The UI blocks closing while a live operation is running; live solver cancellation is not implemented.

Prerequisites: compatible AutoCAD, licensed Thermal Desktop and SINDA, the required compiler/toolchain, Python `pythonnet`, and the matching .NET runtime. This machine has AutoCAD 2024 and TD 2026 R1. The default adapter uses the vendor .NET Framework assembly in `InstallUtils/gac`. Before launching AutoCAD, it loads the installed Visual Studio x64 C++ build environment into the workbench process so Intel Fortran can find `link.exe` and SDK libraries. Windows-wide environment settings are not modified. If Visual Studio C++ Build Tools or the Windows SDK is absent, the run reports a prerequisite error.

Optional environment settings before launch:

```powershell
$env:OPENTD_HOME = 'C:\Program Files\ANSYS Inc\v261\CRTech\Thermal Desktop'
$env:OPENTD_ACAD = 'C:\Program Files\Autodesk\AutoCAD 2024\acad.exe'
$env:OPENTD_RUNTIME = 'netfx'
```

For a compatible AutoCAD 2025+ installation, select `OPENTD_RUNTIME=coreclr`, set the matching AutoCAD executable, and install .NET 8 Windows Desktop Runtime. Restart the workbench when changing runtime; pythonnet cannot switch an initialized CLR in place.

**Integration status:** a real OpenTD/SINDA calibration completed end to end on this computer: two nodes, a 293.15 K boundary, a 1 W/K conductor and 25 W heat input produced **318.15 K**, matching `293.15 + 25/1`. The actual `.sav` file was read using the vendor `SaveFile` reader and temperature identifier `CHECK.T1`, then published as Markdown, CSV, SVG and JSON through the same prepared-case pipeline used by the UI. A single-record steady-state result is supported.

The supplied user drawing also connected successfully and its case/nodes were retrieved. Its case reached the model-check stage, which reported 80 duplicate node IDs. The model owner chose to preserve their shared temperatures, and the copied-model run accepted that choice. Thermal Desktop then stopped before solving: `Sum of From Edge Lengths is zero. Cannot do calculations for Edge conductance`, identifying `Edge Contactor[MAIN][1]::318`. That contactor's source-edge geometry must be corrected in the prepared model before temperatures can be exported; no nodes were renumbered or thermal connections removed. The standalone preview also completed a run linked to the supplied SolidWorks assembly. All 148 automated tests pass at 100% statement and branch coverage; vendor API contract doubles supplement, rather than replace, the live calibration.

Older drawings may display version-backup/default-change dialogs in AutoCAD, which block OpenTD until handled. If startup times out, inspect that newly launched AutoCAD window before retrying; do not repeatedly launch more instances.

Vendor references: [OpenTD Python guide](https://developer.synopsys.com/docs/opentd-2025-r2/getting-started/appendix-B-using-opentd-with-python.md), [ThermalDesktop API](https://developer.synopsys.com/docs/opentd-net8-reference-2025-r2/class_open_t_d_1_1_thermal_desktop.xhtml).

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests include analytic adiabatic heating, Newton cooling, time-varying heat integration, radiation step convergence, expression rejection, cancellation, atomic report publication, real Tk widgets, and OpenTD adapter error/success contracts. Pytest enforces **100% statement and branch coverage** of all application modules, with no source exclusions. GUI tests require a working Tk display. All Python files remain below 150 lines.

## Layout

The requested frontend/backend separation is preserved. `frontend/interface.py` calls graphics helpers and `frontend/connections.py`; the controller queues worker events; `backend/main_processes.py` coordinates the local solver and result export. `backend/opentd_trials.py` coordinates the live path through `backend/open_td_api.py`. See `AGENT_INSTRUCTIONS.MD` for the full file map.

## Queued tests and saved results

The single DWG workflow provides a FIFO test queue. Configure a file and its settings, then click **Queue test**; change the form and add the next test while the current one runs. Each entry keeps its submitted settings. Tests run one at a time in the queue, and failures do not discard later tests. **Remove waiting tests** clears pending entries without stopping the active test. Queues are kept for the current application session.

**Load saved / run** and **Queue test** reuse the newest complete matching saved result by default. If no match exists, the test runs normally. New reports include `reuse.json` with the submitted configuration and SHA-256 fingerprints of the direct input file and adjacent default DWG databases. Changing these inputs triggers another run. Older reports are eligible when their configuration matches and their direct inputs have not been modified since publication. Externally referenced assembly parts, meshes and include files are not fingerprinted; use a forced rerun after changing those dependencies.

Click **Re-run entirely** to run the current form from scratch. To repeat a particular queued/completed configuration, select its row and click **Re-run selected test entirely**. This retains that row's original file/settings even if the form has since changed. Forced reruns always create another timestamped trial folder and preserve earlier results. Saved-result loading does not launch Thermal Desktop or require its license.

## Selecting a result node

Choose a prepared drawing in the main window, then click **Load available nodes** below **Result node**. Select the desired node from the dropdown; the first available node is selected initially. Shared-temperature IDs appear once, sorted by submodel and numeric node ID. You can still type an ID manually when loading existing results without OpenTD.

Node discovery runs through the background queue and requires installed/licensed AutoCAD and Thermal Desktop. It opens a separate drawing copy, reads the thermal nodes without running a case, and closes that inspection instance afterward. Changing the drawing clears the dropdown so nodes from the previous drawing are not offered. Click **Load available nodes** again after editing a drawing externally.

## All-node results

Select **All nodes** in the result-node dropdown to collect every unique thermal node present in the case's saved results. This option is available before loading the drawing's node list. Thermal Desktop still solves the prepared case once; the exporter reads all saved thermal nodes, including boundary nodes, rather than repeating the simulation for each node.

Each result folder includes:
- `nodes.csv`: time in seconds and one temperature-in-kelvin column per unique saved node.
- `node_summary.csv`: arithmetic mean, minimum, maximum and node count at every saved time.
- `results.csv` and `temperature.svg`: the mean temperature history, also linked from `report.md`.

The average gives every unique saved submodel/node ID equal weight. Shared-temperature IDs count once. It is not mass-, area-, or heat-capacity-weighted. Nodes excluded from the case's saved outputs cannot be included. Missing, mismatched or nonfinite node histories fail the export instead of silently changing the averaging population. All-node and single-node configurations have separate saved-result matches; all-node reuse requires both additional CSV files.

The actual two-node calibration save file was read through the new all-node adapter: CHECK.1 = 318.15 K and CHECK.2 = 293.15 K gave a mean of 305.65 K. Automated tests also verify changing averages on transient time grids.

## Proposed thermal-image integration (not implemented)

Temperature-colored images of the model require more than capturing the AutoCAD viewport. The installed API exposes `CaptureGraphicsArea`, but result-dataset activation, displayed time and temperature color-scale control still need a verified postprocessing workflow. The data export above is complete; image automation is awaiting the user's choice on this plan:

1. Load the completed case's saved temperatures into postprocessing on its isolated drawing copy. Establish and validate commands/API calls for selecting each saved time and temperature display.
2. Export PNG model views at the first, middle and final saved times (one image for steady state), using a fixed camera and a common Kelvin color scale. Include timestamps and a temperature legend.
3. Save PNGs under `thermal_images/` with a manifest of source result, time, units, limits and camera; link them from the report. If rendering fails, preserve numerical results and report the image failure explicitly.
4. Validate on a model with visible thermal geometry and known hot/cold regions. The existing two-node calibration validates numerical extraction, while the supplied assembly drawing still requires its edge-contactor issue to be corrected before its temperature fields can be rendered.

## Simulation controls and interface

The dark ORBIT interface keeps simulation customization collapsed until enabled. Hover over a field label for two seconds to see its explanation. The OpenTD form exposes initial temperature, duration, save interval, maximum solver step, battery volumetric heating, fixed VED emissivity, and optional orbit-cycle/period/altitude/inclination/beta controls. These controls require a prepared DWG with named symbols bound to its actual physics and solver settings. See [DWG preparation and parameter contract](DWG_PREPARATION.md) before enabling them. Existing drawings can continue with customization off. Dynamic VED switching remains a model-author responsibility.

## Unified workflow

Launch `app.py` for one screen: choose a prepared DWG, enter its case and result nodes, configure simulation parameters, and add tests to the queue. There are no separate preview/automation tabs. The standalone lumped preview remains a backend utility, but it is no longer presented as an alternative simulation mode in the application. Delayed label help, saved-result reuse, forced reruns and all-node reporting remain available in the main workflow. Source modules remain separated for maintainability; users have one application entry point.

## Case selection and scrolling

After choosing a DWG, click **Load case names** and select an existing case from the dropdown. Names are displayed with their groups, and selection fills the exact case and group fields. Discovery uses an isolated drawing copy and closes its inspection instance. Changing drawings clears old choices; late discovery results for another drawing are ignored. An empty drawing reports zero case sets. Loading case names requires the installed Thermal Desktop environment.

Use the mouse wheel over the form to scroll. Help opens only after hovering over a field label for two seconds; leaving the label cancels or hides it. Focusing an input no longer triggers help.
