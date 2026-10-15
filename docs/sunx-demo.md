# SUNX source gate

The pinned public [SUNX v2.1 design](https://github.com/Open-Air-Foundation/pcb-module-SUNX/tree/9cee7482c6b3bbd63293f53376335bed6659457f) is an exposed development candidate. Its publisher marks it untested work in progress. Native support and routing results are still pending.

The fetch profile preserves six originals, including the existing local-settings file (`sunx.kicad_prl`), and makes two byte-identical creator-notice copies for the native packet. It verifies every file against its fixed URL, size, Git blob and SHA256. It acquires no models, firmware, libraries or scripts. Hardware CC-BY-SA4 permission and AirGradient attribution remain in the complete README/LICENSE; individual assets and independent ancestry are not established.

Preview acquisition without a network request:

```sh
.venv/bin/python -B scripts/fetch_led_demo.py --project sunx-v21 --output .data/sunx-v21-demo-001
```

Acquire the exact six-file packet once into a new folder:

```sh
.venv/bin/python -B scripts/fetch_led_demo.py --project sunx-v21 --fetch --output .data/sunx-v21-demo-001
```

The next original-design gate uses the existing shared diagnostic, preserving the source, PRL, rules and all findings:

```sh
.venv/bin/python -B experiments/original_project_native_v1/driver.py --project sunx-v21 --output .runs/sunx-original-native-001 --run-native --protect-local-settings
```

This runs saved original refill and complete-schematic DRC, without an export or routing engine. Acquisition or a completed diagnostic is not routing acceptance. Any unsupported constraint, warning, failure or source change remains visible; no result is assumed here.

Actual original001 now completed: saved Native0opens/0blocking/15warnings; fullSCH original-shell0/0/19 withfour genuine source parity findings. Two locked mountingholes contain NPTH pads and duplicateREF** withoutboard_only; C5 DNP differs betweenSCH/PCB. Variable-dependent surface text also blocksnormalexport. All135originalroutes/fulloriginalAST/PRL remainexact in the finaldiagnostic; source repair, aliaswaiver, engine/routing admission and physical function are unqualified. [Actual source gate](../evidence/sunx-original-native-001.json). Do not repeat acquisition/Native/readback to obtain a different result.
