# Task-copper fidelity control

This owned GPL control tests a demonstrated partial-routing failure: native DSN
export rounds submicrometre coordinates and unlocked source routes may be
reshaped. The product now fixes only the already-derived task copper in memory
while exporting and importing. It restores original lock flags before saving.
The original exact-record matcher, original rules, real refill, full-schematic
DRC and candidate-bound proof remain mandatory. No coordinate tolerance, copper
merging, flag stripping or warning suppression is introduced.

The normal worker flag is internal. Source-bound readers require the paired
export/import operations from captured producer code, including zero protected
routes and nested incumbents. Old producers retain their original contract.
Explicit KiCad10.0.7 does not enable this unqualified new worker path.

Generate a fresh source and run the normal CLI (substitute a new directory):

```sh
.venv/bin/python -B -c 'from experiments.task_copper_fixed_v1.fixture import write; write(".runs/task-copper-source-NEW", "alias-free-gap")'
.venv/bin/python -B -m autorouter route .runs/task-copper-source-NEW/owned1007-transport.kicad_pcb --scope partial --adapter both --seconds 90 --output .runs/task-copper-route-NEW
.venv/bin/python -B -m autorouter check-result .runs/task-copper-route-NEW/result.json
```

`submicron` tests split unlocked source copper. `alias-free-gap` additionally
has a real connection gap onto fixed copper, mixed source locks, a free via and
two duplicate padless board-only marks. It has literal schematic field parity.
Both are variants of one exposed owned family, not independent evaluation data.
The unchanged exposed NUS board is a separate preservation control; its source
already has zero opens, so its passing partial route is not added completion.

The diagnostic `driver.py`/`native_probe.py` are retained experimental wrappers.
They deliberately use a worker that production proof readers do not admit;
production invalidation is expected even where their Native checks pass. They
are not a routing/acceptance API. Use the normal CLI above for product tests.

Retained alias-control prerequisites are failures:001has noncanonical free-field
order;002has a missing footprint-library warning;003has the base fixture's
Datasheet '~'/empty warning with extra board-only footprints, outside that
narrow field-equivalence qualifier.004is a newly authored complete control, not
an unattended first attempt. No retained source or finding was modified. The
in-format invalid capping control also shows that geometrically clean Native
DRC does not establish preservation of manufacturing intent.

See `evidence/task-copper-fixed-native-001.json` for actual producers, hashes,
positive/negative results, costs and limits. This is shared interchange and
protected-scope support, not a routing algorithm or superiority over B2.
