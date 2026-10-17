#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME KICAD_API_SOCKET KICAD_API_TOKEN
cd /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-018/runtime
exec /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-018/runtime/.venv/bin/python -B /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-018/runtime/scripts/install_gui.py --launch /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-018/runtime/.runs/gui-launcher066/install.json
