# Native SVG compatibility review — frozen

No remaining blocker found in the final bounded compatibility change. Exact reviewed source and real preserved native SVG hashes are in `final-bindings.json`; historical source is retained under `source-001`, corrected source under `source-002`. The first native plot remains byte-identical (SHA-256 `57f2a2df28a113ef4c952556f6a3f7e01d22b26beb3235c319d6ea1410091ac6`). No native or browser process was executed by this review.

Two concrete defects were reproduced before correction. A display SVG replaced immediately after its write was rehashed as authoritative and left a ready handoff. Also, a linked XML stylesheet processing instruction and a SMIL `set` element were accepted and retained. These are file-consistency/content-policy failures; no browser exploit or external fetch was attempted or claimed. Failed controls remain in `handoff-001` and `svg-boundary-001.json`.

ROOT's correction hashes intended display/HTML bytes before writing and requires immediate exact readback, carrying that intended digest into later handoff checks. It rejects non-initial-XML processing instructions and SMIL animation nodes. The standard native SVG1.1 declaration remains narrowly recognized; other DTDs, duplicated declarations and entities reject. ElementTree is given the declaration-stripped bytes, not an external DTD. Raw native plots remain separately hash-bound under `plot-work/native-plots`; only display copies under `plot-work/plots` feed HTML images.

The unchanged eight-case whole-handoff probe now preserves its ready positive and rejects prior display/raw SVG changes, copied/original project changes, final HTML tampering, cancellation, and the original write-boundary display mutation. A ninth supplemental case changes HTML at the same write boundary and also rejects. Rejections leave no canonical ready HTML; original evidence/candidate inputs remain unchanged except the deliberately changed disposable source fixture. The real saved native SVG is accepted byte-for-byte, and its derived display is exactly the same bytes with the one observed standard declaration removed (`svg-boundary-002.json`). Both previously accepted linked/active variants reject. Seven targeted source tests pass; their full result is retained in `tests-002.log`.

The original command contract is retained: KiCad `pcb export svg --mode-single`, requested copper plus Edge.Cuts, board-fitting extent, drawing-sheet exclusion and explicit filename under the bounded plot job. No zone refill, save, engine or new DRC is invoked by plotting. Existing source/candidate/evidence freshness and 30-second handoff wall/full-CPU boundary remain authoritative. The new derived output binding also covers HTML escaping/CSP construction; it does not claim atomic protection against arbitrary concurrent filesystem mutation.

Scope: the actual first SVG establishes compatibility of this particular standard declaration and drawing with the pure parser. The full handoff probes fabricate the plot subprocess and central accepted-receipt answer while using the real renderer/handoff and real disposable files. They do not qualify a fresh native run, visual appearance, electrical correctness or browser behavior. ROOT owns the subsequent fresh native plot test. No original run/source, tracked file, native tool, JVM, network, Git or delegated process was modified/launched here.

Reproduction scripts take a fresh output directory name:

    python3 -B .runs/review-native-svg-compat-001/handoff_probe.py NEW-OUTPUT
    python3 -B .runs/review-native-svg-compat-001/handoff_html_probe.py ANOTHER-NEW-OUTPUT
    python3 -B -m unittest discover -s tests -p test_review_view.py -v

All writes in this review are frozen at the manifest. Public selection excludes copied fixture trees and duplicate source snapshots; all are retained and hash-bound in the full review manifest.
