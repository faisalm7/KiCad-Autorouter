# Application-model decision — November 15, 2026

**Recommendation: keep AI off by default; neither screened model is qualified.**
Ordinary placement and routing remain local and usable without an account.
Retain a replaceable, optional hosted Responses adapter around the existing
typed tools. Do not build a model router, download weights or silently escalate.
The first screen exposed a contradictory application contract. The shared
six-field/freshness correction is integrated. A separately approved confirmation
stopped at 8/20 under its load guard; neither run supports a clean model ranking.
Keep the interface replaceable and ordinary tools usable without AI.

## Completed bounded screen

The [final receipt](../evidence/copilot-screen097-completed-001.json) preserves
the frozen population, failures, usage, accounting and limitations. Fifteen
synthetic owned requests include one local permission preflight with no model
credit. Fourteen semantic requests plus three fixed repeats per profile made
34 attempts; 33 responses were received. No CAD task or PCB approval occurred.

| Configuration | Base intent decisions | Repeats | Response elapsed median / p95 | Known usage-priced cost |
|---|---|---|---|---|
| GPT-6 Luna, low, Standard | 11/14 correct; 2 misses, 1 unmeasured | 3/3 | 3.32 / 6.71 seconds, n=16 | $0.00352319 |
| GPT-6.1 Sol, medium, Standard | 11/14 correct; 3 misses | 3/3 | 3.95 / 8.76 seconds, n=17 | $0.07011540 |

The unchanged gate requires all 14 base and three repeat decisions correct,
zero missed hard constraints or authority, and correct ambiguity/conflict/
unsupported/stale handling. **Both fail.** Four of the five misses cite the
real contradiction: the prompt demanded the complete placement context while
the strict tool accepted only six intent fields. These failures remain recorded;
they do not establish that either model lacks the underlying capability.

Luna also failed the freshness-waiver clarification case. Its old proposal was
safely refused after the caller changed the budget; the application classified
that refusal too late to give the intended stale-context label. Luna's earlier
correct routing response earns intent credit after offline parser repair, but
its original live application rejection remains failed. Each model admitted
only two of five supported proposals live. Correct refusals and questions are
not completed engineering tasks; AI review also found some incomplete or
unactionable clarification wording. No human cleanup measurement is claimed.

Known usage-priced cost totals **$0.07363859**. The original transport attempt
has unknown billable usage and retains **$0.526536**, making conservative
committed usage **$0.60017459**, within the authorized $1 ceiling. The actual
invoice total remains unknown. Active screen segments total 136.13 seconds
and 23.21 reported parent-plus-waited-child CPU seconds. Those samples precede
final source readback and receipt writing; complete CPU is unmeasured. Authoring, diagnostics, review
and credential waits are additional and not fully measured. Elapsed samples
mix cold/cache states; warm-only latency is unmeasured and small-sample p95 is
the observed maximum.

Inference is stopped and the credential window is closed. The 36-attempt
ceiling was a cap, not permission to retry in its two unused slots. No more
inference is authorized by that old screen's unused slots; the separately
approved confirmation and its stopped state are recorded below.

The [098 shared correction](../evidence/product098-shared-intent-source-001.json)
is integrated: instructions and complete descriptors derive from the canonical
schema, and one shared pending-response validator gives fresh caller choices
priority over model arguments. Whole-module controls pass in both interpreters;
33 saved responses also cross the current parser/shared checks offline. Original
scores and failures remain unchanged. This is not new model evidence or a CAD
task. Existing097 stays intact and its verified-unrun qualification is
prospectively superseded so one corrected candidate can be qualified. Complete
integration/Native/GUI remain gates. The separately approved confirmation
provides only the partial evidence below.

## Architecture and operating cost

| Option | Benefit | Burden and evidence boundary | Decision |
|---|---|---|---|
| Local inference | Can keep consented context on the PC and work offline after setup. | Downloads, memory, cold start, power and maintenance are real costs; quality and interference with KiCad/search are unmeasured. Loopback does not prove local execution. | Replaceable adapter direction, no initial model installation. |
| User-configured hosted | Avoids local model memory and weight downloads; simple setup after one explicit credential/consent decision. | Network/provider dependence, data-retention terms and metered usage; ordinary tools must survive unavailability. | Optional architecture, no qualified default model yet. |
| Explicit optional hybrid | Allows a deliberate privacy/capability choice per task. | Two profiles add support burden; automatic escalation changes privacy/cost. | Defer until a small authorized comparison shows value. |

