# Actual-evidence copied receipt controls

All nine controls passed: one unchanged relocated positive and eight deliberately invalid copies. Every negative first passed the complete production `check_result` after relocation, so a rejected copy with broken paths was not counted as a success. Original native001 run and original fixture source remained byte-for-byte unchanged.

Each case has its own complete run copy and disposable source copy. Only run-local absolute paths in top-level JSON were rebound, followed by the required native-context, policy, final-audit and whole-inventory hashes. Boards, original rules, DSN, SES, logs and code bytes initially remained exact copies; each later mutation is recorded separately. Copied receipt metadata is synthetic relocation, not a new execution.

The validator rejected missing SES, missing import, missing refill, an arbitrary source command whose step/process JSON was consistently rewritten, policy downgrade, a generated 0.2 mm track where 0.3 mm guidance was required, candidate clearance severity relaxation, and a changed disposable source board. Superficial evidence inventory hashes were refreshed after each mutation; intended deeper checks still rejected. Exact reasons and positive prerequisites are in `summary.json` and each case's `control.json`/`relocation.json`.

Artifacts consumed approximately 7.76 MB, under the 16 MiB cap. No native tools or engine ran. These controls establish mutable evidence consistency and fail-closed behavior, not authenticity, fresh DRC, routing quality, physical safety or human PCB review. The initial authoring syntax typo was detected before execution and retained in `syntax-attempt.log`; there were no failed relocation attempts.

Reproduction: the stored script refuses to overwrite this completed control directory. To repeat, place an unchanged copy of `controls.py` in a fresh direct `.runs/<new-control-id>` directory and run it with `python3 -B`; it reads the same retained original native001 run and creates only its own bounded cases. The implementation hashes used here are retained in the summary.
