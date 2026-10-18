# Protected legacy via import

This development control closes one documented partial/locked-routing blocker.
It is adapter fidelity shared by corrected baselines and the proposed system,
not a new routing algorithm or a completion gain over tuned Freerouting.

KiCad10.0.0's pinned parser treats omitted covering, plugging, capping and
filling as six OFF values in pre-20250228 files. Modern omission inherits the
board defaults. The new policy is restricted to already-supported20241229
originals and20260206 imports from the pinned production toolchain. Each eligible
protected via must import all four canonical groups exactly once, with all six
values explicitly `no`. Geometry, nets, layers, locks, uniqueness and collisions
remain checked. The complete original node, UUID and field omissions are restored.
Modern sources and explicit manufacturing fields retain their strict behavior.
Historical producer receipts keep their original policy; new producer code and
tool declarations force the source-derived policy independently of receipt labels.

`fixture.py` derives three GPL-owned complete-schematic projects from the existing
owned transport factory. All enable board manufacturing defaults, retain a locked
via and both-layer KEEP copper, and require a new ROUTE connection and real zone
refill. They distinguish legacy omission, modern inheritance and explicit legacy
values. No external CAD or model is used. `observe.py` writes separate native
saved outputs and checks source hashes. Its mode getters return opaque SWIG
objects in this binding; integer pointer conversions are **not enum observations**.

To reproduce with the pinned local toolchain, choose a fresh durable output:

```sh
.venv/bin/python -B - <<'PY'
from pathlib import Path
from experiments.legacy_via_import_v1 import fixture
root = Path('.runs/legacy-via-reproduction-NEW').absolute()
root.mkdir()
for case in fixture.CASES:
    fixture.write(root / case, case)
PY
.venv/bin/python -B -m autorouter route \
  .runs/legacy-via-reproduction-NEW/legacy-omitted/owned1007-transport.kicad_pcb \
  --scope partial --adapter both --seconds 90 \
  --output .runs/legacy-via-reproduction-NEW/route
.venv/bin/python -B -m autorouter check-result \
  .runs/legacy-via-reproduction-NEW/route/result.json
.venv/bin/python -B -m unittest \
  tests.test_legacy_via_import tests.test_normal_selected_import
```

The development record retains failed initial load, unused-zero-net export,
opaque-pointer interpretation and missing-schema controls. Declaring tested
`net_settings.meta.version=3` in **new** controls preserves the authored Default
dimensions; it does not repair any retained source or relax any rule. All final
candidates require their own real Native/refill/full-schematic/original checks.
Warnings and whole-project cleanliness remain separate from routing acceptance.

An exposed NUS partial trial remains rejected:21 original non-UUID records are
missing and33 differ/add after import. Native DSN already rounds source endpoints;
the new via rule grants no coordinate or topology waiver. Do not reinterpret this
trial as a completion gain or start another normalization cycle without a precise
faithful transport mechanism. Selected-locked combinations, new installed-build
GUI qualification, broader board families and release gates remain separate.
