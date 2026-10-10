# Native DSN quote-parser correction

The failed native001 run remains unchanged. Its 138,282-byte DSN has the normal KiCad bare quote declaration at line 3, `(string_quote ")`. The board S-expression parser treats the declaration as a quoted string start and ultimately rejects an unmatched token. The existing strict adapter DSN parser succeeds; no new grammar or fallback is needed.

The runtime fix is exactly the mapping import and parser call. Worker, lifecycle, production gates, board/source/project bytes and DSN geometry remain unchanged. Synthetic fixtures now use the existing DSN serializer with a real quote declaration, so the old false-positive fixture grammar no longer hides the mismatch.

Hash-bound retained actual native data reanalysis resolves 236 connected pins (247 total pads), 376 original route UUIDs and both custom pads. The full original project, actual001 run, core, current helper and public raw subset inventories match before/after. This establishes correspondence parsing only: original-rule DRC did not run in native001, and no native worker ran in this fix task. Native geometry/format/routing qualification remains false. The source-only JP1 clearance/hull hypotheses still require the unchanged-original native DRC.

36 pure tests passed in 2.483 seconds (`tests-001.log`), including the original 31 controls with realistic synthetic DSN headers and five new retained-evidence methods. Missing, duplicate, misplaced or unterminated quote grammar, unbalanced structure, reserved sentinel, wrong terminal net and missing custom padstack all reject. `verify_saved.py` independently reproduces the exact old error and validates the fixed mapping against immutable saved artifacts.

Only three files are proposed for promotion: mapping.py, test_driver.py and README.md. Unmodified local driver/worker copies enable isolated pure tests. The original snapshot is retained under original/. The patch must be integrated only if base hashes still match; ROOT owns source checkpoint and fresh native002 execution.

Reproduce without native work:

```sh
python3 -B -m unittest discover -s .runs/pic-custom-observer-fix-001 -p test_driver.py -v
python3 -B .runs/pic-custom-observer-fix-001/verify_saved.py
```
