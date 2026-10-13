# Final original-cost metadata fix

The remaining cost-reporting counterexample is rejected by exporter SHA256 `e4a7decd5dbfab1bf4f2df34df417ec79899cf4f92b915a1aadd874bf3f06d9a`, with pipeline unchanged at `34525c04cb7c9c5984cfc0a069bd857b055b184111bdf52e7e6f6356208447a5`. Source/test identities remain stable before/after the check.

Only the requested final counterexample and controlling positive were rerun. Changing original-routing cost metadata to arbitrary budgets and zero costs now raises `export delivery fields differ from validated project`. Restoring the exact original export record passes again. Source/review material stays unchanged. This append-only subreview preserves the earlier frozen four-fix review and its historical open-gap finding; no earlier record was rewritten.

The control uses the existing explicit mocked native/checker/tool seams and shared capture/validation/readback paths. No native/JVM/subprocess/Git/network execution, real benchmark cost claim, tracked edit or live symlink occurred. All reproduced exporter consistency gaps are resolved; actual native qualification remains the lead's next gate.
