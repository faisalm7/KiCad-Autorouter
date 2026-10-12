# Legacy zone capability controls (unexecuted draft)

Three new, owned fixtures derive from the complete `fixtures/smoke` project. No original file changes. The board remains unrouted; a successful historical zone predicate is not routing acceptance or DRC cleanliness.

| Case | Only zone-net edit | Required native witness | Historical violation |
|---|---|---|---|
| assigned_gnd | None; original board bytes | GND, positive code, GetPadCount=2 | false |
| assigned_padless | GND → OWNED_PADLESS | Distinct positive code, GetPadCount=0 | true |
| net_zero | Omit the zone net node | code=0, empty name, count not called | false |

Each generated project receives the identical literal `board.design_settings.rule_severities.zone_has_empty_net = error`. All other project fields and the original PRL bytes remain exact. The zone's UUID, polygon, layers and other fields, six pads, footprints, rules and edges remain unchanged. Net0 omission follows the pinned KiCad10 writer; it is not an assumed numeric/string alias.

The historical KiCad6 predicate is `netcode < 0 || (netcode > 0 && GetPadCount(netcode) == 0)`. Net0 is exempt. KiCad10 no longer registers this severity key. Storing it as error cannot establish native enforcement. The independent historical predicate and all actual native findings are reported separately, including opens, warnings, exclusions and any legacy-key findings. No result grants production support, format/dependency qualification, or routing acceptance.

## Reused execution path

The native worker supplies one narrow callback to `autorouter.floor_context.collect`. It constructs owned `CONNECTIVITY_DATA`, calls `Build` on the exact loaded board, and collects a fixed zone and complete six-pad census before and after DSN export. Native source/DSN/project hashes and before/after equality use the existing collector. There is no board save or Python `WriteDRCReport` call.

The controller reuses `FloorJob`, `Job.drc`, the sandbox runner, bounded inventories/readers, and the LiPo diagnostic's committed snapshot and guarded publication helpers. Every case receives two complete disposable project copies. `Job.drc(save=False)` runs the original-rule CLI refill/DRC and retains failure evidence without relaxing existing-PRL preservation. Exactly six sequential native processes are planned; no engine or PAW stage runs.

One existing experiment lock covers the batch. Shared limits are 30 s observed wall and parent-plus-waited-child CPU, 20 MiB total output, 256 KiB per log, and the existing 2 GiB process-group RSS ceiling. Remaining time is passed to every worker. Polling and finite hash samples are not atomic hostile-concurrency guarantees or hard aggregate CPU quotas. Source/core/tool/helper and raw stage bytes are captured before interpretation and resampled after metadata calls and publication. A failed or cancelled run retains all three case rows and available raw artifacts; it cannot publish complete/qualified success.

## Qualification still required

Installed wrapper declarations and pinned source establish constructor, `Build(BOARD)->bool`, and `GetPadCount(int)->unsigned int` signatures only. Their new direct-object lifetime/return behavior is unexecuted. Strict unexpected return types, code/name differences, census changes, export mutation, project bookkeeping changes, missing output, stale hashes or caps abort honestly. The native padless net must actually survive loading/export with zero pads; no expectation will be changed to make a run pass.

## Reproduction

Pure tests (no native imports/processes, valid from draft or promoted location):

```sh
python3 -B .runs/legacy-zone-controls-draft-001/test_controls.py
```

The six promotion files are `driver.py`, `worker.py`, `controls.py`, `test_controls.py`, `PROTOCOL.json`, and this README, under `experiments/legacy_zone_controls_v1/`. ROOT must review, promote, commit, push and verify the exact code/base source before any native execution. The ignored draft refuses execution.

Only afterward, ROOT can run once with a fresh output:

```sh
python3 -B experiments/legacy_zone_controls_v1/driver.py --run-native --output .runs/legacy-zone-controls-001
```

The initial pure failure from an unavailable S-expression quoting helper is preserved in `tests-001.log` with its source snapshot; the fixed implementation uses JSON quoting for these two fixed ASCII identifiers. Pure mocks demonstrate rejection behavior only.
