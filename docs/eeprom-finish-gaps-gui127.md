# EEPROM Finish gaps workflow evaluation

The existing runtime103 installation delivered a fresh, independently checked project after one graphical **Finish gaps** attempt. Native inspection found 19 open connections. The export had zero opens, zero blocking findings and zero exclusions. The original board geometry, requirements and all 38 existing route records passed. It retains the same 36 warnings, comprising 20 library-footprint warnings and 16 footprint/symbol-field warnings, and the same seven ignored checks. The final project remains unopened. [Delivery evidence](../evidence/product103-GUI127-eeprom-finish-gaps-001.json).

This was the previously studied, locally retained CERN-OHL-P-2.0 EEPROM development packet. The attempt used standard Freerouting, both interchange corrections, all source copper layers, engine-default via preference and fixed placement. The routing budget was 420 seconds, review and choice each had 60 seconds, and fresh export had 120 seconds. Explicit acceptance recorded software-test intent. The source and the full licensed output stay local. [Source intake](../evidence/development-eeprom-001.json) · [Prior partial-routing study](benchmark-runtime074-protected-gap.md).

| Measured interval | Elapsed |
|---|---:|
| Timed source/setup preflight to Inspect project dispatch | 7 min 55.73 s |
| Complete setup to first observed delivery in the assistant | 14 min 10.17 s |
| Complete setup through independent final readback | 15 min 27.68 s |
| Seven disjoint application command intervals | 28.26 s |
| Independent reader, included in the full verification interval | 2.09 s |

The seven application commands took 1.96 seconds for inspection, 0.14 for preview, 11.48 for routing, 3.54 for review, 1.99 for the choice, 7.22 for export and 1.93 for the built-in export check. The elapsed session also includes the agent's actions, investigation and delays before observing readiness. For example, 71.57 seconds elapsed from clicking Route to the recorded success observation, including the 11.48-second command. Earlier feasibility reads preceded the timed setup. Human task time and whole-GUI CPU were unmeasured.

The timeline records 32 actions an operator would perform, exercised through automation. They include 17 setup/settings actions, six from inspection through routing, six review actions, two choice actions and one export action. No owner intervention or manual CAD edits were needed. One extra input copy was required to preserve the frozen source. No engineer assessed what further electrical or manufacturing work would be needed.

## Workflow issues to address first

1. **Allow a direct start from a saved project and carry the exact source through the toolbar.** KiCad reopened the previous project on launch. The assistant's saved-PCB field was empty after clicking the icon on the correct new board. Closing PCB Editor rewrote the disposable legacy project's `.kicad_pro`, adding or changing 34 structured paths, including design and class settings. The evaluator stopped that copy before inspection and used a fresh unopened copy of the same frozen bytes. The original and both copies are retained. Let an engineer select a saved complete project directly, and verify any toolbar-supplied identity before associating it with findings. Keep the saved-source and revalidation checks.
2. **Make the review explain what changed.** The editor displayed 39 unrouted before the assistant's original-rule refill and inspection showed 19 opens. The Edge layer plots then showed route changes and newly filled zones together. The details disclosure exposed the findings as structured JSON. Show which counts come from Native inspection, distinguish newly routed and retained copper from derived zone fill, and group inherited warnings into readable summaries with each finding still available.

Automation also had two pre-action setup mismatches and an observer comparison that treated regenerated field-proof metadata as a finding change. The actual findings and ignored checks matched. These delays are included in the full elapsed session. The assistant launch, clipboard-free dialog navigation, sole Route action and fresh export were observed in the running applications.

The selected on-Mac archive reconstructed all 429 evaluation files exactly. Full environment recovery remains pending. [Backup verification](../evidence/backups/selected-product103-GUI127-001.json).

## Next bounded placement task

Use the retained MIT **PushButtonLed** board from a different project and author, pinned at `29c46b7c03d2afd9fe3a58fe2070309b12f94b42`. Propose a new assembly constraint to keep R1 and R2 clear of the lower strip used to access the LED and capacitor. Inspect feasibility of confining the two resistors to the upper region from x 23–42.5 mm, y 24.5–37 mm. Keep their side and orientation, every other part and the 13 unrelated routes fixed. Explicitly review the affected-net rebuild plan, then accept at most one automatic alternative and one protected routing attempt. Measure setup actions, whether the placement proposal meets the service-area objective and any actual manual corrections. The new region is a proposed evaluation task. Its feasibility and delivery are pending. Earlier work on this family remains development evidence. [Pinned publisher licence](https://github.com/gurusaeth12/push-button-led-kicad/blob/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/LICENSE) · [Earlier placement and delivery](../evidence/runtime094-licensed-placement-delivery-001.json).
