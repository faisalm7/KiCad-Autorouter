# Corrected pruning allocation revision002

ROOT identified an UnboundLocalError before native integration: the frozen001 nested attempt shadowed its enclosing temporal reserve with a byte-reserve local. Frozen001 stays unchanged and must not be promoted. The same added runtime regression explicitly reproduces the exact failure in both old paths, with zero validation callbacks.

Revision002 separates `time_reserve` from `space_reserve`. Actual `_prune` execution now reaches the first candidate deletion/copy and mocked validation callback for both default and new paths. It verifies a10-second new work allowance versus12-second legacy maximum, preserves deliberate failed costs and rejects final delivery. All28 targeted pure methods pass in0.082seconds. No native/JVM/Git/network or tracked edit occurred.

The new allocation contract remains standard profile/max85/individual-first/25-second reserve; the legacy contract serialization is unchanged. Source bases still match current tracked files. The complete source.patch and4 promotion files are ready for ROOT, subject to fresh native matched comparison and original-rule/final-candidate validation. Pair001/002 still show no C gain. Pure regression count is not routing quality evidence.
