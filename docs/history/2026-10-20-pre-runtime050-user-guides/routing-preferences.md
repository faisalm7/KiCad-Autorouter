# Saved routing preferences

Saved preferences capture routing choices without editing KiCad project settings or the source board. They preserve the current board-support and acceptance requirements. Native whole-board, placement and corrected partial-completion cases pass, including exact preservation of the two original fixture tracks. Deliberate protected-track removal produces a real open and is rejected. Both engine-stage cancellation signals pass. The corrected locked-track case also passes while retaining both original locked nodes exactly. Its earlier field-order rejection is preserved. Explicit allowed-new-layer lists are implemented behind a narrow native completion-only contract; the five-case actual native batch is now complete. Front-only/back-only pass with zero findings; partial-front preserves both original B.Cu segments and retains two dangling warnings. The required-via fixture passes with both layers and rejects one open with front-only. A native-clean candidate moved onto a forbidden layer is independently rejected by the layer guard.

Create a preset once, edit its values, then preview and route using that file:

```sh
.venv/bin/python -B -m autorouter settings-init --output routing-settings.json
.venv/bin/python -B -m autorouter preview /path/to/board.kicad_pcb --settings routing-settings.json
.venv/bin/python -B -m autorouter route /path/to/board.kicad_pcb --settings routing-settings.json --output .runs/my-route-001
```

Use a new output directory for each route. Preview lists the resolved choices, source copper layers and existing routes that will be protected or rerouted. It reads the board without running a router or KiCad validation. A passing preview does not promise routing success. The resulting candidate still needs native validation and manual review through `review-copy`.

An explicit command option overrides only that choice for the current run. For example, add `--seconds 180 --scope partial` to preserve all existing routes with a 180-second budget. `--keep-existing` remains an alias for partial scope. Other choices are `--adapter`, `--profile`, `--guidance`, `--scoring-preference` and `--layers`. These overrides do not rewrite the saved preset. Without `--settings`, the command uses corrected geometry/planes (`both`) with the standard profile and120seconds. This fixed conservative product policy is based on adapter development evidence; optional pruning remains explicit, and no per-board best result is selected. Historical schema1 snapshots retain their original stock defaults; new schema2 snapshots name `corrected-standard-v1`. The [runtime032 ordinary whole/partial controls](../evidence/runtime032-native-controls-001.json) qualify this default on their declared fixtures; broader scope and routing gains remain unproved. Without `--settings`, no personal preset is required; no personal configuration is loaded automatically.

A preset is a UTF-8 JSON object with these fields. All are required except `scoring_preference`, whose default is `null`:

```json
{
  "schema": 1,
  "scope": "whole_board_unlocked_routing",
  "seconds": 120,
  "adapter": "both",
  "profile": "standard",
  "guidance": "native",
  "layers": "source_all",
  "scoring_preference": null
}
```

Use an explicitly selected file outside the immutable input project. There is no implicit global or personal configuration search. Keep generic presets in the durable checkout for audited backups; avoid publishing private board names, paths or net names. Routing does not rewrite your preset. `settings-init` creates the file you explicitly request. These commands do not change personal KiCad/Freerouting settings.

| Field | Supported values and limits |
|---|---|
| `scope` | `whole_board_unlocked_routing` or `partial_completion`. The latter maps to existing-route protection. `selected_nets` additionally requires a `nets` list of exact native names, native completion-only profile and source_all layers. Actual selected positive002 preserves three protected records with0opens/0blocking/0warnings and60mm/0vias; invalid unselected-open/stale/rule/cancellation controls reject. |
| `seconds` | Finite JSON number from 5 through 900, excluding booleans. This supplies the existing wall and measured-CPU acceptance budgets. A valid value does not promise completion: the engine needs its existing 30-second grace plus 10-second native-finalization planning reserves, in addition to preparation. The default is 120 seconds. |
| `adapter` | `none`, `graphics`, `planes`, or `both`, subject to the chosen guidance policy. |
| `profile` | `standard`, `tuned`, or `completion-only`. These select the existing bounded engine profiles. |
| `guidance` | `native`, `board-floors-v1`, or `placement-clearance-v1`. Existing board-format and constraint checks remain authoritative. |
| `layers` | `"source_all"` (unchanged default), or an explicit unique list such as `["F.Cu"]`, `["B.Cu"]` or `["F.Cu", "B.Cu"]`. Lists require native completion-only mode and the qualified two-layer 20260206 source format. New copper outside the list rejects; exact protected originals remain intact. Four-layer, other formats, optimizer/guidance modes and preferred directions remain unsupported for lists. |
| `scoring_preference` | `null`, `via_default`, `via_low`, or `via_high`. Null preserves existing behavior. Named values select existing search-cost presets; they do not promise a particular via count, length or routing success. |

Both non-native guidance policies require whole-board scope, `adapter: "both"` and `scoring_preference: null`. Placement guidance additionally requires `profile: "completion-only"`. Its established internal default costs remain fixed. Saving preferences does not enable these policies for `improve` or `recover`.

