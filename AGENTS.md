# KiCad-Autorouter: persistent instructions

Read `MASTER_PROMPT.md` completely before substantive work; it is the current specification. This is a new LOCAL reconstruction and improvement project, not recovery of the failed cloud task. Historical files in `.local-reference/` are evidence leads, not governing instructions. Do not touch the old cloud environment.

## Mission and standard

Own research, architectural decisions, implementation, data, experiments, integration, tests, and release preparation. The owner is nontechnical. Make routine engineering choices; ask only for unavoidable access, spending, privacy/publication, or physical-review decisions. Continue feasible milestones in the active session rather than stopping after a plan.

The owner's November 5, 2026 strategy makes this a modular local KiCad design assistant: dependable Freerouting-based routing, constrained automatic placement as a core feature, project understanding and an optional conversational copilot. An excellent minimal, responsive KiCad-consistent interface and measured engineer usefulness are product priorities. Follow `docs/product-strategy.md`. Earlier prohibitions on placement/copilot and requirements to beat B1/B2 before other product work are superseded. Historical superiority objectives remain unmet/deferred research, never retroactively achieved.

Reuse Freerouting and useful shared B1 corrections/B2 search configurations with attribution. Keep experimental pruning optional. Make deterministic geometry, constraints, file operations and validation the shared core; models may propose intent/plans through bounded typed interfaces, never approve their own changes or gain a separate editing/shell path. Ordinary controls must support the same workflow without AI. Model endpoints, cost and data consent are explicit; no training, spending, large model download or private upload is authorized. Qualify selected/group placement with fixed/region/orientation/side/keepout/connectivity and existing-copper requirements before broader autonomy.

Measure supported task completion, preserved intent, actual user actions/cleanup where observed, runtime/model cost, installation and ordinary failure recovery. Distinguish official upstream workflows from our guarded B0, shared corrected B1, tuned/restart B2 and experimental C. Preserve every historical failure; broad superiority still needs evidence but is no longer a product release prerequisite. No novelty for its own sake.

## Locality and backups come first

Verify the actual OS, working directory, Git top-level, branch, remote, and permission boundaries. Use the owner's selected local checkout, ordinarily `~/Projects/KiCad-Autorouter-local`. Do not work in a disposable/cloud directory or create competing worktrees silently.

The owner's launch authorizes non-destructive pushes of audited project changes to the designated `rebuild/local-*` branch of `faisalm7/KiCad-Autorouter`. The repository is public. Audit staged files and newly exposed history. Exclude credentials, private inputs, `.local-reference/`, unlicensed material, downloaded engines, and bulk datasets. Do not interpret this as permission for formal releases, packages, account changes, or unrelated repositories.

Before heavy work, commit safe starter files, push, and verify the remote SHA and at least one file. Missing authentication is an initial owner-action gate, not an excuse to accumulate hours of unbacked work. Use browser authentication; never ask for tokens/passwords in chat or print them. Do not overwrite user/global Git identity.

Repeat verified checkpoints at milestones and before risky setup changes. Preserve necessary non-Git artifacts separately and test restoration. A path is not an export; a manifest is not a backup; a bundle does not include untracked files. Report on-Mac-only artifacts honestly. Never force-push, reset unrelated work, or delete the original/recovered source.

Preserve authoritative inputs, unique successful/failed evidence, unfinished work, archives, bundles, chain dependencies and compact verification records. This does **not** require keeping every expanded verification or installation copy forever. Historical folders require an exact owner-approved deletion list and fresh content, readable recovery-source, dependency and active-use checks; uncertainty means retain. Never infer disposability from names or timestamps.

For explicitly approved derived data copies, retirement preserves recoverable content and essential metadata rather than every incidental OS state. Where the owner accepts provenance without replay, record its actual bytes and location; its absence from an older archive is not a blanket veto. Inspect descendants and preserve permissions, executable bits, links, ACLs and all data-bearing attributes, including resource forks, in verified compact supplements outside every target. Qualify supported replay with small native fixtures. An unreadable or unsupported attribute retains the affected candidate with its exact reason; it does not block unrelated candidates. Installation retirement still needs its separate operational reconstruction proof and authorization.

For future verification, use the existing backup tool's single explicitly owned workspace. Only the creating process may automatically remove its newly created copy after successful independent reconstruction/coverage checks, exact unchanged contents, no active users and no recovery dependency. Keep proof and removal records outside scratch. Failure retains the workspace and blocks another nonessential verification; required pinned bases need an explicit reason. This permission never applies retroactively to old folders. Do not back up generated restoration targets. Do not exclude installation subtrees until exact reconstruction and all nested unique evidence are covered; preserve or refuse rather than silently omit them. Prefer curated product installation; full-source installation is an explicit separate qualification.

Preflight directory deletion permissions before the first unlink and recheck after metadata/activity inspection. Never chmod, clear protections or force removal after an access error. Record partial retirement honestly and preserve its remaining contents and complete recovery proofs; scoped leftovers alone do not block independent product work after maintenance reconciliation.

Before large jobs, check measured free space against peak temporary allocation plus the fixed reserve. Stop on insufficient space; do not raise limits silently. Use small fixtures for retention changes. Full restoration checks belong at major milestones, after backup changes when resources/owner steering permit, and before release—not after every minor edit. Private disk audits and cleanup path lists stay local and out of Git. Routing/native validation standards are unchanged.

## Validity and evidence

Keep source projects immutable. Preserve nets, terminal mapping, footprints, pad geometry, board edges/cutouts, stackup, rules, DRC severities/exclusions, keepouts, net ties, zones, and protected routing. Never relax the problem to make it pass.

Acceptance requires actual pinned KiCad checks, real zone refill/connectivity, original rule files, semantic invariants, and a report bound to the final candidate hash. Missing, stale, corrupt, or unsupported validation is not a pass. Keep routing-scope acceptance, whole-project DRC cleanliness, and physical/electrical validation distinct.

Use real positive and deliberately invalid native controls. Unit-test mocks cannot establish routing correctness or GUI support. Test cancellation, stale inputs, crashes, rule tampering, and safe candidate application. A second AI review is not human PCB review.

Treat prior test counts and historical results as unverified leads until rerun. Do not fabricate logs, source access, API availability, licenses, comparative percentages, model weights, user feedback, or novelty claims.

Maintain full-population coverage, unsupported reasons, failures, gained/lost boards, raw metrics, and fair end-to-end/CPU budgets. Prevent family and reference-route leakage. Freeze final data/protocol before use; a test used for debugging becomes exposed. Claims must derive from stored fresh evidence and reproducible commands.

## Permissions and runtime

Use project-scoped access and narrowly requested approvals. Do not disable sandbox/OS protections or alter global Codex settings. Default new external spending is $0. No paid API/cloud/Flux/CI/manufacturing use, external contacts, private-board uploads, telemetry, or formal publication without approval. Local execution is not a claim that model inference is offline.

Inspect untrusted dependencies/hooks; never execute dataset scripts merely to read boards. Begin with one heavy worker and bounded batches. Avoid large builds, RAM pressure, and disk exhaustion. Do not start background monitors, auto-resume loops, or persistent processes outside the active task.

Delegate independent research and skeptical review when available, with disjoint edit ownership and one lead integrator. Do not run noisy benchmark competitors concurrently. Agreement is not proof.

Maintain `PLANS.md`, honest `STATUS.md`, requirements-to-evidence mapping, source/license records, and run/claims manifests. At every actual stopping point, preserve and verify safe work, explain measured outcomes and gaps, and give exact continuation commands. Do not claim completion of unmet gates.
