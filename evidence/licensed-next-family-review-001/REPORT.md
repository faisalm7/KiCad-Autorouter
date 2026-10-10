# Next licensed development candidates: bounded metadata review

**Recommend one staged batch of Ideal Diode, HSTX PTH and iCE40-DIO, with Video
kept as a separate farther-scope project.** These are four reviewable acquisition
candidates, not four complete/eligible/independent families. None has freshly
verified dependency closure. The two SparkFun candidates provide manageable
matched modern `.kicad_pcb/.kicad_pro/.kicad_sch` inputs; the legacy and larger
projects must not displace them merely because they are harder.

Nine new exact primary metadata requests returned 31,504 bytes, all matching the
cached Git blob and byte counts. No request failed in this review. Zero board,
project, schematic, rule, footprint, symbol, model, engine or executable payloads
were acquired; no code from a source repository was executed. All four candidates
were designated development before new requests in EXPOSURE.md. No acquired
population, manifest, support gate, reserved lineage or family count changed.

## Fixed acquisition order and exact scope

| Order | Pinned candidate | Proposed original scope / bytes before closure | Value and next gate |
|---|---|---:|---|
|1|[SparkFun Ideal Diode](https://github.com/sparkfun/SparkFun_Ideal_Diode_Breakout/tree/c950f439b55c08009e14fecc60f0fecd5832a42e)|Complete Hardware directory (native triple plus assembly STEP), original LICENSE/README: 6 files / **3,025,609 B**|Small modern four-channel analog power-selection circuit. Likely less architectural work than another legacy migration, but layers, source rules, actual copper and external references are unseen. Inspect all referenced asset origins; the assembly model is retained in the proposal, not silently discarded to call the directory complete.|
|2|[SparkFun HSTX PTH](https://github.com/sparkfun/SparkFun_HSTX_PTH_Breakout/tree/48e2aab291a360cfd6449c322a052e6c15edda3d)|Complete Hardware native triple and original LICENSE/README: 5 files / **607,950 B**|Simple 22-pin breakout could be a useful baseline anchor. Publisher states four differential pairs and power/I2C; geometric routing does not qualify its signal integrity. External stock/SparkFun library/model references remain unseen.|
|3|[OLIMEX iCE40-DIO](https://github.com/OLIMEX/iCE40-DIO/tree/6c8b27b36c55a7c2b59877957e7eb389e367c208)|**Entire** 22-file repository / **1,382,603 B**, including `.pro/.sch`, symbol cache, netlist, BOM and fabrication outputs|GPIO extension with programmable logic-level DAC adds a different interface circuit. This is a genuine native legacy project, not a modern `.kicad_pro` project. Native original-format/settings and dependency identity need their own gate; no conversion is proposed here.|
|4|[KiCad Video](https://github.com/KiCad/kicad-source-mirror/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/video)|Complete 47-file demo directory plus two original root notices: 49 files / **8,283,758 B**|Hierarchical video/PCI complexity with 32 local footprints and local symbols/models. Keep as farther-scope constraint coverage; no present two-layer/current-policy eligibility claim. Fifteen original KiCad6 stock aliases remain unresolved.|

`recommendations.json` supplies every proposed path, fixed commit, Git blob SHA-1,
size, original raw URL, destination and rights basis. SHA256 is null for unacquired
payloads; it is never inferred from a filename. Exact cached tree/ledger and fresh
metadata hashes are bound there and in fetch-receipt.json.

The first three listed scopes total **5,016,162 bytes** before external closure;
Video requires a separate **8,283,758-byte** invocation. Each project and each
acquisition invocation retains a **10 MiB** cap. These are initial source scopes,
not complete global closure or permission to raise the existing aggregate corpus
budget. The lead must count current acquired storage and closure reserve before
fetching. If necessary referenced files exceed any cap, preserve the candidate
as incomplete and stop; do not prune references or silently increase limits.

## What is fresh, what is cached, and what remains unknown

Freshly reread metadata includes both SparkFun publisher hardware grants, both
project README files, Ideal Diode's hardware overview, OLIMEX's license/README,
and KiCad's demo license statement plus Video footprint table. All match their
pinned cached tree blobs. Tree census, native file names/sizes, lack of a listed
custom-rule file or submodule, and the Video complete-directory list are **cached
facts reanalyzed offline**, not newly fetched source contents. Missing native
`.dru` files in a tree do not prove there are no project-level geometric rules,
netclass exceptions, keepouts or dependencies.

- SparkFun's [Ideal Diode license](https://github.com/sparkfun/SparkFun_Ideal_Diode_Breakout/blob/c950f439b55c08009e14fecc60f0fecd5832a42e/LICENSE.md) and [HSTX license](https://github.com/sparkfun/SparkFun_HSTX_PTH_Breakout/blob/48e2aab291a360cfd6449c322a052e6c15edda3d/LICENSE.md) explicitly grant hardware CC-BY-SA-4.0; their MIT code section is not the hardware grant. No firmware or vendor datasheet is proposed for execution or blanket redistribution.
- The [Ideal Diode hardware overview](https://github.com/sparkfun/SparkFun_Ideal_Diode_Breakout/blob/c950f439b55c08009e14fecc60f0fecd5832a42e/docs/hardware_overview.md) establishes four repeated MOSFET/transistor-array channels and identifies a KiCad-exported assembly model. Its electrical discussion includes operation beyond a component's nominal gate rating; no electrical/thermal suitability claim follows. A root grant and export description do not establish every embedded model's origin. Retain the original model in ignored acquisition staging and inspect headers/notices before publication.
- The [OLIMEX license](https://github.com/OLIMEX/iCE40-DIO/blob/6c8b27b36c55a7c2b59877957e7eb389e367c208/LICENSE) is the actual Apache-2.0 text. README's spelling `LICENSE.txt` does not replace the observed `LICENSE`. The cache library is listed, but historical stock symbols/footprints and any model paths remain unknown until authorized source inspection.
- KiCad's [scope statement](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/LICENSE.README) explicitly grants demos/* CC-BY-SA-4.0. The [Video table](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/video/fp-lib-table) still contains fifteen `${KICAD6_FOOTPRINT_DIR}` aliases alongside its local library. Repeating failed old-mirror tag lookups is not a closure plan; exact authentic versions must be tied to original references, without global path substitution.

For near-term execution the honest result is: **no cached candidate has proven
complete reference closure or immediate routing eligibility**. Ideal Diode and
HSTX are the smallest modern next audits with explicit grants and intact native
triples, not promised successes. If their original references reproduce the
already unresolved SparkFun historical-library pattern with no new authentic
revision evidence, record that and stop that closure branch rather than starting
another broad library crawl.

## Family reasoning and exclusions

The frozen screen remains 48 considered repositories, 47 completed tree requests,
one retained Kria rate-limit failure, 34 unambiguous publisher-grant/modern-triple
repositories and 29 **provisional** ancestry groups. None is proven independent.
All 48 dispositions remain in recommendations.json. Video is an existing later
metadata lead, not secretly added to the old 48-repository screen.

Ideal Diode's four channels are repeated subcircuits within one board, not four
families. HSTX follows RP2350/Raspberry Pi connector pinouts; compare its terminal
partition, connector/template identities and source history with prior passive
adapter designs before treating it as independent. Shared SparkFun logos, header
footprints and project templates are expected and cannot either establish or
refute whole-circuit independence on their own. OLIMEX iCE40-DIO is expressly a
daughter module for iCE40HX1K/HX8K boards; keep that parent/system lineage grouped
until circuit-level source ancestry is known. Video's common KiCad maintainer,
stock libraries and possible demo templates warrant comparison with the existing
FPGA/CPU demos; a distinct folder does not resolve family separation. No layouts
or reference routes were exposed in this review, and no holdout was consumed.

Cynthion was considered, then deferred on exact cached evidence: its complete
65-file tree is **17,874,795 bytes**, including seven local model blobs totaling
**9,553,879 bytes**, plus custom rules and hierarchical USB/FPGA intent. It exceeds
the current project cap. Downloading only the attractive native triple or dropping
models would not establish a complete project; no additional Cynthion request was
made. CANbardo, Tillitis and Blackmacro remain reserved and untouched. Acquired
Roller/other initial six, PMOD and LiPo retain their existing failures and closure
limits; they are not new candidates. Mixed/missing grants, oversized Antmicro
projects, software-only repositories and earlier failed requests are retained
as exclusions, not silently relabeled as absent designs or filtered successes.

After a lead-authorized bounded acquisition, inspect original project settings,
all hierarchical sheets, every library/model reference, source version/layers,
keepouts/custom rules and original notices first. Freeze manifests and full
considered outcomes before any native stage. Native load/export/refill and
positive/invalid support controls remain lead-only future work under unchanged
constraints. No new acquisition, native eligibility, electrical endorsement,
independent-family count, pooled success rate, C novelty or release claim is
made by this recommendation.
