#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME KICAD_API_SOCKET KICAD_API_TOKEN
cd /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-019/runtime
exec /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-019/runtime/.venv/bin/python -B /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-019/runtime/scripts/install_gui.py --launch /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-019/runtime/.runs/gui-launcher067/install.json
