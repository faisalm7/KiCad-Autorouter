# Saved-project workspace

Open **Open Saved Project.command** from your prepared Copperpath launcher. Choose **Place components**, pick a saved `.kicad_pro` and click **Inspect project**. Save and close the KiCad project first. The board stays visible beside Settings, Findings, Request and Schematic.

- Click parts on the board or check them in Settings. Draw the allowed area on the board. Other components stay fixed. Choose how to handle affected copper before finding alternatives.
- Request accepts explicit local lines such as `Select J1, J2`, `Area 8, 8 to 30, 12 mm` and `Routing time 75 s`. Preview shows the changes on the board. **Edit suggestion** reveals the exact values. Preview any edits and choose **Use settings** to adopt them into Settings. The optional hosted pilot is a separate control with its own consent.
- Schematic shows saved sheet instances and the links from selected board components to schematic symbols. Pin and net details use the matching saved PCB pad assignments. This shows which pads belong to a net. Schematic wire parity, routed continuity and electrical requirements need their own checks.
- **Find alternatives** opens the placement draft and its findings. Review the moves and copper plan before validating. Continue to routing and use explicit review, acceptance and fresh validation to deliver a separate project.

Schematic context checks the exact saved project when you open the pane, return to the app or change the displayed selection there. Changed files require a fresh inspection. Missing sheets, ambiguous instance links and unsupported project formats produce a visible refusal without inventing component matches. The context is read-only. You can inspect the same details with `python -m autorouter inspect-schematic PROJECT.kicad_pro` in the installed runtime.

## Observed on this build

The installed window was observed at 960 × 650 using its normal macOS controls. The project picker resolved the matching PCB. J1 and J2 appeared together on the board and the proposed region was visible. A typed 75-to-85-second edit required a fresh preview before adoption. The Schematic pane showed that J1 pin 1 shares ROUTE_A with J2 pin 1 and J1 pin 2 shares ROUTE_B with J2 pin 2. Deselecting J1 updated the open pane. Changing the disposable schematic caused the pane to withhold the earlier details. The hierarchy tests also cover repeated child sheets, changed or missing files and swapped instance paths. This check used an owned board and zero model calls.

Automatic live writes and Undo still need the bounded editor qualification. The saved-project workspace is a separate window. [Editor results and scope](live-editor-milestone.md)
