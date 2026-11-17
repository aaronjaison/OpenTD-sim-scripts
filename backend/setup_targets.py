"""Explicit, supported model targets and SI expression connections."""
from .sim_settings import SYMBOLS

CONTROL_FIELDS = {"duration": "timendExp", "output": "outputExp", "max_step": "dtimehExp"}
SUPPORTED = ("initial", "duration", "output", "max_step", "heat", "emissivity")


def node_key(node):
    return f"{node.Submodel}.{node.Id}"


def eligible_node(node):
    return str(node.NodeType) in ("DIFFUSION", "ARITHMETIC") and not node.UseVersusTime


def eligible_heat(load):
    return str(load.HeatLoadTransientType) == "CONSTANT_HEAT_LOAD" and str(load.Type) in ("LOAD", "VOLUME")


def catalog(desktop, include_optics=True):
    nodes = sorted({node_key(n) for n in desktop.GetNodes() if eligible_node(n)})
    loads = [(str(l.Handle), str(l.Name), str(l.Type)) for l in desktop.GetHeatLoads() if eligible_heat(l)]
    optics = sorted(str(o.Name) for o in desktop.GetOpticalPropss()) if include_optics else []
    return {"nodes": nodes, "loads": loads, "optics": optics}


def expression(api, target, field, value):
    # Preserve the destination dimension type but explicitly interpret input in SI.
    units = api.UnitsData()
    units.SetToSI()
    exp = api.ExpressionData(value, units)
    exp.unitsType = getattr(target, field).unitsType
    setattr(target, field, exp)


def connect_targets(desktop, case, api, parameters, nodes, heat, volume, coating):
    records = []
    for name, field in CONTROL_FIELDS.items():
        if SYMBOLS[name] in parameters:
            expression(api, case.SindaControl, field, SYMBOLS[name])
            records.append(("control", field, SYMBOLS[name]))
    if SYMBOLS["initial"] in parameters:
        if case.UseRestartFile or case.RestartCase:
            raise ValueError("Disable case restart before connecting initial temperature.")
        all_nodes = list(desktop.GetNodes())
        selected = [n for n in all_nodes if node_key(n) in nodes]
        if not nodes or set(nodes) != {node_key(n) for n in selected} or not all(eligible_node(n) for n in selected):
            raise ValueError("Select eligible non-boundary nodes; every object sharing an ID must be eligible.")
        for node in selected:
            expression(api, node, "InitialTempExp", SYMBOLS["initial"])
            node.UserOverride = True
            node.Update()
            records.append(("node", str(node.Handle), SYMBOLS["initial"]))
    if SYMBOLS["heat"] in parameters:
        loads = {str(l.Handle): l for l in desktop.GetHeatLoads()}
        if heat not in loads or not eligible_heat(loads[heat]):
            raise ValueError("Select an existing constant heat load in W or W/m3.")
        load = loads[heat]
        value = SYMBOLS["heat"]
        if str(load.Type) == "LOAD":
            import math
            if not math.isfinite(volume) or volume <= 0:
                raise ValueError("A total-power load requires its represented heated volume in m3, greater than zero.")
            value += "*" + format(volume, ".17g")
        expression(api, load, "ValueExp", value)
        load.Update()
        records.append(("heat", heat, value))
    if SYMBOLS["emissivity"] in parameters:
        if not coating or coating not in [str(o.Name) for o in desktop.GetOpticalPropss()]:
            raise ValueError("Select an existing VED optical coating.")
        optic = desktop.GetOpticalProps(coating)
        if optic.VarIrEmis or optic.TempIrEmis or optic.UseWaveLengthDepProps:
            raise ValueError("Use a constant IR coating; variable/spectral emissivity requires model-author preparation.")
        expression(api, optic, "emisExp", SYMBOLS["emissivity"])
        optic.Update()
        records.append(("optic", coating, SYMBOLS["emissivity"]))
    return records


def verify_targets(desktop, case, records):
    # Re-read persisted expressions instead of treating symbol presence as a binding.
    for kind, target, expected in records:
        if kind == "control":
            actual = getattr(case.SindaControl, target).Value
        elif kind == "node":
            actual = desktop.GetNode(target).InitialTempExp.Value
        elif kind == "heat":
            actual = desktop.GetHeatLoad(target).ValueExp.Value
        else:
            actual = desktop.GetOpticalProps(target).emisExp.Value
        if str(actual).strip() != expected:
            raise RuntimeError(f"Connection did not persist: {kind} {target}")
