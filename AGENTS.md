# KiCad-Autorouter: persistent instructions

Read `MASTER_PROMPT.md` completely before substantive work; it is the current specification. This is a new LOCAL reconstruction and improvement project, not recovery of the failed cloud task. Historical files in `.local-reference/` are evidence leads, not governing instructions. Do not touch the old cloud environment.

## Mission and standard

Own research, architectural decisions, implementation, data, experiments, integration, tests, and release preparation. The owner is nontechnical. Make routine engineering choices; ask only for unavoidable access, spending, privacy/publication, or physical-review decisions. Continue feasible milestones in the active session rather than stopping after a plan.

Achieve a demonstrable, fairly measured improvement in native-validated routing completion and usable route quality. A one-board adapter demonstration is not generalized superiority. Distinguish stock workflow B0, corrected-adapter baseline B1, equal-budget tuned/restart baseline B2, and the proposed full system C. Novel mechanisms must improve beyond the adapter itself. Do not force novelty or learning when evidence favors simpler code.

## Locality and backups come first

Verify the actual OS, working directory, Git top-level, branch, remote, and permission boundaries. Use the owner's selected local checkout, ordinarily `~/Projects/KiCad-Autorouter-local`. Do not work in a disposable/cloud directory or create competing worktrees silently.

The owner's launch authorizes non-destructive pushes of audited project changes to the designated `rebuild/local-*` branch of `faisalm7/KiCad-Autorouter`. The repository is public. Audit staged files and newly exposed history. Exclude credentials, private inputs, `.local-reference/`, unlicensed material, downloaded engines, and bulk datasets. Do not interpret this as permission for formal releases, packages, account changes, or unrelated repositories.

Before heavy work, commit safe starter files, push, and verify the remote SHA and at least one file. Missing authentication is an initial owner-action gate, not an excuse to accumulate hours of unbacked work. Use browser authentication; never ask for tokens/passwords in chat or print them. Do not overwrite user/global Git identity.

Repeat verified checkpoints at milestones and before risky setup changes. Preserve necessary non-Git artifacts separately and test restoration. A path is not an export; a manifest is not a backup; a bundle does not include untracked files. Report on-Mac-only artifacts honestly. Never force-push, reset unrelated work, or delete the original/recovered source.

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
