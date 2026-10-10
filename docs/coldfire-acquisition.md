# ColdFire/Xilinx development acquisition

The complete KiCad ColdFire/Xilinx demo was acquired at source revision
`69cafb907ebc09e7722a2a464b1d466fc2e3608d` and added to `data/sources.json`.
It adds one development board, bringing the manifest to six project groups,
seven native boards, and 144 files including license notices (13,654,726 bytes).
The project groups are provisional; they are not six proven independent families.
All seven boards are exposed development data, with no final holdout.

The new project is at
`.data/boards/kicad-coldfire-xilinx/kit-dev-coldfire-xilinx_5213.kicad_pcb`.
Its original 50 files total 4,366,787 bytes. The two original license notices
bring this acquisition to 52 files and 4,384,337 bytes. Every original was checked
against its pinned Git blob ID, SHA-256, size, and Git mode `100644`; none is an
executable or symlink. Board SHA-256:
`392cf6bf4b9b62beb435f965ccd7671a46decb17f947b74bfde482acd2132a5e`.
The separate original acquisition under `.data/corpus-audit-coldfire-001/project`
was retained. Both copies were verified after copying. No dataset scripts,
native KiCad process, or routing engine were executed by this acquisition.

## Rights and provenance

The [pinned upstream license notice](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/LICENSE.README)
assigns demo files to CC-BY-SA 4.0. That notice and the
[original license text](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/LICENSE.CC-BY-SA-4.0)
are preserved under the project's `_licenses` directory. A scan of all 47
UTF-8 original files found no conflicting textual license or copyright notice.
Three binary Wings 3D source files are preserved under the same upstream scope;
their metadata was not represented as fully decoded. Datasheet references in
footprint descriptions remain intact; linked datasheets were not downloaded.
Redistributed boards must retain applicable attribution, notices, and share-alike
terms; the autorouter's code license does not replace the board's license.

The path history contains 51 commits through the pinned revision. Its earliest
observed import, [3df3f6a09ffe96c8cd5bbbb984c2972210f55bbd](https://github.com/KiCad/kicad-source-mirror/commit/3df3f6a09ffe96c8cd5bbbb984c2972210f55bbd),
added eight legacy project files on 2009-02-21 with author attribution `charras`.
The source API records additions, not renames. Its parent already contained
sonde, interf_u, pic_programmer, and test_xil_95108. This establishes a distinct
import event, not independent design ancestry. Shared maintenance and possible
subcircuit reuse remain unresolved.

Read-only parsing finds four copper layers, 160 footprints, 825 pads,
278 connected-net partitions, three zones, and no custom pads. A sorted
net-terminal partition differs from the six previously acquired boards.
That comparison ignores net names but retains reference designators and pad
numbers; it does not detect arbitrary graph renaming or prove independence.

## Complete population and support limits

Read-only `autorouter.pipeline.preflight` at code revision `dd2cce9` was applied
to all seven acquired boards. Source hashes matched before and after. This is
a static eligibility screen, not native validation or an electrical review.

| Project / board | Static eligibility | Remaining unsupported reasons |
| --- | --- | --- |
| sonde xilinx | Eligible for bounded native audit | None in this static gate |
| interf_u | Eligible for bounded native audit | None in this static gate |
| pic_programmer | Unsupported | Custom pads; four unqualified rule-severity keys |
| complex_hierarchy | Unsupported | Nonliteral class bindings; unqualified `zone_has_empty_net` severity |
| multichannel routed | Unsupported | Original `padstack` check is not blocking |
| multichannel unrouted | Unsupported | Missing same-basename project; unqualified board format |
| ColdFire/Xilinx | Unsupported | Nonliteral `+3.3V` class binding; original `starved_thermal` check is not blocking; four layers also exceed the two-layer class-mapping scope |

This records two statically eligible boards and five unsupported boards. Original
rules, classes, severities, and source files remain unchanged. The paired
multichannel variants stay in one provisional family. No routing result,
whole-project cleanliness, manufacturing readiness, or generalized superiority
is inferred from acquisition or static eligibility. Earlier coverage snapshots
remain historical records and require explicit reconciliation with this population.

## Acquisition and restoration bounds

`data/fetch.py` now distinguishes a 32 MiB total manifest limit from a 10 MiB
per-project limit including notices and a 10 MiB missing-file download limit
per invocation. It validates selected existing files and the proposed download
volume before making network requests. An empty restore of the whole population
is rejected before downloading because it exceeds the per-invocation limit.
Use two bounded batches:

```sh
python3 data/fetch.py --project kicad-sonde-xilinx --project kicad-pic-programmer --project kicad-complex-hierarchy --project kicad-interf-u --project kicad-multichannel
python3 data/fetch.py --project kicad-coldfire-xilinx
python3 data/fetch.py --verify
```

The batches are 9,270,389 and 4,384,337 bytes. After promotion,
`python3 data/fetch.py --verify` checked all 144 files and reported zero downloads.
Separate controls rejected an oversized batch, project, and total population.
This does not replace the project's independent backup and restoration tests.

Raw acquisition, source API history, Git modes, structural inspection, and
promotion-control receipts are preserved in `.runs/coldfire-audit-001/`.
The data files and raw receipts remain ignored rather than being published
as bulk data. `data/sources.json` records each downloadable original and its hashes.
