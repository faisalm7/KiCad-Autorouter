# Local clearance transport: narrow post-load diagnostic

The supported implementation path is a post-load item-class assignment, leaving net classes and routing widths unchanged. This is source/API feasibility plus authored observation code, not routing, SES, pair-collision or general rule-equivalence qualification. ROOT reported the four separate native local-clearance controls passed; this task did not rerun them.

Pinned Freerouting source is commit `b647a2f824cfbc54bc4dcaee71b03b7cd945eb76`; actual declaration receipts bind JAR SHA `f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7`. `bindings.json`, `mode-bindings.json` and `network-receipt.json` contain exact byte/hash paths. Six additional official text reads total 89,673 bytes; no fetched code was executed. The local cached upstream sources are GPL-3.0 research material; public selection excludes them pending the lead's normal license/publication audit.

## Why direct item assignment

Both anchors and synthetic copper areas need the local override. Actual mixed005 retains JP1/1 pin+area at POWER class3, while JP1/2 pin is smd2 and its area default1. The matrix currently asks 280µm between POWER and Default despite the two pads' observed 250µm footprint override. Changing only the copper area leaves its POWER anchor as a different clearance obstacle. Keep each net's original class and width (POWER800µm, Default500µm).

The public [`Item.changeClearanceClassIndex`](https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/board/model/items/Item.java#L1010) changes the item class and clears derived data; the plain setter does not perform the same refresh. [`ClearanceMatrix.appendClass`](https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/rules/ClearanceMatrix.java#L281) copies default values into the added row/column. Its setter at lines100–116 rounds odd board units upward, so the authored mode first requires an exact positive even representation of 250µm, then writes and reads back both symmetric cells.

DSN does support placement pin clearance names (`Component.java`301–339, resolved by cached `Network.java`1021–1035) and wire/area clearance names (`Wiring.java`420,438–448,476–486). However, unknown pin names fall back, and net-class insertion (`Network.java`730–761,1319–1321) can initialize a later POWER class with larger cross-clearances. Precreating POWER changes that branch's default-item behavior. A DSN-only rewrite therefore has additional unqualified ordering semantics; it is not the selected finite probe.

## Authored mode and refresh

Only `MixedClassProbe.java` was changed by this agent. Invocation is:

```text
MixedClassProbe <existing mixed.dsn> <fresh observations.json> local250
```

Omitting the third argument retains the existing two-argument path. Static reverse reconstruction in `verify_source.py` proves that path's statements are unchanged; this is not a runtime compatibility test.

After the existing manager `awaitPostLoad()`, the mode records `state_before_local`. It requires exactly `null/default/smd/POWER/board_edge` in that order and two layers. It resolves JP1/1 on VCC and JP1/2 on `/pic_sockets/VCC_PIC`, each with one unique reciprocal same-net USER_FIXED area. It appends index5 `native_local_250` and assigns exactly those four items. For each layer, the symmetric new row is null0 and default/smd/POWER/self250µm. Board-edge entries preserve the original pins' symmetric250µm values; unexpected original values reject.

The mode calls [`clearanceValueChanged`](https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/board/searchtree/SearchTreeManager.java#L111), then `reinsertTreeItems` (186–199), which clears cached shapes during reinsertion. The actual JAR public declarations were obtained by ROOT in `.runs/pic-local-clearance-api-001`. `validateEntries` is recorded for all four items. It checks tree-entry consistency, not collision-free routing or every pair's electrical rule.

Output retains the full after-state and `local_override` with class name/index, changed IDs, raw row, original edge values, APIs and refresh/entry booleans. ROOT's validator reverses only the four class indices and matrix extension and requires exact prior state equality, including original5×5 matrix, net classes/widths, geometry, contacts, fixed states, planes and other items. Raw and compensated readings remain distinct: actual005 uses a16-board-unit safety margin even on null raw0.

The authored Java does not initialize KiCad, route, optimize or write SES. ROOT owns controller/protocol/test changes, source checkpoint and actual compile/import. Static retained005 checks confirm both expected target sets and edge values; actual mutation success remains unobserved at this freeze.

## Remaining boundaries

The manager applies settings before the awaited deferred work (`HeadlessBoardManager.java`839–881); the new assignment occurs after it. No running solver is present. Later settings reload, restore or solver lifecycle needs another snapshot/guard rather than assuming assignments persist.

Cached `SesWriter.java`153–181,331–416,514–550 writes placements and route/area geometry but no per-item clearance assignments or clearance matrix. Thus SES cannot carry this override faithfully by itself. Retain a bound sidecar, preserve original native pads/rules, and separately qualify any reload, exact synthetic-area removal and SES import. No SES equivalence is claimed here.

For a future generic adapter, local-vs-local pairs need the maximum applicable positive override plus original board minima; special edge/hole/keepout/custom-rule relationships need their own preserved profiles. This exact two-override mode is not a generic PIC-name whitelist for production. The global `plane_as_obstacle` switch still also changes the original GND area: the unresolved original-plane adapter question remains separate.
