# Saved-project workspace

Open **Open Saved Project.command** from the Copperpath launcher. Pick a saved `.kicad_pro` and click **Inspect project** for placement and schematic context, or **Route saved board** to go directly to protected routing. Save and close the KiCad project first. Keep its PCB, schematic and rules together.

- Click parts on the board or check them in Settings. Draw the allowed area on the board. Other components stay fixed. Choose how to handle affected copper before finding alternatives.
- **Preview placement** reads explicit local lines such as `Select J1, J2`, `Area 8, 8 to 30, 12 mm` and `Routing time 75 s`. Preview shows the selection and area on the board. **Edit suggestion** reveals the proposed values. Preview any edits and choose **Use settings** to adopt them. It starts no placement or routing job.
- Open **Conversation** beside the board. Choose a task and use **Review data and send…** to see the exact data and cost of a hosted turn. Only the selected parts can move in a placement task. Other parts stay in place and KiCad locks stay as saved. A protected-routing suggestion can show the saved board even before placement inspection. Review the proposal, adjust it with **Edit suggestion**, preview the edit, and choose **Use settings**. Editing the request invalidates pending settings. **New conversation** clears the history. The earlier conversation remains available beside routing review for the same saved project revision.
- Schematic shows saved sheet instances and the links from selected board components to schematic symbols. Pin and net details use the matching saved PCB pad assignments. This shows which pads belong to a net. Schematic wire parity, routed continuity and electrical requirements need their own checks.
- **Find alternatives** opens the placement draft and its findings. Review the moves and copper plan before validating. **Continue to routing** keeps the validated placement and affected nets in the same window. After routing, **Review result** shows new, retained, protected and removed tracks and vias by layer. **Placement** preserves the component view. **Findings** shows KiCad's post-refill connection counts, groups inherited warnings and retains the full details. The optional detailed report includes pads and zone fill.
- Review the findings, acknowledge them and choose **Accept result** or **Reject**. Acceptance records your intent. **Export checked copy** runs fresh KiCad validation before offering **Open checked export**. The original project stays unchanged. If files changed, start from a current saved project and review again.

Schematic context checks the exact saved project when you open the pane, return to the app or change the displayed selection there. Changed files require a fresh inspection. Missing sheets, ambiguous instance links and unsupported project formats produce a visible refusal without inventing component matches. The context is read-only. You can inspect the same details with `python -m autorouter inspect-schematic PROJECT.kicad_pro` in the installed runtime.

## Observed on this build

The installed window was observed at 960 × 650 using its normal macOS controls. The project picker resolved the matching PCB. J1 and J2 appeared together on the board and the proposed region was visible. A typed 75-to-85-second edit required a fresh preview before adoption. The Schematic pane showed that J1 pin 1 shares ROUTE_A with J2 pin 1 and J1 pin 2 shares ROUTE_B with J2 pin 2. Deselecting J1 updated the open pane. Changing the disposable schematic caused the pane to withhold the earlier details. The hierarchy tests also cover repeated child sheets, changed or missing files and swapped instance paths. This check used an owned board and zero model calls.

The saved-project workspace is a separate window. A distinct isolated KiCad 10.0.8 companion test passed one checked footprint move and native Undo on its owned fixture. [Editor results and scope](live-editor-milestone.md)

## Moving parts into a destination area

On builds with **Approve placement and validate**, choose the destination on
the board or under **Precise area · mm**. When the supported pair starts
outside the destination and its courtyard needs to start there directly,
Copperpath selects that start policy and shows it in the plan. See **Advanced
settings** for the policy and routing time. Review the first alternative and
its copper plan, then choose **Approve placement and validate**. **Continue to
routing** opens routing in the same window. If the selected placement nets
have no retained routing or zones, Copperpath preselects those editable nets.
Where any of those nets has existing copper or zones, **Finish gaps** remains
the default. [Supported geometry and exact trial scope](current-placement-scope.md)

The installed check on the owned via example reached a fresh export in 92 seconds
and 22 operator-equivalent actions. On the unchanged licensed PushButtonLed
workflow, the first alternative and all three selected nets passed through
independent delivery in 2 min 45 s. That observation includes a pause from the
accessibility tool during export. The copper plan and findings still require
switching tabs. The recorded tests made no manual CAD corrections.
[Owned evidence](../evidence/product-workspace-through-via-001.json) · [Licensed workflow](../evidence/product-workspace-licensed-2427-001.json)
