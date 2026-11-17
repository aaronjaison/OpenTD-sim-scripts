# Connect settings through the tool

1. Choose a prepared thermal DWG and select its existing case/group. The geometry, mesh, materials, contacts, environment and target heat loads must already exist.
2. Enable **Customize simulation**. Check only the individual settings you want to change and enter their values. Unchecked values are neither parsed nor overridden. No longer prepare all six basic connections just to change duration.
3. Click **Connect settings…**. Inspection opens a separate drawing copy in a new Thermal Desktop instance; the app queue serializes it with tests.
4. Review the selected overrides and select targets for any initial-temperature, heating or emissivity changes. Timing needs no target beyond the selected case.
5. Click **Create connected copy**. The tool creates symbols and real expressions, saves a separate DWG, reads back its expressions, and writes `connections.json` beside it. The resulting drawing becomes the selected input. Failed setup does not select/publish a successful result.
6. Review the report and use **Re-run entirely**. Confirm generated inputs and temperature histories before trusting the physical model. Once connected, subsequent runs can change checked values without repeating setup.

## Supported connections

| Setting | Connection and scope |
|---|---|
| Duration | Selected case's `SindaControl.timendExp = SIM_DURATION_S` |
| Save interval | Selected case's `outputExp = SIM_OUTPUT_S` |
| Maximum solver step | Selected case's `dtimehExp = SIM_MAX_STEP_S`; verify it suits the case's solver procedure |
| Initial temperature | Selected diffusion/arithmetic node IDs, in K. Every object sharing an ID is connected; boundary/time-varying nodes are excluded. Node UserOverride is enabled so generated geometry nodes retain the expression. Restart cases are rejected for this connection. |
| Battery heating | One explicitly selected existing constant heat load. A VOLUME load receives W/m3 directly. A LOAD in W receives `SIM_BATTERY_QVOL * represented_volume_m3`; enter the volume represented by that entire load. Flux/time-varying loads are unsupported. The existing load expression is replaced; no new heat source is added. |
| Fixed emissivity | Selected existing constant IR coating's `emisExp = SIM_VED_EPS`. The effective case optical database is copied privately; solar absorption is retained. All faces using that coating are affected. Variable/temperature/spectral emissivity is rejected. RadCAD is enabled and its task-database option is set to RECALCULATE. |

Selected cases become transient. Node/load changes apply throughout the copied model; the wizard does not infer which parts are batteries or distinguish faces sharing a coating. Select targets deliberately. Existing symbols with the same exact SIM_* name receive the chosen setup values in the copy; matching case-local symbol overrides are synchronized. Other cases sharing those symbols may be affected within that copy.

All dimensional expressions are explicitly SI, independent of drawing display units. Intentional shared-temperature node IDs are retained. Keep the generated optical file at its recorded location. Moving a connected drawing alone will not move its absolute database references. Other external model dependencies remain referenced as before; the wizard does not make an arbitrary model portable.

The wizard supports the six basic settings above. Orbital connections still require model-author preparation. Nonzero orbit-cycle overrides require a selected period and a duration connection, because the tool calculates duration = cycles * period. The presence of a symbol alone cannot prove a manually prepared model uses it correctly.

## Validation performed

On an isolated copy of Recreated_VED_Sweep.dwg, setup and a separate reopen retained all three timing expressions, the selected node expressions (six objects sharing MAIN.1), the heat-load expression and the VED emissivity expression. A fresh short solve changed these values after setup: duration 90 s, output 15 s, maximum step 5 s, MAIN.1 initial temperature 295 K, heat generation 20000 W/m3 times a test volume of 0.00001 m3 (= 0.2 W), and emissivity 0.55.

Generated SINDA input confirmed 90/15/5; the saved history contained seven times through 90 s, MAIN.1 began at 295 K, other spacecraft nodes began at 293 K and SPACE.1 remained 3 K. Generated VED optical rows showed IR emissivity 0.55 and solar absorptivity 0.85. This was a connection/functionality check using an explicitly selected existing electronics load as a test target, not a new physical battery study or a rerun of the previous six-case sweep.

`connections.json` verifies API expression readback after SaveAs. It is not a general solver-convergence or model-physics certification. Review custom solver logic, time steps, restart behavior, loads and coating assignments for each model. Force a fresh run after external database changes; not all external references participate in current cache fingerprints.