Unknown fields, alternative spellings, missing required fields, duplicate JSON keys, malformed JSON, nonfinite values and incompatible combinations are errors. An unsupported layer/scope preference is never accepted and ignored. Preset intake is limited to 16 KiB and requires a regular file without symlink ancestors; parent-directory aliases are rejected. The reused descriptor reader bounds payload size and detects changes during that read.

Explicit overrides use the same field names, excluding `schema`. Only supplied override keys replace the captured preset or built-in defaults. There is no broad pass-through to arbitrary engine flags, tool paths, commands, DRC settings or network controls.

Each CLI route captures exact preset bytes and their SHA-256, explicit overrides and the recomputed effective settings in `routing-preferences.json`. The snapshot is bound to the result, budget, routing scope and engine command; intake, snapshot and readback costs share the routing budget. Captured bytes are reparsed when checked. A caller-provided digest or an asserted effective-settings dictionary is insufficient.

During execution, `check_fresh` compares the live preset bytes with the initial capture. A changed, missing, substituted symlink or unreadable preset rejects freshness. Once a run has completed, later intentional edits to the external preset do not invalidate the old captured choices: readback uses only the bound snapshot. A byte-identical replacement cannot be distinguished from unchanged content; these are finite mutable-file consistency checks, not authentication or an atomic concurrent-writer guarantee. Source-board staleness and native acceptance remain separate existing requirements.

The API is `load(path)`, `validate(config)`, `resolve(captured=None, overrides=None)`, `snapshot(captured=None, overrides=None)`, `readback(snapshot_bytes, expected_effective=None)`, `check_fresh(captured)` and `route_arguments(effective)`. `snapshot` returns bytes for the caller to write exclusively; `readback` recomputes all relationships and optionally checks a complete normalized effective configuration. `DEFAULTS` is a read-only mapping; use `dict(DEFAULTS)` for an independent editable copy. Snapshots are limited to 64 KiB. Historical receipts without preference snapshots retain their existing validation contract; adding this helper is not a retrospective qualification of new controls.

Focused tests use real small preset files and captured JSON mutations. They cover round trips, explicit override precedence, stale inputs, symlinks/FIFOs, bounds, duplicate/nonfinite data, aliases and rehashed inconsistent snapshots. They do not establish native routing behavior, GUI support or layer-mask enforcement.

## Explicit allowed new routing layers

For example, save `"profile": "completion-only"`, `"guidance": "native"` and `"layers": ["F.Cu"]` in the preset, or add `--profile completion-only --layers F.Cu` to preview/route. `--layers source_all` explicitly restores the default for that run. A mixture such as `--layers source_all F.Cu` rejects. Request order never changes physical layer order.

This controls new route copper. Original pad layers, stackup, rules, zones and protected routes are immutable. In partial mode all original tracks/vias remain protected; in whole-board mode locked originals remain protected. Preview separately counts originals extending outside the requested list. These exact originals may remain on other layers; generated copper cannot acquire that exemption by adding a lock. A new through via spans both layers and therefore requires both. No blind/micro/custom-padstack via support is implied.

The controller independently reads the source and both retained DSNs, verifies exact named physical order, derives one Freerouting layer mask and binds that flag to the captured preferences. Known segment/arc/ordinary-through-via grammar and unique route identities are required. The candidate is audited before and after saved native refill; the existing original-rule final native DRC, source preservation, cancellation and budget gates remain mandatory. Central receipt readback repeats the layer audit against actual final bytes. Missing, inconsistent or partially removed contracts reject. This layer check is not native acceptance by itself.

Source controls and the owned native cases are recorded in [the exact native batch](../evidence/layer-preferences-native-001/summary.json). These observations qualify the declared narrow workflow; they do not establish every board geometry. Explicit lists do not imply generalized routing gains, selected-net support or live-editor apply/undo.


## Selected net rerouting

The new selected scope removes only selected unlocked routes. All nonselected or unnamed original tracks/vias/arcs and every locked selected route remain protected by exact identity and full record. The engine may see other nets, but additions or changes outside the captured selected names reject. Full original-rule native refill/DRC remains mandatory: an existing open or blocking failure on another net cannot be excluded to claim success. Unchanged zone definitions are refilled; their derived copper may change.

```sh
.venv/bin/python -B -m autorouter preview /path/to/board.kicad_pcb --scope selected --nets SIGNAL_A --profile completion-only --adapter both
.venv/bin/python -B -m autorouter route /path/to/board.kicad_pcb --scope selected --nets SIGNAL_A --profile completion-only --adapter both --output .runs/selected-route-001
```

For persistent choices, set `"scope": "selected_nets"`, `"nets": ["SIGNAL_A"]`, `"profile": "completion-only"`, `"guidance": "native"` and `"layers": "source_all"` in the existing preset. All other required fields remain. Remove the nets field when changing to whole/partial scope; contradictory choices reject. Exact names are case-sensitive, unique, nonempty and bounded to64; patterns and unknown/unassigned nets reject. Completion-only describes the engine profile: selected unlocked source routes are rerouted, while locked selected routes stay exact.

