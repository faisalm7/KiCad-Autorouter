# PAW fixed-placement SES continuation

This unexecuted actor owns only the missing corrected SES import and Native
validation. It reuses actual001's five format observations and task export,
plus actual002's successful obstacles, engine and raw SES. Neither failed run
is modified or relabelled. There is no new export, obstacle worker, engine run,
source migration, format whitelist edit or production admission. All aggregate
`accepted`, `production_admitted` and `format_admitted` flags remain false.

Actual002 stopped after its successful import moved U1 by 48 nm through the
SES placement grid. The current core fixed-placement import omits only the
optional placement clause in a fresh derived SES. Actual003 must preserve the
entire retained original Native emission's nonroute AST exactly, including all
footprint poses and pad geometry. Its imported absolute route records must
match actual002's raw imported routes exactly as a multiset, excluding only
regenerated route UUIDs; all other attributes and multiplicity remain exact.
There is no placement or route tolerance.

The actor retains real worker paths and producer snapshots for both prefixes.
It replays complete source/task/export bindings, process journals, all five
format comparisons, actual002's raw DSN/obstacles/adapter/edge correction, engine
argv/logs and raw SES. Copies in actual003 are explicitly linked to those old
paths and hashes. Old Native/engine steps stay under `retained_phase` and
`retained_engine`; the new root `steps` contains exactly five workers: corrected
import, positive saved refill/final DRC, and invalid-net saved refill/final DRC.

The original engine budget float was not saved before actual002 failed. It is
not reconstructed. `engine_profile_settings('tuned', 96,
strict_class_targets=True)` is used solely as an explicitly labelled canonical
argv reference. The actual 56-second CLI deadline implies a former input in
`[96,97)` under that settings function; it does not identify the actual float.
The diagnostic does not emit a recovered `engine_budget`, invoke full profile
receipt replay on that fiction, or claim a new fair routing comparison. The
actual process and full measured outer costs remain retained.

A fresh complete 14-file original project and exact zero-route task copy feed
the corrected import. The imported routes are transplanted into the unchanged
original shell. Shared candidate validation and retained-stage readers enforce
real saved refill, original rules/companions, fresh full-schematic final Native
checks, PRL protection and the legacy-zone witness. A second candidate changes
all imported MISO routes to GND and must fail fresh Native opens or blocking
checks. The exact negative derivation is replayed. Shared normal-policy readback
also requires and rederives the new `imported.routes-only.ses` and JSON proof
from captured Native/adapter policy sources. Completed inventories, prefix and
tool/code/source freshness, publication/cancellation and final PRL metadata
checks remain required.

The cumulative limit is 120 seconds wall and full CPU. Actual001's complete
outer cost is 6.000073082977906 wall / 5.19436 CPU seconds. Actual002 adds
10.981839040992782 wall / 14.475297 CPU seconds. Before this actor begins, the
charge is therefore 16.981912123970687 wall / 19.669657 CPU seconds; a further
three seconds is reserved for new bootstrap. Positive workers preserve a
12-second negative-control reserve. Stored actor accounting precedes final
delivery: the lead's bounded outer controller must add the entire new launch,
publication and readback to those prior charges and enforce both cumulative
caps. Older qualification/acquisition costs remain separately disclosed.

The lead must review and checkpoint the code and create `input-pins.json`
before execution. Required fields are `status: prospectively_frozen`,
`budget_seconds: 120`, `bootstrap_allowance_seconds: 3`, `actor_sha256`, complete
`code_sha256`, complete file/directory `prefixes`, and honest `prior_costs`.
Code closure is all current `tool_manifest().implementation_sha256` sources,
this actor and its `EXTRA` paths. Prefix closure includes both actual001 and
actual002 run/execution directories and every unchanged prefix in their
retained prospective pins. This implementation task did not generate pins.

After review, checkpoint and pins, launch only through that cumulative bounded
outer controller, with no concurrent Native/JVM worker:

```sh
.venv/bin/python -B experiments/paw_ses_fixed_placement_v1/actor.py \
  --run-native --output .runs/paw-format-ses-native-003
```

The output must be fresh. New retained output is capped at 64 MiB, each worker
directory at 20 MiB, worker group RSS at 4 GiB and each log at 256 KiB. Polling
guards may overshoot. No actor, tests, Native/JVM command, acquisition or new
engine run was executed while authoring these two files.
