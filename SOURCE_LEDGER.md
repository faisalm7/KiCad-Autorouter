# Source and provenance ledger

Prepared October 9, 2026. The master prompt's mechanisms, thresholds, and workflow choices are proposed engineering requirements, not findings established by these sources. Recheck mutable documentation, versions, permissions, and APIs when executing.

## Checked while preparing this local handoff

1. GitHub API reads for `faisalm7/KiCad-Autorouter` returned a public repository, size zero, and an empty branches collection. This is a point-in-time observation, not permission to overwrite later work.
   - https://api.github.com/repos/faisalm7/KiCad-Autorouter
   - https://api.github.com/repos/faisalm7/KiCad-Autorouter/branches?per_page=100
2. OpenAI's current environment documentation distinguishes direct Local work, local worktrees, and Cloud. It documents `Work in > This computer` for local execution. UI labels can differ by build; verify actual runtime.
   - https://learn.chatgpt.com/docs/environments/modes
3. OpenAI's current desktop documentation describes opening a folder and selecting Codex. Its local-work documentation notes that messages/task context may still be stored in the cloud.
   - https://learn.chatgpt.com/docs/app
   - https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex
4. OpenAI's permission documentation distinguishes scoped workspace access from unrestricted access and explains that Git/config paths may require specific approvals. No permission profile was changed by this handoff.
   - https://learn.chatgpt.com/docs/permissions
5. OpenAI documents project `AGENTS.md` discovery and an instruction-size limit. That is why the concise file points to an explicitly read full specification rather than assuming a long document is loaded automatically.
   - https://learn.chatgpt.com/docs/agent-configuration/agents-md
6. OpenAI's living-plan guidance supports outcome-based milestones and self-contained continuation. The engineering plan here is newly authored and does not claim that a single session will finish every research/external-validation requirement.
   - https://developers.openai.com/cookbook/articles/codex_exec_plans
7. OpenAI's subagent documentation describes delegation and cautions about parallel-write conflicts and additional token use. The master prompt proposes bounded roles rather than unbounded workers.
   - https://learn.chatgpt.com/docs/agent-configuration/subagents
8. GitHub documents cloning as creating a local copy and the CLI's browser authentication flow. Credentials for another connected application do not by themselves verify this Mac's Git authentication.
   - https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository
   - https://cli.github.com/manual/gh_auth_login
9. KiCad's macOS download page listed stable version 10.0.7. The CLI documentation identifies the usual macOS bundle path; discover and test the actual installed binary and its flags.
   - https://www.kicad.org/download/macos/
   - https://docs.kicad.org/9.0/en/cli/cli.html
10. Freerouting's latest-release link resolved to v2.5.0. Its performance claims have NOT been independently reproduced in this handoff.
    - https://github.com/freerouting/freerouting/releases/latest

## Historical materials supplied by the owner

`.local-reference/HISTORICAL_STATUS_2026-10-05.md` and `.local-reference/PREVIOUS_BUILD_BRIEF.md` are copies of the uploaded files. The historical prompts were extracted from the earlier uploaded launch ZIP. They are preserved as reference material, not current experimental evidence or active instructions. No missing source code, old Git bundle, or old verification receipt was recovered.

Historical numerical results must be described as reported in the status, not measured by this new project. The master prompt restates the main leads and explicitly requires fresh replication. The revised specification changes execution to local work and grants only the owner's scoped, audited checkpoint-push permission supplied through the launch message.

## Engineering research leads to inspect during execution

These locations and concepts are carried forward as leads. The new handoff did not install, benchmark, or audit every project's current implementation. Do not treat inclusion as validation or a license clearance.

- https://github.com/freerouting/freerouting
- https://github.com/drandyhaas/KiCadRoutingTools
- https://github.com/LGAI-Research/PCBWorld
- https://github.com/LGAI-Research/PCBWorld-Engine
- https://github.com/tscircuit/tscircuit-autorouter
- https://github.com/bbenchoff/OrthoRoute
- Find Topola's current official source and ownership before use.
- https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/
- https://docs.kicad.org/10.0/en/cli/cli.html
- https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html
- https://github.com/freerouting/freerouting/issues/879
- https://github.com/freerouting/freerouting/issues/716
- https://www.flux.ai/p/blog/ai-auto-layout-winter-update

Verify latest primary sources, artifact-specific rights, geometry/rule fidelity, actual buildability, and version compatibility before making comparisons or design commitments. The source ledger is a research start, not evidence that a router outperforms another one.

## Fresh reconstruction research (October 9, 2026)

- Installed Mac interfaces actually exercised: KiCad10.0.0 CLI and pcbnew, Java25.0.2; hashes in toolchain.lock.json. Official CLI reference https://docs.kicad.org/10.0/en/cli/cli.html corroborates refill/report flags; actual installed help and execution determine compatibility.
- Freerouting2.5.0 release/source, unconditional version-check path and alternative engines: docs/research-foundation.md. Network deny was actually tested with a socket probe; no claim that disabling analytics alone makes the engine offline.
- Official sonde native project and file-specific CC BY-SA4.0 evidence pinned at69cafb907ebc09e7722a2a464b1d466fc2e3608d: data/sources.json, docs/data-provenance.md. Download and offline verification executed.
- Isolated KiCad configuration experiments and source trace: docs/kicad-config-investigation.md. Working recipe established; earlier crash cause unresolved.

- Freerouting2.5.0 optimizer stopping settings were checked in the tagged primary source: https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/settings/OptimizerSettings.java . Default improvement threshold2.5 percent motivated a development B2 profile with0.1 percent and larger pass/failure caps. Runtime confirmation and measured outcomes belong to the fresh quality experiment, not this source reading.
- Executed KRT0.23.0 native spikes and pinned extension/dependency/source hashes: docs/krt-spike.md and evidence/krt-spike-001/002. Both reject; this updates the earlier integration lead without asserting a general comparison.
- Five complete official KiCad development projects acquired at the pinned source revision;92 files verified,6PCBs counted including unsupported sibling: docs/data-provenance.md and evidence/coverage.json.

## Newly checked October 10, 2026

- Actual pinned Freerouting2.5.0 JAR settings/parser probes: `evidence/optimizer-profile-probe-001` (57 checks) and `002` (201 checks /12 profile-budget cases). Older suffixed timeout strings parse null; repaired HH:mm:ss values parse as intended. The correct threshold CLI fraction0.001 becomes0.1 percent. These probes load no boards. Primary implementation: https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/util/TextManager.java ; exact JAR/tool/source hashes and raw outputs are retained.
- Complete ColdFire acquisition extends the verified official-demo population to6projects/7boards/144files. Static audit002 has2eligible/5unsupported, not2native routing successes. `docs/coldfire-acquisition.md` and `evidence/corpus-audit-002.json` supersede earlier counts without changing historical audits.
- Metadata-only prospective source research screened48 public repositories;47 tree requests completed and one rate-limit failure is retained. The64 listed native board filenames are not acquired or validated boards.34 repositories have unambiguous observed root hardware licenses plus modern basename triples, forming29 provisional ancestry groups; none is independently established. `evidence/corpus-next-001/source-ledger-draft.md` and JSON preserve pinned primary URLs, license evidence, exceptions, all considered repos and the prospective pool. Dependency closure/file-level rights remain gates. A separate later six-candidate development audit is not silently folded into this frozen metadata screen.
- Read-only independent quality003 audit checked3548 source/tool/candidate/report/metric/budget relationships and every433-file public subset byte. It retains the inner-timeout defect and incomplete-subset limits. `evidence/review-quality003-001` is a consistency audit, not new native execution or human review.
