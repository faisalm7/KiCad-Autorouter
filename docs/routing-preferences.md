# Persistent routing settings in runtime056

Save/load presets in the graphical window, or pass an explicit JSON file with `--settings`. Presets live outside the saved source project. Jobs capture their exact bytes; changing the source or captured settings invalidates the job. There is no implicit personal/global configuration search, and routing does not rewrite the preset or original KiCad rules.

The current selected KiCad10.0.7 path has the following contract. A value accepted by the JSON schema is not automatically supported by that tool profile.

| Choice | Current ordinary Route | Other status |
|---|---|---|
| Scope/protected copper | Whole-board reroutes unlocked copper and preserves locked routes. Finish gaps (`partial_completion`, CLI `--scope partial` or `--keep-existing`) preserves every existing route. | Selected-net scope has historical10.0.0 controls, but is unsupported by current056/10.0.7. |
| Budget | Explicit finite5–900 seconds, excluding booleans. Default120. Both wall and measured CPU limits apply; preparation and final validation consume this budget. A small valid setting may still refuse for lack of safe reserve. | GUI Improve/recovery require at least90 seconds. Export separately receives30–120 seconds, derived from the captured budget; it does not enlarge routing time. |
| Profile/corrections | `standard`, `both`. This corrected-standard/B1 default is fixed across boards. | Ordinary tuned/completion-only and other adapter choices refuse on selected10.0.7. Baseline administration is a separate contract. |
| Guidance | `native`; original source rules remain authoritative. | Other implemented guidance contracts are not admitted by the current ordinary profile. No electrical intent is inferred from net names. |
| Allowed new layers | `source_all`, preserving the original layer stack. | Explicit front/back lists and single-layer routing have historical10.0.0 controls only; current10.0.7 refuses them. Four-layer subset restrictions remain unqualified. |
| Via/optimization preference | `scoring_preference: null` remains default. Explicit `"via_high"` has current056 Native CLI whole/partial2/4Cu delivery controls. It increases the search cost of using vias; fewer vias are not guaranteed. | `via_low` and `via_default` remain unsupported on current10.0.7. Improve/recovery require `null`. Actual current GUI selection/save/load is pending. These are search preferences, not electrical requirements. |

These limits are incomplete customization support, not fulfillment of every original requirement. Keep sensitive copper locked, or use Finish gaps to protect all existing copper. Current, impedance, timing, return-path and other electrical requirements need their own checks and review; DRC alone cannot establish them.

Create a fresh preset from the **runtime directory**, then edit only its documented fields:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-056/runtime'
.venv/bin/python -B -m autorouter settings-init --output .runs/my-settings-001.json
```

A current ordinary partial-completion preset is:

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

To request the optional higher via cost, change only `"scoring_preference": null` to `"scoring_preference": "via_high"` in a fresh ordinary preset. Keep all original design constraints. This does not promise electrical suitability, a lower via count or a comparative gain.

Use the GUI's **Load settings…** and verify the displayed choices before Preview, or supply `--settings /absolute/preset.json` to CLI preview/route. Explicit CLI options override only that run's corresponding setting; they do not edit the file. Do not place settings in the immutable input project. Absolute runtime Python alone is insufficient when the current directory is the source checkout: change into the runtime first.

**Improve** selects its own whole-board/native/tuned/both/source_all/default-score contract and reserves25 seconds internally for returning a checked incumbent. It remains experimental, requires a qualified2Cu/flat/single-Default source and does not guarantee a better result or safe return after every failure. Cancellation, stale inputs and invalid constraints never authorize fallback. Thermal recovery is a distinct narrow method. See [GUI contracts](gui-workflow.md) and [current requirements](../REQUIREMENTS.md).

[Eleven current Native deliveries](../evidence/runtime056-native-milestone-001.json) qualify their own cases and preserve warnings, ignored checks and original/protected evidence. Current GUI089 is prepared only; [historical GUI086](../evidence/gui-runtime050-086-progress-001.json) remains partial and transfers no current qualification. They do not renew all historical combinations, establish electrical suitability or prove broad quality gains. [CLI commands](quickstart.md) · [Current support gates](experimental-rc.md). The [previous schema/advanced-mode guide is preserved unchanged](history/2026-10-20-pre-runtime050-user-guides/routing-preferences.md); its older controls are not current056 qualification.