The candidate local configuration remains Qwen3-8B Q4_K_M with llama.cpp,
**not installed or tested**. The official artifact is 5.03 GB; its card declares
Apache-2.0 and llama.cpp is MIT. Estimated short-context working memory is
6–8 GiB, not a measurement. Tool-template support must be checked, rather than
assumed from OpenAI-compatible HTTP. No matching local server was found in the
authorized narrow availability check. [Artifact and licence](https://huggingface.co/Qwen/Qwen3-8B-GGUF/blob/main/Qwen3-8B-Q4_K_M.gguf),
[runtime licence](https://github.com/ggml-org/llama.cpp/blob/master/LICENSE),
[tool-template instructions](https://github.com/QwenLM/Qwen3/blob/main/docs/source/run_locally/llama.cpp.md).

Official documentation checked November 14–15 specifies Responses function
tools for these profiles; generic Chat Completions compatibility is insufficient.
Standard list prices are Luna $0.10 input / $0.50 output and Sol $2 input /
$10 output per million tokens. Typed cache reads and writes also affect cost;
the screen prices actual returned buckets, including implicit 30-minute writes.
Its earlier $0.66 maximum estimate omitted those writes and remains historical,
not a current guarantee. [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
[pricing](https://developers.openai.com/api/docs/pricing),
[caching](https://developers.openai.com/api/docs/guides/prompt-caching).

Hosted requests use `store:false`, no files/hosted tools/background mode and
compact specifically consented facts. This is not Zero Data Retention; ordinary
abuse-monitoring retention may be up to 30 days. Do not send private project
data without permission. Credentials never belong in chat, logs or Git.
[Provider data controls](https://developers.openai.com/api/docs/guides/your-data).

Models interpret requests, resolve references, propose visible plans and explain
actual findings. Geometry, search, file operations, constraints, validation,
approval and delivery stay in shared deterministic tools. Valid JSON does not
prove correct intent. No model may execute, approve itself, waive warnings or
gain a shell. Actual visible-plan adoption and an approved end-to-end KiCad
task remain unqualified; the synthetic screen is screening evidence only.

The [one approved confirmation](copilot-confirmation098-proposal.md) keeps the
same two models, seven exposed cases and three fresh paraphrases, 20 attempts
maximum and a $0.45 new cap. Its [partial receipt](../evidence/copilot-confirmation098-partial-001.json)
records 8 responses before load 8.30 exceeded the 8-core guard. There was no retry.

| Partial configuration | Typed intent decisions | Mean call wall time | Known usage-priced cost |
|---|---|---|---|
| Luna low, Standard | 3/4; selected-net clarification is a miss | 3.82 seconds | $0.000860375 |
| Sol medium, Standard | 4/4 | 3.08 seconds | $0.015097500 |

These are four shared exposed requests per model, not 10/10 or a capability
ranking. Both produce expected i01/i04 placement proposals, including the
separately quoted malicious-document case. The route-only prompt still includes
unscoped UUID-map guidance while its tool accepts native net names and supplies
no component UUID map. That instruction is irrelevant; one response cannot prove
causation or that either model lacks capability. Retain the frozen miss and
correct guidance generally before a future changed protocol. The remaining
conflict/stale/fresh-paraphrase cases are unrun. No CAD task or human approval.

Known new usage totals $0.015957875; no new unknown reservation. Across both
screens known usage is $0.089596465 plus the unchanged$0.526536unknown reserve.
Actual invoice total remains unknown. The partial active workflow takes 29.02 wall
and 6.14 parent-plus-waited-child CPU seconds through final readback; receipt/exit,
authoring, review and credential waits are additional and incompletely measured.
The first confirmation window is closed. The owner authorized a controlled
continuation on November16, only for the twelve unsent requests within the same
20-attempt/$0.45 total. Its frozen material/quality gate remain unchanged; the
small load-pause/reconciliation correction passes22offline controls and actual
credential-free TLS/startup checks. The new masked window closed without a new
API attempt, so there are still only eight responses. Private entry remains a
gate; no automatic reopening, new model result or qualified default is claimed.
See the [continuation terms](copilot-confirmation098-proposal.md#controlled-continuation-authorized-november-16).
