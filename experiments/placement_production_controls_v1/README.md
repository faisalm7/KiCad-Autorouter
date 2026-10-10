# Placement production qualification controls

These project-owned controls adapt the earlier floor/native fault controls and actual cancellation harness. They are prepared, not yet executed natively. Pure tests use retained exposed diagnostic fixture data and do not establish native or engine correctness.

After a source checkpoint and a fresh accepted `placement-clearance-v1` CLI fixture, `driver.py` requires its explicit `--positive` receipt and `--run-native`. Five fixed cases share60 seconds of wall and parent plus waited-child CPU: unchanged clean candidate, one undersized track, one undersized via, required via removed, and one changed rule severity. Every case gets a complete disposable project and real pinned native DRC; the production validator must reject invalid geometry or changed rules. This qualifies the unchanged inner floor/native contract. Production receipt/chain tests qualify the outer placement policy separately. No source project is edited, and no engine runs in this driver.

`cancellation.py` requires `--run-native --signal SIGINT` or `SIGTERM`, routes the owned placement fixture with the actual engine, and signals only its observed CLI PID. The control checks rejected schema3 output, the requested engine cancellation signal, process-group cleanup and unchanged originals. It tests engine-stage cancellation only; interstage/editor/OS-crash handling remains unqualified. Both helpers require committed implementation/toolchain/helper bytes before native work and use the single foreground experiment lock. Polling limits are not hard OS quotas.

Fresh-output commands (do not reuse completed output names):

```sh
python3 -B -m unittest discover -s experiments/placement_production_controls_v1 -v
python3 -B experiments/placement_production_controls_v1/driver.py --run-native --positive .runs/placement-production-native-001/result.json --out .runs/placement-production-controls-native-002
python3 -B experiments/placement_production_controls_v1/cancellation.py --run-native --signal SIGINT --output .runs/placement-production-cancellation-int-001
python3 -B experiments/placement_production_controls_v1/cancellation.py --run-native --signal SIGTERM --output .runs/placement-production-cancellation-term-001
```

Attempt001 stopped before native work because the harness incorrectly required an unrouted original. The owned original contains eight known reference routes; production removes these in the whole-board task. The corrected harness pins the exact original board/project and checks the declared stripped task hash, preserving all areas and rejecting protected routes. Failed001 remains immutable; the next native control output is002.
