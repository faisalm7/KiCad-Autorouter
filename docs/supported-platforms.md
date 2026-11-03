# Platform and version qualification

Support is limited to exact tested scope. [STATUS](../STATUS.md) identifies the current artifact and active qualification; [release gates](experimental-rc.md) remain open.

| Platform | Dependency | Actual evidence and limit |
|---|---|---|
| macOS27.0.1, Apple silicon arm64 | Isolated official KiCad10.0.7; Freerouting2.5.0 | [072 headless Native/invalid/class milestone](../evidence/runtime072-installed-native-milestone-001.json), [finite GUI103 observations](../evidence/gui-runtime070-103-qualification-001.json) and [large delivery regression](../evidence/runtime070-single-delivery-001.json). Changed072 has fresh full integration/install/doctor; its Native/invalid/class cohort passes and STM32 delivery failed. No fullGUI/release/cleanOS/account/standalone claim. |
| Same Mac | Official stable KiCad10.0.8 | Publisher release checked November3; **unqualified**. No download, upgrade or app modification performed. |
| Other macOS versions or Intel | No qualified combination | No current Native/GUI qualification. |
| Standard GitHub Windows2022 x64 runner | Isolation controls only | [Windows015](../evidence/windows015-lowbox-mutation-actual001.json) compiled/loaded, then failed at contained WFP entry. Equivalent object/handle/network/crash/cancellation and persistent cleanup guarantees are unproved. No Native/JVM/installer/product admission. |
| Windows10/11 or arm64 | No qualified product | Equivalent safeguards precede actual export/routing/import/refill/validation/cancel/export. No unsandboxed fallback or installer retry. |
| Linux | No qualified product | A Linux substitute cannot qualify Windows. |

The global KiCad10.0.0 binary remains unchanged; tested10.0.7 is isolated inside the checkout. CLI installations use copied no-pip Python3.11.9; GUI imports use that KiCad app's bundled Python3.9.13/wx. Java/native tools are pinned external dependencies. Same Mac/account/dependencies are not an independent clean installation. A shutdown observation launched a normal-profile owned KiCad instance, which was specifically terminated; normal startup preference writes were not measured or claimed unchanged.

Ordinary Route admits qualified whole/partial two/four-copper tasks, corrected-standard/both/native/all source layers and default or explicit high via cost. Whole routing preserves locked copper; Finish gaps preserves all existing copper. Selected nets and explicit layer subsets remain closed on10.0.7. Improve is narrower and requires a verified incumbent and40-second internal reserve within its whole budget. Cancellation, stale inputs and invalid constraints never authorize fallback. Source-specific guards and Native checks remain mandatory. [Settings](routing-preferences.md).

Graphical delivery launches from KiCad into a separate project with explicit review intent. Saved source editors must be closed. Exact queued-open timing, every cancellation phase, live application/undo and advanced electrical fitness remain unqualified. Use Microsoft Edge for qualification previews.

Broad completion gains, independent installation, engineer cleanup/review, physical/electrical tests and full recovery remain unmet. [SOURCE_LEDGER](../SOURCE_LEDGER.md) records vendor checks; publisher release status is not project qualification.
