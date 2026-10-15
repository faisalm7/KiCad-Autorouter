# Closure: empty during-alias geometry

**ALIAS-GEOMETRY-EMPTY is closed at the source SHA recorded in findings.json.** The exact earlier counterexample now fails: source-derived copper layer keys are mandatory for pads and copper graphics/fields, those maps need nonempty polygon lists, and polygon rings need at least three integer-nanometre vertices. Zone outlines, copper glyphs and area outlines cannot be erased.

The zone-fill exception is justified: KiCad allocates per-layer empty containers when no source fill is present. Exact source-zone copper keys remain mandatory; sourcefilled layers still require nonempty retained fill. This preserves absent derived fill without allowing erasure of zone intent or existing source fill.

Lead-produced census004 passes against the same exact current source on retained actual Roller during/restored observations: 0.843193958 wall seconds / 0.394873 full CPU seconds, no new Native/JVM work. Failed001–003 remain preserved. This closure review ran no project code/tests/Native and changed no live source. It closes only this finding; current normal workflow qualification remains separate.
