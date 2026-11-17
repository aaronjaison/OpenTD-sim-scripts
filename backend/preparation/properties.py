"""Create private SI property databases and assign explicitly selected components."""
from pathlib import Path
import shutil


def si(api):
    units = api.UnitsData()
    units.SetToSI()
    return units


def dimensional(api, target, field, value):
    setattr(target, field, type(getattr(target, field))(float(value), si(api)))
    if hasattr(target, field + "Exp"):
        getattr(target, field + "Exp").Value = ""


def databases(desktop, folder):
    # Preserve existing definitions for nodes/loads not replaced by component mappings.
    for name, getter, method in (("prep-materials.tdp", "GetThermoPropDBPathname", "OpenThermoPropDB"),
                                 ("prep-optics.rco", "GetOpticalPropDBPathname", "OpenOpticalPropDB")):
        path = Path(folder) / name
        source = Path(getattr(desktop, getter)())
        if source.is_file():
            shutil.copy2(source, path)
        else:
            path.write_text("[UNICODE]\n", encoding="utf-8-sig")
        getattr(desktop, method)(str(path))


def assign(desktop, api, objects, parts, group):
    surfaces = 0
    for part in parts:
        name = "PREP_" + part["name"]
        material = desktop.CreateThermoProps(name)
        for field, key in (("Density", "density"), ("Conductivity", "conductivity"), ("SpecificHeat", "cp")):
            dimensional(api, material, field, part[key])
        material.Update()
        optic = desktop.CreateOpticalProps(name)
        optic.Alph, optic.Emis = float(part["alpha"]), float(part["epsilon"])
        optic.Soltrns, optic.Irtrns, optic.Solspc, optic.Irspc = 0, 0, 0, 0
        optic.Update()
        for handle in part["handles"]:
            obj = objects[handle]
            for field in ("DensityMult", "KuMult", "KvMult", "KwMult"):
                if hasattr(obj, field):
                    setattr(obj, field, 1.0)
                    getattr(obj, field + "Exp").Value = ""
            if hasattr(obj, "TopMaterial"):
                if obj.UseTopMaterialStack or obj.UseBotMaterialStack or obj.UseTopMLI or obj.UseBotMLI:
                    raise ValueError("Layer stacks/MLI need model-author preparation; use an unlayered mesh for this workflow.")
                obj.TopMaterial = obj.BotMaterial = obj.TopBotMaterial = name
                dimensional(api, obj, "TopThickness", part["thickness"])
                dimensional(api, obj, "BotThickness", 0)
                obj.TopOpticalProp = obj.BotOpticalProp = name
                obj.GenerateCCData = int(not part["skin"])
                if hasattr(obj, "GenerateCCDataExp"):
                    obj.GenerateCCDataExp.Value = ""
                obj.AnalysisGroups.Clear()
                obj.AnalysisGroups.Add(api.RadCAD.AnalysisGroupSurfaceInfo(group, api.RadCAD.RcEntityData.Active.BOTH))
                surfaces += 1
            else:
                if part["skin"]:
                    raise ValueError("Radiation-only skins must be surface elements, not solid volumes.")
                obj.ThermoMaterial = name
                obj.GenerateCondCap = 1
                if hasattr(obj, "GenerateCondCapExp"):
                    obj.GenerateCondCapExp.Value = ""
                if hasattr(obj, "OutsideOpticalProperties"):
                    for i in range(len(obj.OutsideOpticalProperties)):
                        obj.OutsideOpticalProperties[i] = name
                        obj.InsideOpticalProperties[i] = name
                    obj.AnalysisGroups.Clear()
                    obj.AnalysisGroups.Add(solid_group(api, group))
                    surfaces += 1
            obj.Update()
    if not surfaces:
        raise ValueError("Radiation requires exterior surface/skin elements or TD finite-difference solids. Export exposed surfaces from the mesher.")


def solid_group(api, group):
    from System import Array, Int32
    return api.RadCAD.FdSolid.AnalysisGroupSolidInfo(group, api.RadCAD.FdSolid.RcFdSolidData.Active.OUTSIDE,
                                                    Array[Int32]([]))
