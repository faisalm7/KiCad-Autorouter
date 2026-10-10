# KiCadRoutingTools 0.23.0 capability spike

Prepared October 9, 2026. Acquisition and CLI startup have run on this Mac. No
routing, native candidate acceptance, or comparative improvement has yet been
established by this spike. The lead runs competitors sequentially and owns the
independent validator.

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

Only the following engine command has run:

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

Create a new `.runs/krt-sonde-001/` directory. Copy the complete original project
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
validation report, not a replacement for the failed raw result. No such routing
experiment has run yet in this spike.
