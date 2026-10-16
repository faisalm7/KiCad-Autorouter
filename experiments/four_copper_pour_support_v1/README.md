# Four-copper pour support control

This exposed, GPL-owned fixture tests a documented support failure: a canonical
four-copper source with an inner-layer copper-pour prohibition was rejected by
the former two-layer grammar. It is derived from the existing forced-inner
fixture, not an independent benchmark family or a held-out board.

The supported new form has an omitted area net, explicit island-removal mode 0,
disabled placement and only copper-pour prohibition. All five flags must be
explicit. Copper identities/order remain F.Cu/In1.Cu/In2.Cu/B.Cu with physical
IDs 0/4/6/2 and signal types; the existing stackup, source-version and full-via
guards remain. Numeric-zero restricted modern sources, copper aliases, other
area restrictions and other native versions remain outside this qualification.
The source-net decoder was not broadened.

[Current runtime006 evidence](../../evidence/runtime006-four-cu-pour-integration-001.json)
binds source `773c5271`, actual installed production Route/review/test-intent/
fresh Native export/current readers, both final candidate hashes, original
design checks, ten protected traces, both inner fill rows and full-schematic
observations. It retains six warnings/two ignored checks and false whole-project
cleanliness. The direct final-runtime injected-fill control rejects without
refilling the defect away. A separate actual short produces eight blocking
findings. Two-layer Improve and full138 also pass on the same product modules.
No GUI window was run for006; actual GUI056 tested the unchanged GUI code on004.

Reproduce the installed routing control on this prepared Mac using fresh paths:

```sh
.venv/bin/python -B - <<'PY'
from pathlib import Path
import hashlib, json
from autorouter import sexpr as sx
from experiments.four_copper_pour_support_v1 import fixture
base = Path('.runs/pour-reproduction-new')
base.mkdir()  # Refuses an existing path; never overwrite retained evidence.
source = base / 'source'
source.mkdir()
files = fixture.files()
name = fixture.STEM + '.kicad_pcb'
tree = sx.parse(files[name].decode())
display = {'9':'F.Adhesive','11':'B.Adhesive','5':'F.Silkscreen',
           '7':'B.Silkscreen','17':'User.Drawings','19':'User.Comments',
           '21':'User.Eco1','23':'User.Eco2','31':'F.Courtyard','29':'B.Courtyard'}
for row in sx.one(tree, 'layers')[1:]:
    if row[0] in display:
        assert len(row) == 3 and row[2] == 'user'
        row.append(json.dumps(display[row[0]]))
files[name] = (sx.dump(tree) + '\n').encode()
expected = json.loads(Path('evidence/runtime006-four-cu-pour-integration-001.json').read_text())['source_hashes']
assert {n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()} == expected
for n, raw in files.items():
    (source / n).open('xb').write(raw)
PY
.venv/bin/python -B scripts/prepare_runtime.py --output "$PWD/.runs/pour-reproduction-new/runtime" --copy-local-engine
.venv/bin/python -B -m venv --copies --without-pip .runs/pour-reproduction-new/runtime/.venv
mkdir .runs/pour-reproduction-new/runtime/.runs
.runs/pour-reproduction-new/runtime/.venv/bin/python -B scripts/qualify_runtime_workflow.py --runtime "$PWD/.runs/pour-reproduction-new/runtime" --source "$PWD/.runs/pour-reproduction-new/source/owned-four-copper-forced-inner.kicad_pcb" --output "$PWD/.runs/pour-reproduction-new/runtime/.runs/workflow" --method route
```

The controller performs a **software-test acceptance intent**, then a new native
validated export; this is not human PCB approval or live application. It uses
the pinned installed KiCad10.0.0, Java25.0.2 and existing cached Freerouting2.5
JAR, with no network or AI account. Allow one heavy job at a time. Inspect every
result and warning; do not require a repeated candidate hash, because new runs
create new route identities. The source hashes must match. A later product
change needs its own fresh qualification.

For user operation, follow [the graphical workflow](../../docs/gui-workflow.md)
and [persistent settings](../../docs/routing-preferences.md). Native routing
acceptance, whole-project DRC and electrical/physical approval remain separate.
`controls_fixture.py` reproduces the earlier three metadata forms;
`saved_fill_recipe.py` documents their exact retained-byte positive/negative
construction. Neither is a second validator. Raw prior runs remain local;
adjacent evidence records their hashes, actual findings, costs and failures.

The new scope does not admit HFE: unnumbered unassigned conductive pads,
schematic partition proof and the selected native-version obligations remain.
There is no comparative completion, cleanup-time or broad superiority claim.
