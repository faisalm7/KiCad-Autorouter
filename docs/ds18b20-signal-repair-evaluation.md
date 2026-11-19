# DS18B20 signal repair trial

The task is to rebuild the saved `/SIG` connection on the Ampnics DS18B20 temperature interface and preserve its existing power and ground routing. The board family appeared in earlier whole-board comparisons. This is a different task on a different board from the EEPROM and 555 workflow trials. It gives development evidence about a signal repair.

## Fixed before the trial

- Source is the retained KiCad project from `ampnics/DS18B20` commit `c5420f538a77e0af03974031a5ee1c36a5b5e0a1`. The PCB SHA-256 is `2ce74b0cfa4863e15ff282ed6e77d628bd3f13756886fdd133cd20c5e7404f13`. Md Ammar Maniyar (Ampnics) licenses the design under MIT in the pinned README. The project and license notices remain local. [Publisher's grant](https://github.com/ampnics/DS18B20/blob/c5420f538a77e0af03974031a5ee1c36a5b5e0a1/README.md#-license)
- Prepare one new copy with the nine existing unlocked `/SIG` segments omitted. The saved CAD identifies the terminals as R1.2, J1.2 and U1.2. Preserve all 11 GND and 7 VDD segments, placement, project rules, schematic and notices. The original is untouched. This simulates a signal rip-up.
- Use the installed saved-project controls and **Finish gaps**, standard profile, both copper layers, Native validation and default scoring. Inspect the source within 60 seconds, route once within 120 seconds, review and choice each within 60 seconds, and fresh export within 120 seconds. Use Edge for graphical review and the existing independent export readback. No model calls or manual PCB corrections are authorized in this trial.
- Success requires all signal terminals connected, all 18 protection records exact, original constraints unchanged, zero new blocking or warning findings and fresh checked delivery. Record all inherited warnings, ignored checks and opens. Terminate the attempt at any refusal. Record setup-to-delivery elapsed time, tool wait, operator-equivalent actions, manual corrections and any automation intervention.
