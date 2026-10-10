# Original pic custom-pad observation: unexecuted diagnostic

Lead-only prospective observation of the complete original `pic_programmer`
project. This does not strip its 376 existing routes, route anything, save a
board, alter rules, enable production custom-pad support or establish whole
geometry/electrical/library/format qualification. Four newly researched severity
keys remain blocked by production preflight. Original schematic field parity is
not performed by this ordinary CLI DRC command.

The opt-in Python callback in `floor_context.collect` observes the same loaded
board before and after native DSN export. With callback absent, the existing CLI
arguments and output records are unchanged. There is no runtime monkeypatch or
generic configured plugin. The callback records all 247 terminal identities and
63 footprint transforms plus the two custom pads' explicit B.Cu merged-local,
world-transformed and effective polygons, anchor/size/drill/offset/orientation.
Every observed native state must agree across export's temporary footprint flips.
Unknown/opaque native API returns fail with preserved process evidence; declaration
inspection and synthetic tests do not establish that these APIs work at runtime.

The installed legacy `GetCustomShapeAsPolygon(layer)` silently selects F.Cu;
this worker never uses it. Explicit-layer `MergePrimitivesAsPolygon` includes the
anchor. `TransformShapeToPolygon` uses zero clearance,1nm max error,ERROR_INSIDE;
`GetEffectivePolygon` is a separately observed API. The raw DSN retains component,
image, pin, padstack and network correspondence. No equality between its hull
and original copper is asserted, including for back-side/reflected footprints.

After export, a second complete unchanged copy receives nonsaving native refill
and original-rule all-severity DRC. Its original 15 files must remain byte-exact;
only its new run-local `.kicad_prl` is permitted. Source manifest, original board/
project, committed helper/core bytes, tool pins, native wrapper and HEAD are
bound. All observations/log/process evidence freeze before caller parsing, and
final material checks follow subprocess-bearing metadata. Strict publication
preserves invalidated/partial records on cancellation, staleness or cap failure.
The final bounded output scan precedes both saved/in-memory record equality and
the final wall/CPU sample; a late scan cannot leave an expired or changed positive.
Successful export/captured-artifact facts precede correspondence parsing. A failed
mapping remains failed with its first cause and raw DSN/process hashes retained;
any later publication failure is recorded separately, without granting geometry
or routing qualification.
Finite samples are not atomic authentication against hostile concurrent writes.

Shared caps:60s observed wall and parent+waited-child CPU,20MiB complete output,
2GiB polled native process-group RSS,256KiB log/stage; two complete copies are
reserved before launch. CPU is an acceptance cap, not hard OS preemption. The
single project experiment lock and scoped SIGINT/SIGTERM handlers prevent
competing project jobs and restore handlers. Existing native failures and all
original inputs remain intact. No network or external spending.

Planned promotion is `driver.py`, `worker.py`, `mapping.py`, `test_driver.py` and
this README under `experiments/pic_custom_observer_v1`, plus the narrow optional
callback patch to `autorouter/floor_context.py`. Commit/audit/push first. Root
must run the integrated suite, historical receipt readbacks and a fresh default
placement fixture regression before the new native observation. No native job
has been run from this draft.

Pure reproduction (project Python3.11, no native import):

```sh
python3 -B -m unittest discover -s .runs/pic-custom-observer-draft-001 -p test_driver.py -v
```

Prospective ROOT invocation after promotion, review and source checkpoint:

```sh
python3 -B experiments/pic_custom_observer_v1/driver.py --run-native --output .runs/pic-custom-observation-001
```

The first observation may fail. Retain it, explain the actual API/native finding,
and do not substitute guessed polygons, remove JP1 or weaken any constraint.
Actual route-contact/false-hull/foreign-net controls are a separate later gate.
