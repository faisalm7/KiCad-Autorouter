# Native development data and provenance

Checked October 9, 2026, America/Los_Angeles. All sources inspected for this work are development-exposed. No final evaluation set or training corpus exists. Historical board names are leads; the supplied historical status has no source revision or file hashes, so exact byte identity with the old experiment remains unknown.

## Acquired smoke project

The first acquired source is KiCad's **sonde xilinx** demo, schematic title **PARALLEL CABLE III**. Its canonical upstream is [KiCad's source repository](https://gitlab.com/kicad/code/kicad). Downloads use the KiCad-maintained [GitHub source mirror](https://github.com/KiCad/kicad-source-mirror). The queried GitHub name `KiCad/kicad` redirects to that mirror.

| Field | Verified value |
| --- | --- |
| Upstream tag | `10.0.7` |
| Annotated tag object | `93a8a4827b0b2a01a6d1599733e6964e6ea94cf9` |
| Dereferenced source commit | `69cafb907ebc09e7722a2a464b1d466fc2e3608d` |
| Demo subtree object | `e50b536c7322568d4e148a81a76666a93ed005da` |
| Exact source directory | `demos/sonde xilinx/` |
| Board file | `sonde xilinx.kicad_pcb` |
| Board Git blob | `26781327d86bc390ce22dbad8f1861f6faae2d4c` |
| Family | `kicad-sonde-xilinx`, including every revision and derived task |
| Split | Development only |
| Source project population | All 14 regular files in the directory, 668,217 bytes |
| Acquired population | 14 project files plus two upstream license documents; 16 files, 685,767 bytes |
| Transformations in acquisition | None; verified original bytes |

The source files are board, project settings, schematic, project symbol library, symbol/footprint library tables, and eight project footprint files. There is no custom `.kicad_dru` in this source directory; the original `.kicad_pro` is retained. Both library tables point to project-local resources. The original board/footprints also refer to optional external 3D models through `KICAD6_3DMODEL_DIR` and `KICAD8_3DMODEL_DIR`. Those model files are not in this demo directory and were not acquired; this is a complete upstream native project directory, not a hermetic 3D-library bundle. Native DRC, schematic parity, source cleanliness, and routing eligibility are separate checks owned by the pipeline, not established by download verification.

The source files stay under ignored `.data/boards/kicad-sonde-xilinx/`. `data/sources.json` records the exact path, bytes, SHA-256, Git blob SHA-1, file mode, and license scope for every downloaded file. The pinned commit, not a mutable branch/tag name, appears in each constructed URL. Files are downloaded individually; no archive, installer, hook, or dataset script is executed. The manifest and fetch implementation are project-owned tracked artifacts; fetched boards are not added to Git.

From the checkout, these commands are implemented and have actually run:

```sh
python3 data/fetch.py
python3 data/fetch.py --verify
```

The initial run reported all 16 sonde files verified. The expanded manifest now fetches/verifies all five projects described below, while retaining the original top-level sonde `board` field for compatibility. `--verify` makes no network request. Existing mismatched files cause an error instead of replacement. Fetches reject executable/symlink source modes, unreviewed paths/file types, ambiguous or escaping paths, symlink destination components, size/hash mismatches, and a manifest above 10 MiB. Source creation uses a temporary file and an atomic no-overwrite hard link. These protections are not a hostile-process filesystem sandbox. An initial path check accepted a doubled slash; a targeted safety exercise found this, the check was fixed, and rerun exercises rejected traversal, doubled separators, backslashes, modified content, and symlink destinations.

## Rights and notices

At the pinned commit, [LICENSE.README](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/LICENSE.README) explicitly assigns `demos/*` to **CC BY-SA 4.0**. The [complete upstream license text](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/LICENSE.CC-BY-SA-4.0) is acquired alongside the source notice. The sonde directory has no overriding license file. This board-specific scope is the basis for acquisition; the main KiCad program's GPL license was not substituted for the board license.

Preserve the original notices, identify KiCad's demo and exact upstream source, link CC BY-SA 4.0, and identify every routing-task/output modification when sharing a derived board. Distributed board adaptations must retain a compatible ShareAlike license. The [Creative Commons license summary](https://creativecommons.org/licenses/by-sa/4.0/) explains attribution and modification notices; the acquired legal text governs. This data review does not establish rights for trained weights, and no model training is proposed from this smoke source. Attribution must not imply KiCad endorsement.

Suggested output notice: “Derived from the KiCad project demo ‘sonde xilinx’ (PARALLEL CABLE III), source commit 69cafb907ebc09e7722a2a464b1d466fc2e3608d, licensed CC BY-SA 4.0. Original project notices are retained. Modifications: [exact preparation and routing transformations from the run manifest].” Supply clickable upstream/license links and the actual transformation record when distributing an output.

## Acquired five-project development population

The second historical name resolves to [`demos/pic_programmer/`](https://github.com/KiCad/kicad-source-mirror/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/pic_programmer) in the same commit. Its board is `pic_programmer.kicad_pcb`, Git blob `b4d4adb82a1345cf5a6e97f78162e723292186e5`. The directory contains 13 files totaling 1,349,048 bytes: native PCB/project/schematic, a second schematic sheet, project symbols, library tables and local library files. The pinned demo license scope applies; the tree contains no local overriding notice. These are freshly identified sources, not proof that the historical run used this revision. It remains development-only whether supported or rejected. No new native validation of pic-programmer is claimed here.

The following complete project directories were acquired from the freshly read, non-truncated pinned demo tree. Every original was checked against its Git blob and SHA-256, followed by a full offline verification. All five directories match their expected file inventories exactly; no extra or missing files were found. This verifies acquisition, not native routing eligibility, independence, or accepted benchmark tasks. Native preflight, ancestry/structural deduplication, and reference-route separation must precede scoring.

| Acquired project directory | Original files | Original bytes | Intended audit role |
| --- | ---: | ---: | --- |
| `sonde xilinx` | 14 | 668,217 | Historical adapter regression |
| `pic_programmer` | 13 | 1,349,048 | Netclass/custom-pad capability counterexample |
| `complex_hierarchy` | 17 | 1,148,108 | Complete hierarchical project ingestion |
| `interf_u` | 23 | 1,473,421 | Another native project and constraint audit |
| `multichannel` | 15 | 4,543,845 | Routed/unrouted sibling leakage and task preparation |

The five directories total **82 original files / 9,182,639 bytes**. Two unchanged license documents are included under `_licenses/` in each project, giving **92 acquired files / 9,270,389 bytes**, below the 10 MiB ceiling. The expansion downloaded 76 new files and verified the 16 existing sonde files. `python3 data/fetch.py --verify` then independently checked all 92 local files without network access. Every acquired file is a regular non-executable source data/notice file; no script or archive was run.

The root demo license statement applies to these five directories, and their inventories contain no competing local license document. File contents were also searched for copyright/license/permission statements. Ten multichannel native files retain embedded CC-BY-SA-4.0 library notices with a schematic ShareAlike exception; `data/sources.json` identifies those notices without widening that exception to the whole PCB project. The original notice bytes remain in the acquired files.

`interf_u` contains Tux artwork as a BMP and native conversions. Retain the supplemental credit **Larry Ewing and The GIMP** with these files and related outputs. The official [Linux kernel FAQ](https://www.kernel.org/faq.html) identifies the author/tool and permits use, including commercially, with author credit. This acknowledgement supplements KiCad's scoped demo license record; it does not imply ownership by this project. The original author's historical web URL returned 404 during this check, so the maintained official FAQ is the retrievable attribution evidence.

There are six PCB files in five project directories. Routed and unrouted multichannel files remain one provisional family, never two independent observations. Only `multichannel_mixer.kicad_pro` exists upstream; the `multichannel_mixer-unrouted.kicad_pcb` sibling lacks a same-basename project file. The manifest names the intended original project file, but native validation of that sibling is **pending explicit task/rules mapping**. Do not validate it using default project settings. No mapping or source-file rename was performed during acquisition.

`evidence/coverage.json` contains all five considered projects and all six exact board paths/hashes, acquisition status, static preflight outcomes, pending native checks, scope decisions, and the unrouted-sibling rules gate. Prior sonde run evidence remains separate and is not silently generalized to the other projects. The static capability audit below keeps every rejected input in the denominator.

## Read-only static capability audit

All six original PCB files were passed to the actual `autorouter.pipeline.preflight` function; no native executable, routing engine, conversion, or source write was invoked. The 92 acquired file hashes matched the pinned manifest before and after both audit passes, and a subsequent `python3 data/fetch.py --verify` passed. The current measured pipeline file SHA-256 is `e7fb090df5437c6317c0646f04dec2dff5def7b786b27ff3a6284fc02ee1b469`; parser SHA-256 is `c65b209def530fab9ca1481c67ed2d8217a294b73df8e5e41458e269f917b6dd`.

The current gate admits **one of six native board files** for a subsequent native audit and rejects five. This is implementation coverage, not a routing completion rate or a claim of native legality. All six declare two canonical copper layers. Passing this static gate does not establish low-voltage electrical scope, source cleanliness, schematic parity, or physical correctness.

| Source PCB | Footprints | Pads | Custom pads | Netclass classes / patterns | Current static outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| `sonde xilinx.kicad_pcb` | 25 | 108 | 0 | 1 / 0 | Eligible for native audit |
| `pic_programmer.kicad_pcb` | 63 | 247 | 2 | 2 / 2 | Custom pads; netclass binding; four unqualified severity keys |
| `complex_hierarchy.kicad_pcb` | 68 | 165 | 0 | 2 / 5 | Netclass binding; unqualified `zone_has_empty_net` severity key |
| `interf_u.kicad_pcb` | 25 | 379 | 0 | 2 / 2 | Netclass binding |
| `multichannel_mixer-unrouted.kicad_pcb` | 114 | 327 | 0 | 1 / 0* | Missing same-basename project; unqualified format `20241030` |
| `multichannel_mixer.kicad_pcb` | 114 | 327 | 0 | 1 / 0 | Required `padstack` check is nonblocking in original rules |

*The unrouted sibling's descriptive netclass counts were read from the separately named original `multichannel_mixer.kicad_pro`; those settings were not attached to the source PCB or used to bypass its missing-project rejection. Pic-programmer's four additional unqualified severity keys are `footprint_symbol_field_mismatch`, `missing_tuning_profile`, `text_on_edge_cuts`, and `track_on_post_machined_layer`. Complete reason lists, features, and hashes remain in the coverage ledger.

The first audit exposed a capability-gate defect: counting `signal` layer types excluded `complex_hierarchy`'s front copper marked `power`, and counted nine `User.*` layers marked `signal` in the older multichannel sibling. The lead corrected the gate to count canonical copper-layer names and added a regression test. The repeated audit above removes those two spurious layer-count reasons. Independent rejection reasons remain, so the eligible set stayed at one board. `static_preflight_history` preserves the earlier source-code hash and exact results; no source-layer definition was changed.

Limited structural screening confirms that the two multichannel files have identical net-to-terminal partitions when net names are ignored. They have **19 different footprint poses**, after normalizing numeric spelling, implicit zero rotations, rotations modulo 360, and board side. They therefore remain one family but are not equivalent fixed-placement routing tasks. No other exact connectivity fingerprint matched across this small population. The screen retains reference designators and does not canonicalize whole-board translations/rotations or infer subcircuit ancestry; differing fingerprints do not establish independent families. Full ancestry and structural deduplication remain pending.

To repeat the static capability result with the currently checked-out implementation:

```sh
python3 data/fetch.py --verify
python3 - <<'PY'
import json
from pathlib import Path
from autorouter.pipeline import preflight, Rejected
manifest = json.loads(Path('data/sources.json').read_text())
for project in manifest['projects']:
    for item in project['boards']:
        board = Path('.data') / item['board']
        try:
            preflight(board)
            outcome = 'eligible for native audit'
        except Rejected as error:
            outcome = str(error)
        print(board, outcome)
PY
python3 data/fetch.py --verify
```

Other demos are not default ordinary-board inputs. For example, `microwave` and `ecc83` require an RF/high-voltage scope assessment; large processor boards may exceed the current layer/constraint scope. Some newer directories contain their own licenses (`cm5_minima`, `openair-max`, `royalblue54L_feather`, `stickhub`, `tiny_tapeout`, and `jetson-agx-thor-baseboard`). Their artifact-specific notices must be reconciled before use rather than assuming the root demo statement settles every file. Large full directories such as `vme-wren` (126,031,593 bytes) and `jetson-agx-thor-baseboard` (96,843,810 bytes) are intentionally outside this initial acquisition.

Five exposed source projects do not satisfy the 30–50-family development requirement. These are provisional family identifiers, not five independently established board families. The next corpus stage should audit original public hardware repositories individually, preserving native project/rule/library files and hardware-specific permissions. No unreviewed repository is declared cleared here, and no final holdout should be assembled from these exposed families.

## Evidence and backup limits

Provenance queries used the official GitHub tag, tag-object, content, and recursive-tree APIs, plus the pinned raw license files. The recursive demo tree reported `truncated: false`. The initial fetch and offline verification ran locally; source hashes are reproducible in `data/sources.json`. Inspection of installed `/Applications/KiCad` found native templates but no sonde/pic demo boards in that searched application tree, so installed templates were not silently substituted.

Downloaded originals currently exist on this Mac and are publicly refetchable. A manifest is not a backup of native routing outputs or unique evidence. The lead's checkpoint/restore workflow must preserve those separately. No old cloud environment, private board, external contact, or paid service was used for this data work.
