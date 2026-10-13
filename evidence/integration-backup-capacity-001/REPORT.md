# Integration, installation and restoration capacity admission

Recommend two finite admission changes for the next milestone: **140,000 files/directories and 48 MiB per receipt**. Keep the existing **4 GiB byte ceiling, 128 MiB total chain-receipt ceiling, 16-node chain, all three scopes, and every secret/path/archive/restoration guard**. No exclusion, deletion or backup redesign is needed. No tracked or global cap was changed by this read-only task.

The existing shared backup inventory passed with its original constants in 39.093 seconds. Its cutoff was October 13, 2026, 13:06:05–13:06:44 UTC. The actual file count remained below 120,000, so no in-memory elevation was needed.

| Exact shared-inventory scope | Files | Directories | File bytes |
|---|---:|---:|---:|
| .runs | 119,585 | 29,141 | 3,426,373,474 |
| .data | 359 | 62 | 39,571,920 |
| .local-reference | 6 | 1 | 62,155 |
| Total | 119,950 | 29,204 | 3,466,007,549 |

The retained installation009 complete tree has 12,838 files, 1,832 directories and 300,484,533 bytes. Its checkout alone has 12,798 files, 1,813 directories and 296,816,884 bytes. Forecasting one additional complete installation-shaped tree preserves its logs, native artifacts and checkout. It yields 132,788 files, 31,036 directories and 3,766,492,082 bytes. This is shape arithmetic, not an actual new installation. Changed source/evidence and installation behavior can increase it.

| Receipt serialization forecast | Bytes | Existing 32 MiB admission |
|---|---:|---|
| Current full | 30,908,154 | Fits at cutoff |
| Current incremental from latest | 34,483,456 | Exceeds |
| After one installation-shaped addition, full | 34,413,340 | Exceeds |
| After one installation-shaped addition, incremental from current | 40,665,765 | Exceeds |

The latest actual receipt is 29,878,286 bytes, schema1, with 115,829 files / 3,151,968,106 input bytes. Its chain is one full receipt. Existing metadata structure and complete actual inventories determine the forecasts; future artifact sizes, hashes, time/head fields and base-verification references introduce small unmeasured differences. No archive was created.

At the forecast, the recommended file cap leaves 7,212 files and the unchanged byte ceiling leaves 528,475,214 bytes of headroom. A 48 MiB receipt cap leaves 9,665,883 bytes over the projected incremental receipt. A 40 MiB alternative leaves only 1,277,275 bytes; that margin is too narrow for an installation from a newer source/evidence tree. The recommended 48 MiB remains finite. A current full plus the projected installation incremental uses about 71.6 MB of receipt bytes, below the unchanged 128 MiB chain cap; more future checkpoints must still pass the actual chain guard.

The filesystem reported 406,685,786,112 free bytes. This is not a reservation or a prediction of compressed archive/Git bundle size. Actual backup, installation and full restoration remain required. Use the established source checkpoint and backup workflow, keep all earlier evidence, run targeted admission-boundary controls, then complete the scheduled full restoration after the cap change and major integration. Do not infer restoration success from this forecast.

Concurrent .runs writers were possible. The shared per-file immutability/secret/path guards passed, but no second complete inventory equality or Git-state certification ran. This report is a cutoff forecast, **not a certified snapshot, backup or restored checkpoint**. The original stat pre-scan and later hash inventory differ by 31 files because the working population grew. No Git, native/JVM, network, archive or restoration command ran.

Only aggregate observations and a canonical inventory hash are published here; no private reference contents or full inventory paths are exported. `facts.json` stores exact counts, serialization assumptions, prior receipt hashes and the later checkout stat observation. `forecast-001.log` is the initial forecast; facts.json additionally records the stat follow-up and recommendation. Update stale helper comments/error labels to the actual caps when ROOT changes the two constants.
