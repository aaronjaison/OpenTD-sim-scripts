"""Import CAD into a private native copy, check the license, and request a mesh."""
from pathlib import Path
import hashlib
import json
import tempfile
from .rpc import DesignerRPC
from .session import launch, ready, session_root
from .probe import script, verify
from .status import wait_mesh


def run(source, output, progress=lambda text: None):
    source = Path(source).resolve()
    if not source.is_file() or source.suffix.lower() not in ('.sldasm', '.sldprt', '.dwg'):
        raise ValueError('Choose an existing SolidWorks assembly/part or DWG first.')
    Path(output).mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='designer-', dir=output)).resolve()
    root = session_root()
    previous = set(root.glob('*'))
    receipt = {'source': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    client = DesignerRPC()
    try:
        progress('Opening TD Designer and importing CAD…')
        launch(source)
        ready(client, source.stem)
        probe = folder / 'license_import.py'
        probe.write_text(script(folder / 'license_import.json'))
        client.script(probe)
        receipt.update(verify(folder / 'license_import.json'))
        progress(f"License checked out; imported {receipt['bodies']} bodies. Saving working copy…")
        client.call('ansys.api.dbu.v0.designs.Designs', 'SaveAs', {'filepath': str(folder / 'model.dsco')}, 120)
        progress('Generating thermal mesh. Large assemblies can take several minutes…')
        client.call('ansys.api.dbu.v0.dbuapplication.DbuApplication', 'RunCommand',
                    {'command': 'CRTech.ArtemisMesh', 'data': ''}, 120)
        mesh = wait_mesh(folder, lambda: set(root.glob('*')) - previous)
        receipt['mesh'] = str(mesh)
        return f'Mesh exported: {mesh}. Import this TD Direct mesh into a new Thermal Desktop drawing before material/contact preparation.'
    finally:
        receipt['source_unchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == receipt['sha256']
        (folder / 'receipt.json').write_text(json.dumps(receipt, indent=2))
        client.close()
