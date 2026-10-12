# Saved routing preferences

Saved preferences capture routing choices without editing KiCad project settings or the source board. They preserve the current board-support and acceptance requirements. The initial native whole-board and placement cases pass. The first partial-completion case was safely rejected because KiCad regenerated protected segment IDs during SES import; its correction is pending. Both engine-stage cancellation signals pass real controls.

Create a preset once, edit its values, then preview and route using that file:

```sh
python3 -B -m autorouter settings-init --output routing-settings.json
python3 -B -m autorouter preview /path/to/board.kicad_pcb --settings routing-settings.json
python3 -B -m autorouter route /path/to/board.kicad_pcb --settings routing-settings.json --output .runs/my-route-001
```

Use a new output directory for each route. Preview lists the resolved choices, source copper layers and existing routes that will be protected or rerouted. It reads the board without running a router or KiCad validation. A passing preview does not promise routing success. The resulting candidate still needs native validation and manual review through `review-copy`.

An explicit command option overrides only that choice for the current run. For example, add `--seconds 180 --scope partial` to preserve all existing routes with a 180-second budget. `--keep-existing` remains an alias for partial scope. Other choices are `--adapter`, `--profile`, `--guidance` and `--scoring-preference`. These overrides do not rewrite the saved preset. Without `--settings`, the command uses the documented defaults; no personal configuration is loaded automatically.

A preset is a UTF-8 JSON object with these fields. All are required except `scoring_preference`, whose default is `null`:

```json
{
  "schema": 1,
  "scope": "whole_board_unlocked_routing",
  "seconds": 120,
  "adapter": "none",
  "profile": "standard",
  "guidance": "native",
  "layers": "source_all",
  "scoring_preference": null
}
```

Use an explicitly selected file outside the immutable input project. There is no implicit global or personal configuration search. Keep generic presets in the durable checkout for audited backups; avoid publishing private board names, paths or net names. The helper never writes a preset or changes personal KiCad/Freerouting settings.

| Field | Supported values and limits |
|---|---|
| `scope` | `whole_board_unlocked_routing` or `partial_completion`. The latter maps to existing-route protection. Selected nets remain unsupported. |
| `seconds` | Finite JSON number from 5 through 900, excluding booleans. This supplies the existing wall and measured-CPU acceptance budgets. A valid value does not promise completion: the engine needs its existing 30-second grace plus 10-second native-finalization planning reserves, in addition to preparation. The default is 120 seconds. |
| `adapter` | `none`, `graphics`, `planes`, or `both`, subject to the chosen guidance policy. |
| `profile` | `standard`, `tuned`, or `completion-only`. These select the existing bounded engine profiles. |
| `guidance` | `native`, `board-floors-v1`, or `placement-clearance-v1`. Existing board-format and constraint checks remain authoritative. |
| `layers` | Only `source_all`. Individual layer masks and preferred directions are not qualified by this feature and are rejected. Original stackup, layers and rules remain intact. |
| `scoring_preference` | `null`, `via_default`, `via_low`, or `via_high`. Null preserves existing behavior. Named values select existing search-cost presets; they do not promise a particular via count, length or routing success. |

Both non-native guidance policies require whole-board scope, `adapter: "both"` and `scoring_preference: null`. Placement guidance additionally requires `profile: "completion-only"`. Its established internal default costs remain fixed. Saving preferences does not enable these policies for `improve` or `recover`.

Unknown fields, alternative spellings, missing required fields, duplicate JSON keys, malformed JSON, nonfinite values and incompatible combinations are errors. An unsupported layer/scope preference is never accepted and ignored. Preset intake is limited to 16 KiB and requires a regular file without symlink ancestors; parent-directory aliases are rejected. The reused descriptor reader bounds payload size and detects changes during that read.

Explicit overrides use the same field names, excluding `schema`. Only supplied override keys replace the captured preset or built-in defaults. There is no broad pass-through to arbitrary engine flags, tool paths, commands, DRC settings or network controls.

Each CLI route captures exact preset bytes and their SHA-256, explicit overrides and the recomputed effective settings in `routing-preferences.json`. The snapshot is bound to the result, budget, routing scope and engine command; intake, snapshot and readback costs share the routing budget. Captured bytes are reparsed when checked. A caller-provided digest or an asserted effective-settings dictionary is insufficient.

During execution, `check_fresh` compares the live preset bytes with the initial capture. A changed, missing, substituted symlink or unreadable preset rejects freshness. Once a run has completed, later intentional edits to the external preset do not invalidate the old captured choices: readback uses only the bound snapshot. A byte-identical replacement cannot be distinguished from unchanged content; these are finite mutable-file consistency checks, not authentication or an atomic concurrent-writer guarantee. Source-board staleness and native acceptance remain separate existing requirements.

The API is `load(path)`, `validate(config)`, `resolve(captured=None, overrides=None)`, `snapshot(captured=None, overrides=None)`, `readback(snapshot_bytes, expected_effective=None)`, `check_fresh(captured)` and `route_arguments(effective)`. `snapshot` returns bytes for the caller to write exclusively; `readback` recomputes all relationships and optionally checks a complete normalized effective configuration. `DEFAULTS` is a read-only mapping; use `dict(DEFAULTS)` for an independent editable copy. Snapshots are limited to 64 KiB. Historical receipts without preference snapshots retain their existing validation contract; adding this helper is not a retrospective qualification of new controls.

Focused tests use real small preset files and captured JSON mutations. They cover round trips, explicit override precedence, stale inputs, symlinks/FIFOs, bounds, duplicate/nonfinite data, aliases and rehashed inconsistent snapshots. They do not establish native routing behavior, GUI support or layer-mask enforcement.
