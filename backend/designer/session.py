"""Start an isolated TD Designer document and wait for its local API."""
import os
from pathlib import Path
import socket
import subprocess
import time

LAUNCHER = Path(r'C:\Program Files\ANSYS Inc\v261\CRTech\TD Designer\TDDLauncher\TDDLauncher.exe')


def launch(source):
    # Refuse to overwrite a user-owned document in an existing API session.
    with socket.socket() as connection:
        if connection.connect_ex(('127.0.0.1', 50051)) == 0:
            raise RuntimeError('TD Designer is already open. Save and close it, then retry Import / mesh. '
                               + 'The tool will start a separate working copy.')
    if not LAUNCHER.is_file():
        raise RuntimeError('TD Designer 2026 R1 launcher was not found: ' + str(LAUNCHER))
    subprocess.Popen([str(LAUNCHER), str(source)])


def ready(client, name, timeout=360):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            client.call('ansys.api.dbu.v0.admin.Admin', 'Health')
            active = client.call('ansys.api.dbu.v0.designs.Designs', 'GetActive')
            if active.get('isComplete') and active.get('name', '').casefold() == name.casefold():
                return active
        except client.grpc.RpcError:
            pass  # The translator and API start after the launcher process exits.
        time.sleep(2)
    raise TimeoutError('TD Designer did not finish loading within six minutes. Check its window and license status.')


def session_root():
    return Path(os.environ['LOCALAPPDATA']) / 'Temp' / 'Discovery'
