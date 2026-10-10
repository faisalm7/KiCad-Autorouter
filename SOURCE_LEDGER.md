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
