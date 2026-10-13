# Original KiCad8 diagnostic continuation

This project-owned diagnostic continues only the eight unexecuted ideal-diode load/save/refill stages. The original run `.runs/kicad8-native-compat-001` remains **failed**, with its DSN failure and all raw evidence intact. It reads back the completed positive, missing-track and narrow-track native controls using the existing shared validation helpers; it never executes those controls again.

The lead must review, promote these four files to `experiments/kicad8_native_compat_continuation_v1/`, commit and verify the checkpoint before native execution. The draft guard refuses all execution from `.runs`. Run pure controls with:

```sh
.venv/bin/python -B .runs/kicad8-native-compat-continuation-draft-001/test_driver.py
```

After promotion, the ROOT lead's bounded outer runner must launch the committed driver under the existing network-denied sandbox with a fresh monitored directory such as `.runs/kicad8-native-compat-continuation-001/run`:

```sh
.venv/bin/python -B experiments/kicad8_native_compat_continuation_v1/driver.py \
  --output "$PWD/.runs/kicad8-native-compat-continuation-001/run" --run-native
```

The direct command illustrates the worker; it does not replace the existing outer process monitor. Require the established 20MiB output polling, bounded memory, cancellation/cleanup, and full outer wall/CPU receipt. Final cumulative acceptance is the original outer **14.101435208998737s wall / 9.084805000000001s full CPU** plus the full continuation outer cost, under **90s wall and 90s full CPU**. These are observed acceptance caps, not an OS aggregate CPU quota. Inner remaining budgets are 75.89856479100126s wall and 80.915195s CPU. Do not quote only the driver’s prepublication totals or uncharged native-step sum.

The complete 196-file failed-run inventory and original acquisition/tree pins are part of `PROTOCOL.json`. The readback verifies all thirteen retained native processes, actual owned-control DRC reports and exact source/rule/input bindings. The continuation uses the shared finalizer and process-control/publication helpers, not a new routing auditor.

All new contexts use `final` mode and never request a DSN. Original and saved and original-shell current-native emissions compare complete non-fill AST and route AST without header stripping. The exact original20240108 shell and unchanged original project files are required. Effective same-load contexts compare geometry/rules across all three final-mode observations; final-mode contexts omit export-only obstacle capture, so the full emitted AST comparison remains material. Original-rule DRC findings, severities, exclusions and ignored checks remain in both saved and final raw reports. A native DRC failure on the original board is preserved as an observation; it is not made into routing acceptance.

The footprint census records every footprint by UUID, including duplicate padless label references. It compares the source AST to the actual original native emission and to both subsequent native emissions. This can establish native retention of the duplicate references that the pinned exporter source rejects. The original caught C++ exception was not captured, and this continuation does not manufacture one. It does not rename, delete or alias label references; change source rules; retry DSN; route/import SES; or open the production format guard.

`observations_complete` means only this bounded continuation's unchanged load/save/refill observations completed. `dsn_export_supported`, `routing_accepted`, `production_supported`, `format_support_qualified`, `ses_import_qualified`, `dependency_complete` and `physical_electrical_validation` stay false. Failures, original-input mutation, code/tool/protocol changes, cancellation, stage-scope changes or resource excess fail closed. New output is preserved on failure. All actual real-board payloads, current-native emissions and DRC raw data remain local until the lead audits redistribution rights separately; this draft publishes only project-owned code/protocol/tests/documentation.
