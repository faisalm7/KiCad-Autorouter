# Empty unrestricted rule-area identity fix

Frozen candidate for lead integration; no tracked edits, native or engine work.
The actual fixture001 failure at8497654 is preserved. Source DRC and combined
native export succeeded; the engine never started. The floor resolver rejected
`(net 0) (net_name "")` on the all-allowed placement area because the rest of
this KiCad10 board has named pad references and no root numeric net table.

`promotion.patch` changes only `source_net_identity`. Its recursive walk passes
the exact owning AST node. In named mode the zero marker means empty only when
it belongs to an actual top-level board zone, has exactly one numeric zero net,
exactly one literal empty net_name and all five unique explicit allowed keepout
flags. Genuine flags, missing/conflicting identities, ordinary copper zones,
footprint zones, duplicate fields, pad/route numeric references and undeclared
nonzero codes remain rejected. Declared old numeric tables and quoted numeric
net names preserve their distinct semantics. No board byte is rewritten.

The pinned KiCad10 parser source in
`.runs/placement-area-export-review-001/source/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp`
lines8471–8498 explicitly clears rule-area netcode to zero, then may restore a
nonempty legacy net_name. Requiring the literal empty name avoids that later
legacy fixup and does not turn a connected reference into an alias.

`diagnosis.json` binds the exact retained raw export, both contexts, source/task,
old code and candidate code. Pure replay verifies original source/native input
inventories, all four terminal UUID/ref/number/net/layer mappings and both named
net declarations. The existing floor edit gives width0.3, clearance0.3,
via1.5/drill0.3mm; exact placement removal deletes only two generic keepouts.
No further engine/import/native-acceptance result is inferred from this replay.

Promotion: apply `promotion.patch`, then copy
`test_board_floor_empty_area.py` to `tests/test_board_floor_empty_area.py`.
The promoted tests import current production core normally and load the exact
SHA-pinned old core from public evidence to reproduce the original failure.
Public fixture contexts retain their original absolute historical source path;
the test compares that stored path via the typed binding helper and uses the
public retained byte inventory. It never reads that historical absolute path.
Thus the tests work in another checkout without fabricating a new native call.

`python3 -B .runs/placement-routing-fix-001/verify_draft.py` ran15 pure controls
successfully in0.038s. The verification harness injects only the candidate pure
module into the test namespace; it never replaces a production runtime module.
First logs are retained:001 had a test assertion typo (`targets_nm` versus
`derived_nm`);002 used a draft import name without the relative package needed
by `adapter_bytes`. The final003 corrects only the test/harness setup. The
production candidate patch did not change across those runs.

All invalid outcomes remain evidence. Lead should run the promoted tests/full
suite and existing accepted readbacks, checkpoint, then perform a fresh owned
fixture002 native run under the new code. Native scope and routing validity are
unchanged gates; this correction alone is not a route acceptance.
