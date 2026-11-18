# Owned placement-and-routing example

This small GPL-3.0-or-later development board demonstrates the ordinary controls without an AI account. It is a software-test design, not an electrically reviewed product. Its primary PCB, project and complete schematic bytes match the recorded [live application task](../../evidence/copilot102-owned-live-delivery-001.json).

1. Open `source/owned-placement-ordinary.kicad_pro` through your installed isolated KiCad launcher, open PCB Editor and click the Autorouter toolbar icon.
2. Save and close the PCB/schematic editors, then choose **File → Close Project** in KiCad manager. In the assistant, choose the exact saved PCB and a separate output folder.
3. Open **Place components…**, inspect the project and use **Load settings…** to select this folder’s `settings.json`. Review J1/J2 as movable, J3–J6 fixed, the 14–22 × 8–13 mm area, and the explicit affected-net rebuild policy. KEEP and locked/unrelated copper remain protected. The outside-area initializer is explicitly experimental.
4. Choose **Find alternatives**, inspect the diagram and findings, and acknowledge the exact moves and copper plan. The current build returns to **Board** and enables **Validate placement** once the preview renders. On older builds, select **Board** if needed. Validate and continue to the guarded routing settings.
5. Preview, route, create the review and inspect every finding/layer. Explicitly accept or reject. **Fresh export** runs new checks and creates a separate project. The inherited 0.7 mm silkscreen-text warning against a 0.8 mm minimum remains; success is not whole-project DRC cleanliness or electrical approval.

For the optional, separately consented copilot interface, select the same visible controls and ask:

> Keep the fixed components and protected trace unchanged, place these two components inside this region, then route their approved connections.

Review its visible plan before using it to find alternatives. Model/data/cost consent and engineering approvals are separate; no model endpoint, account or spending permission is supplied by this example. Do not reuse an old receipt as approval.

The recorded run also retained optional local UI settings and a KiCad-generated backup. Those are omitted from this portable example and remain in the local evidence. Its complete file-set identity must therefore be captured afresh after opening/saving. No new Native run or model result is claimed merely from publishing these same primary design bytes. This family is exposed development data, never an untouched confirmation case.
