# Optional raw SES observation source

Only `experiments/pic_mixed_transport_probe_v1/MixedClassProbe.java` was edited by this agent. The untouched prior Java bytes are retained in `MixedClassProbe-before-ses.java`. The new literal third argument is `local250-ses`; two arguments and `local250` preserve their existing control statements and output fields. Source reverse comparison confirms this separation, not runtime compatibility.

The mode imports the same supplied DSN and applies the existing local250 procedure. Both false/true plane-obstacle cases observe route geometry before and after that assignment. Only the true case writes `raw.ses`, in the JSON output's parent, using the already declared `HeadlessBoardManager.saveAsSpecctraSessionSes(OutputStream,String)` with design name `original-mixed.dsn`. No solver or optimizer is called.

The output stream uses CREATE_NEW and checks the4MiB ceiling before each underlying write, including single-byte and array writes. Existing files/symlinks cannot be replaced through that call. The JSON filename must differ from raw.ses, including case variations on macOS. Closure is attempted after writer failure. Readback is capped at4MiB+1 with NOFOLLOW_LINKS and rejects nonregular/empty/oversized or changed-length output. Driver source/output inventories remain necessary: this is bounded sampling, not atomic protection against concurrent writers.

New-mode-only fields:

- `route_geometry_before_local` and `route_geometry`: trace/via census; every trace's item ID, fixed state, nets, clearance class, layer/index, raw half-width, width in µm and full ordered corners; each via's item identity, position, padstack name, layers and bounds.
- `corners_board_integer`/`position_board_integer` are null for a non-IntPoint, with actual point class plus approximate µm coordinates retained. No rational point is silently rounded into an exact witness. The root validator must reject such a witness for exact survival.
- The true case has `ses={executed,returned,closed,bytes,sha256,path,write_completed,...}`. `executed` means the manager call was attempted; `returned` is its real result or null before return; `closed` means underlying close returned normally. `stream_accepted_bytes` is distinct from file readback length. Errors are retained with bounded4096-character strings.
- `state_after_ses` and `route_geometry_after_ses` are captured after closure, including after a writer/audit failure where possible. First failure is preserved; later observation errors are separate.
- Top-level `ses_executed` becomes true only after the manager returned true, the stream closed successfully and a nonempty write completed. Later observation/readback failure does not erase that actual write fact, but keeps the case status failed. This flag is not an acceptance claim.

Route geometry limits are2048traces,512vias,4096corners per trace and16,384corners total on two layers. Existing16MiB observation limit remains. Stream tests, compilation and actual output validation are ROOT's pending responsibility; this author executed only the source/API comparison script. No JVM, native worker, network access, routing, SES execution or full suite was run.

All required API declarations were already captured: PolylineTrace/Polyline inspection005, Trace/DrillItem inspection002, manager/session writer observation001. Existing source explains writer rounding/snapping and omission of item-clearance classes; those remain explicit root validation obligations. No production support or native copper duplication conclusion follows from this source change.
