# Bounded licensed-project expansion research003

**Recommend three development acquisition/closure audits, not three qualified
new boards:** PMOD-to-Qwiic, LiPo Disconnector, then the official KiCad video
demo. No board, schematic, footprint, model or archive content was downloaded.
Layer counts remain unknown under this metadata-only task; the next acquisition
must verify exactly two or four copper layers before routing eligibility. It
would be dishonest to label any of these a verified two/four-layer addition now.

The existing denominator stays **14 boards,3 eligible,11 unsupported**. No prior
file, source classification, holdout assignment or failed result was changed.
All leads investigated here are proposed for development exposure. Two had an
old metadata-only reserve label; their geometry remains unseen and the old
ledger stays intact. No family independence is inferred from filenames, common
logo footprints, shared UUIDs or distinct Git repositories. The30–50-family and
confirmatory-set gaps remain open.

## Recommended bounded acquisitions

| Priority | Exact project pin | Complete root | Proposed initial root + pinned local dependencies | Why investigate / remaining gate |
|---|---|---:|---:|---|
|1|[solderparty/pmod_to_qwiic_adapter](https://github.com/solderparty/pmod_to_qwiic_adapter/tree/14b1141eca4fb4ff84d9898e756ee8e5445b6c1f)|9files,3,136,974bytes|3,663,021bytes|Small I2C adapter can supply a baseline-success/control input rather than only hard failures. Actual layers, complete stock/model closure and rule support are still unknown.|
|2|[solderparty/lipo_disconnector_hw](https://github.com/solderparty/lipo_disconnector_hw/tree/e70656fad7e7756d6595a1598037d724dcd0e5d6)|10files,3,838,231bytes|4,194,990bytes|Simple low-voltage battery interconnect offers a second bounded native task. It may be trivial; no difficult-routing or independent-family claim.|
|3|[KiCad demos/video](https://github.com/KiCad/kicad-source-mirror/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/video)|47files,8,266,208bytes|8,283,758bytes with root notices|A complete official complexity lead with32 local footprint files and local symbols. Stock KiCad6 aliases, actual layers and PCI/high-speed electrical intent are explicit gates; no geometric-only electrical claim.|

`retrieval-plan.json` lists every proposed file, exact repository/commit/path,
Git blob SHA-1, byte count, destination and raw URL. SHA-256 is deliberately null
for content not yet acquired; known root notices retain previously verified
SHA-256. Each future project is capped at10MiB including dependency closure.
This manifest is a reviewable proposal, not an acquisition or backup.

## Concrete rights and dependency evidence

The two Solderparty roots contain publisher CERN-OHL1.2 notices. The exact cached
license/README/.gitmodules bytes were checked against fresh pinned tree blobs;
notices are copied unmodified here. The LiPo notice has non-UTF8 punctuation;
byte identity is preserved rather than silently recoding it. Their local
`fp-lib-table` files name only `${KIPRJMOD}/modules/Symbols_Extra.pretty`.
This directory is fully present at both recorded submodule revisions and has
15 files/355,693bytes. The shared paths/blobs establish reusable logo templates,
not circuit-family ancestry. [PMOD table](https://github.com/solderparty/pmod_to_qwiic_adapter/blob/14b1141eca4fb4ff84d9898e756ee8e5445b6c1f/fp-lib-table),
[LiPo table](https://github.com/solderparty/lipo_disconnector_hw/blob/e70656fad7e7756d6595a1598037d724dcd0e5d6/fp-lib-table).

The exact footprint dependency pins are
`arturo182/kicad-modules@813d15802ba11589749847e9e03fbcbd1c3a7a05` (PMOD) and
`@9bde9c1677d7002a26a9c11c747fe226a62b70db` (LiPo). Both complete nontruncated
trees contain the same MIT notice blob `b72430dd28b649c004e6e82ecfa008ae4cecdb48`,
whose actual text was retrieved and Git-blob verified. It carries arturo182's
2019 copyright. The PMOD symbol dependency is pinned to
`arturo182/kicad-library@3b3f989c6b1778cbe8901a18d363393a0305b51a`,30files/169,288bytes,
with the same exact notice blob. Its complete symbol repository is included in
the proposal, despite no root sym-lib-table; linkage must still be checked.
[Module notice](https://github.com/arturo182/kicad-modules/blob/813d15802ba11589749847e9e03fbcbd1c3a7a05/LICENSE),
[symbol tree](https://api.github.com/repos/arturo182/kicad-library/git/trees/3b3f989c6b1778cbe8901a18d363393a0305b51a?recursive=1).

The full module repositories are95,932,508 and193,844,618bytes. Downloading them
wholesale would add unrelated models and rights work. The proposal instead
fetches the complete explicitly table-referenced directory plus notice, then
requires exact reference closure after original source acquisition. This is
**not yet complete global footprint/symbol/model closure**. Any additional named
asset must have authentic source/identity/rights or the project remains blocked.
An embedded footprint cannot substitute for proving its upstream identity.

KiCad's pinned root statement explicitly assigns demo files CC-BY-SA4.0. Video
contains its custom footprint/symbol/3D source locally. Its15 additional footprint
table aliases refer to `${KICAD6_FOOTPRINT_DIR}`; these are not arbitrary third-party
libraries, but authentic version/parity still needs qualification. No local or
global alias was changed. A proposed6.0.11 tag lookup in the old GitHub footprint
mirror returned404 twice; the returned tag list contains5.x, not6.x. Do not
substitute the latest library or invent a6.x pin. Resolve the canonical modern
library source and exact required files in the next bounded closure step.
[Scope statement](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/LICENSE.README),
[video table](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/video/fp-lib-table).

Root grants and metadata are concrete permission evidence, not proof that every
uninspected asset lacks conflicting embedded terms. Preserve notices, author
attribution and modifications; inspect each acquired asset's notices before
public redistribution. Circuit geometry and native rules remain unchanged.

## Negative and repeated exclusions retained

- **OpenAir-max:** publisher CC-BY-SA4.0 notice is confirmed, but its local library
  tree has three vendor-named3D models and `type-c-31-m-12-1.snapshot.5.zip`.
  Their asset notices/contents were not read. No claim that the ZIP or models
  inherit unrestricted rights automatically, and no archive execution/extraction.
  Remains a secondary9.61MB complete-project lead, not closed.
- **RoyalBlue54L:** README states CERN-OHL-Pv2, but retained .gitmodules declares
  two external libraries under paths absent from the inspected local library
  tree. Four vendor-named3D models are present; notices remain uninspected. Radio/
  antenna task scope and a sibling antenna design also remain. No silent closure.
- **Type-C CP2102:** reused metadata shows a44,627,880-byte assembly STEP plus
  two external library pins. The complete root exceeds the proposed10MiB batch;
  not prioritized by silently dropping that file and calling the root complete.
- **Roller Encoder:** prior001/002 missing custom footprint and model-notice
  gaps remain; no repeated ancestry queries or hidden fallback to embedded cache.
- **StickHub/high-voltage/RF-only and oversized official demos:** prior explicit
  licensing/scope/size exclusions remain. No mass rescanning or removal from the
  existing considered population. The48-repository screen remains metadata only.

## Lead's next bounded gate

Acquire PMOD first into a NEW ignored staging directory, only after reviewing
this manifest; cap the root plus closure at10MiB. Fetch exact listed raw blobs
without clone hooks/scripts, reject symlinks/LFS pointers/unlisted entries, and
compute both Git blob identity and SHA-256. Preserve all root files including
original cache/notes. Do not execute project scripts or load geometry into a
solver. Statically inventory layers, original rules/severities/exclusions,
footprint/symbol/model references and per-file notices. Mark every unresolved
item explicitly; do not broaden the current native gate or relax any rule.

Only after authentic dependency closure, rights audit, same-basename project
binding and low-voltage two/four-layer task qualification should the lead add
its immutable manifest to the full denominator and schedule actual native source
checks. Perform the same process for LiPo, then Video if its version/scope gates
are tractable. Keep simple baseline successes and harder failures, group related
boards conservatively, and reserve untouched future families separately.

23 primary HTTP requests produced21 saved responses/219,103bytes; two404s are
retained. No geometry assets, datasets or executables were fetched; no native,
engine, package, global setting or tracked file was changed. `fetch-receipt.json`
and offline `analyze.py` bind all saved metadata and reused notices. This is a
small concrete next acquisition plan, not completion of representative coverage.
