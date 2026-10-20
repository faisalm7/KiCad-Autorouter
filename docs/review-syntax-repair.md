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
