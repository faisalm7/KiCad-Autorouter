# Start or continue a KiCad design

Open **Copperpath.app** in Finder. Use **Start a new design** to create a project in KiCad Manager, **Continue an existing design…** to inspect a saved project, or **Open example** to try the supplied board. [First setup on Mac](docs/install-existing.md#first-setup-with-existing-mac-tools) · [Owned example](examples/owned-placement-routing/README.md)

For a blank design, create the project in KiCad Manager with **File → New
Project → Default**. Complete the schematic, footprint and outline setup in
KiCad, then open the complete saved project. [Design journeys](docs/design-lifecycle.md)

1. **Choose the saved project.** Select its `.kicad_pro` beside the matching PCB, schematic and rules. Copperpath inspects it and displays the board automatically. For a project open in KiCad, save and close the editors, use **File → Close Project** in KiCad Manager, and choose **Refresh inspection** in Copperpath.
2. **Choose what to change.** Select movable parts and draw an allowed area, or open **Request** to preview an explicit local instruction. Conversation stays beside the board. Review the moves and protected copper before you approve placement. Choose **Route saved board** to keep the saved placement, or **Continue to routing** after validating a placement. [Workspace controls](docs/saved-project-workspace.md)
3. **Preview, route and review.** **Finish gaps** uses KiCad to find the missing connections and preserves existing tracks. Preview checks your requested scope. After routing, **Review result** shows changed copper and findings. Choose **Accept result** or **Reject** after reviewing them. **Detailed report** offers full plots.
4. **Export a checked copy.** Fresh export reruns KiCad checks and saves a separate project. **Open checked export** verifies the current result before opening. To edit the copy and continue, save and close it in KiCad, then start a fresh inspection with that copy as the source.

**Cancel** requests cancellation of owned work, revokes positive state and retains evidence. Wait for cleanup before closing the assistant or starting another action. Changing the source, settings, target-region policy or reviewed pose also revokes earlier validation and handoff authority. A stale or cancelled result needs a fresh explicit workflow.

Keep an untouched complete copy before opening an older project in newer KiCad. Closing the editor can update project settings even without a board edit. If the original settings must be preserved byte for byte, select the untouched saved copy in the assistant. [Observed EEPROM workflow](docs/eeprom-finish-gaps-gui127.md).

Routing-scope acceptance, whole-project DRC cleanliness and electrical suitability are separate checks. Warnings and ignored checks remain visible. The optional checked move and native Undo use the supplied example on isolated KiCad 10.0.8. General live editing, Windows Native, independent installation and human PCB review remain open. [Checked move setup](docs/install-existing.md#try-the-checked-move-on-the-supplied-example) · [Requirements](REQUIREMENTS.md)
