# Project-specific KiCad configuration on this Mac

Checked October 9, 2026, America/Los_Angeles. The installed KiCad CLI identified by the lead as 10.0.0 successfully ran real native DRC on a copied synthetic smoke board using newly created project-specific configuration, cache, and documents directories. No personal preference files were copied into the test configuration. Empty settings work; inventing or copying a populated `kicad_common.json` is unnecessary for this tested command.

The original lead run `.runs/smoke-stock-001/source-drc-process.json` recorded exit `-11` and no report/log content. The exact cause of that earlier crash was not isolated. The working probes changed several path conditions together, so it would be unsupported to attribute the crash specifically to `KICAD_CONFIG_HOME`, or to claim this resolves every native startup failure.

## Working recipe

Provide absolute paths for all three official KiCad environment variables to each child process:

| Variable | Base path inside this task | Versioned directory KiCad uses |
| --- | --- | --- |
| `KICAD_CONFIG_HOME` | `<run>/kicad-config` | `<run>/kicad-config/10.0` |
| `KICAD_CACHE_HOME` | `<run>/kicad-cache` | `<run>/kicad-cache/kicad/10.0` |
| `KICAD_DOCUMENTS_HOME` | `<run>/kicad-documents` | `<run>/kicad-documents/kicad/10.0` |

Create these directories under the fresh run before launching the worker. Pass the three variables in a copied child-process environment; do not modify global environment or the user's home variable. Keep original projects immutable and run DRC against a copied board/project. All probes used this installed executable:

`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`

Its locally measured SHA-256 is `998aed348399000335b0e29edf747daa18819f2ac417bac066f4216fdc5d90d1`.

The exercised command shape was:

```text
kicad-cli pcb drc --format json --severity-all --all-track-errors
  --refill-zones --exit-code-violations --output <run>/drc.json
  <run>/smoke.kicad_pcb
```

This recipe isolates the documented KiCad preference/cache/document locations. It is not an OS-level filesystem or network sandbox and does not prove every library read or platform write is confined. The investigator did not enumerate or read personal KiCad settings. Installed application resources and public upstream source were read for diagnosis.

## Actual probes and interpretation

Six bounded probes ran sequentially using only scratch projects under `.runs/config-research/`. Each had a new cache and documents base and copied `fixtures/smoke/smoke.kicad_pcb` plus `.kicad_pro`. The subprocess timeout was 15 seconds; every run completed in approximately 0.75–0.77 seconds. No routing engine benchmark was run during this investigation.

| Case | Config content before launch | Return code | Parsed report |
| --- | --- | ---: | --- |
| `empty` | Empty `config/10.0/` | 5 | 2 unconnected items, 0 violations |
| `common-empty` | `config/10.0/kicad_common.json` containing `{}` | 5 | 2 unconnected items, 0 violations |
| `common-pcb-empty` | Above plus empty `pcbnew.json` | 5 | 2 unconnected items, 0 violations |
| `common-pcb-tables` | Above plus empty symbol/footprint library tables | 5 | 2 unconnected items, 0 violations |
| `all-isolated-empty-base` | Existing empty config base, no `10.0/` | 5 | 2 unconnected items, 0 violations |
| `all-isolated-no-base` | Config base did not yet exist | 5 | 2 unconnected items, 0 violations |

Exit 5 in these tests is an expected negative routing result under `--exit-code-violations`, not a startup crash or a clean board. KiCad produced nonempty native JSON and reported the smoke board's two required unconnected items. None of these tests proves an accepted routed candidate. The empty/missing-base cases show that KiCad created versioned settings directories successfully in this configuration; explicit creation remains useful for early permission checks.

Raw commands, child-only environment overrides, timings, logs and native reports are retained under each named scratch directory. `.runs/config-research/results.json` covers the first four probes; `followup-results.json` covers the last two. Every case has `result.json`, `process.log`, and `drc.json`. These ignored raw files are on-Mac evidence until the lead's evidence archive preserves them; this tracked document alone is not their backup.

## Primary-source explanation

Inspected upstream tag `10.0.0`, tag object `b0e9d3b0656e3770d11324b15e09b097f7fc33da`, source commit `0feeca2a807f428ad2b3fa7c1e39625cb769f02c`:

- [`common/paths.cpp`](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/common/paths.cpp): `CalculateUserSettingsPath` honors `KICAD_CONFIG_HOME` and appends the major/minor version. The cache/documents helpers append `kicad` plus the version to their override bases. `EnsureUserPathsExist` creates the user paths used at startup.
- [`common/settings/settings_manager.cpp`](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/common/settings/settings_manager.cpp): the settings manager creates the settings directory if missing and permits missing common settings while using defaults. This agrees with the successful empty-settings native probes.
- [`common/pgm_base.cpp`](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/common/pgm_base.cpp): initialization ensures user paths, initializes monitoring, initializes the settings manager, then loads common settings. Configuring only the preference base therefore does not isolate every startup path.
- [`common/app_monitor.cpp`](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/common/app_monitor.cpp): the local Sentry opt-in marker lives in the user cache directory. Giving each worker a fresh project-specific cache prevents inheriting a personal cache opt-in marker. The source also considers platform policy; no OS network-isolation claim follows from this source inspection.

No application upgrade, library replacement, personal-config reset, global preference change, security-control change, unrelated process termination, or upstream contact was performed. The lead can use the verified three-variable recipe immediately while preserving the earlier crash as an unresolved failure receipt.
