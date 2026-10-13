# Original KiCad 8 native compatibility probe

This prospective ROOT-run experiment does not admit another source format or claim new routing. No native call has run from this draft.

First, three project-owned controls use an explicitly authored KiCad 8 board grammar: version20240108, numeric net declarations, old numeric layer indices, UUIDs and property references. This is not a modern board with its version edited. The positive has four ordinary through-hole terminals, one signal bridge and a GND zone; the deliberately invalid controls remove that bridge or reduce its width below the unchanged original project minimum. The attributed project-settings template and license/notice files remain unchanged.

The positive uses the existing `floor_context.collect` export observations and `native.py roundtrip` worker. Actual current-native emissions of the original load, saved-refill reload and final old-shell reload must have identical complete non-fill ASTs **and routes**. No header or arbitrary field is stripped. Separate same-load contexts must preserve pads, nets, route geometry, copper obstacles and original floors/class dimensions; only local numeric netcodes may be renumbered while net names remain exact. This probes saved semantic equivalence, including the explicit ideal-diode stackup, without inventing a new stackup SWIG API or pretending a handful of API fields describe the entire board.

The shared `pipeline.validate_candidate` performs saved native refill, transfers only derived zone fills into the exact original shell, checks protected routing/invariants/project bytes, and invokes actual final DRC against the original rules. That function returns diagnostic native findings; production preflight remains blocked for20240108. Fresh process/report bindings and source/candidate hashes are checked through the shared floor helpers. The two invalid controls run this same saved/final DRC path and require exact unexcluded native connectivity or width findings; full geometry observation is not unnecessarily repeated for these one-route changes.

Only after those controls pass does the unchanged acquired ideal-diode project receive one full observation. Its actual four-file Hardware project tree is copied exactly, including its STEP file. All six acquired files and both root notices remain pinned against the original acquisition receipt, SHA256 values and Git blob IDs. No PRL exists in that acquisition. An unexpectedly present PRL stops the experiment instead of adding an exemption. The existing DRC rule-file and PRL preservation policy is unchanged.

The two full cases use eight native processes each; each invalid uses two. All20 calls run sequentially under one90-second wall/parent-plus-waited-child CPU cap and20MiB output acceptance ceiling. Use the existing outer runner with matching workdir polling for growing-output termination. This is measured/cooperative and polling enforcement, not an OS aggregate CPU/disk quota. Every failure is retained. Complete raw real-board geometry and native emissions remain local; select only hashes/summary, authored controls and project-owned source for public checkpointing until redistribution review permits more.

ROOT must review, promote to `experiments/kicad8_native_compat_v1`, run pure tests, commit/push and independently read the checkpoint back before the actual invocation:

```sh
.venv/bin/python -B experiments/kicad8_native_compat_v1/driver.py --output .runs/kicad8-native-compat-001 --run-native
```

Use a fresh output, after the current benchmark finishes. The driver takes the existing native quality lock. A positive compatibility observation does not qualify SES import, a newly routed result, whole-project cleanliness, independent-family improvement, editing-library closure or electrical/physical validation. All warnings and existing ignored checks remain visible. Keep the actual original format and globally blocked production guard until the lead evaluates the fresh evidence and remaining controls.

The lead may use a fresh `run` child inside an existing direct `.runs/kicad8-native-compat-*` wrapper directory so the existing outer runner monitors the entire growing output. Arbitrary nested paths, reuse and symlinks reject. The output guard follows the already qualified owned-controls pattern; it does not change input or PRL policy.
