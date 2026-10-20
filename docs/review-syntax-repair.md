# Review performance repair in development

The frozen runtime050 two-family comparison remains unchanged. Improve's IR
route passed Native validation, but its rendered review exceeded the existing
30-second wall or full-CPU acceptance ceiling and was **not delivered**.

A separate cProfile diagnostic of that retained receipt recorded 641 syntax
parses taking 17.20 cumulative seconds in a 38.73-second instrumented run. It
rejected during the first central check; profiling overhead makes this unsuitable
as normal runtime evidence. The profiler returned zero despite the CLI's rejected
JSON, so that exit is not workflow success. The original failed review had
completed all four plots; their recorded time was only 1.74 seconds.

The proposed repair reuses pure S-expression parsing inside the existing live
validation session. Cache keys use exact input text and current parser/tokenizer
policy. Stored trees are immutable; each caller receives independent mutable
lists. Input retention is bounded to 8 MiB, 250,000 tree nodes and 64 entries,
with eviction and uncached fallback for valid larger inputs. These bounds are
not a claim of an 8 MiB total Python heap. The memo ends with the operation and
clears on parsing/session errors or cancellation.

File reads, original-source hashes, all semantic checks, private incumbent
authority, Native evidence, tool identity and final PRL metadata fences still
run. Native7 parent and private-child result reuse remains excluded. The review
ceiling stays unchanged. Targeted regression controls pass; this source change
still needs full integration and a freshly numbered installed Native/GUI
qualification. No routing-quality or completion improvement is established by
this performance diagnosis.

[Evidence and additional costs](../evidence/review-syntax-repair-001.json).

## Failed installed051 regression and follow-up

Full integration201 passed. Fresh runtime051 (`d44c2d70`) then ran one frozen
IR Improve regression with the unchanged source and 420/450/600-second
route/method/delivery budgets. Its 18-trial route again passed Native checks
with 42 warnings, but review rejected at 34.92 seconds wall / 34.23 CPU.
Complete external cost was 167.50 seconds wall / 152.12 CPU. It remains
**not delivered**; no new GUI or broader qualification was attempted.

A separate instrumented profile recorded 86 uncached syntax parses among
708 calls, versus 641 parsing calls in the earlier profile. It also showed
three complete incumbent replays in one central check and repeated parent/tool
admission within each final guard. These profiles stop at different points and
include instrumentation overhead; they are not a paired speed measurement.

The follow-up source removes the early incumbent replay for admitted selected7
parents. Both mandatory import-contract checks still perform full private-child
validation. Direct pruning-parent imports and non-Native derived policy refuse.
Final guard collection shares its already reconstructed context, then freshly
checks the context, exact parent settings and sidecar before the final material
and all-root PRL fences. Public collectors keep full admission. No private-child
or parent result is cached. Tests inject late source, code, settings, sidecar,
tool, ownership and directory-identity changes, including coherent hash edits.

This follow-up still needs full integration and a new installed Native/GUI
qualification. [Failed051 evidence](../evidence/runtime051-review-regression-001.json)
is separate from the unchanged runtime050 comparison.
