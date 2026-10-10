# Acquisition004 corrected source review

No remaining scoped source blocker was found in corrected fetch.py `26266d986acdbd2d65294fdc95acf96f3ffe72adf08805d7164cc20b036511ae`, test_fetch.py `6d81189236f6752e85fc0f3ab20bce2ea4f2621581e05685ec1645c2f6476e2f`, and author manifest `4ea2362f4bc8f6b7aed13f16ce891e38b9ecc3d9dc3f0ee639a08a89884b36be`. This is source review clearance for lead integration/checkpoint, not an acquisition or licensing result.

The original source incorrectly retained successful receipts after a late helper change, HEAD change, or verified response change. The exact original four-case reproducer now preserves the unchanged success and rejects all three stale variants with failed canonical receipts. Both generations of actual tiny-file evidence are retained; Git and HTTP were mocked, not file contents or acquisition/publication logic. The correction samples bounded helper and direct local HEAD/ref material after metadata subprocesses and places the final output scan before full stability/canonical/deadline checks. No pinned evidence is adopted after a mutation.

The independent copied control suite passed all 31 tests in 0.115 seconds, including actual self-SIGINT/self-SIGTERM with handler restoration, failed corrective publication, raw-response mismatch, case/path/symlink/mode rejection, exact pins and byte/deadline guards. All six copied source files were unchanged afterward. All 107 entries of the corrected author manifest and all nine entries of the original draft manifest were checked byte-for-byte.

The current real project data was independently hashed once with the bounded expected-inventory walker: exactly 312 files and 32,392,408 bytes matched the frozen baseline. The fixed metadata proposes 33 files / 5,016,162 bytes from three pinned public repositories. The proposed 64 MiB whole-data ceiling, unchanged 10 MiB per project/response-body invocation ceiling, 300-second foreground deadline, no retries/redirects, and separate static rights/dependency audit remain explicit. No network, native tool, engine, GUI, project-data mutation or tracked edit occurred in this review.

The helper's final checks are finite consistency samples. They do not authenticate against an arbitrary concurrent adversary or guarantee persistence after abrupt host failure. Download success cannot establish original-file rights, full dependency closure, native eligibility, routing success or independent families. Current acquisition population is unchanged.

Reproduction commands (offline and reviewer-owned output only):

```sh
python3 -B .runs/review-licensed-acquisition-004/reproduce.py --source .runs/licensed-acquisition-004-fix-001/fetch.py --output .runs/review-licensed-acquisition-004/reproduction-NEW
python3 -B .runs/review-licensed-acquisition-004/fixed-source-002/test_fetch.py
```

Use a fresh reproduction output name; existing original and corrected evidence must remain intact. `review.json` records exact source, manifest, baseline and test bindings.
