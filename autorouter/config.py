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
