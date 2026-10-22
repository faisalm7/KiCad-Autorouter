# Current platform and version qualification

This is a development build with the remaining gates in [REQUIREMENTS.md](../REQUIREMENTS.md). Vendor availability and this project's actual qualification are separate.

| Platform | Selected dependency | Project evidence and limit |
|---|---|---|
| macOS27.0.1, Apple silicon arm64 | Isolated official KiCad10.0.7, Freerouting2.5.0 | runtime058 source `8f5e96b8…`, original manifest `4f923e05…`: eleven Native workflows/three invalid controls, IR and EEPROM Improve regressions; actual ordinary/high/Improve GUI092 roles and one fresh-root ordinary GUI093 delivery (manifest `19bdfe08…`). Both fresh-root CLI slices pass. Qualified combinations only, no fullGUI/release or cleanOS/account/standalone claim. |
| Other macOS versions or Intel | KiCad vendor supplies macOS builds | No current project qualification. The vendor's macOS12+ requirement does not qualify this router on every such system. |
| Windows10/11 x64 | Official KiCad10.0.7 available | Windows011's finite isolation protocol failed owner1307/finalC4389. No Native routing/cancellation/export qualification. Equivalent safeguards are required; no unsandboxed fallback or third installer loop. |
| Windows arm64 | Official KiCad10.0.7 available | No project qualification or actual Native slice. |
| Linux | No selected qualified runtime | Unsupported by the current product evidence. A Linux run cannot qualify Windows. |

The tested Mac remains unchanged globally: KiCad10.0.0 is still installed; the10.0.7 app resides inside this checkout. CLI jobs use the copied Python3.11.9 environment; the actual GUI uses the selected KiCad app's bundled Python3.9/wx. Java25 is an existing pinned external dependency. Do not mix Python ABIs. [Install instructions](install-existing.md) describe the same-Mac dependency limits and the need to change into the installed runtime before invoking its CLI.

Each delivered candidate requires its own pinned Native refill, connectivity, complete schematic, original-rule, design-preservation and protected-copper evidence. Current058 ordinary admits whole/partial2/4Cu standard/both/native/source_all with default `null` or explicit `via_high`; source constraints/protection remain unchanged. Improve is separately narrow2Cu/flat/single-Default whole/tuned/default-score. Other combinations remain refused or unqualified as described in the [settings contract](routing-preferences.md). Current, return-path, impedance, timing and manufacturing suitability are not established by DRC.

Graphical delivery uses a separate project and explicit acceptance intent. Save and close the exact source editors first. Live transactional application/undo remains unqualified. Current GUI evidence does not establish every schedule, the exact ordinary queued-open interval, every cancellation phase or independent-user usability. Native and GUI findings retain warnings and ignored checks.

Official release metadata was rechecked on October20,2026 UTC: the [KiCad macOS page](https://www.kicad.org/download/macos/) and [Windows page](https://www.kicad.org/download/windows/) list10.0.7; [Freerouting's latest release](https://github.com/freerouting/freerouting/releases/latest) resolves to2.5.0. This source check downloaded or installed no dependency and transferred no platform qualification. Vendor benchmark claims are not this project's results.

[Current058 Native](../evidence/runtime058-native-milestone-001.json) · [Fresh CLI installation](../evidence/runtime058-install-existing-001.json) · [GUI092 observations](../evidence/gui-runtime058-092-observations-001.json) · [Actual new-root GUI093](../evidence/gui-runtime058-install093-observations-002.json) · [Windows blocker](windows-portability.md). High/Improve/installed GUI proof bytes remain local; observation metadata is not their backup. Historical [057 Native](../evidence/runtime057-native-milestone-001.json), [installation](../evidence/runtime057-install-existing-001.json) and [GUI091](../evidence/gui-runtime057-install091-delivery-001.json) retain their own build scope.

The091 planned post-reader control aborted before mutation; no actual queued-timing/guard pass. Current092/093 pre-action and editor-stale refusals do not establish that exact queued interval. The STOP method stays stopped. Full restoration remains [capacity-blocked](../evidence/backups/runtime041-receipt-capacity-001.json); newer raw050–058/GUI/Cheapino stays owner-Mac-only/outside010. Licensed breadth, untouched confirmation, engineer cleanup, physical/electrical and full release gates remain open.
