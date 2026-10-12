# Protected disposable DRC input (unexecuted diagnostic)

This finite hypothesis preserves complete input bytes by denying worker writes, rather than accepting or undoing PRL migration. It does not qualify production, legacy-format interpretation, `zone_has_empty_net` enforcement, dependencies, routing, or physical suitability.

The fixed sequence is: (1) write-denial canary, (2) known accepted owned fixture plus the exact previously tested synthetic legacy PRL, (3) the same project with only its required via removed, (4) one new protected PAW DRC. PAW's earlier export/DRC and failure remain immutable. There is no export, engine, board save, deletion of original PRL, PRL exclusion, permission-bit workaround, restoration or normalization. Only owned copies receive the generated legacy PRL/removal recipe.

The controller reuses `FloorJob`, unchanged `Job.drc(save=False)`, the shared runner, original-project guard, strict parser/process check, existing missing-via recipe/predicate, and LiPo snapshot/publication helpers. A narrow step override prepends one fixed sandbox profile: network denied; `file-write*` denied on both the literal canonical input directory and its subpath. Actual reports/logs and isolated config/cache/temp are outside that protected directory. The default production path is unchanged.

The canary reads no user files and attempts overwrite, append, truncate, create, mkdir, unlink, rename, atomic replacement, chmod, and input-directory rename against owned sentinel files. Every operation must fail with EPERM/EACCES; a missing-file failure or success rejects. Writing the external result/replacement source must succeed. Complete directory inventories must remain identical. The chmod attempt tests a denial; no controller chmod is used.

The positive must retain zero native findings and its exact seven effective ignored checks (five explicit original settings). The negative requires actual unexcluded error rows in `unconnected_items` naming the exact separated route UUID pair; unrelated opens, blocking errors, exclusions or ignored-key changes reject. All warnings remain recorded. PAW requires the full parsed report to equal the retained baseline: currently 0 opens/errors, 17 library warnings, 0 exclusions and eight effective ignored checks (five explicit settings). Any new difference stays a failed hypothesis, not a waived result.

One lock and one shared 30-second observed wall/parent-plus-waited-child CPU budget cover all preparation/checking and four sequential workers. Output is capped at 20 MiB, per log 256 KiB, group RSS 2 GiB. Copy capacity is reserved before workers. Original accepted receipt is checked centrally before use; acquisition and all source/failed-run inventories are pinned. Runtime/helper snapshots must be committed and exact. Raw stage files and actual input inventories freeze before parsing; complete final source/stage checks follow metadata and output scans. Interrupted/stale/capped publication preserves invalidated records and cannot publish completed success. Polling and finite consistency samples are not atomic authentication or hard aggregate CPU quotas.

Actual sandbox behavior and KiCad completion under denied migration saves are untested. KiCad may reject, emit an incomplete report, or take a different initialization path: every such outcome is retained. Blocking persistence does not prove that legacy settings are interpreted identically in memory.

Pure tests, with no sandbox/native/Git/network execution:

```sh
python3 -B .runs/drc-input-protection-draft-001/test_driver.py
```

Promote the five files `driver.py`, `canary.py`, `test_driver.py`, `PROTOCOL.json`, `README.md` to `experiments/drc_input_protection_v1/` only after review. ROOT must checkpoint/push/read back before its sole actual invocation, with a fresh output:

```sh
python3 -B experiments/drc_input_protection_v1/driver.py --run-native --output .runs/drc-input-protection-001
```

The ignored draft refuses actual execution. Pure mocks are not native qualification. Original complete projects are copied only at actual execution; this draft contains source and hash inventories, not copied board/media payloads.
