# Independent thermal repair audit and prepared negative control

Stored repair-only native evidence passed 112 independent consistency checks: exact source/project/tool and frozen code binding, final raw DRC and candidate hash, strict original netclass dimensions, unchanged fill, and the previously independently checked positive-margin geometric paths. The first generated bridge has zero native opens, errors, warnings, and exclusions. This is repair-only evidence, not equal-budget end-to-end C acceptance or physical PCB validation.

Removing exactly bridge UUID `5f46c41d-abc3-5586-b349-38f2b4862fcd` reproduces failed board SHA-256 `922c6ce93556732940b5bccc06794c84b35fd164f86abd0ac3f6faf5b76e3f41` byte for byte. The prepared driver expects fresh native validation to reproduce the original sole starved_thermal error at the exact target pad and zone, with zero opens, warnings, and exclusions. Original positive and source inputs remain immutable.

`negative_control.py` has not been run natively by the reviewer. Its 30-second shared wall/CPU budget includes all preparation. Five pure interruption, publication, path, and CPU-cap controls passed on 2026-10-10. The lead will execute the native counterfactual sequentially after reviewing the frozen files.

Execution from the project root:

```sh
python3 -B .runs/review-thermal-auto-001/negative_control.py --output .runs/thermal-auto-negative-001 --run-native
```

The positive run froze commit `893f63ad9070ed440ffd29bdfbfec378aa1efa44`. Later pipeline edits preserving raw DSN evidence are recorded separately. The reusable audit verifies historical snapshot bytes against that commit and requires equivalent current validation functions and unchanged validation dependencies before the negative driver runs.
