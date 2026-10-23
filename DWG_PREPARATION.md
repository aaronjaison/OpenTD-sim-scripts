# Prepared DWG contract

The workbench runs copies of prepared Thermal Desktop drawings. Model authors own geometry, mesh quality, materials, contacts, optical assignments, attitude and orbital/environment definitions. A plain AutoCAD solid is not a prepared thermal model.

## Before handing over a drawing

1. Build and validate the thermal mesh/network, material assignments and connections. Define battery heated regions and the VED faces explicitly. Keep intentional shared-temperature node IDs; resolve accidental duplicates and invalid contactors. The supplied troubleshooting drawing currently fails on edge contactor MAIN.1, handle 318 (zero source-edge length).
2. Provide an exact case name and optional case group. Verify that case runs successfully in Thermal Desktop, saves temperatures, and uses seconds/Kelvin/SI inputs consistently.
3. Supply referenced meshes, material/optical databases, include files and assemblies. Adjacent TdThermo.tdp and RcOptics.rco are copied automatically; other references must resolve on the execution machine. Do not rely on another user's absolute paths.
4. Define the symbols below in the drawing and connect their expressions to the appropriate model or case settings. Merely creating named symbols does not make them control the simulation. The script verifies their existence, but cannot establish whether an arbitrary model uses each symbol correctly.
5. Document which nodes/regions each symbol controls. Validate a baseline and at least one changed value in Thermal Desktop before using queued comparisons.

## Basic simulation parameters

These six symbols are required when **Customize simulation** is enabled. Their values are case-local overrides; the original drawing is unchanged. The script also sets the selected case to transient analysis.

| Symbol | Units | Default | Required connection in the prepared DWG |
|---|---|---|---|
| SIM_INITIAL_K | K | 293 | Initial temperatures of the participating thermal nodes. Do not replace boundary-temperature histories. Disable restart initialization if it would override this setting. |
| SIM_DURATION_S | s | 3300 | End time, starting from time zero, in the case's transient control expressions. |
| SIM_OUTPUT_S | s | 10 | Saved temperature output interval. This is not the internal integration step. |
| SIM_MAX_STEP_S | s | 1 | Maximum internal integration step for the selected transient solver. Confirm the appropriate SINDA control for the solver procedure used. |
| SIM_BATTERY_QVOL | W/m³ | 12000 | Volumetric generation in the named battery regions. For nodal loads, use Q_i = SIM_BATTERY_QVOL * V_i with nonoverlapping volumes in m³. Never apply the whole block power to each cell. |
| SIM_VED_EPS | dimensionless | 0.85 | Infrared emittance of the designated VED surface optical property, including its applicable sides. Preserve independently specified solar absorptivity. |

Use battery-generation values 12000, 20000, 60000 or 120000 to reproduce the requested comparisons. Queue fixed-emissivity cases at 0.35 and 0.85. The UI does not implement a dynamic switching law: a model author must prepare and validate that law separately, using advanced overrides as appropriate. Fixed-state comparisons do not simulate switching.

The script does not directly rewrite individual node/property expressions. It expects model authors to make the bindings above, avoiding geometry-dependent edits. Values use the listed units even if the drawing display units differ: model expressions must convert where needed. 293 K is 19.85°C; enter 293.15 for exactly 20°C.

## Optional orbital parameters

Enabling **Apply orbital parameters + recalculate RadCAD** requires all basic symbols plus the following. It also requires an existing radiation-task list and enables radiation calculation for the case. Users must verify that the tasks actually calculate the intended loads; their presence alone cannot establish correctness.

| Symbol | Units | Default | Required connection |
|---|---|---|---|
| SIM_ORBIT_PERIOD_S | s | 5400 | Prepared orbit's period/time mapping, consistent with its orbit definition. |
| SIM_ALTITUDE_M | m | 400000 | Altitude above the selected reference body. |
| SIM_INCLINATION_DEG | degrees | 51.6 | Inclination in the prepared orbit's applicable coordinate convention. |
| SIM_BETA_DEG | degrees | 0 | Solar beta angle for a supported beta-defined orbit/environment configuration. |
| SIM_ORBIT_CYCLES | count | 0 | Run-length bookkeeping: zero uses Duration; a positive integer makes the script set SIM_DURATION_S = cycles × period. This symbol need not be connected to an additional physics expression. |

The defaults are example inputs, not a validated mutually consistent orbital solution. Do not independently constrain quantities that the selected orbit representation derives from other elements. The model author must choose compatible orbit/attitude definitions and unit conversions; the script performs range checks, not orbital consistency calculations.

Prepare direct solar, albedo and Earth IR radiation tasks, eclipse/shadow handling, attitude, surface absorptivities and the applicable space/radiation boundary. Ensure generated environmental loads and radiation exchange reflect the overridden optical state. Five orbits is a run length, not proof of periodic thermal equilibrium.

## Running and auditing

- Leave customization off to preserve the drawing's existing case settings and continue using the established workflow.
- Turn it on only for a drawing following this contract. Enter settings, then queue tests. Each job retains its own immutable settings.
- Advanced overrides use one NAME=expression per line and cannot duplicate enabled simulation symbols (case-insensitive check). They are for existing, deliberately bound model parameters.
- Results record the entered settings and resolved symbol overrides in config.json. Enabled customization changes the saved-result identity. External referenced-file changes still require **Re-run entirely**.
- Check all-node mean/minimum/maximum histories as well as individual battery and casing nodes; a global mean can conceal local hot spots.

## Acceptance checks for a model author

Change one parameter at a time. Verify initial node values, final saved time, output cadence, emitted solver step limit, and total battery power q'''V against the intended volume. Verify an emissivity change affects radiation as expected and check environmental fluxes for the selected orbit/attitude. Compare a baseline and refined time step/mesh with the original COMSOL setup using the same contact assumptions, initial conditions and loads. The workbench cannot infer those assumptions from a DWG.
