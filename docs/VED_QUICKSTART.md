# Run the VED sweep

This study repeats six **fixed-emissivity** cases from `Recreated_VED_Sweep.dwg`. It is a reproduction of the supplied sweep, not a validation of a flight design or a reproduction of the binder's separate COMSOL study.

## Start here

1. Extract `VED-study-bundle.zip` to a permanent folder. Keep its `model` folder: the DWG alone is insufficient.
2. From the scripts repository, run the preparation command below once. It creates a new drawing and prints its path. Repeat this step if you move the bundle.
3. Start the app. Choose the **printed drawing path** and click **Load case names**.
4. Select `VED_e030`, leave the group blank, choose **All nodes**, leave **Customize simulation OFF**, and leave **Advanced symbol overrides empty**.
5. Click **Re-run entirely** for a fresh trial. Select each remaining case and add it to the queue. If you need fresh results for previously saved cases, use **Re-run entirely** for each one.
6. Open the result folder when complete. A queued test keeps the settings it had when added.

```powershell
# First setup only, using Python 3.11 or newer:
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[opentd,test]"

# Replace this path with your extracted folder:
.\.venv\Scripts\python.exe -m backend.ved_bundle "C:\path\to\VED-study-bundle"
.\.venv\Scripts\python.exe app.py
```

Requires licensed AutoCAD 2024, Thermal Desktop/RadCAD/SINDA 2026 R1, and the Visual Studio x64 C++/Intel Fortran tools required by SINDA. The preparation command also needs Thermal Desktop. The installation-check button only checks API loading; a completed solve verifies more than that check.

**For this drawing, the existing cases already contain the solver and optical setup.** Checked custom overrides require `SIM_*` bindings that the original drawing does not have. The new **Connect settings** wizard can create selected basic bindings in a copy (see SETUP_WIZARD.md), but leave customization off to reproduce this unchanged reference sweep. Typing a value there cannot create a model connection. No `Q_BAT`, `EMIS`, or `SIM_*` overrides are needed for these six cases.

## Exact trial inputs

| Setting | Value |
|---|---|
| Cases | `VED_e030`, `VED_e040`, `VED_e050`, `VED_e060`, `VED_e070`, `VED_e080` |
| Case group | Empty/default |
| VED IR emissivity | 0.30, 0.40, 0.50, 0.60, 0.70, 0.80 respectively |
| VED solar absorptivity | 0.85 in every case |
| Orbit | Circular Earth orbit, altitude 600 km, beta angle 53.6 degrees |
| Solar flux / albedo | 1367 W/m2 / 0.32 |
| Earth IR flux | 202.700914 W/m2 in generated heating data (binder: 202.7) |
| Attitude | Existing planet-oriented, velocity-constrained setup |
| Orbital period | 5801.23510345288 s |
| Run interval | 0 to 29006.18 s, approximately five orbits |
| Output interval | 30 s plus final point: 968 saved times |
| Solver | Transient, automatic step; `DTIMEI=0`, `DTIMEH=30 s` |
| Initial spacecraft temperature | 293 K (19.85 C) |
| Space boundary | 3 K |
| Internal heating | 3 W total; no added volumetric battery source |
| Result identities | 705 unique saved nodes, including `SPACE.1` |
| Radiation | Fresh RadCAD calculations for each case |

Use the evaluated orbital period above: an older inactive Period field in the setup audit differs; generated `hrPeriodSec` and the heating time array establish the actual period.

The six `.rco` files select the emissivity states. The binder's 0.85/0.35 switched-emissivity function is **not** used here. Existing shared-temperature node IDs are retained.

## What the output means

- `nodes.csv`: every saved node in kelvin. Match columns by node ID, not column position.
- `node_summary.csv` and the app graph: equal-weight mean/min/max across all unique saved nodes, including the 3 K boundary. This mean is **not** the component average shown in the supplied graphs.
- Study `data/*_component_means_C.csv`: area-weighted VED, chassis, boards and PV means in Celsius, using `component_node_weights.json`. Chassis includes the VED; groups overlap.
- Study `comparison.csv`: fresh-minus-reference bias, RMSE, and largest absolute error in kelvin. Celsius temperature differences have the same numerical values.
- Study `comparison.json` and `verification.json`: detailed comparison and completeness evidence. A complete file must reach 29006.18 s; the mere existence of a `.sav` file does not prove completion.
- `output/errors`: error details and the request settings. Read the dialog first; the log has the full traceback.

The study bundle includes source checksums, model databases, weighting definitions, supplied reference CSVs/graphs, newly generated results, and comparison evidence. Raw solver directories remain under `output/ved-reproduction-20261103` on this machine.

## Rebuild the comparison after another run

Copy each run's `nodes.csv` to the bundle's `data` folder as `VED_e030_all_nodes_K.csv`, etc. Use all six fresh files, then run:

```powershell
.\.venv\Scripts\python.exe -m backend.ved_report "C:\path\to\VED-study-bundle"
```

This regenerates component averages and comparison tables. It rejects missing node IDs, nonfinite data and incomplete time coverage. It linearly interpolates fresh results onto reference times and never extrapolates outside the run (apart from 1 microsecond of endpoint roundoff). No pass/fail engineering tolerance is assumed.

## Important differences from the design binder

The binder contains multiple studies. Pages 11-13 describe a battery/standalone VED COMSOL study with a 1000 km orbit, 6600 s period, 33000 s duration and varying emissivity. Appendix A lists a different period, 5968.62 s. Figure 12 (page 22) is a point-temperature graph, not this study's area-weighted VED mean. Those are not the 600 km reference sweep's inputs; they must not be mixed into its reproduction.

Appendix A (pages 45-48) is the material/environment reference. Its PV density of 2 kg/m3 and heat capacity of 1 J/kg/K, Kapton heat capacity of 1.09 J/kg/K, and swapped density/heat-capacity symbols require review. They are preserved for reproducibility, not endorsed. The model uses inferred component assignments. The reference itself reports omitted battery heating and ongoing orbit-to-orbit drift; five orbits are not proof of periodic equilibrium. Repair material values and confirm assignments before making design decisions.

## Common problems

- **Missing SIM symbols:** disable Customize simulation for this study.
- **Missing material/optical database:** run the preparation command after extracting or moving the bundle.
- **Wrong temperatures:** check Kelvin vs Celsius and equal-node vs area weighting before changing physics.
- **Saved data opens instead of a new run:** use Re-run entirely.
- **License/connection failure:** verify network licensing and AutoCAD startup. A previous failure involved an unresolved `license-ansys` hostname; a current successful run is the relevant test.

See [reflectivity options](REFLECTIVITY.md) for the next study extension and [DWG preparation](../DWG_PREPARATION.md) for the general parameterized-model workflow.
