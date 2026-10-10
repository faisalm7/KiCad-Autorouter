# Production placement qualification and current population

The explicit command passed the owned required-via fixture and exposed multichannel board using pinned KiCad10.0.0 and Freerouting2.5.0. Full-board native result: zero opens/blocking/exclusions, 96 warnings, 21 vias and2,647.385729mm. This is production integration of the earlier fixed adapter/search policy, not a new comparative or generalized result. Original constraints and all16 considered inputs remain preserved.

`summary.json` binds original receipts and prior immutable population records. `generate.py` reconstructs this narrow deterministic summary with current actual-receipt readback and original source hashes. Run from the durable checkout with a fresh output name, then compare bytes:

```sh
python3 -B evidence/placement-production-qualification-001/generate.py --output .runs/qualification-summary-reproduction-NEW.json
cmp evidence/placement-production-qualification-001/summary.json .runs/qualification-summary-reproduction-NEW.json
```

Complete `.runs` evidence is required; selected public subsets are not standalone runnable receipts. The [independent review](../review-placement-production-native-001/REVIEW.md) verified fixture83, cancellation40, native-controls168, full-board83 and population/public912 checks. Counts describe observations, not broad correctness. Reviewer-only failed assumptions and all native/control failures are preserved. Original diagnostic and production full-board routes have identical normalized topology, so no quality improvement or speed comparison is inferred.

Source/native fixture checkpoint d6f7f81; corrected native controls and full replay eab7540. Original sources remain unchanged. GUI handoff/current installation, family-independent evaluation, whole-project cleanliness, human PCB and physical/electrical validation remain separate pending gates. All raw artifacts still require the forthcoming full archive/restoration; a GitHub subset is not their full backup.
