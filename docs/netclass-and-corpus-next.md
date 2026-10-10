# Native netclass support and the next development corpus

Research and a bounded native capability probe on this Mac, October 10, 2026.
The second `interf_u` probe passed after a native Python binding failure in the
first attempt. A third passed after correcting monitor CPU accounting. All
runs are retained. No routing solver was run, pipeline
eligibility was not broadened, original files were not modified, and no new
board dataset was acquired. These are development findings, not held-out results
or additional independent-family claims.

## Recommended next capability test

Start with `interf_u`. Its existing exclusion is netclass qualification; the
current `complex_hierarchy` also has an unqualified `zone_has_empty_net` rule
severity and is not admitted by a netclass result alone. Read-only inspection of
their immutable `.kicad_pro` files gives the following millimetre values:

| Project / configured class | Track width | Clearance | Via diameter / drill | Configured pattern strings |
|---|---:|---:|---:|---|
| interf_u / Default | 0.4 | 0.254 | 1.4 / 0.6 | Fallback |
| interf_u / Power | 0.5 | 0.254 | 1.6 / 0.6 | `GND`, `VCC` |
| complex_hierarchy / Default | 0.4 | 0.3 | 1.651 / 0.6 | Fallback |
| complex_hierarchy / power | 0.6 | 0.3 | 1.651 / 0.6 | `-VAA`, `/12Vext`, `GND`, `HT`, `VCC` |

Both projects have complete configured values, one nondefault class and no
explicit label-assignment map in the JSON. The table lists configuration, not
independently proven resolved membership. Preserve all original files and let
KiCad resolve membership; do not flatten to the Default width or substitute a
home-grown matcher.

### What the pinned KiCad implementation does

