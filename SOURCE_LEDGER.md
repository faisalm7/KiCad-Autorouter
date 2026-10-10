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

- Pinned KiCad10.0.0 primary-source and actual-native exclusion investigation: `evidence/support-scope-review-001` and `evidence/native-exclusion-002`. Native JSON carries `excluded: true` independently of severity; an actual positive/negative control and old/new parser regression verify the fix. Broader padstack/severity support remains a proposal.
- Fixed via-search-cost portfolio derived from tagged Freerouting implementation; source URLs and hashes in `evidence/baseline-strength-review-001`. Actual JAR reflection passed539/539 checks across18 configurations. These search costs do not replace native geometric rules, and the probe performs no routing. Independent control-flow review reproduced and verified a cancellation fix (`evidence/review-portfolio-001`).

- Fresh paired run at2f36e2c and independent consistency audit: `evidence/portfolio-paired-001`, `evidence/review-portfolio-paired-001`. The actual search-cost alternatives change routing, and low-costB2 improves on default before comparison with C. All528 public subset files (526 raw plus scope/hash manifest) are distinguished from complete local native-input trees.
- Native thermal bridge positive at655207c and exact bridge-removal negative at0517174: `evidence/interf-thermal-bridge-002`, `evidence/interf-thermal-negative-001`. Pinned KiCad thermal-provider source/manual-spoke limitations and candidate-only geometric witness audit are recorded in `evidence/review-thermal-bridge002-001`; no general automatic repair or electrical performance claim follows from this diagnostic.

- Pinned KiCad10 parser source explicitly discards SMD/CONN drills: https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp#L5487 . Native pad-stack controls001/002 retain the failed SMD-hole recipe and successful PTH1nm replacement. `padstack` warnings must be rejected by routing policy even when native blocking count is zero; no severity changes were made.

- Thermal geometry interpretation and bounded proposal evidence: `evidence/thermal-path-proposal-001`. Pinned KiCad10 `SHAPE_POLY_SET::IsPolygonSelfIntersecting` returnsbool and uses integer-rounded segment collision distances; exact4/17nm² gaps explain native self-intersection flags. The earlier optional-wrapper suspicion was disproved. Two path searches failed before a separately declared graph search found unvalidated candidate bridges. Primary source URLs/hashes are retained; no native routing success is inferred.

- Actual pinned native board-floor export/context controls: `evidence/board-floor-context-001`. Same loaded board produced native floor/class/terminal observations and the raw DSN. Missing-project negative observed native default substitution; native API availability and the specific export defect were executed, not inferred from declarations.

- Bounded Roller Encoder closure follow-up inspected five primary GitHub metadata pages (exact URLs, pins, hashes and failed request in `evidence/source-closure-review-001/fetch-receipt.json`). Published three-commit ancestry and historical roller-model path were narrowed; current model blob is a lead, not acquired or rights-qualified. Shared footprint UUIDs identify logo/standoff template reuse, not independent circuit ancestry. Custom footprint and per-model historical identity/rights remain unresolved; no source promotion, model download, global path change or native job occurred. See `evidence/source-closure-review-001/review.md`.

- Second bounded Roller Encoder closure follow-up: six successful primary responses /654,117bytes, no asset payloads or native jobs. Exact five old-path model blobs match introduction61dfcfce, contemporaneous library2c1fb711 and later25af7; the historical README blob gives CC-BY-4.0 publisher permission. This narrows revision targets but leaves asset-specific notice/authorship and custom footprint origin unresolved. Complete historical/later trees and initial board tree lack that standalone custom footprint. No source or independent-family promotion; `evidence/source-closure-review-002/review.md` contains pinned primary links and remaining gates. Stop repeating broad metadata screens for the same missing source.

- New placement-area export investigation: root exactly matched four all-allowed original placement zones to eight retained native DSN generic keepouts. Pinned KiCad10.0.0 exporter at0feeca2a807f428ad2b3fa7c1e39625cb769f02c uses generic keepout when neither tracks nor vias are prohibited; native DRC skips all-five-allowed keepout flags. Exact source URLs, hashes, failed404, API declaration limits and conservative correction proposal are in `evidence/placement-area-export-review-001/REPORT.md`; exact local mapping in `evidence/placement-area-diagnosis-001`. This is an interchange hypothesis, not a causal completion result; native controls and explicit policy qualification remain pending.

- Actual placement native001 confirmed all-allowed placement exports but missed deliberately prohibited track/via geometry. Independent47-binding audit preserves the failed suite. Pinned `zone.cpp`, `drc_rtree.h` and disallow-provider source support an empty-shape/implicit-rule-path explanation, still distinguished from the pending no-placement counterfactual. Exact pins and raw observations: `evidence/review-placement-area-native-001/diagnosis-sources.json`, `docs/placement-area-diagnostics.md`. No current-version/general KiCad claim or upstream confirmation.

