# PIC005 imported class naming and remaining rule gap

The failed005 class assertion compared a DSN spelling with the engine's internal name. It is explained by the pinned parser and does not demonstrate lost width or POWER membership. The existing run stays failed and untouched; this task did not modify transport, rerun validation, execute Java/native code, or qualify production support.

## Exact normalization

Cached `Network.java` at `.runs/pic-clearance-api-001/source/Network.java`, SHA256 `410d4a82f88f3c52b7ec7b412c2fc0ce7bdb79ed97a2aff495907edeeb207e12`, lines436–445 selects the existing default netclass when `KiCadNetClassNames.isKiCadDefaultNetClassName` recognizes the DSN name. Lines474–478 assign the listed nets to that object; lines486–489 apply its width/clearance rules. This happens during import, before manager post-load processing; an optimization is not needed to explain it.

The one newly fetched [official pinned helper](https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/io/KiCadNetClassNames.java#L6-L40), SHA256 `928a1bfcf8913d628fc88247e3f4d2a39edf20a87642707bf9d2c370e1b21f93`, is1479 bytes. Lines6–14 document the reserved internal `default` and define `kicad_default`; lines23–27 recognize that spelling and case-insensitive default names; lines36–40 resolve it to the existing default object. `network-receipt.json` records exact URL/pin/hash. Source is retained locally; the selected public subset omits the fetched source pending the normal license audit.

A narrow future observer correction can expect exact observed internal `default` only for the native Default/DSN `kicad_default` class, retain exact POWER, and preserve every member/width/matrix check. It should not turn into arbitrary case-insensitive class aliases or a rule-equivalence pass. This report makes no such code change.

## Existing raw005 observations

`facts.json` binds existing `observations.json`, raw/derived DSNs, expected identities, context, own-clearance observations and import process to their recorded `summary.json` hashes. All inspected bytes were identical after this work. Both completed imports contain240 pins,339 traces,6 vias,3 areas,63 components,111 nets and2 layers. Both contain109 internal-default nets with500 µm widths on both layers, and GND/VCC in POWER with800 µm widths. Router/optimizer are disabled, post-load was awaited, and no solver/SES ran.

JP1's POWER body actually has clearance class3/POWER, as does its anchor. Its Default body has class1/default while its anchor has class2/smd. Both native-derived rings match exactly (areas1,875,000 and1,350,000 µm²), with reciprocal anchor contacts. Their obstacle flags follow false/true in the two cases. The preexisting GND area also changes its obstacle flag. This is whole-area activation, not isolation of only the two custom bodies. The original plane and routes remain, so these observations do not prove an unrouted all-terminal solution.

Cached `Wiring.java`, SHA256 `46a81a6595f3c130374d307151ae2f422b7991ef4ec57eae1cf7421df20eaedb`, lines437–448 uses the actual net's class, and476–486 assigns its AREA default unless an explicit class resolves. The POWER body therefore did not fall back to Default.

## Remaining blocker and smallest next step

The raw matrix on both layers gives default↔default250 µm and default↔POWER/POWER↔POWER280 µm; smd↔smd is62.6 µm. Compensated readings add1.6 µm. Thus the representation has not proved equality to native pad-specific rules: both saved JP1 own/local getter rows report250 µm, but POWER-class body interactions use280 µm; Default body↔smd uses250 µm while smd↔smd is62.6 µm. The getter record explicitly leaves initialization and pairwise rule qualification false. These differences can be conservative restrictions; they are not by themselves native illegality or permission to lower any matrix entry.

First correct only the source-proven expected class spelling and replay the existing read-only semantic checks, preserving005's failed status. Next resolve the item-pair clearance contract for body plus anchor with original rules intact, including a targeted invalid pair and preservation of unrelated matrix entries; retain raw versus compensated values. SES roundtrip and solver behavior remain separate later gates. Do not repeat the six completed Default toy scenes or infer original mixed-class equivalence from them.
