Local KiCad Autorouter runtime directory

This is a curated, path-bound Mac runtime directory, not a standalone app.
It requires the selected pinned KiCad app and Java 25.0.2 installation,
plus a new local Python 3.11 environment at .venv. Nothing is downloaded here.
The original toolchain.lock.json remains authoritative. If the local Freerouting
JAR was not explicitly copied at preparation, routing remains unavailable.

Create the environment with Python 3.11: python3.11 -m venv --copies .venv
Use copies so strict local artifact backups can retain regular interpreter files.
Check dependencies with: .venv/bin/python -B -m autorouter doctor
Prepare a NEW separate GUI launcher directory with:
  .venv/bin/python -B scripts/install_gui.py --output /absolute/new-launcher
Use that launcher's README for the save/close/route/review/export workflow.
Candidates remain separate from the saved source project. Native acceptance,
whole-project DRC, and physical/electrical review are distinct checks.

Keep this directory and pinned external applications at their prepared paths.
The manifest records build-source HEAD, not a live Git checkout. Immutable
product files are checked afresh. Only .runs and .venv are reserved mutable
directories: their contents are not pinned by this manifest or copied from the
source checkout. Do not add research archives, datasets, .git or other files.
Use -B / PYTHONDONTWRITEBYTECODE=1; generated __pycache__ is outside the curated
population and will refuse. Placement-guidance modes require source checkout
proof and remain unsupported here. A changed product requires a new directory.

This local artifact is not publication authorization. A copied Freerouting JAR
remains an external local cache artifact; binary redistribution and release
compliance have not been qualified. GPL project license is retained in LICENSE.
Qualification and source history stay in the original source repository.
