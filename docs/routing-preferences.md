# Persistent routing settings in runtime059

Save/load presets in the graphical window, or pass an explicit JSON file with `--settings`. Keep presets outside the saved source project. Jobs capture exact bytes; changing source or captured settings invalidates the job. There is no implicit personal/global configuration search, and routing does not rewrite presets or original KiCad rules.

A value accepted by the JSON schema is not automatically supported by selected KiCad10.0.7:

| Choice | Current ordinary Route | Limit |
|---|---|---|
| Scope/protection | Whole-board reroutes unlocked copper, preserving locked routes. Finish gaps (`partial_completion`, CLI `--scope partial` or `--keep-existing`) preserves every existing route. | Selected nets remain unsupported. Historical10.0.0 controls do not transfer. |
| Budget | Finite5–900 seconds, excluding booleans; default120. Preparation/final checks consume wall and measured CPU limits. | Small budgets may refuse. GUI Improve/recovery require90+. Separate export30–120s does not enlarge routing time. |
| Profile/corrections | `standard`, `both`; corrected-standard/B1 remains default. | Ordinary tuned/completion-only and other adapters refuse. Comparison administration is separate. |
| Guidance | `native`; original rules remain authoritative. | Other guidance is not ordinary-profile admission. |
| Allowed new layers | `source_all`, preserving original stackup, on supported2/4Cu sources. | Explicit subsets/single-layer choices remain refused. |
| Via preference | `scoring_preference: null` default, or explicit `"via_high"`. | Higher search cost does not guarantee fewer vias or electrical suitability. Other scores refuse; Improve/recovery require `null`. |

Use the runtime CWD before invoking its module:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-059/runtime'
.venv/bin/python -B -m autorouter settings-init --output .runs/my-settings-001.json
```

A partial90 ordinary preset is:

```json
{
  "schema": 1,
  "scope": "partial_completion",
  "seconds": 90,
  "adapter": "both",
  "profile": "standard",
  "guidance": "native",
  "layers": "source_all",
  "scoring_preference": null
}
```

For optional higher via cost, change only the final value to `"via_high"` in a fresh preset. Use Load settings and verify displayed choices before Preview, or supply `--settings /absolute/preset.json`. Explicit CLI options override only that run; they do not edit the file. Keep sensitive copper locked or use Finish gaps. Current, impedance, timing and return-path requirements need their own checks and review; DRC alone cannot establish them.

Improve is a separate narrow2Cu/flat/single-Default whole/native/tuned/both/source_all/default-score method. Runtime059 uses a40s internal return reserve and scoped proof construction/parsing. Its [Native regression](../evidence/runtime059-native-milestone-001.json) completes the exposed EEPROM90 delivery; current GUI and fresh installation qualification remain pending. This reserve reduces time available to search and never increases total wall/CPU caps. Immutable058 used25s and retains its failed return control; old comparisons remain version-pinned. Cancellation, stale inputs or invalid constraints never authorize fallback; safe return after every failure is unproved. Thermal recovery is distinct and not current GUI-qualified. [Method requirements](gui-workflow.md).

[Twelve059 Native workflows](../evidence/runtime059-native-milestone-001.json) include default/high whole/partial2/4Cu cases and narrow Improve regressions. Previous058 [GUI092](../evidence/gui-runtime058-092-observations-001.json) and [installed GUI093](../evidence/gui-runtime058-install093-observations-002.json) retain their own scopes; they cannot qualify059, every preset combination, exact queued timing, fullGUI or electrical/broad quality. [Previous guide](history/2026-10-20-pre-runtime050-user-guides/routing-preferences.md) remains historical. [CLI](quickstart.md) · [Current gates](experimental-rc.md).
