# HFE original-source diagnostic

This opt-in developer experiment observes an unchanged public transistor-measurement project. It cannot admit routing or change the source. Its exact six local source hashes and upstream revision are fixed in `driver.py`; acquisition and rights records are in `evidence/hfe-source-static-001.json`. The CAD stays local. No external repository script or optional model is executed.

After a verified, clean source checkpoint, use the same full SHA for both commands:

```sh
.venv/bin/python -B experiments/hfe_original_native_v1/driver.py --mode prepare --source-head CHECKPOINT_SHA
.venv/bin/python -B experiments/hfe_original_native_v1/driver.py --source-head CHECKPOINT_SHA
```

Preparation and execution create fresh fixed `.runs/hfe-original-native-*` directories. Never overwrite them or launch the private worker mode directly. The signed, separately installed KiCad 10.0.7 receipt must already exist; production tool pins remain unchanged. This experiment needs no AI service, account, paid API, routing engine execution or route-time network.

The shared `FloorJob`, immutable-PRL guard, saved-refill stage reader and guarded publisher validate the original shell with all 785 original route records. The final stage requests full schematic parity. Each native worker has a 30-second cap; the enclosing experiment has 120 seconds wall/full CPU including measured preparation and publication allowances, 128 MiB scratch and 2 GiB sampled RSS limits. Polling/process-group limitations still apply.

Current static routing refusal—four-layer netclasses and inner-layer pour-area metadata—is retained. A source failure, unavailable parity or unqualified 20260306 effective-field bridge remains a failure with raw reports/journals. Raw population counts are labelled unqualified. `accepted` and production-support qualification always remain false. No Native result exists merely because the script or cancellation tests pass.

Review found raw-report capture swallowing cancellation. Four exact-body controls preserve the before failures and verify the corrected cancellation boundary; they do not establish native correctness or human PCB review. Actual original feasibility must precede broader support work.
