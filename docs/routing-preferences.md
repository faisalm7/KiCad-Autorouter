# Persistent routing settings in runtime060

Save/load presets in the graphical window, or pass an explicit JSON file with `--settings`. Keep presets outside the saved source project. Jobs capture exact bytes; changing source or captured settings invalidates the job. There is no implicit personal/global configuration search, and routing does not rewrite presets or original KiCad rules.

A value accepted by the JSON schema is not automatically supported by selected KiCad10.0.7:

| Choice | Current ordinary Route | Limit |
|---|---|---|
| Scope/protection | Whole-board reroutes unlocked copper while preserving locked routes. Finish gaps (`partial_completion`, CLI `--scope partial` or `--keep-existing`) preserves every existing route. | Selected nets remain unsupported; historical10.0.0 controls do not transfer. |
| Budget | Finite5–900 seconds, excluding booleans; default120. Preparation/final checks consume wall and measured CPU limits. | Small budgets may refuse. GUI Improve/recovery require90+. Separate export30–120s does not enlarge routing time. |
| Profile/corrections | `standard`, `both`; corrected-standard/B1 remains default. | Ordinary tuned/completion-only and other adapters refuse; comparison administration is separate. |
| Guidance | `native`; original rules remain authoritative. | Other guidance is not ordinary-profile admission. |
| Allowed new layers | `source_all`, preserving original stackup, on supported2/4Cu sources. | Explicit subsets/single-layer choices remain refused. |
| Via preference | `scoring_preference: null` default, or explicit `"via_high"`. | Higher search cost does not guarantee fewer vias or electrical suitability. Other scores refuse; Improve/recovery require `null`. |

Use the installed runtime CWD before invoking its module:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime060 fresh install 001'
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

For higher via cost, change only the final value to `"via_high"` in a fresh preset. Load it and verify displayed choices before Preview, or pass `--settings /absolute/preset.json`. Explicit CLI options override only that run; they do not edit the file. Keep critical copper locked or use Finish gaps. Current, impedance, timing and return-path requirements need their own checks/review; DRC alone cannot establish them.

Improve is a separate experimental canonical2Cu/flat/single-Default whole/native/tuned/both/source_all/default-score method. Its whole budget includes tuned incumbent, pruning trials, final checks and40s internal return reserve; the reserve does not enlarge wall/fullCPU caps or guarantee completion. Runtime060 help reflects40s. [GUI095](../evidence/gui-runtime060-095-observations-001.json) observed incumbent progress and a trial log in a separate cancellation control. Cancellation, staleness or invalid constraints never authorize fallback. Thermal Recover is distinct and not current GUI-qualified. [Method requirements](gui-workflow.md).

[Thirteen installed060 Native workflows/three invalid controls](../evidence/runtime060-installed-native-milestone-001.json) and GUI095 ordinary/high/Improve roles retain exact source/protection/warning/check scope. They do not qualify every preset, fullGUI, exact queued timing or electrical/broad quality. Historical [059 Native](../evidence/runtime059-native-milestone-001.json)/[GUI094](../evidence/gui-runtime059-094-observations-001.json), [058 comparison](benchmark-runtime058-installed.md) and [previous guide](history/2026-10-20-pre-runtime050-user-guides/routing-preferences.md) remain version-specific. [CLI](quickstart.md) · [Current gates](experimental-rc.md).
