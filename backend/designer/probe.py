"""Generate a hosted vendor script; its explicit receipt confirms license and import."""
import json


def script(receipt):
    # The vendor hosts Python with GetRootPart injected; never change geometry here.
    return """import json
import System
from System import AppDomain
adaptor = next(a for a in AppDomain.CurrentDomain.GetAssemblies() if a.GetName().Name == 'ThermalAdaptor')
type_ = adaptor.GetType('CRTech.ThermalAdaptor')
licensed = type_.GetMethod('FetchLicense').Invoke(None, System.Array[System.Object]([System.Boolean(False)]))
result = {'licensed': bool(licensed),
          'bodies': len(list(GetRootPart().GetAllBodies())),
          'name': GetRootPart().Name}
with open(PATH, 'w') as stream:
    stream.write(json.dumps(result))
""".replace("PATH", repr(str(receipt)))


def verify(path):
    data = json.loads(path.read_text())
    if not data['licensed']:
        raise RuntimeError('TD Designer license checkout failed. Check Ansys licensing.')
    if data['bodies'] < 1:
        raise RuntimeError('The CAD importer returned no bodies. Check assembly references and translator support.')
    return data
