# DS18B20 signal repair trial

The task is to rebuild the saved `/SIG` connection on the Ampnics DS18B20 temperature interface and preserve its existing power and ground routing. The board family appeared in earlier whole-board comparisons. This is a different task on a different board from the EEPROM and 555 workflow trials. It gives development evidence about a signal repair.

## Fixed before the trial

- Source is the retained KiCad project from `ampnics/DS18B20` commit `c5420f538a77e0af03974031a5ee1c36a5b5e0a1`. The PCB SHA-256 is `2ce74b0cfa4863e15ff282ed6e77d628bd3f13756886fdd133cd20c5e7404f13`. Md Ammar Maniyar (Ampnics) licenses the design under MIT in the pinned README. The project and license notices remain local. [Publisher's grant](https://github.com/ampnics/DS18B20/blob/c5420f538a77e0af03974031a5ee1c36a5b5e0a1/README.md#-license)
- Prepare one new copy with the nine existing unlocked `/SIG` segments omitted. The saved CAD identifies the terminals as R1.2, J1.2 and U1.2. Preserve all 11 GND and 7 VDD segments, placement, project rules, schematic and notices. The original is untouched. This simulates a signal rip-up.
- Use the installed saved-project controls and **Finish gaps**, standard profile, both copper layers, Native validation and default scoring. Inspect the source within 60 seconds, route once within 120 seconds, review and choice each within 60 seconds, and fresh export within 120 seconds. Use Edge for graphical review and the existing independent export readback. No model calls or manual PCB corrections are authorized in this trial.
- Success requires all signal terminals connected, all 18 protection records exact, original constraints unchanged, zero new blocking or warning findings and fresh checked delivery. Record all inherited warnings, ignored checks and opens. Terminate the attempt at any refusal. Record setup-to-delivery elapsed time, tool wait, operator-equivalent actions, manual corrections and any automation intervention.

## Observed outcome

With the installed workspace at source `a7b142216`, the derived project
passed KiCad 10.0.7 admission with two open connections, zero blocking
findings, 11 warnings and seven ignored checks. The sole routing attempt
closed both opens in 7.56 seconds of internal route wall time. The fresh
export contained five new `/SIG` route records. All 18 retained records
matched exactly, and the source files, placement, project rules and
schematic stayed intact. The same 11 warning records and seven ignored
checks were present in the final KiCad report. There were no excluded
findings or schematic parity findings.

The rendered review opened in Microsoft Edge. Explicit software-test intent
and fresh validation produced a separate project. Independent readback
confirmed the current export. The export was left unopened after the check.
There were zero manual CAD corrections and zero model calls.

Setup through checked delivery took **7 min 5 s** in the observed automation
session. The independent receipt completed at **7 min 55 s**. The eight
sequential command wrappers totalled **24.74 s**, including both export
checks. The 16 recorded operator-equivalent actions include two closure
acknowledgement attempts and two Inspect presses. The first centered click
missed the checkbox. Copperpath refused before any Native dispatch and the
test controller waited for a receipt that could not exist. Clicking the
checkbox itself resolved this. The observer also corrected its scope label
and receipt path checks without re-running Preview or dispatching another
route. These were control and observation delays. This timing describes
the observed session, with no measured human task time.

Review still required switching to Edge, returning to Copperpath and
acknowledging that review editors were closed even though only the browser
report was opened. The saved-schematic lookup separately refused this
board's empty symbol project-instance names. Routing proceeded through its
usual Native checks. That read-only context gap remains visible.
[Qualification receipt](../evidence/product-workspace-batch-f51-001.json)
