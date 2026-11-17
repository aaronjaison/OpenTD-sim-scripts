# Reflectivity: recommended next step

**Use RadCAD through OpenTD first.** RadCAD already traces reflected radiation between surfaces and supports diffuse/specular reflection and transmission in solar and infrared bands. OpenTD is the automation interface; RadCAD calculates radiation exchange/heating and SINDA calculates temperature. No additional optical solver is needed when the coating properties are known. [RadCAD capabilities](https://www.crtech.com/products/radcad)

## What “solve for reflectivity” means

Thermal Desktop can calculate the *thermal effect* of specified optical properties. It does not identify an unknown coating reflectivity from a temperature trace automatically. That needs measured reflectance data, an optical material model, or a separately designed parameter-fitting study. Temperature-only fitting can confuse reflectivity with emissivity, contact conductance, heating, or heat capacity.

For each wavelength band, conserve incident energy: `absorptivity + reflectivity + transmissivity = 1`. For an opaque surface, transmission is zero, so solar reflectivity is `1 - solar absorptivity`. Under the corresponding grey IR/Kirchhoff assumptions, IR reflectivity is `1 - IR emissivity`. Do not use `1 - IR emissivity` as **solar** reflectivity: the bands differ. [NASA optical-property relations, equations 1-3](https://ntrs.nasa.gov/api/citations/20180003390/downloads/20180003390.pdf?attachment=true)

The six supplied case optical files have `SOLTRANS=IRTRANS=0` and `SOLSPEC=IRSPEC=0` for VED: opaque, diffuse surfaces. For our current VED, solar absorptivity 0.85 means solar reflectivity 0.15. IR emissivities 0.30 to 0.80 imply IR reflectivities 0.70 to 0.20. Therefore this sweep already changes IR reflection along with emission, while solar reflection stays fixed. This is an inference from the optical inputs, not a newly measured coating property.

The fresh reproduction generated `C1A1DirectAbsorbed.xls`, `C1A1ReflectedAbsorbed.xls` and `C1A1TotalAbsorbed.xls` (tab-separated reports with `.xls` extensions). The reflected-absorbed report contains nonzero powers. Reflection is already participating in this model; adding another reflected heat load would risk double counting. These reports are included in the study bundle under `radiation/`.

## How to extend our scripts

1. Add a separate, optional optical-settings section targeting the VED coating only. Require an explicit coating/surface selection; do not change every material.
2. Accept solar reflectivity, solar transmission and reflected specular fraction. Compute solar absorption as `1 - reflectivity - transmission` and reject negative absorption or any fraction outside 0..1. Keep IR emissivity independent, with its own transmission/specularity settings.
3. In a copied case optical database, update `Alph`, `Emis`, `Soltrns`, `Irtrns`, `Solspc`, and `Irspc`, then call `Update()`. Confirm the installed version's specularity convention before assigning values; a specular *fraction of reflected energy* is not the same as absolute reflected power. Read the values back and check generated optical reports. [OpenTD optical API](https://developer.synopsys.com/docs/opentd-net4-reference-2025-r2/class_open_t_d_1_1_rad_c_a_d_1_1_optical_props_data.xhtml)
4. Recalculate RadCAD heating and radiation exchange for each optical state, then solve SINDA. Include the optical-file checksum and all optical settings in cache identity. The current cache fingerprints only the DWG and default adjacent sidecars; it does not track every external case database, so **force fresh runs** for optical studies.
5. Validate opaque energy balance, black-surface/mirror limits, a two-surface reflection test, and ray-count convergence. Compare absorbed power as well as temperature. Do not add a second manual reflected-flux load on top of the same RadCAD contribution.

The installed OpenTD 26.1.4 API exposes these property names. The vendor's 2026 R1 example also supports wavelength-dependent optical tables and requires a RadCAD license. [OpenTD optical-property example](https://developer.synopsys.com/docs/opentd-2026-r1/getting-started/creating-td-model/optical-properties.md)

This is a proposed extension; the current GUI does not yet expose a reflectivity control.

## When another module helps

| Need | Option | How it would connect |
|---|---|---|
| Known coating reflectance/absorptance | RadCAD alone | Set measured solar/IR properties and recalculate |
| Predict reflection/transmission from a stack of thin films | NIST pySCATMECH `FilmStack` | Python computes R/T versus wavelength/angle from layer thicknesses and complex refractive indices |
| Licensed optical thin-film workflow | Ansys Lumerical STACK through Python | `stackrt` computes layer-stack reflection/transmission; export tables |

NIST documents `OpticalFunction`, `Film` and `FilmStack`, including wavelength-dependent complex refractive indices and incidence angle. This is suitable for planar thin-film optical-property generation, not a substitute for spacecraft thermal ray tracing. [NIST Fresnel module](https://pages.nist.gov/pySCATMECH/UsingFresnel.html)

Lumerical's Python API exposes `stackrt` and demonstrates a gold thin-film calculation. This adds a separate licensed optical workflow. [Lumerical Python example](https://optics.ansys.com/hc/en-us/articles/360041579954-Script-Commands-as-Methods-Python-API)

For either option, compute `A(lambda,theta)=1-R-T`, integrate solar absorptivity against the incident solar spectrum, and integrate thermal emissivity against the appropriate temperature-dependent Planck/angular weighting (or supply validated spectral tables). Import the resulting properties into RadCAD. Required inputs are coating layer order, thicknesses, substrate, complex refractive index versus wavelength, incidence/polarization assumptions, surface roughness/specularity, and VED-state dependence. We do not have enough of those inputs to predict the physical coating's reflectivity yet.

**Recommendation:** start with a measured or explicitly assumed solar-reflectivity sweep using RadCAD. Use pySCATMECH or STACK only if the goal is to design/predict the coating itself. Keep that new study separate from the fixed-emissivity reproduction.
