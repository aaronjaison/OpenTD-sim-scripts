"""Create explicit nodal loads, conductors and a radiation/solver baseline."""
from .properties import dimensional
from ..setup_targets import expression


def case_and_environment(desktop, api, recipe, nodes, folder):
    name = recipe["case"]
    if any(str(c.Name) == name and not str(c.GroupName) for c in desktop.GetCaseSets()):
        raise ValueError("Choose a new case name; an existing default-group case has that name.")
    env = recipe["environment"]
    case = desktop.CreateCaseSet(name, "", name)
    case.SteadyState, case.Transient = 0, 1
    case.UseRestartFile, case.RestartCase = 0, 0
    for key, field in (("duration", "timend"), ("output", "output"), ("max_step", "dtimeh")):
        symbol = "SIM_" + {"duration": "DURATION_S", "output": "OUTPUT_S", "max_step": "MAX_STEP_S"}[key]
        existing = {str(s.Name): s for s in desktop.GetSymbols()}
        if symbol in existing:
            existing[symbol].Value = str(env[key]); existing[symbol].Update()
        else:
            desktop.CreateSymbol(symbol, str(env[key]))
        dimensional(api, case.SindaControl, field, env[key])
        expression(api, case.SindaControl, field + "Exp", symbol)
    dimensional(api, case.SindaControl, "timeo", 0)
    dimensional(api, case.SindaControl, "dtimei", 0)
    dimensional(api, case.SindaControl, "dtimel", 0)
    for node in nodes.values():
        dimensional(api, node, "InitialTemp", env["initial"])
        node.InitialTempExp.Value = ""
        node.UserOverride = bool(node.UserDefined)
        node.Update()
    # Named environment submodel avoids modifying an existing boundary node.
    if any(str(n.Submodel) == "PREP_SPACE" for n in desktop.GetNodes()):
        raise ValueError("PREP_SPACE already exists; start from the thermal mesh rather than a previous prepared output.")
    desktop.CreateSubmodel("PREP_SPACE")
    boundary = desktop.CreateNode()
    boundary.Submodel = api.SubmodelNameData("PREP_SPACE")
    boundary.Id = 1
    boundary.NodeType = api.RcNodeData.NodeTypes.BOUNDARY
    dimensional(api, boundary, "InitialTemp", env["space"])
    boundary.Update()
    task = api.RadiationTaskData()
    task.AnalGroup = "PREP_RADIATION"
    task.SpaceNode = "PREP_SPACE.1"
    task.RkSubmodel = "PREP_RAD"
    task.TypeCalc = api.RadiationTaskData.calcType.RADK
    dimensional(api, task, "SpaceTemp", env["space"])
    case.RadiationTasks.Add(task)
    if env["mode"] == "Existing orbit":
        desktop.GetOrbit(env["orbit"])  # Fail before publication if the name is missing.
        heating = api.RadiationTaskData()
        heating.AnalGroup, heating.OrbitName = "PREP_RADIATION", env["orbit"]
        heating.HrSubmodel = "PREP_HEAT"
        heating.TypeCalc = api.RadiationTaskData.calcType.HEATRATE
        case.RadiationTasks.Add(heating)
    case.CalculateRadiation = 1
    case.RadiationTaskDbOption = api.CaseSetData.RadiationTaskDbOptions.RECALCULATE
    case.SaveTemp, case.RunSinda, case.RunSindaShowPlot = 1, 1, 0
    case.UseUserDirectory, case.UserDirectory = 1, str(folder)
    case.OpticOverride, case.ThermoOverride = 0, 0
    case.Update()
    return case


def loads_and_contacts(desktop, api, recipe, nodes):
    for item in recipe["loads"]:
        load = desktop.CreateHeatLoad(api.Connection(nodes[item["node"]]))
        load.Name = "PREP heat " + item["node"]
        load.Value = float(item["watts"])
        load.Type = api.RcHeatLoadData.HeatLoadTypes.LOAD
        load.Update()
    for item in recipe["contacts"]:
        contact = desktop.CreateConductor(api.Connection(nodes[item["from"]]), api.Connection(nodes[item["to"]]))
        contact.Submodel = api.SubmodelNameData("PREP_LINK")
        contact.Value = float(item["conductance"])
        contact.UseMaterial, contact.IsRadiation, contact.IsPerArea = 0, 0, 0
        contact.Update()
