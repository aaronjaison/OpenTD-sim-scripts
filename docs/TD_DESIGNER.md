# Import and mesh with TD Designer

In **Prepare model > 1 Source / mesh**, choose the top-level SolidWorks assembly or part, then **Import / mesh in TD Designer**. Raw DWG is also offered; its CAD translator must support the drawing. Keep assembly dependencies in their original relative folders. Save and close an already open TD Designer session first: the tool refuses to replace an existing session's document.

Requires installed, licensed **TD Designer 2026 R1** (Discovery host, Thermal Adaptor and local API Server add-in). Install the tool's optional dependencies in the same Python environment: `python -m pip install -e ".[designer]"`. The launcher is detected at the standard Ansys v261 installation path. This integration is specific to that release; it does not configure licensing or install CAD translators.

The queued action opens the source, waits for CAD import, requests a real TD Designer license checkout, counts imported bodies, saves `model.dsco` in a new `output/designer-*` folder, and requests the vendor's automatic thermal mesh. Progress appears in the workbench. TD Designer remains open so you can inspect its geometry and status window. Large assemblies can take several minutes (six-minute import and thirty-minute mesh limits).

A successful action reports the `femodel.xml` path. **This is a mesh export, not yet a prepared thermal DWG or solved simulation.** Import it using Thermal Desktop's TD Direct mesh importer into a new drawing, save the DWG, then select **Thermal mesh DWG > Inspect thermal mesh** in the wizard. Assign materials/coatings, contacts, heat and environment using the remaining pages. CAD material labels alone do not establish thermal contacts or loads. Confirm geometry units, retained parts and mesh convergence before using temperatures.

The tool uses the installed automatic mesh defaults. Explicit mesh-size controls and automatic geometry repair are not yet exposed. It does not suppress small parts, remove invalid faces or claim that a partial mesh is usable. Existing shared-temperature node IDs remain untouched by this feature.

## Errors and receipts

The existing workbench error dialog records failures. Each run saves `receipt.json` and, after the hosted check, `license_import.json` plus its Python probe. The receipt records the source SHA-256 before/after; it checks the selected source file, not every assembly dependency. `model.dsco` is a separate native copy. On a native meshing failure, `mesh-error.json` preserves the exact scoped face/body references. A successful command response alone is never considered mesh completion; the export must be complete XML and no scoped native failure may be present.

For `DSMESH_FACENOTACCEPTABLE`, open TD Designer's Meshing Status diagnostics and locate the scoped geometry. Repair the source or the working native copy and inspect the result before meshing again. Do not discard a body simply to make the mesher pass. Repairing an imported working copy is a manual step in this version; the tool imports the selected source afresh on each run.

## Actual assembly test: 16 November 2026

Source: `AntSat 01 Full Assembly 2025dec06.SLDASM`, from the supplied `Current Full Assembly [Fall 2025]` folder.

- Real TD Designer license checkout: **passed**, `FetchLicense(False)` returned true; `HaveLicense` was true afterward.
- SolidWorks translator/import: **passed**, 787 bodies; active document reported complete.
- Native working copy saved: `output/designer-assembly-al0ce601/AntSat.dsco` (99,070,699 bytes).
- Meshing: **failed**, `DSMESH_FACENOTACCEPTABLE`. Native operation `bc2e8629-e858-4cee-8486-ef409afe461a` reported four faces across two body occurrences. This is a geometry failure, not evidence of a license denial. No complete `femodel.xml` was produced.
- Occurrence path `21 / 697 / 704`, native body reference `2895`: face `240102`.
- Occurrence path `21 / 697 / 715`, native body reference `2942`: faces `244887`, `245952`, `244935`.

Component instance names are blank in this imported subtree, so these are session-scoped native identifiers, not guessed SolidWorks part names. They may change on reimport. Detailed evidence is in the local `output/designer-integration` folder (`runtime-audit.json`, `product_probe.json`, `mesh-error.json`, `bodies.json`). These large/private CAD artifacts are not committed to GitHub. The automated license probe and failure detector were also exercised against the live session; automated UI/session tests use fakes and do not prove a successful full assembly mesh.
