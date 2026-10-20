"""Prepare a process-local Microsoft compiler environment for SINDA."""
import os
from pathlib import Path
import shutil
import subprocess


def prepare_toolchain():
    """Import the installed VS x64 build environment without changing Windows settings."""
    if shutil.which("link.exe") and os.environ.get("LIB"):
        return
    installer = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
    locator = installer / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not locator.is_file():
        raise RuntimeError("SINDA needs Visual Studio C++ Build Tools, including the x64 linker and Windows SDK.")
    found = subprocess.run([str(locator), "-latest", "-products", "*", "-requires",
                            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                            "-property", "installationPath"], capture_output=True, text=True,
                           check=True, timeout=30)
    script = Path(found.stdout.strip()) / "Common7" / "Tools" / "VsDevCmd.bat"
    if not script.is_file():
        raise RuntimeError("Visual Studio x64 C++ tools are missing. Install the Desktop development with C++ workload.")
    # The script path comes from Microsoft's local installer, not model input.
    command = f'cmd.exe /d /s /c ""{script}" -no_logo -arch=x64 -host_arch=x64 >nul && set"'
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
    environment = {}
    for line in result.stdout.splitlines():
        key, separator, value = line.partition("=")
        if separator and key:
            environment[key] = value
    os.environ.update(environment)
    if not shutil.which("link.exe") or not os.environ.get("LIB"):
        raise RuntimeError("Visual Studio initialization did not provide a linker and LIB paths.")
