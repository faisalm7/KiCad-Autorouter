#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME KICAD_API_SOCKET KICAD_API_TOKEN
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime042 fresh install 001'
exec '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime042 fresh install 001/.venv/bin/python' -B '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime042 fresh install 001/scripts/install_gui.py' --launch '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime042 fresh install 001/.runs/gui-launcher082/install.json'
