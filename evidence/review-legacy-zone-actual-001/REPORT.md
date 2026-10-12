# Legacy-zone native controls001 — independent readback

**Passed as a bounded observation experiment.** The canonical receipt, all six native stages, same-load observations, original/derived inputs, runtime snapshots, installed tool/wrapper pins and final raw reports verify at `8f9ffeb68ab1e250163ae26214c8d7fd6894adf6`. The full **107-file / 872,305-byte** run and original three-file smoke project remain unchanged across this audit. No native, JVM, network or Git command ran during the audit.

| Owned case | Actual code / GetPadCount | Historical predicate | Native opens / blocking / warnings / exclusions |
|---|---|---|---|
| Assigned GND | 3 / 2 | Pass | 2 / 0 / 0 / 0 |
| Assigned OWNED_PADLESS | 4 / 0 | Reject | 3 / 0 / 1 / 0 |
| Unassigned | 0 / not queried (`None`) | Exempt | 3 / 0 / 1 / 0 |

All three raw reports contain **no `zone_has_empty_net` finding**. Both negative/unassigned reports retain an `isolated_copper` warning. All missing-connection items and original effective ignored-check records are retained in audit.json and the raw DRC. Each DRC exit 5 is consistent with its findings. These are unrouted cases, never accepted routing candidates.

The exact derived fixtures reproduce from the shared recipe. The positive board keeps original bytes; the others change only the zone net node, with reversible AST proof. All three generated projects add the explicitly declared legacy severity `error` to the minimal owned project; the original fixture project is untouched. Existing PRL bytes, complete observation copies and DRC copies remain exact. Nonsaving DRC uses `--refill-zones` in memory, without saved board/fill mutation.

The worker successfully constructed direct `CONNECTIVITY_DATA`, observed `Build(BOARD) == true`, and queried `GetPadCount` for the two positive native net codes. Both pre-export and post-export calls use the same loaded BOARD as the shared context/DSN exporter. The exact six pad UUID/net/position records, zone UUID/B.Cu/outline and native net identities agree with source and context. Installed wrapper overload declarations and pinned `_pcbnew.so` bytes match. The source registry/provider and wrapper caches were hash-rechecked without acquisition or execution.

**A pad count is not physical contact.** Pinned KiCad6 provider lines120–143 checks negative net codes or assigned nets with no pads; code0 is exempt. `CONNECTIVITY_DATA::GetPadCount` counts valid PCB_PAD_T items on the net (KiCad6 lines577–592; pinned KiCad10 lines727–743). It tests neither zone overlap nor pad-to-zone connectivity. The native DRC observations remain separate. This finite result supports those direct API calls for the owned ordinary-pad/one-zone scenes; it does not qualify PAW's F&B.Cu zone, old format/PRL semantics, dependency closure, negative native net codes, arbitrary zone types, or production admission. All five support/acceptance flags remain false.

Stored accounting is **5.971280 s wall / 3.930279 s CPU** before final publication. The bound outer wrapper records **6.222554 s wall / 4.126042 s waited-child CPU**, including the later work. Both remain within the shared30-second caps; output stays below20MiB. Six sequential sandboxed processes have complete cleanup and untruncated logs; the2GiB process-group guard is polling, not an OS quota.

The first reviewer run used an incorrect literal Python `Build(self, aBoard)` assertion. The actual SWIG wrapper uses `Build(self, *args)` with the recorded BOARD overload in its docstring. The initial source/log/failure are preserved; the corrected actual declaration assertion and all shared readbacks pass. This was an audit assertion error, not a native failure.

Reproduction: `python3 -B .runs/review-legacy-zone-actual-001/audit.py` (offline readback only; use a new evidence directory for later work to preserve this frozen record). Compact selection contains no copied boards, native binaries or cached third-party source payloads. ROOT owns checkpoint/backup; the full originals remain on this Mac.
