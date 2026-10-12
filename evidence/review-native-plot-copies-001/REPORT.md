# Private native plot input review

Disposition: no remaining blocker found in the reviewed private-copy and publication changes. This is source and small-file consistency testing, not a fresh native rendering qualification.

The retained actual `review-render-fixture-002` ran one successful plot, then correctly rejected because the advertised original copy acquired `fixture.kicad_prl`. Independent comparison confirms that is its only difference from the original project: no original file changed or disappeared. The run and original source remained unchanged during this readback. The failed preview remains failed.

The new renderer makes a complete private project per plot, verifies the copy before execution, and applies the shared project-preservation guard afterward. Only a newly generated exact-basename PRL is admitted; modifying an existing PRL remains rejected. Actual private inputs, before/after inventories, process/logs, native/display SVG and HTML are bound. Advertised original/candidate copies remain immutable. No rule or existing-PRL exception was introduced.

One concrete defect was reproduced on renderer `e8c2b223…`: adding a rule file to a completed private input while a later plot ran left a successful result, because only previously listed file hashes were checked. ROOT corrected this by freezing complete input-directory inventories, returning them with the renderer receipt, and checking those inventories throughout handoff publication.

The unchanged five-case probe now passes: unchanged and new-PRL positives remain positive; changed existing PRL, changed completed file and late-added rule reject. A separate real-file handoff probe preserves the unchanged ready positive and rejects an added rule after canonical ready publication; ready metadata and HTML are archived, canonical status is rejected and no advertised ready HTML remains. Original source/receipt/candidate trees stay exact. The handoff probe mocks central validation, rendering and runtime inventory; it does not assert native validity.

Final reviewed hashes:

- `review_view.py`: `8f765624a8527df770a98594a7b27fe88776b300ec276f809c179ec7f6f60fb7`
- `handoff.py`: `b197c058b34885288adf3cf5dba3d8779a7678c81f837a95a09348c355f00814`
- `test_review_view.py`: `84f622fcecad0741bb95da1d366f7a7831dc8990dc8bb2e00b8b5cd3283f3847`

No source edits, native/GUI/network commands or full suites were performed by this reviewer. Existing scoped signal handling and 30-second observed wall/full-CPU budget remain in the handoff transaction. Optional rendering verifies its pinned plotter; other installed native tools are not revalidated. Directory and file checks are finite samples, not atomic protection against hostile concurrent writes.

Reproduce the focused checks from the repository root with fresh output paths:

```
python3 -B .runs/review-native-plot-copies-001/probe.py .runs/review-native-plot-copies-001/probe-fresh
python3 -B .runs/review-native-plot-copies-001/probe_publication.py .runs/review-native-plot-copies-001/publication-fresh
```

The original failing output is retained separately. `final-source-bindings.json` corrects a metadata-label mistake: preserved `baseline-bindings.json` and `initial-diff.patch` captured the intermediate `ae930075…` revision, not the earlier source exercised by the failing probe. The earlier probe records its exact `e8c2b223…` source hash; an unavailable exact source snapshot is not claimed.
