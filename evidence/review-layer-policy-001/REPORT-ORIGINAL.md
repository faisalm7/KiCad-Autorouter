# Layer-policy review: original draft

Two narrow scope gaps should be corrected before integration. All 6 author files and 7 basis pins match manifest `834b9d8a5b1fee17235bc941105897bd587569f3feebca886f26a440be6b95af`; reviewed helper SHA `b9726bbd2c63af31b6542e831d1bd0a7d466489c0159f1376236ee33e9663594`. No production/native acceptance bypass is claimed.

1. **Copper declaration order:** the helper accepts F.Cu, F.Adhes, B.Cu interleaving because it filters the whole layer list. Pinned KiCad `parseLayers` stops collecting copper at the first noncopper row. Require the two copper rows first, followed only by allowed noncopper declarations.
2. **Unsupported route grammar:** unknown segment fields, missing segment width and a custom via padstack are classified with `layer_scope_passed:true`. The acceptance/native flags correctly remain false, and this is not evidence that native validation would accept them. Before integration, narrow route parsing should reject unknown atoms/children and malformed/missing required singleton shapes. It need not duplicate complete geometric/native validation.

The unchanged front-only segment passes. New B.Cu copper, a new through-via under front-only, a newly locked B.Cu route spoofing an exemption and a renamed technical layer all reject. Protected exemptions are correctly derived from original scope/lock state and exact original nodes. Bindings are reconstructed from independent captured choices and both DSNs; Boolean/integer aliases remain distinguishable. `source_all` is outside this helper and stays unchanged.

Nine independent tiny pure scenarios were run; original outcomes are retained. No native, JVM, network, full suite, source edit or recursive delegation occurred. The author has been notified; correction/review is pending.

Integration should reject any layer markers or reserved `--router.layers...` arguments without the captured contract before legacy dispatch, including actual retained engine process bytes. Full argv comparison with an intact captured snapshot remains authoritative. Layer audit must run before and after native refill.
