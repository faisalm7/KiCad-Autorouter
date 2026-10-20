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

## Failed052 regression and fixed-bound LRU follow-up

Full202 passed. Fresh052 again produced a Native-valid 18-trial IR route with
42 warnings, then review rejected at 30.63 seconds wall / 30.19 CPU. Complete
external cost was 154.94 seconds wall / 141.84 CPU. It remains not delivered;
the [052 receipt](../evidence/runtime052-review-regression-001.json) preserves
that failure. No 052 profile or broader Native/GUI qualification was run.

The next source change refreshes syntax-cache recency on a hit. A constructed
hot-source/cold-trial sequence demonstrates fewer parses than FIFO eviction.
The existing 8 MiB / 250,000-node / 64-entry bounds, independent mutable return
trees and every validation guard remain unchanged. Eight parser controls and
skeptical source review pass. Full203 and one fresh runtime053 delivery
regression are still required; neither a faster pure-parser control nor a near
miss of the acceptance ceiling establishes delivered routing.


## Retained-data projection in the same next build

The earlier051 instrumented profile also showed repeated copies of derived
zone fill that invariant comparison immediately discarded. The new projection
filters only root routes and direct root-zone derived fill before copying the
retained tree. Fill transplant still checks route/net identity first and copies
new Native fill. Unknown fields and nested lookalike records remain intact.
Both public operations return detached lists and leave their inputs unchanged.

Seven focused tests pass against the exact previous implementations, including
unknown intent, input/output isolation and real route/net/UUID/kind refusals. An
owned synthetic differential also produced identical trees; its timing is not
actual job performance. [Evidence](../evidence/immutable-projection-repair-001.json)
records these controls and additional costs. This change and LRU will enter the
same fresh053 build after full203; no installed success is claimed yet.


Full203 passed with2,541 tests and one skip. The separately frozen053 IR
regression still failed review at30.34 seconds wall /30.03 CPU after18
Native-valid trials with42 warnings. Complete cost154.50wall/141.03CPU;
[retained failure](../evidence/runtime053-review-regression-001.json). No
choice/export/delivery or broader Native/GUI qualification ran. The copying
changes are insufficient. The next bounded assessment concerns repeatedly
reconstructed authority Context, while retaining all full child/trial/Native
checks and late freshness fences. No budget increase or parent acceptance cache.


## Reconstruction-only authority reuse

The new source repair retains one originally reconstructed private Context
within the existing validation operation, bounded to eight definitions. It
never stores a parent or child acceptance result. Each use checks current
source/snapshot/code/preferences and tools, exact constructor inputs, saved
shape/definition seal, critical live methods and the original captured owner.
A same-byte replacement directory cannot renew that original owner. Failures,
cancellation and operation exit clear the definitions. All full child, trial,
selection, Native, process, Default and final PRL readers still run.

The first existing regression run exposed a changed error path for a forged
marker. Exact shape admission now precedes reuse intake, preserving its typed
refusal;138 existing targeted tests pass. New hostile controls and
[evidence](../evidence/native7-context-reconstruction-repair-001.json) are source
qualification only. Full204 and one fresh054 installed delivery are required.


Full204 passed with2,553 tests/one skip. Fresh054 still failed review after
all four plots:30.02wall/29.32CPU; complete158.04wall/142.57CPU, no delivery.
[Failure and additional profile](../evidence/runtime054-review-regression-001.json)
remain separate from earlier runs. The rejected instrumented profile spent
18.22cumulative seconds in one full parent/two private-child reads, including
9.19trial selection; repeated final guards took9.13overlapping seconds. These
samples cannot be summed or presented as normal user-visible timing.

Parent-result caching is deferred: final guards do not independently replay
full child/trial validation. The bounded next change keeps one full review
check before any copying, checks live reader identity before and after it,
keeps all captured material constant during pure copying/rendering, and runs
current original-Context, preview, PRL and publication fences. Fresh Native
export and all acceptance criteria remain. This is an unqualified proposal
until implementation, hostile controls and a new installed trial complete.


[Implemented review/choice lifecycle](../evidence/review-single-full-repair-001.json)
now performs one complete central read before copying/rendering or intent
construction. Checker identity is captured before and checked after it, not
adopted after a late callback. Constant byte and in-memory input records, the
original Context owner/seal, and full current preview/PRL/publication guards
bind the same checked candidate through pure writes. There is no saved parent
or private-child acceptance cache. Ordinary full-read schedules and fresh
Native export remain.

160 existing and24 focused controls pass. The first existing run aborted at its
log bound because an uppercase XML-module import was mistaken for a policy
constant; renaming the alias preserves XML behavior and strict policy intake.
Exact owner checks now also reject equal-valued bool/int and int/float changes
in both Context owner maps. Full205 and a fresh055 installed delivery are
still required; software controls and source review establish no routing gain.


Full205 passed2,563 tests/one skip. [Fresh055 IR qualification](../evidence/runtime055-ir-delivery-001.json)
completed the entire actual delivery with18trials and0/0/42/0 findings,
complete308.82wall/291.69CPU. Review17.39s and choice13.62s fit unchanged30s
ceilings; fresh Native export81.85s and checked-path23.00s also passed. This
repairs this exposed delivery control; prior failures and frozen050 comparison
stay unchanged. Seven owned Native tasks/current GUI/install/invalid controls
still need this build's own qualification. No wider routing/electrical claim.
