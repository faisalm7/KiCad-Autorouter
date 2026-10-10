# KiCadRoutingTools 0.23.0 capability spike

Prepared October 9, 2026. Acquisition, CLI startup, two bounded native routing
experiments, and independent KiCad 10.0.0 validation have run on this Mac. Both
raw engine outputs and both separately recorded routes-only adaptations were
rejected. This is one exposed development family, not a generalized comparison.
The lead coordinates competitors sequentially and owns the independent validator.

## Pinned acquisition

`python3 scripts/setup_krt.py` completed using native arm64 CPython 3.11.9.
`python3 scripts/setup_krt.py --check` subsequently verified the existing assets,
extracted files and installed package metadata without downloading anything.

The [annotated v0.23.0 tag](https://api.github.com/repos/drandyhaas/KiCadRoutingTools/git/ref/tags/v0.23.0)
is tag object `ac0fc0265bafb0cc3bb31dc8228875b07c1bf349`; its
[target commit](https://api.github.com/repos/drandyhaas/KiCadRoutingTools/git/tags/ac0fc0265bafb0cc3bb31dc8228875b07c1bf349)
is `9399bfb29e072bfe60b10d9cdae20c274fc2a17a`. This is distinct from the moving
main revision recorded in the earlier landscape research.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| [KRT package](https://github.com/drandyhaas/KiCadRoutingTools/releases/download/v0.23.0/KiCadRoutingTools-0.23.0.zip) | 14,844,957 | `d325f617492bd69943e50dd9f5a9119d328c854e33ab54cac4c96e90d05c52a1` |
| [macOS arm64 extension](https://github.com/drandyhaas/KiCadRoutingTools/releases/download/v0.23.0/grid_router-macos-arm64.so) | 1,039,632 | `ed667cfbde051e3824c25a21635b322b5adec10d5b1475ad80f1c3e4d066d8d7` |

The package has 463 ZIP entries totalling 33,034,536 uncompressed bytes. The setup
script verifies size and digest, rejects path traversal, symlinks, special files,
and oversized archives, and extracts the `plugins/` subtree into
`.tools/KiCadRoutingTools-0.23.0`. It omits platform-specific binaries from that
extraction and installs the separately verified arm64 asset as
`rust_router/grid_router.so`. Existing differing files are rejected.

The upstream build script can fall back to Cargo and its plugin initializer can
register with KiCad. Neither was run. The project setup creates only
`.tools/krt-0.23.0-venv`, using exact binary wheels with their pinned sizes,
URLs and SHA-256 values in `scripts/setup_krt.py`:

| Package | Version | Wheel metadata source |
|---|---|---|
| NumPy | 1.26.4 | [PyPI version JSON](https://pypi.org/pypi/numpy/1.26.4/json) |
| SciPy | 1.13.1 | [PyPI version JSON](https://pypi.org/pypi/scipy/1.13.1/json) |
| Shapely | 2.0.6 | [PyPI version JSON](https://pypi.org/pypi/shapely/2.0.6/json) |

Wheel installation used `--no-index --no-deps --no-cache-dir` under a per-process
network-denying macOS sandbox. No global packages, KiCad bundle libraries, plugin
registrations, user preferences, or repository settings were changed. Downloads
and their setup receipts remain in ignored `.tools/krt-0.23.0-assets/` and are
reproducible acquisition material, not source/evidence backup claims.

## License record

The pinned [KRT LICENSE](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/LICENSE)
is MIT, copyright 2026 drandyhaas. Its exact text is retained as
`.tools/KiCadRoutingTools-0.23.0/LICENSE`. Other distributed notices, including
vendored three.js, remain with the extracted source. Dependency wheel notices are
retained in each package's `.dist-info` directory. Shapely also includes
`LICENSE_GEOS`; NumPy and SciPy notices include bundled-library terms. These local
dependencies are not committed or bundled into a published package. A future
distributable requires auditing the complete corresponding notice set. This
does not grant redistribution rights to boards merely because KRT can read them.

## Actual startup experiment

The initial startup check was:

```sh
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  .tools/krt-0.23.0-venv/bin/python \
  .tools/KiCadRoutingTools-0.23.0/py_router/route.py --help
```

The launcher used absolute paths, one thread for the numerical libraries,
`PYTHONNOUSERSITE=1`, and `PYTHONDONTWRITEBYTECODE=1`. The bounded runner reported
exit 0, 3.971324 seconds wall time, 0.943972 CPU seconds, 120,848,384 bytes kernel
peak RSS, complete process cleanup, and an untruncated 35,161-byte log. This is a
dependency/CLI startup result, not routing performance.

Local receipts:

* `.tools/krt-0.23.0-assets/help.log`
* `.tools/krt-0.23.0-assets/help-process.json`
* `.tools/krt-0.23.0-assets/setup-receipt-*.json`

The [parser source](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/py_router/kicad_parser.py)
contains numeric-net and KiCad 10 name-net handling (`board_uses_name_nets`,
`parse_nets`, and pad net parsing). Thus native KiCad 10 input is implemented in
the inspected source. This does not prove fidelity for our board; no downgrade,
rule relaxation, geometry movement, or omitted object is acceptable.

## Constrained routing invocation for the lead

Create a new run directory. Copy the complete original project
snapshot, then remove only the task-authorized unlocked routing from that copy
using the existing structural preparation code. Keep the original board basename
and its sibling `.kicad_pro`, `.kicad_dru`, libraries and other project files.
Use native board input, not `task.dsn`. Do not route the already-routed stock
candidate as though it were an equivalent unrouted input.

Pass this argument array to the existing bounded worker, substituting absolute
paths. `ROOT`, `INPUT`, `OUTPUT` and `STATS` below are Python string variables;
there is no shell interpolation:

```python
argv = [
    "/usr/bin/sandbox-exec", "-p",
    "(version 1)(allow default)(deny network*)",
    ROOT + "/.tools/krt-0.23.0-venv/bin/python",
    ROOT + "/.tools/KiCadRoutingTools-0.23.0/py_router/route.py",
    INPUT, "--output", OUTPUT,
    "--nets", "*", "--layers", "F.Cu", "B.Cu",
    "--no-fix-drc-settings", "--escalation", "off",
    "--fab-tier", "standard", "--strict-sizes",
    "--keep-input-copper", "--no-stub-layer-swap",
    "--max-iterations", "100000", "--max-ripup", "3",
    "--json-out", STATS,
]
```

Use the run's directory as working directory, a 120-second external deadline,
bounded logging, and one worker. Supply these process-local environment values:

* `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`,
  `NUMEXPR_NUM_THREADS=1`, `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`.
* `KICAD_RIP_PREEXISTING=0`, `KICAD_FINALIZE_RIP=0`.
* `KICAD_CLI` and `KICAD_PYTHON` set to the project's verified KiCad paths.
* `KICAD_CONFIG_HOME` and `TMPDIR` set to fresh directories inside this run.
* Remove inherited `PYTHONPATH`, `PYTHONHOME`, `REDO_MANIFEST`, and unrelated
  `KICAD_*` tuning overrides before adding the intended settings.

The [actual CLI source](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/py_router/route.py)
and fresh help explain why the guard flags matter: default escalation permits
smaller geometry, default DRC writeback adjusts project floors, and cleanup can
rewrite pre-existing copper. `--escalation off` prevents size descent;
`--no-fix-drc-settings` disables DRC floor writeback; `--strict-sizes` fails if
the run nevertheless delivers below its requests; `--keep-input-copper` limits
cleanup. Do not enable clearance ceilings, relaxed severities, pad swaps,
placement changes, or new layers. These flags do not replace validation.

The standard fabrication floor may conservatively restrict some boards. For the
sonde development input, the original Default values inspected were 0.635 mm
track width, 0.254 mm clearance, 1.651 mm via diameter and 0.635 mm drill. Preserve
their source semantics; do not reduce them merely to improve routing completion.
The internal A* iteration cap is an exploratory configuration, not proof this is
the best possible KRT configuration. Complete conversion/validation time must be
included before any equal-budget comparison.

Retain the raw KRT output and check immutable geometry and original-rule hashes
before independent native refill/DRC. If raw output moves text or changes other
immutable objects, record that failure. A subsequent route-only transfer onto a
pristine task is a separately named adapter experiment, with its own costs and
validation report, not a replacement for the failed raw result.

## Actual routing and independent validation

`scripts/experiment_krt.py` implements the constrained invocation above. It uses
the immutable `.runs/sonde-stock-002/snapshot/sonde xilinx.kicad_pcb` project and
checks every source file against that earlier run's stored source hashes. It
removes only unlocked route objects and derived zone fill on a task copy, keeps
all original rules, and retains raw engine output separately. The second run
changes only whitespace in the engine input after asserting equality of every
parsed S-expression atom. Both runs retain source, code and environment hashes,
full process receipts, stdout, native JSON DRC and candidate hashes.

Completed commands, each with its own 120-second whole-pipeline deadline:

```sh
python3 scripts/experiment_krt.py --output .runs/krt-spike-001
python3 scripts/experiment_krt.py --pretty-input --output .runs/krt-spike-002
```

These paths are existing immutable receipts; rerun with a new direct child of
`.runs`. The script refuses an existing output directory. The engine ran inside
the network-denying sandbox, with no other benchmark competitor running. Neither
attempt needed the script's explicitly labelled extra diagnostic validation
budget. End-to-end time includes both raw validation and the separate routes-only
adaptation, so neither is presented as an isolated engine-speed measurement.

| Outcome | Spike 001: one-line task | Spike 002: conventional newlines |
|---|---:|---:|
| Engine exit | 0 | 0 |
| Zones observed by KRT parser | 0 | 1 |
| Raw immutable equality | Failed: eight copper texts moved | Failed: eight copper texts moved |
| Raw native unconnected / blocking errors | 0 / 4 | 0 / 4 |
| Routes-only native unconnected / blocking errors | 0 / 8 | 0 / 12 |
| Whole-pipeline wall seconds | 7.760829 | 10.918892 |
| Whole-pipeline CPU seconds | 5.338643 | 8.265590 |
| Routes-only vias / track length mm | 8 / 694.950028 | 18 / 556.197663 |
| Source, snapshot and task input unchanged | Yes | Yes |
| Accepted candidate | None | None |

The route lengths and via counts describe rejected candidates, not valid quality
gains. All four native reports have one `lib_footprint_mismatch` warning; whole
project cleanliness and physical/electrical validation are not established.

### Formatting failure isolated by a read-only parser probe

The pinned [zone parser](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/py_router/kicad_parser.py#L5546)
uses a regular expression requiring a newline before a top-level `(zone`.
Our original one-line S-expression serializer preserves zone semantics for KiCad
but exposes no zone to this parser. The second run first parsed both equivalent
task serializations: zone counts were 0 versus 1, while both had 25 footprints,
108 pads and 43 net entries. `parser-probe.json` stores these counts, and
`parser-probe.py` plus its hash preserve the probe. The second routing run used
the pretty-printed input. This resolves the identified zone omission but did not
produce a valid route.

### Copper text is not preserved or avoided

The pinned [output writer](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/py_router/output_writer.py#L84)
unconditionally calls `move_copper_text_to_silkscreen`,
`move_copper_graphics_to_silkscreen`, and `strip_zero_length_edge_cuts`. The
inspected CLI and writer have no flag that disables the text/graphics move.
The eight changed `gr_text` objects are the only immutable-tree differences
found in these two raw outputs. The native raw errors are four `silk_overlap`
violations caused by the moved text. Other original project-file hashes match.
The raw candidates therefore fail both immutable preservation and native DRC.

Copying only KRT's route objects onto the pristine task restores the source text
and other immutable objects, but exposes actual copper collisions: spike 001 has
four `shorting_items` and four `clearance` errors; spike 002 has seven
`shorting_items` and five `clearance` errors. The violation items pair tracks with
the preserved source copper text. These are not fixed by moving or deleting that
text, shrinking rules, changing severities, or calling the raw output complete.

KRT is a viable native routing implementation to investigate further, but these
settings do not satisfy this board's unchanged geometry. A next KRT experiment
would need verified copper-text obstacles and preserved writer semantics, then
new native controls. It would be an additional adapter/engine change with all
costs counted, not evidence for a novel routing mechanism. No upstream changes,
dependency patches, global preferences, or original boards were modified here.

### Receipt bindings

| Run | Result SHA-256 | Raw candidate SHA-256 | Routes-only candidate SHA-256 |
|---|---|---|---|
| `.runs/krt-spike-001` | `227279551eda93a664089829eeac8638286dbfc74960cad0fcf80385e5d2eeca` | `6524a34cfff00ecbfadd95a9d1bb7d5b81c5818973f8067239ae511dfbec6970` | `dc5e9d86bdb13bb5d046904f43c3912e6892704aba854ff8b5b1e43fdfb4da08` |
| `.runs/krt-spike-002` | `4f593741a9428e9f028b3fb5423c5b5aa1ed1c6b8069b83615e6ea83306053ae` | `e7c44c68b98030c3cab35cbfed10c3122387c4340e5ea08a9a25330622181282` | `1891152fefc9001aabaa954be3dbb96f9b2e59898aaa020b36c5434bb33a1924` |

Each run's `diagnosis.json` records immutable differences and native violation
types. Exact reports are `raw-validation/native-diagnostic.json` and
`route-transfer-validation/final-drc.json`. Artifacts reside only on this Mac
until included in a verified project backup; this document is not itself a
backup of those artifacts. The experiment is developmental and supplies no
held-out, family-generalized, equal-budget superiority claim.
