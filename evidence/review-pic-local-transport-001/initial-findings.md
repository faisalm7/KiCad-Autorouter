# Initial frozen-source review: local250 transport

Two consistency gaps were reproduced before execution on driver
`0b60ad8eb9d72b07d243b7b61aec74ac710f87fef1caf2b638a9b07e043b9a1a`
and transport checker
`592cba2ea25d8237f658613ab17597523e3edaceeffeeedcccd4242ab00745b7`.

1. The new cached-native inventory runs after current tools, helper sources and
   original files are sampled. Mutating any of those three categories during the
   late cached scan leaves `runtime()` equal to its initial witness. The outer
   stable guard's second scan covers the output, not these external materials.
   Put the cached inventory before the protected current-material samples.
2. `validate_local` accepts contradictory duplicated evidence: post-load census
   says five classes despite six names, a per-item tree-entry check reports false,
   target audit identifies the wrong items, or the raw-row audit says 280 µm
   while the checked matrix says 250. Its aggregate booleans do not bind these
   emitted details. Require census/targets/tree rows/raw-row agreement with the
   independently validated before/after states, or remove unused redundant data.

`probe.py` uses the existing retained005-based synthetic constructor and tiny
review-owned files; `probe-001.json` and its log retain unchanged positives and
all demonstrated failures. No native process, JVM, network operation or actual
cached/original-source mutation occurred. Author source hashes were unchanged
through the probe.

The source-level experiment is otherwise appropriately narrow: a new class is
assigned only to two JP1 pins and their same-net synthetic bodies after actual
manager initialization; the original 5×5 matrix and observed item fields must
remain unchanged, with complete six-class matrix readback afterward. All 240 DSN
pins and 236 assigned terminal identities remain checked separately from 247
native pads. Both manager instances keep router and optimizer disabled. The
exact Java APIs are declared in retained pinned inspection outputs; this review
does not qualify their execution.

The cached failed005 summary is explicitly pinned and remains failed. Its
complete frozen evidence, original project and same-loaded-board observation
are rechecked before reuse. The new run uses compile and JVM import only; native
cost is not silently relabeled as fresh validation. Same-net reciprocal contacts
are required before and after the post-load change. Item observation does not
include every original trace polyline; the corrected wording makes this limit
explicit. Original board-edge matrix cells for classes 1/2/3 were independently
read from retained005 as 250 µm on both layers.

This is not routing, SES, pair-collision enforcement or native-rule equivalence.
All 180-second/full-CPU, 64 MiB, heap, network-denial, source-freeze, scoped signal,
stage-capture and publication mechanisms remain shared with the existing probe.
Final review is pending the two narrow corrections and unchanged falsifier rerun.