- Bounded official stable-source check on2026-10-10 verifies KiCad10.0.7 tag69cafb907ebc09e7722a2a464b1d466fc2e3608d, with rule-area effective-shape and implicit-disallow fixes addressing the diagnosed10.0.0 paths. The102-line board-area DSN keepout block remains byte-identical. Exact official links,5source pins,344,764downloadedbytes and unchanged-block hash are in `evidence/keepout-upstream-fix-review-001/REPORT.md`. Installed10.0.0/binary pins remain unchanged; no binary or native10.0.7 qualification is implied.

2026-10-10: Newly checked curved-pad export mechanism at KiCad10.0.0 source0feeca2a807f428ad2b3fa7c1e39625cb769f02c. `specctra_export.cpp` fixed36-segment radius compensation differs from actual max_error-based polygon segmentation; `geometry_utils.cpp` rounds counts, and `pad.cpp` retains exact native rounded copper. Actual saved geometry reproduces0.299394522/0.299465233mm native clearances versus0.301629101/0.301699812mm exported-polygon gaps. Independent direct corner projection agrees. Evidence/primary links: `evidence/placement-clearance-research-001/REPORT.md`. GPL-2.0-or-later source payload remains ignored; a20µm engine-only margin is prospective, not a universal bound or accepted route.

2026-10-10: Pinned Freerouting2.5.0 source and retained actual-JAR settings evidence explain placement-pair stagnation: best9internalunrouted atpass9, hardcoded10pass global stop atpass19. Maxpasses30/internal60secondtimeout were not the stop. Verified scoring presets50/5 and25/3 provide a bounded prospective tuning comparison; no seed/stagnation CLI invented. Exact sources/pins/logs: `evidence/placement-search-research-001/README.md`.770saved tracks match SES; no new native or engine invocation in this research.

2026-10-10: Prospective placement/search v2 was executed at24ab168d after same-code owned fixture qualification.20µm planning margin/default costs passed native routing while zero-margin and lower-cost alternatives failed. The exporter geometry diagnosis motivated the fixed parameter; search-path changes also affect completion, and no universal bound is established. Exact raw summary and all failures: `evidence/placement-search-three-arm-001/summary.json`.

2026-10-10: Bounded metadata-only expansion003 verified pinned Solderparty CERN-OHL1.2 root notices, exact arturo182 MIT dependency notices/submodule trees, and official KiCad Video demo licensing/table references.23requests/21responses/219,103bytes; no geometry payloads. Exact retrieval proposals, failed6.x mirror lookups, vendor/RF/size exclusions and remaining closure gates are in `evidence/licensed-expansion-research-003/REPORT.md`. No acquisition, routing support, independent-family or holdout claim follows.

2026-10-10: Actual bounded acquisition003 subsequently downloaded the reviewed PMOD-to-Qwiic and LiPo Disconnector root/subset dependencies:81files /7,858,011bytes, every Git blob and SHA256 checked. One native board each raises the acquired denominator14→16; both were designated development before exposure. Exact pins/URLs/hashes and unchanged offline preflight failures: `evidence/licensed-acquisition-003/`. Original-format and referenced model/stock-library closure remain unqualified. No source payload redistribution, dataset execution, native run, independent-family or holdout claim.

2026-10-10: Independent source closure audit003 rechecked all81 acquired files and original references unchanged. Two-layer counts, legacy version/rule failures, rounded outlines, three missing project-local models (510,932bytes) and unresolved stock-library identities are now evidence, not research leads. Whole-project redistribution and native compatibility remain unqualified; exact records and scope: `evidence/licensed-closure-audit-003/REPORT.md`.

2026-10-10: Bounded closure followup004 used20requests /952,778responsebytes and staged three exact models separately. S2B model matches Gregory Davill upstream at47107d92f4ad33e915fb0a173a66457c68952ca6 after exactly3,210CRLF conversions, with original MIT2018 notice verified at the same commit; arturo MIT2019 notices verified at all three model introduction commits. Other model origins and historical stock-library identities remain unresolved. Models stay ignored; no board support or population change. Primary links and exact limits: `evidence/licensed-closure-followup-004/REPORT.md`.

## Original-format compatibility lead after acquisition003

The independent static LiPo audit reverified all 26 acquired files and the already cached KiCad10.0.0 parser source. Legacy tstamp identifiers, fp_text references and two explicit legacy teardrop zones require actual native semantic observation before support can expand. No new native/engine/network execution or original edits occurred; dependency closure remains incomplete. Exact source hashes, pinned parser lines and the bounded proposed diagnostic are in `evidence/lipo-format-plan-001/PLAN.md`. This is a tested static failure lead, not format compatibility or accepted routing.

2026-10-10: Actual LiPo diagnostic001 failed the pinned DSN exporter before any JSON context or DRC report. The exact pinned all-footprint duplicate-reference check, scripting wrapper catch-all-to-false and no-layer via-width warning fallback were independently inspected; primary source URLs/hashes and five bounded requests are recorded in `evidence/lipo-export-failure-research-001/REPORT.md`. Four original padless KiBuzzard footprints share a reference, providing a source-backed failure explanation pending native all-footprint reference observation. No renaming, removal, format migration or support expansion occurred. The two via warnings did not stop execution and are not identified as the export cause. Original26-file hashes remain unchanged.
