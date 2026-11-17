"""Distinguish native mesher failures from a completed mesh export."""
import json
import time
import xml.etree.ElementTree as ET


def wait_mesh(folder, sessions, timeout=1800):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # Read explicit native failure outputs before accepting any export.
        for session in sessions():
            for path in session.rglob('Output.op'):
                try:
                    data = json.loads(path.read_text())
                except (OSError, ValueError):
                    continue  # The mesher may still be writing the file.
                if data.get('discriminator') == 'ErrorOperationOutput':
                    (folder / 'mesh-error.json').write_text(json.dumps(data, indent=2))
                    raise RuntimeError('TD Designer could not mesh the geometry. Native diagnostics: '
                                       + str(folder / 'mesh-error.json')
                                       + '. Repair the reported faces in TD Designer; no components were removed.')
        mesh = folder / 'femodel.xml'
        if mesh.is_file() and mesh.stat().st_size:
            try:
                ET.parse(mesh)
                return mesh
            except (OSError, ET.ParseError):
                pass  # A partially written XML file is not a completed export.
        time.sleep(2)
    raise TimeoutError('TD Designer meshing did not produce femodel.xml before the time limit. '
                       + 'Inspect its Meshing Status window and ' + str(folder))
