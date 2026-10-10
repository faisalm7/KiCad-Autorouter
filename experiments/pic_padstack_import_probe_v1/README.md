# Prospective pinned-JAR padstack import probe

This diagnostic has not been compiled or executed with Java. It imports five tiny owned DSN padstack scopes into fresh two-layer `Padstacks` objects through the actual pinned Freerouting 2.5.0 scanner and `Library.readPadstackScope`. It never creates a routing board, invokes routing, saves a KiCad board, runs native CAD, opens a renderer or reads the original PIC project. It does not change any production support or severity gate.

The five cases are a convex polygon control, the exact five-vertex concave control recipe, disjoint same-layer rectangles in both orders, and the same rectangles on separate layers. Inputs use integer micrometres, scale1 and zero offsets. The notch point(-600,0) is outside original concave copper and its anchor but inside its hull. Raw concave area is1,350,000µm²; expected imported hull area is1,725,000µm². Static pinned bytecode predicts convexification and last-shape overwrite. The observed area, corners, bounds, point membership, exact input hashes and importer census are retained. Unexpected observations falsify that prospective expectation; they never grant routing support.

The Java source uses only signatures present in the lead’s saved API/bytecode inspections, whose receipt hashes are in `PROTOCOL.json`. Native API/transform results and the geometry library are not inferred from a test mock. The code remains uncompiled until the lead runs the reviewed, committed helper. One runtime check verifies that scalar transform1 and−600 remain identical; every scope starts by consuming exactly OPEN_BRACKET/PADSTACK and must end at EOF with exactly one named padstack.

## Commands and bounds

Offline pure tests, with no Java/compiler/network/native calls:

```sh
python3 -B .runs/pic-padstack-import-probe-draft-001/test_driver.py
```

Proposed promotion consists of exactly `driver.py`, `PadstackImportProbe.java`, `test_driver.py`, `PROTOCOL.json`, and `README.md` into `experiments/pic_padstack_import_probe_v1`. Source must be reviewed, committed, pushed and read back first. Only the lead may then run:

```sh
python3 -B experiments/pic_padstack_import_probe_v1/driver.py --run-import --output .runs/pic-padstack-import-probe-001
```

The ignored draft refuses actual execution. The controller requires the designated ordinary local rebuild branch with a loose ref; no managed worktree/Git indirection. All five helpers, runner, package initializer and tool lock must equal their exact committed blobs. Their bytes and the local HEAD/ref are copied or recorded and checked again after metadata processes. Pinned Java/Javac/JAR/sandbox/Python files are checked; the JAR is read in bounded chunks, never copied into evidence. The same source/tool material is checked after every stage and final output scan. This is finite consistency sampling, not atomic protection against a hostile concurrent writer.

One existing foreground experiment lock prevents competing jobs. Argument parsing, lock acquisition, snapshotting, compile, import and final checks share60 seconds of observed wall and total parent plus waited-child CPU. Each worker is capped at30 wall seconds or the smaller remaining shared allowance. CPU caps are checked after stages and publication; they are not hard CPU preemption. The stored sample precedes final publication checks, which are still charged for acceptance. Java and compiler heap limits are256MiB; the existing runner polls the owned group at1GiB and the entire output directory at10MiB, caps each log at256KiB, and kills only the owned group. Polling may overshoot. All child environment variables are explicitly supplied; HOME/user.home and TMPDIR/java.io.tmpdir are isolated in the fresh output. Both compiler and importer run under the existing macOS network-denial sandbox; annotation processors are disabled.

Raw logs/process receipts/classes/observation output are frozen before semantic parsing. Every case remains in the Java observation file even if an individual import fails. A failed or cancelled worker cannot yield a complete controller result. Final publication scans before rechecking material and canonical/in-memory equality; stale/cancelled positive summaries and partial writes are archived. A failed corrective write leaves no canonical positive summary. SIGINT/SIGTERM handlers are scoped and restored. No background job is created.

An expected negative representation result is useful evidence about this importer, not a native route failure or a custom-pad qualification. Arbitrary rotations, chiral reflections, holes, layer aliases, multi-pin decomposition and changes to the engine require separate proposals and actual native controls. Both fixed source custom polygons are symmetric in Y; this probe makes no general reflection claim.

## Geometry attribution

The two polygon coordinate recipes derive from the official KiCad `pic_programmer` demo at commit `69cafb907ebc09e7722a2a464b1d466fc2e3608d`, released under CC BY-SA 4.0. The original [license notice](../../evidence/pic-custom-observation-002/_licenses/LICENSE.README) and [license text](../../evidence/pic-custom-observation-002/_licenses/LICENSE.CC-BY-SA-4.0) remain in this repository. This diagnostic converts the local coordinates to integer micrometres and places them in isolated owned DSN scopes; the disjoint-rectangle cases and probe software are project-authored. Original board and project files are not changed or imported.
