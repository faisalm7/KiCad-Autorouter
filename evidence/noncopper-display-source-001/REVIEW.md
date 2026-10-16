# Noncopper display metadata: narrow skeptical review

**No material defect found in the inspected delta.** The new exception accepts a fourth display atom only after the physical row has matched an exact recognized NONCOPPER ID, canonical name and user type. It does not infer physical identity from the display string. Copper rows still require signal type and exactly three atoms; exact canonical four-copper IDs/names/order and the existing stackup/route/via guards remain mandatory. Duplicate physical IDs/names, foreign canonical rows and hidden copper types still refuse.

The display reader requires a bounded quoted atom, permits only quote/backslash escapes, limits decoded UTF-8 to256 bytes, rejects empty/edge-whitespace/ASCII-control/DEL strings, and checks casefold collisions against all qualified canonical copper/noncopper names, including supported noncopper rows absent from the table. Only its own exact canonical spelling may serve as that row's display. Repeated/escaped/Unicode-casefold-equivalent displays refuse. The source atom and all AST fields remain unchanged; no project rewrite or alias normalization was introduced.

I ran56 bounded pure controls using the actual netclass function and an owned in-memory layer table: all22 own canonical noncopper displays; ordinary/default and quoted/backslash/UTF-8 bounds; active copper/other canonical collisions; duplicate casefold/escaped displays; foreign/duplicate physical IDs or names; signal disguise; a fourth copper atom even spelling its own canonical name; copper reordering/interleaving; nested/extra/unterminated/unsupported-escape atoms. All passed with the expected accept/refuse outcomes and unchanged complete input AST on every call. Both reviewed source hashes matched before/after. No Native/JVM, preflight/project execution, broad tests, Git, network or delegation occurred. Only this owned review/control directory was written.

Controls are retained in `controls.py` and `controls.json`. The recorded .005814s wall/.005815s CPU measures the pure control body after imports, not interpreter startup or a routing benchmark. The separately supplied22-method target receipt records exit0 and the same source pins; I did not rerun that suite. These controls establish the narrow software guard, not actual installed4Cu transport or routing correctness. Copper physical aliases remain refused; no HFE parity/pour support is added. The lead's fresh installed4Cu forced-inner Native pipeline,10 protected routes, fresh export and current-reader qualification remain separate pending gates.

SHA256 read pins:

- `autorouter/netclass.py`: `a483d40e48a5774e4485afc187ec6c7fad3d1f69a74b35a6f96624223446aa0b`
- `tests/test_four_copper_classes.py`: `4d4244e169b19ad331799679d904e027ba24e6a6199668bd811f629472bf4881`
- `controls.py`: `d127f12163ef23c9f301c42d0ca5dd4cf1f049c238132cefec39e1745810f797`
- `controls.json`: `41de7644feb24e3b8cfeebc8ddc649a2b0b002eec2b741fca7ea215c5c183064`
