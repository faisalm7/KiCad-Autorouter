"""Explicit, project-scoped tool paths; installed application is never changed."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
KICAD = Path('/Applications/KiCad/KiCad.app/Contents')
CLI = KICAD / 'MacOS/kicad-cli'
PYTHON = KICAD / 'Frameworks/Python.framework/Versions/3.9/bin/python3.9'
PCBNEW = KICAD / 'Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/_pcbnew.so'
JAVA = Path('/Library/Java/JavaVirtualMachines/temurin-25.jdk/Contents/Home/bin/java')
JAR = ROOT / '.tools/freerouting-2.5.0.jar'
JAR_SHA256 = 'f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7'


def resolve_tool_path(value):
    """Resolve a lock path; project-relative pins cannot escape this checkout.

    Installed application pins remain absolute, including their OS-managed path
    layout. Relative pins must be canonical and contain no symlink components.
    Resolving a path does not replace the caller's mandatory digest check.
    """
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('invalid tool pin path')
    path = Path(value)
    if path.is_absolute():
        return path
    if str(path) != value or any(part in ('.', '..') for part in value.split('/')):
        raise ValueError('noncanonical or escaping relative tool pin')
    result = ROOT / path
    if result == ROOT or not result.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('relative tool pin escapes project')
    current = ROOT
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('symlink in project-relative tool pin')
    return result
