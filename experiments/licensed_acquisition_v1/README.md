# Acquisition004 preparation — no payload fetched

This is a proposed bounded development acquisition, awaiting lead review, source checkpoint, and explicit invocation. It does not change the acquired board population or claim complete dependency closure, native eligibility, independent families, or redistribution clearance.

The fixed order is Ideal Diode, HSTX PTH, then OLIMEX iCE40-DIO: 33 original files, 5,016,162 bytes. The first two include every file in their native `Hardware` directory plus root license/README. The OLIMEX selection is the entire 22-file repository at its pinned revision. Omitted website/vendor/automation files and reference closure obligations are recorded in `protocol.json`. KiCad Video is not in this invocation. Reserved prospective holdouts are untouched.

## Explicit proposed capacity change

The existing `data/fetch.py` 32MiB limit covers only its six-project manifest and is unchanged. This separate acquisition proposes a 64MiB (67,108,864-byte) aggregate limit over **all of `.data`**, including already acquired subsets outside that manifest. This is a project-level acquisition guard, not an OS setting or resource-limit bypass. It requires reviewed, committed protocol/source bytes before network execution.

The complete baseline is 312 files / 32,392,408 bytes:

| Subtree | Files | Bytes |
|---|---:|---:|
| boards | 144 | 13,654,726 |
| coldfire | 52 | 4,384,337 |
| expansion | 35 | 6,495,334 |
| expansion003 | 81 | 7,858,011 |

If the fixed batch succeeds, the all-data total will be 345 files / 37,408,570 bytes. No old input is deleted, overwritten, or evicted. `existing-data-inventory.json` records every old file's SHA256/size and every directory. The per-project and per-invocation response-body limits remain 10MiB. All three projects together fit that unchanged invocation limit. HTTP protocol headers are not counted as payload bytes.

## Offline preparation and later commands

Preparation in the ignored draft:

```sh
python3 -B .runs/licensed-acquisition-004-fix-001/fetch.py
python3 -B .runs/licensed-acquisition-004-fix-001/test_fetch.py
```

The default command performs plan and real baseline checks without networking. `--fetch` refuses this ignored path. Intended eventual promotion consists of exactly `fetch.py`, `test_fetch.py`, `protocol.json`, `existing-data-inventory.json`, `README.md`, and `STATIC_AUDIT.md` under `experiments/licensed_acquisition_v1`. The lead must audit and checkpoint those exact files before the following **future, not executed** command:

```sh
python3 -B experiments/licensed_acquisition_v1/fetch.py --fetch --output .runs/licensed-acquisition-004-run-001
```

The runtime independently compares all six files to Git HEAD before any network request and throughout the batch. The output and `.data/expansion004` must both be fresh. Any previous failure remains intact, and this helper refuses automatic resume/overwrite. A failed partial acquisition requires a separately reviewed continuation decision; it does not silently retry or reset its baseline.

## Runtime boundaries and evidence

Only the exact 33 HTTPS raw-file URLs, commits, nonexecutable Git blob modes, paths, expected sizes and Git blob SHA1s in the frozen protocol are admitted; existing SHA256 pins are also checked. Every acquired file receives a SHA256. No archive, hook, dataset script, Git checkout, shell command, model program, native tool or engine executes. Git metadata read commands check this project's helper, not downloaded repositories. Redirects, transformed encoding, LFS pointers, unexpected HTTP status, altered byte counts/hashes and path/symlink/case ambiguity reject.

One foreground acquisition lock, a 300-second invocation timer, and at most 30 seconds for any request cover preparation through final verification. The 33 requests have no automatic retries. The data walker caps files (2,048), entries (4,096), each read (10MiB), and all data (64MiB); it rejects unknown baseline members before reading them. Request response bodies, HTTP metadata, consumed byte counts, errors and measured request times are retained under the fresh output, subject to a 24MiB output ceiling. Response bytes are bound exactly to the verified source file bytes before capture. Failure bodies can be bounded/truncated, so retained bytes are not a claim of having received a whole unsuccessful server response.

Each stage and final publication rechecks all old sources, completed new sources, completed response bodies and exact committed helper bytes. Source checks follow Git subprocesses. Exact helper bytes and a bounded direct local Git HEAD/ref witness are sampled again after metadata subprocesses and response/source scans, without another Git subprocess. The final output scan precedes that full stability check, then canonical receipt equality and the final wall-cap check. This intentionally supports only an ordinary local `.git` directory, including loose or packed local branch refs; gitfile/worktree indirection is rejected. These are finite samples, not atomic protection against an adversarial concurrent writer. SIGINT/SIGTERM invalidate a positive canonical receipt and restore handlers. Failed, interrupted and invalidated evidence remains; no positive label implies closure or native qualification. Stored time samples precede final publication checks; deadline enforcement includes them. These are application/process controls on this foreground helper, not an OS-wide disk quota or guarantee against abrupt host failure.

The source-only development exposure decision and metadata rights evidence are pinned by `recommendations_sha256` in the protocol. Per-file notices and external dependencies still need the audit in `STATIC_AUDIT.md`. Root grants do not automatically clear embedded third-party models. No acquired payload may be published based only on this fetch receipt.
