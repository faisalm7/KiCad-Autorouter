# Native pad-component experiment

This observes a complete pad census and pad-seeded `GetConnectedItems(pad,0)` partitions after caller-qualified saved refill. It neither routes nor accepts a board. `GetConnectedPads` is immediate adjacency; zone parent UUIDs can represent different islands and must never merge components. Source basis: pinned KiCad0feeca2a connectivity_data.cpp581–605 and connectivity_algo.cpp340–460; exact source/hash notes remain in the local run support.

The first native controls are an owned multitrack chain, removed bridge, one zone with two pad-bearing islands after a narrow neck is removed by refill, an unbridged layer gap, a via bridge and an actual different-net short. Shared Job, Native report/process/refill, original-shell reconstruction, source inventory and publication helpers remain authoritative. Original smoke fixtures are never modified. PCB-only schematic parity is explicitly unavailable. Missing/mismatched evidence fails. The observer must never replace thermal, short, full original-design or complete-schematic validation.

Pure controls reproduced and fixed unknown pad attributes/netted NPTH exclusions and duplicate UUIDs in the new fixture clone. The native Python wrapper, interpreter and extension are explicitly pinned; loaded module paths are checked. Native return conversion, transitivity, zone-island/layer behavior are still unexecuted at this source checkpoint.

Prelaunch review also found a stale pass flag after publication invalidation, missing freshness witnesses for completed cases, and a short control that accepted any blocking error. The first and third were reproduced before correction. Regression controls now require a failed final status to clear the pass flag, retain bounded per-case file/directory witnesses, and bind an unexcluded contact error to the deliberate bridge and crossed track UUIDs. Unrelated DRC errors cannot qualify the short control. Full091 passes1397 software controls; this is not Native API evidence.

Limits: initially2Cu/256pads/128source nets/4000returned items per query/50000total/1MiB output and60seconds worker; outer checks remain necessary because C++ allocations/calls precede Python checks. One worker, deny-network sandbox, source files never saved. Components can change after routing/refill. Stale input/refill/short/thermal/cancellation and final candidate qualification remain separate gates; this initial observer grants no routing admission. Existing whole-net helpers cannot express component representatives and currently block65-net Universal at64.

After a verified source checkpoint, run the initial sequential controls once:

```sh
.venv/bin/python -B experiments/native_components_v1/controls.py --run-native --output .runs/native-components-controls-001
```

Every later invocation needs a fresh output. All generated controls and failures are retained. No benchmark improvement or new supported board family follows from passing this diagnostic.
