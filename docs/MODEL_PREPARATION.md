# Guided model preparation

Click **Prepare model…** in the workbench. This opens five stages in one preparation window. It accepts SolidWorks assemblies/parts and DWGs as source references, stores a project draft, and builds a new Thermal Desktop model copy from an inspected thermal DWG.

## 1. Source and thermal mesh

Select the original `.SLDASM`, `.SLDPRT` or `.dwg`. Keep SolidWorks referenced parts together. The source file is recorded and checksummed; it is not rewritten or tessellated by this release.

For raw SolidWorks or plain CAD solids, import, simplify and mesh the geometry using licensed **TD Designer (2026 R1)**, or legacy **TD Direct/SpaceClaim** (or the appropriate Thermal Desktop meshing tools). Check model dimensions and units. Preserve component names/layers so you can recognize thermal entities. Save a DWG containing Thermal Desktop surfaces/solids or supported thermal finite elements, then select it as **Thermal mesh DWG**. A DWG already containing thermal entities can be used directly. **Inspect thermal mesh** checks for supported thermal geometry and diffusion nodes; it rejects a geometry-only DWG.

This is an explicit vendor-tool handoff, not an automatic SolidWorks mesher or an embedded CAD editor. The local installation includes TD Designer 2026 R1 and Discovery 2026 R1. The TD Designer launcher is `C:\Program Files\ANSYS Inc\v261\CRTech\TD Designer\TDDLauncher\TDDLauncher.exe`; Discovery is `C:\Program Files\ANSYS Inc\v261\Discovery\Discovery.exe`. Use **Start menu > Ansys 2026 R1 > Thermal Desktop > TD Designer 2026 R1**. License availability and a real SolidWorks import/mesh still need validation. The earlier check for SpaceClaim.exe missed the Discovery-based replacement; absence of that filename is not evidence that the CAD preparation software is missing. The workflow can save a draft before this prerequisite is complete.

## 2. Materials and coatings

Select entities by their handle, type, layer and comment. Enter a component name, measured density (kg/m3), isotropic conductivity (W/m/K), specific heat (J/kg/K), shell thickness (m), solar absorptivity and IR emissivity. Assign every listed thermal entity exactly once. Values are not guessed from CAD material labels. Remove an assignment to change it.

Solids use their existing mesh volume; shell thickness can be blank for solids. For exterior surface elements over a volume mesh, mark **Radiation-only skin** to avoid adding duplicate shell mass/conduction. Do not use that option for actual volume elements. Layer stacks, anisotropy, MLI and other advanced model behavior require model-author preparation. The builder uses constant material properties and opaque diffuse coatings. Solar reflectivity is 1 - absorptivity; IR emissivity is independent.

New component property names use `PREP_<component>`. The builder creates private copies of the material and optical databases, retaining existing definitions. It assigns surfaces/solid elements, enables their intended conductance/capacitance and creates a radiation group. Existing node override flags are respected by the connection wizard; generated nodes in this new-model workflow retain geometry-generated heat capacity.

## 3. Contacts and heat

Add explicit pairs of diffusion node IDs and a total conductance in W/K for each link. This is a point-to-point conductor, not automatic face contact discovery or node stitching. The tool does not infer contact pressure, gaps, fasteners or thermal interface material from touching geometry. Obtain/justify conductance values and refine the network as needed.

Add constant heat power in W at explicitly selected nodes. Split a battery/electronics total across its participating nodes; do not apply the whole total to each node. Existing heat loads and conductors in the input mesh are retained; inspection reports the existing heat-load count. Review them to avoid double counting. Existing shared-temperature node IDs are retained.

## 4. Environment and case

Enter initial diffusion-node temperature, the new space boundary temperature, transient duration, saved-output interval and maximum automatic-solver step. Other existing boundary nodes retain their values. The tool creates a new `PREP_SPACE.1` boundary and a radiation task for the assigned geometry. Generated radiation and user contacts use separate conductor submodels to avoid ID collisions.

**Deep space** calculates radiative exchange/emission without solar, albedo or Earth-IR heating. It is useful for a first baseline; it is not an orbital environment.

**Existing orbit** adds a heating task using an already configured, validated orbit/attitude in the thermal DWG. Create that orbit/environment in Thermal Desktop and re-inspect before selecting it here. New orbit/attitude authoring, eclipse assumptions, pointing, solar/albedo/Earth-IR values and orbital convergence remain explicit model-author work. This release does not derive a correct orbital environment from a CubeSat CAD model.

The selected case name must be new in the default group. The resulting case is transient, starts at zero, saves temperatures, uses the private property databases and recalculates RadCAD. The generated timing settings are connected to `SIM_DURATION_S`, `SIM_OUTPUT_S` and `SIM_MAX_STEP_S`. Use **Connect settings…** afterward for additional supported override targets.

## 5. Build and verify

Build validates complete material mapping, finite SI values, node targets, nonduplicate contact pairs, run controls and orbit selection. A new DWG and private property files are saved with `project.json` and `preparation.json`. Keep that entire folder; absolute database references will break if you move only the DWG. The original CAD and thermal mesh remain unchanged.

The prepared model becomes the workbench input with its new case selected, **All nodes** selected, and customization off. Run **Re-run entirely** for its baseline. API model authoring is not solver or physical validation: check emitted masses/capacitances, total applied power, contacts, coating assignments, saved time range, ray-count/time-step/mesh convergence and component temperature limits.

Drafts can be saved/reloaded as JSON. Reloading requires another mesh inspection; a changed mesh fingerprint clears stale material/contact/load mappings. Changing settings while a build is running does not modify its submitted recipe.

## Validation evidence

A two-cell, 0.1 m by 0.1 m shell was added to an isolated calibration drawing and prepared through this builder. At thickness 0.001 m, density 2700 kg/m3 and specific heat 900 J/kg/K, the emitted capacities were **12.15 J/K per cell**, matching total mass 0.027 kg and total capacity 24.3 J/K. The assigned conductivity was 205 W/m/K; opaque coating solar absorption was 0.2 and IR emissivity 0.8. A selected nodal heat load and a 0.5 W/K contact were added. Existing calibration nodes/loads were retained, as the UI reports.

The resulting newly created case completed a real RadCAD/SINDA run through 10 s with 11 saved times. The space boundary was 3 K. This is a small model-authoring/integration check; it does not validate a full imported SolidWorks assembly, a volume FE mesh, an orbital heating study or an engineering spacecraft design. Source assembly import/meshing cannot be claimed as tested here.

## Vendor references

- [TD Designer 2026 R1 prerequisites](https://ansys.synopsys.com/support/thermal-desktop-system-requirements)
- [TD Designer replaces TD Direct/SpaceClaim in 2026 R1](https://ansys.synopsys.com/en-gb/blog/whats-new-across-ansys-fluids-2026-r1)
- [Legacy TD Direct CAD preparation and thermal meshing](https://www.crtech.com/products/td-direct)
- [Thermal Desktop model and import capabilities](https://www.crtech.com/products/thermal-desktop)
- [OpenTD mesh importer: external mesh import is distinct from CAD tessellation](https://developer.synopsys.com/docs/opentd-net8-reference-2025-r2/class_open_t_d_1_1_rad_c_a_d_1_1_f_e_mesh_importer.xhtml)