The installed 10.0.0 source revision is
`0feeca2a807f428ad2b3fa7c1e39625cb769f02c`. Its
[DSN exporter](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/specctra_import_export/specctra_export.cpp#L105)
calls native netclass synchronization before conversion. It collects in-use
effective classes and exports each class's member net names, width, clearance
and via selection. Default is named `kicad_default` in DSN. Distances are
converted from native nanometres to micrometres; class dimensions use six
significant digits. The via identifier includes diameter and drill, while its
padstack contains copper circles for the layers. An export audit must inspect
both the selected identifier and its actual padstack, and fail if decimal
rounding prevents exact representation. This is already implemented native
export behavior, not a proposed adapter rewrite.

[BOARD synchronization](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/board.cpp#L2692)
returns early without an attached project. A native report containing only
Default can therefore be a project-loading failure, not evidence that the
patterns are irrelevant. The probe requires observed nondefault membership and
checks resolved dimensions against original configured class values.

[NET_SETTINGS](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/common/project/net_settings.cpp#L683)
combines explicit and pattern assignments, handles priority, and fills missing
values from Default. Its call named `StartsWith` must not be mistaken for simple
prefix matching: [the CTX_NETCLASS matchers](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/common/eda_pattern_match.cpp#L413)
are anchored regular-expression and wildcard matchers. The probe evaluates no
pattern strings. Composite, implicit, incomplete or conflicting classes remain
outside its narrow qualification.

The installed `pcbnew.py` wrapper exposes
`BOARD.SynchronizeNetsAndNetClasses`, `GetNetsByName`,
`NETINFO_ITEM.GetNetClass` / `GetNetClassSlow`, and the name/width/clearance/via getters. The official
[NETINFO_ITEM API](https://docs.kicad.org/doxygen-python-10.0/classpcbnew_1_1NETINFO__ITEM.html)
and [NETCLASS API](https://docs.kicad.org/doxygen-python-10.0/classpcbnew_1_1NETCLASS.html)
also document these calls. Actual run 001 found that `GetNetClass()` returns a
raw `SwigPyObject` without `GetName` in this installed binding. Using the
documented shared-pointer accessor `GetNetClassSlow()` fixed that API mismatch
in run 002; native membership resolution was retained.

KiCad's [10.0 netclass documentation](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#net-classes)
distinguishes class routing values from board minimum constraints and custom
rules. A clean native DRC report alone must not be treated as proof that a
router used the intended class track width. Preserve the class targets and
compare imported route/via dimensions against the recorded native mapping as
well as running native DRC before admitting a solver result. This capability
probe does not perform that solver/import test.

### Bounded probe and actual results

Run only when the lead grants the sequential native slot:

```sh
python3 scripts/netclass_probe.py --project interf_u --output .runs/netclass-interf-004
```

The output path must be new and a direct child of `.runs`. The script uses a
60-second native job deadline, the existing bounded runner, pinned tool hashes,
network denial, and project-local config/cache/documents directories. It:

1. Verifies the complete source inventory against `data/sources.json`, including
   the original project/rules and notices, then makes snapshot and native-input
   copies. It retains code and source hashes.
2. Loads only the native-input copy, synchronizes classes, records each net's
   native effective name and integer dimensions, and exports DSN without saving
   the board. It compares copper-terminal net inventories and explicit DSN
   membership, class widths/clearances, and through-via IDs/shapes against native
   values. Original board floors remain enforced by the audit.
3. Saves separate DSN counterexamples with one nondefault width and clearance
   halved. Both must fail the mapping audit. They are diagnostic export copies,
   not new native boards, DRC controls or routed outputs.
4. Requires source, snapshot and native-input inventories to remain unchanged.
   `result.json` contains the raw native report/DSN bindings, process receipt,
   counterexample results, wall/CPU accounting and explicit limitations.

After a passing probe, the lead still needs native routing, original-rule DRC,
imported per-net dimension checks and adversarial mapping controls before
changing eligibility. A failed probe is retained and diagnosed. The analogous
`--project complex_hierarchy` invocation can follow separately; its severity and
electrical-scope gates remain independent.

The lead granted the native slot after the quality batch. Actual commands used
`.runs/netclass-interf-001`, `002`, and `003`; those existing directories must
not be reused. Attempt 001 exited with the binding error described above. Its
source and immutable snapshot hashes remained unchanged. Attempt 002's mapping
and preservation results passed, but its recorded 0.655216 CPU seconds omitted
the separate monitor CPU and must not be used as complete compute accounting.
Its immutable receipt remains unchanged. The script was corrected to add the
runner's `monitor_cpu_seconds` to parent and native-worker CPU.

Attempt 003 repeated the passing mapping and controls in 0.871110 seconds wall
time and 0.711736 total CPU seconds: 0.141571 parent, 0.516633 native worker and
0.053532 monitor. Native KiCad 10.0.0 ran successfully, with no solver or DRC.

| Actual native class | Nets | Width mm | Clearance mm | Through-via diameter / drill mm |
|---|---:|---:|---:|---:|
| Default / DSN `kicad_default` | 171 | 0.4 | 0.254 | 1.4 / 0.6 |
| Power | 2 (`GND`, `VCC`) | 0.5 | 0.254 | 1.6 / 0.6 |

All 173 native nets matched the exported copper-terminal net inventory and
explicit DSN class membership. GND had 42 copper pads and VCC had 23. Original
project class dimensions, board floors, DSN rules, via IDs and copper-circle
shapes agreed. The separate Power-width counterexample (0.25 mm) and clearance
counterexample (0.127 mm) both failed with `DSN class differs from native mapping
for GND`. These are mapping-audit rejections, not native DRC counterexamples.

The complete 25-file original inventory, immutable snapshot, native-input copy,
original project file and unmodified exported DSN all passed preservation
checks. No custom `.kicad_dru` file was present. The recorded pipeline hash and
saved code were inspected after the probe; this remains an isolated capability
measurement, not a frozen comparative routing experiment.

| Binding | SHA-256 |
|---|---|
| `.runs/netclass-interf-003/result.json` | `93d10697735d2ad9845093f86ef6b7bfea051a583a228d1dcbdba78aa8a9c39f` |
| `native-netclasses.json` | `36f132fe2f9974c9f91b6552ddc53add5bcb64b3e78c102d03bc391de0bf8604` |
| `native.dsn` | `cde7d766197a0f344dd08d953f279858a96edb7ab0981f4bafca8fbbc0f6ad41` |
| Original `interf_u.kicad_pro` | `b9908a96e6113e6e51f488482108dc87aa5d9bcd838f9e3345c85e0db09bffa9` |
| Executed probe script | `698ffa1918534f5fff3533f7dfd24726a18365a2f45a54f651691478f76fe938` |
| Recorded `autorouter/pipeline.py` | `11ad7346bac7d7781627e206684bf861847d19f6203fa74965b92ae8e7462976` |

Attempt 002's retained result SHA-256 is
`4897707f5a0fcb954cc76b749f776152f831bf799e3e233dff2e09322e981694`.
The lead changed the pipeline implementation between attempts; this is recorded,
not presented as a frozen timing comparison. DSN bytes also include output-path
metadata, so each native export has its own file hash.

The full receipt contains every source hash and raw process records. These raw
artifacts are on this Mac until included in a verified backup. This document
does not change the six-board coverage receipt or admit `interf_u` to routing.

## Complete official-demo research screen

The GitHub tree API for source commit
`69cafb907ebc09e7722a2a464b1d466fc2e3608d` returned `truncated: false`.
It contains **16 demo directories with 19 native board files**. The acquired
population remains the original five directories / six boards; this larger
metadata screen is not silently counted as acquired or native-tested data.
All additional candidates, including likely failures and unsupported electrical
scopes, are listed here to keep the next selection visible.

The pinned [root license statement](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/LICENSE.README)
assigns `demos/*` to CC-BY-SA 4.0. This does not justify ignoring a conflicting
directory or embedded notice. Every new acquisition still needs a file-level
notice audit and exact hashes. Directory byte totals below include all original
files, not added copies of root notices.

| Demo directory | Native boards | Complete-directory bytes | Current disposition |
|---|---:|---:|---|
| sonde xilinx | 1 | 668,217 | Acquired development; narrow routing evidence |
| pic_programmer | 1 | 1,349,048 | Acquired; current preflight unsupported |
| complex_hierarchy | 1 | 1,148,108 | Acquired; current preflight unsupported |
| interf_u | 1 | 1,473,421 | Acquired; first netclass capability target |
| multichannel | 2 | 4,543,845 | Acquired; one provisional family, both unsupported |
| kit-dev-coldfire-xilinx_5213 | 1 | 4,366,787 | Best small additional complete-project lead; netclass/electrical-scope qualification pending |
| ecc83 | 2 | 847,109 | Small, but valve/high-voltage scope requires explicit exclusion or separate qualified scope; keep variants together |
| microwave | 1 | 120,667 | Small RF demo; outside current electrical qualification |
| openair-max | 1 | 9,613,871 | Own CC-BY-SA 4.0 notice; next bounded complete-project lead after metadata/scope audit |
| stickhub | 1 | 2,937,922 | Conflicting restrictive directory license; defer redistribution/training acquisition |
| video | 1 | 8,266,208 | Fits a separate 10 MiB batch; high-speed/scope and notices need audit |
| cm5_minima | 1 | 50,364,333 | Over current per-batch ceiling; local notices and high-speed scope pending |
| jetson-agx-thor-baseboard | 1 | 96,843,810 | Over ceiling; local notices and high-speed scope pending |
| royalblue54L_feather | 2 | 12,990,976 | Over ceiling; own CERN-OHL-P v2 notice; RF/antenna variants require scope audit |
| tiny_tapeout | 1 | 31,488,420 | Over ceiling; local notices/scope pending |
| vme-wren | 1 | 126,031,593 | Over ceiling; notices/scope pending |

### Rights exceptions and bounded acquisition recommendation

* [StickHub LICENSE.md](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/stickhub/LICENSE.md)
  explicitly uses CC-BY-NC-SA 4.0 with conditional commercial-use exceptions.
  Its [README](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/stickhub/README.md)
  attributes Stefan Hamminga and points to that notice. This conflicts with the
  permissive interpretation of the root demo statement. Do not claim unrestricted
  CC-BY-SA rights for it; defer it rather than assuming an exemption applies.
* [Openair-max LICENSE.txt](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/openair-max/LICENSE.txt)
  is CC-BY-SA 4.0, consistent with the root statement. Its 11-file complete
  project fits a separate 10 MiB batch including root notices. Other file notices
  and electrical scope still need inspection before acquisition is marked audited.
* [RoyalBlue54L LICENSE](https://github.com/KiCad/kicad-source-mirror/blob/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/royalblue54L_feather/LICENSE)
  is CERN-OHL-P v2. Retain that project-specific notice; do not replace it with
  a root-only attribution. The whole directory exceeds the present batch cap.

Acquire [the complete ColdFire/Xilinx project](https://github.com/KiCad/kicad-source-mirror/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/kit-dev-coldfire-xilinx_5213)
first only after auditing its 50 files and embedded notices. The tree contains
matching board/project files and no separately named license/readme. Root
CC-BY-SA 4.0 is the identified license evidence, subject to that remaining audit.
Its board Git blob is `a4ed1e0328db8992d9acbcf34963b9c7e14ca87c`.
The original project has Default/POWER classes (0.2/0.4 mm tracks, both 0.15 mm
clearance) and patterns for `+3.3V`, `GND`, `GNDA`, so successful netclass
qualification would address a real shared capability gap. Do not count the
directory as an independent family until ancestry/structural checks complete.

Then consider Openair-max as its own bounded batch, not bundled with ColdFire.
Neither operation should execute dataset scripts or omit rule/library files to
fit a limit. Preserve the complete official screen and acquired unsupported
population as the corpus expands. No new download above 10 MiB is proposed here.
