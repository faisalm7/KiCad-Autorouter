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

Both reported all 16 files verified. `--verify` makes no network request. Existing mismatched files cause an error instead of replacement. Fetches reject executable/symlink source modes, unreviewed paths, ambiguous or escaping paths, symlink destination components, size/hash mismatches, and a manifest above 10 MiB. Source creation uses a temporary file and an atomic no-overwrite hard link. These protections are not a hostile-process filesystem sandbox. An initial path check accepted a doubled slash; a targeted safety exercise found this, the check was fixed, and rerun exercises rejected traversal, doubled separators, backslashes, modified content, and symlink destinations.

## Rights and notices

At the pinned commit, [LICENSE.README](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/LICENSE.README) explicitly assigns `demos/*` to **CC BY-SA 4.0**. The [complete upstream license text](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/LICENSE.CC-BY-SA-4.0) is acquired alongside the source notice. The sonde directory has no overriding license file. This board-specific scope is the basis for acquisition; the main KiCad program's GPL license was not substituted for the board license.

Preserve the original notices, identify KiCad's demo and exact upstream source, link CC BY-SA 4.0, and identify every routing-task/output modification when sharing a derived board. Distributed board adaptations must retain a compatible ShareAlike license. The [Creative Commons license summary](https://creativecommons.org/licenses/by-sa/4.0/) explains attribution and modification notices; the acquired legal text governs. This data review does not establish rights for trained weights, and no model training is proposed from this smoke source. Attribution must not imply KiCad endorsement.

Suggested output notice: “Derived from the KiCad project demo ‘sonde xilinx’ (PARALLEL CABLE III), source commit 69cafb907ebc09e7722a2a464b1d466fc2e3608d, licensed CC BY-SA 4.0. Original project notices are retained. Modifications: [exact preparation and routing transformations from the run manifest].” Supply clickable upstream/license links and the actual transformation record when distributing an output.

## Pic-programmer and a bounded expansion

The second historical name resolves to [`demos/pic_programmer/`](https://github.com/KiCad/kicad-source-mirror/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/pic_programmer) in the same commit. Its board is `pic_programmer.kicad_pcb`, Git blob `b4d4adb82a1345cf5a6e97f78162e723292186e5`. The directory contains 13 files totaling 1,349,048 bytes: native PCB/project/schematic, a second schematic sheet, project symbols, library tables and local library files. The pinned demo license scope applies; the tree contains no local overriding notice. These are freshly identified sources, not proof that the historical run used this revision. It remains development-only whether supported or rejected. No new native validation of pic-programmer is claimed here.

The following modest acquisition order is proposed from the freshly read, non-truncated pinned demo tree. Only sonde is acquired by the current manifest; the other rows are not implemented downloads or accepted benchmark tasks. Eligibility and reference-route leakage must be checked before scoring.

| Candidate project directory | Regular files | Source bytes | Intended audit role |
| --- | ---: | ---: | --- |
| `sonde xilinx` | 14 | 668,217 | Historical adapter regression |
| `pic_programmer` | 13 | 1,349,048 | Netclass/custom-pad capability counterexample |
| `complex_hierarchy` | 17 | 1,148,108 | Complete hierarchical project ingestion |
| `interf_u` | 23 | 1,473,421 | Another native project and constraint audit |
| `multichannel` | 15 | 4,543,845 | Routed/unrouted sibling leakage and task preparation |

These five directories total **9,182,639 bytes** before shared license documents, within a 10 MiB initial download allowance. Each requires a reviewed inventory, all applicable local notices, hash-pinned download, immutable originals, and native preflight. Routed and unrouted multichannel files are one family, never separate independent observations. Merely residing in different demo directories does not prove family independence; structural deduplication remains required. Keep failures and unsupported cases in the considered-population manifest.

Other demos are not default ordinary-board inputs. For example, `microwave` and `ecc83` require an RF/high-voltage scope assessment; large processor boards may exceed the current layer/constraint scope. Some newer directories contain their own licenses (`cm5_minima`, `openair-max`, `royalblue54L_feather`, `stickhub`, `tiny_tapeout`, and `jetson-agx-thor-baseboard`). Their artifact-specific notices must be reconciled before use rather than assuming the root demo statement settles every file. Large full directories such as `vme-wren` (126,031,593 bytes) and `jetson-agx-thor-baseboard` (96,843,810 bytes) are intentionally outside this initial acquisition.

Five exposed candidates do not satisfy the 30–50-family development requirement. The next corpus stage should audit original public hardware repositories individually, preserving native project/rule/library files and hardware-specific permissions. No unreviewed repository is declared cleared here, and no final holdout should be assembled from these exposed families.

## Evidence and backup limits

Provenance queries used the official GitHub tag, tag-object, content, and recursive-tree APIs, plus the pinned raw license files. The recursive demo tree reported `truncated: false`. The initial fetch and offline verification ran locally; source hashes are reproducible in `data/sources.json`. Inspection of installed `/Applications/KiCad` found native templates but no sonde/pic demo boards in that searched application tree, so installed templates were not silently substituted.

Downloaded originals currently exist on this Mac and are publicly refetchable. A manifest is not a backup of native routing outputs or unique evidence. The lead's checkpoint/restore workflow must preserve those separately. No old cloud environment, private board, external contact, or paid service was used for this data work.
