# Saved-project design workflow

The current [102live workflow](../evidence/copilot102-owned-live-delivery-001.json) inspects a saved owned project, proposes the correct visible placement/routing plan, requires explicit software-test approval, runs the shared constrained tools and freshly validates a separate export. Ordinary controls work without AI. One exposed task is not broad engineering validation. Older075and subsequent version-specific results remain recorded.

The first workflow adds project understanding to the existing router:

1. Save and close the PCB and schematic editors, then choose **File → Close Project** in KiCad manager. Select the exact project and a separate output folder.
2. **Inspect project** runs actual KiCad zone refill and complete-schematic DRC on a copy. Read the routing demand, other findings and ignored checks. Unconnected pads are not, by themselves, an invalid source.
3. Choose the scope, copper to preserve and budget. Advanced routing methods and search preferences are expandable. **Finish gaps** keeps all existing copper. Selected routing preserves other nets; a request to also preserve selected copper refuses unless that existing copper is locked and the selected workflow supports it.
4. Check the proposed settings, then explicitly start routing. Progress and cancellation use the existing worker. Create the review, inspect changes/findings, and explicitly accept or reject.
5. Fresh export performs the existing Native/original-design/protected-copper checks again and produces a separate project. Open only its checked export. An inspection or model proposal cannot replace any of these checks.

The **Assistant · optional** tab in Place and route can interpret the visible selected/fixed components, movement region, explicit affected-copper rebuild permission, protection and routing budget. Read the exact data/cost summary before privately entering a key. A live response is only a typed proposal: explicitly use a correct plan to find alternatives, inspect and approve the moves, then follow ordinary Native validation, routing, review and acceptance. The model cannot approve or run these operations. Supported geometry and original requirements are enforced locally. Ambiguous/unsupported requests must clarify/refuse rather than invent electrical requirements. The current hosted Sol/medium profile is opt-in/provisional; its two owned attempts total$0.011689, with the first failed attempt retained. No additional inference is authorized by that evidence.

### Earlier routing-only loopback interface

The optional assistant is an additional way to propose the same settings. It requires an explicitly configured local OpenAI-compatible server; the application does not download/start a model or obtain access from the development subscription. That earlier routing-only client permits literal loopback HTTP only, sends a compact summary rather than PCB files, makes one request, and accepts one `propose_route` function call. It cannot execute commands, write boards, accept candidates or acknowledge warning changes. Review and use a proposal before continuing with ordinary controls.

Current client limits are 30 seconds maximum, 512 output tokens maximum, 64 KiB request, 128 KiB response and 256 listed nets. No retry or tool loop runs. Larger/unsupported cases retain the ordinary controls. The client records actual request duration and valid provider-reported token counts; cost is unknown when the local server does not provide verifiable pricing. A loopback address does not certify that the server itself runs inference locally. Those are the earlier loopback-client limits, not the separately consented hosted placement/routing client.

An explicit local settings file can contain:

```json
{
  "endpoint": "http://127.0.0.1:11434/v1/chat/completions",
  "model": "your-installed-compatible-model",
  "timeout_seconds": 10,
  "max_tokens": 256
}
```

Use an existing compatible server and its actual model name; this example does not install one. If authentication is necessary, `credential_env` may name an environment variable containing a user-supplied credential. The value is sent only in the Authorization header and is not written to the job log or settings. Do not put a secret directly in JSON or Git.

The same deterministic interface works without a model. From this checkout, enter the installed runtime first so the commands use its pinned KiCad profile:

```sh
cd "/path/to/your/installed/runtime"
.venv/bin/python -B -m autorouter inspect-project /absolute/project/board.kicad_pcb --output /absolute/new-inspection --seconds 60
.venv/bin/python -B -m autorouter propose-route /absolute/project/board.kicad_pcb --inspection /absolute/new-inspection/inspection.json --intent /absolute/request.json
```

An explicit request is `{ "action": "route", "scope": "all_remaining", "nets": [], "preserve_existing": true, "seconds": 120, "search": "standard" }`. The result contains exact `effective_preferences`, protected/rerouted counts and the source binding; both execution and approval authority are false. Save the reviewed preferences and use the existing route/review/choice/export commands. `design-tool-schema` prints the narrow function schema for compatible clients. `inspect-project-check` replays retained inspection/source consistency without claiming a new Native run.

Synthetic HTTP tests are not live model evidence. A live copilot demonstration remains pending until an authorized application endpoint is configured. Placement follows through a bounded selected-component proposal workflow; it is not supported by this routing-intent layer.
