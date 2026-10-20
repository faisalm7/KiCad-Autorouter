# Current platform and version qualification

This is a development build with the remaining gates in [REQUIREMENTS.md](../REQUIREMENTS.md). Vendor availability and this project's actual qualification are separate.

| Platform | Selected dependency | Project evidence and limit |
|---|---|---|
| macOS27.0.1, Apple silicon arm64 | Isolated official KiCad10.0.7, Freerouting2.5.0 | runtime050's seven Native workflows and invalid controls; ordinary and Improve GUI086 observations; fresh-folder ordinary GUI087 delivery. Qualified combinations only, no fullGUI/release or cleanOS/account/standalone claim. |
| Other macOS versions or Intel | KiCad vendor supplies macOS builds | No current project qualification. The vendor's macOS12+ requirement does not qualify this router on every such system. |
| Windows10/11 x64 | Official KiCad10.0.7 available | Windows011's finite isolation protocol failed owner1307/finalC4389. No Native routing/cancellation/export qualification. Equivalent safeguards are required; no unsandboxed fallback or third installer loop. |
| Windows arm64 | Official KiCad10.0.7 available | No project qualification or actual Native slice. |
| Linux | No selected qualified runtime | Unsupported by the current product evidence. A Linux run cannot qualify Windows. |

The tested Mac remains unchanged globally: KiCad10.0.0 is still installed; the10.0.7 app resides inside this checkout. CLI jobs use the copied Python3.11.9 environment; the actual GUI uses the selected KiCad app's bundled Python3.9/wx. Java25 is an existing pinned external dependency. Do not mix Python ABIs. [Install instructions](install-existing.md) describe the same-Mac dependency limits and the need to change into the installed runtime before invoking its CLI.

Each delivered candidate requires its own pinned Native refill, connectivity, complete schematic, original-rule, design-preservation and protected-copper evidence. Current ordinary routing admits whole/partial standard routing on all source copper with the default score. Other combinations remain refused or unqualified as described in the [settings contract](routing-preferences.md). Current, return-path, impedance, timing and manufacturing suitability are not established by DRC.

Graphical delivery uses a separate project and explicit acceptance intent. Save and close the exact source editors first. Live transactional application/undo remains unqualified. Current GUI evidence does not establish every schedule, the exact ordinary queued-open interval, every cancellation phase or independent-user usability. Native and GUI findings retain warnings and ignored checks.

Official release metadata was rechecked on October20,2026 UTC: the [KiCad macOS page](https://www.kicad.org/download/macos/) and [Windows page](https://www.kicad.org/download/windows/) list10.0.7; [Freerouting's latest release](https://github.com/freerouting/freerouting/releases/latest) resolves to2.5.0. This source check downloaded or installed no dependency and transferred no platform qualification. Vendor benchmark claims are not this project's results.

[Native milestone](../evidence/runtime050-native-milestone-002.json) · [Fresh installation](../evidence/runtime050-install-existing-001.json) · [Actual new-root GUI](../evidence/gui-runtime050-install087-delivery-001.json) · [Windows blocker](windows-portability.md)