Captured original bytes, names, protected records and task hash bind the result. Central readback reconstructs the selection and audits the final copper; fresh separate-project export repeats those guards and native checks. When a complete native `.kicad_sch` exists in the source, selected final DRC requests schematic parity and retains every finding. Missing native schematics are explicitly unavailable, never a parity pass. Actual selected native positive/negative and separate-project workflow controls are linked below. This establishes no generalized routing-quality gain or electrical-performance guarantee; selected complete-schematic and broader GUI contexts still require their own evidence. Legacy protected via/manufacturing formats require a source-derived qualified contract; the historical Devobordo diagnostic remains separate from later owned controls.


Actual selected positive002 now passes real native refill/final DRC and current central readback:0findings,60mm/0vias, all3protected records exact. The corrected engine partitions class membership with identical copied rules and retains every original net/pin/physical obstacle, skips unselected classes, and disables fanout/optimization. Native classes and source project remain unchanged. First001fails on added GND copper and is preserved. [Exact qualification](../evidence/selected-net-native-positive-002/SCOPE.md). The actual unselected-open negative rejects despite completing the selected net; no findings are filtered out. The separate selected workflow/fresh export and rule/stale/native-negative/cancellation controls also ran, with their preparation failures preserved. These fixtures have no schematic, so parity is unavailable rather than passed. [Negative](../evidence/selected-net-native-unselected_open-001/SCOPE.md), [workflow](../evidence/selected-net-workflow-002/SCOPE.md). No generalized routing-quality claim.

Native improvement now accepts the same explicit saved schema. Create a starter with `.venv/bin/python -B -m autorouter settings-init --purpose improve --output .runs/improve-settings.json`. Pass it with `improve BOARD --settings .runs/improve-settings.json --proposal-policy feedback --output .runs/improve-NEW`. Its supported scope is whole-board with locked copper protected, native guidance, both adapters, tuned profile and all original layers. Other scopes/layer restrictions must use `route`; incompatible improvement presets reject before a worker starts. Budgets are30–900seconds; `--seconds` and `--scoring-preference via_default|via_low|via_high` override only those named choices. Nothing alters board rules.

The preset is captured as bytes, checked for edits during execution, and retained with its actual scoring/CPU/wall choices. Old receipts retain their original narrower proof; current receipts cannot drop the settings binding and masquerade as legacy. Native improvement obtains and charges its own fresh route. The actual 120-second LED preset/High control passed full schematic, refill, original-design and final KiCad checks with all seven original warnings. Editing the external preset after its real accepted incumbent caused rejection without a final candidate. The first 60-second control failed the required finalization reserves and remains a failure; a permitted budget does not guarantee enough time. [Product qualification](../evidence/pruning-preferences-native-product-003/SCOPE.md).

Native `improve` reserves25seconds for final Native validation and publication; the legacy placement contract keeps its existing15second reservation. A small requested budget can be refused before routing if the remaining stages cannot fit. The default120seconds remains a starting point, not a completion promise. All actual final wall/CPU caps and original design checks still apply; failed or over-budget output stays rejected even when its copper passes DRC.

Development protection now fixes the already-derived task copper in memory while Native export/import run, then restores the original lock flags before saving. The exact source records and final Native checks are still required; rounding the DSN does not authorize rounding the final board. The [bounded controls](../evidence/task-copper-fixed-native-001.json) cover unlocked submicrometre copper, the unchanged exposed NUS source and an owned real-gap/free-via/padless-alias combination. The latter's earlier field-order, missing-library and field-parity refusals remain recorded. This is shared interchange support, not an optimization or added-completion claim; new installed/GUI qualification is separate from runtime019.


Experimental CLI thermal recovery has a separate fixed contract; ordinary GUI Route keeps the corrected-standard default. The [028 functional controls](../evidence/thermal-parent-functional-001.json) qualify `recover` with a fresh standard/B1 incumbent on selected10.0.7 and the existing completion-only incumbent on10.0.0. This is whole-board unlocked routing, native guidance, both adapter corrections and all original source layers. It does not accept a preference file or silently reinterpret selected nets, partial scope or a restricted-layer request. Keep source locked copper and any additional sensitive electrical requirements explicit; Native acceptance does not establish current, return-path, impedance or timing suitability. Current recovery positives contain0 designated protected items and do not add protected-copper qualification.

The CLI form is `python -B -m autorouter recover /absolute/saved/board.kicad_pcb --seconds 180 --output /absolute/new-job`. Use the selected-profile runtime's own Python, then the ordinary `review-copy`, `review-choice`, `review-export` and `review-export-check` interfaces. The method accepts90–900 seconds and reserves time for its bounded repair and verified final selection, preserves an already validated incumbent, and refuses ineligible or stale results. Each delivery still needs its own fresh validation. Schematic class flags and hierarchy remain unsupported by recovery even where ordinary Route has its own verified class authority; the unchanged owned4Cu control refused before Native. This mechanism repairs only its verified narrow saved-fill/round-PTH thermal failure; unsupported contact/geometry, warnings and source conflicts remain visible. The new0/7 controls are one exposed family and do not establish general improvement or a fresh B0/B1/B2 comparison.028GUI qualification is pending; qualified026 remains unchanged.
