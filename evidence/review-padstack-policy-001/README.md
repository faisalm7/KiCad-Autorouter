# Independent centralized padstack-policy review

Disposition: no blocking acceptance defect found in the reviewed change. The
194 independent pure/filesystem checks in `audit.json` passed. No native process,
engine, or test subprocess was launched. Tracked files and retained native
reports were read only. This directory's `scratch` holds a controlled synthetic
board/project used to enumerate the preflight exception.

Only the exact original project setting `padstack: warning` is newly admitted.
The same key set to `ignore`, internal finding name `padstack_invalid` used as a
project key, unknown settings, and every other critical warning/ignore setting
remain unsupported. No source severity or exclusion is rewritten.

The shared application policy rejects findings named either `padstack` or
`padstack_invalid` at warning, error, or exclusion severity; all other critical
finding names are likewise rejected. It also rejects errors and excluded
findings even when a direct caller supplies false zero counters. Noncritical
native warnings remain visible and permitted. This does not make a route with
warnings whole-project clean.

Six actual retained native reports from controls 001 and 002 were reread. Their
raw hashes and parsed summaries match the original control receipts. The clean
controls remain accepted; wrong-paste warnings and the tiny-hole
`padstack_invalid` plus `drill_out_of_range` errors reject. The older SMD-hole
case emitted no finding and remains an invalid negative control, preserved as
such rather than relabeled successful.

Read-path review found the central policy applied to route completion, pruning
trial/final acceptance and feedback eligibility, retained result validation,
and diagnostic/KRT acceptance. Handoff and quality/portfolio/paired selectors
recheck through `check_result`. The new receipt tests explicitly attack a
consistently rehashed critical-warning receipt through these consumers. The
existing native parser schema is unchanged, and `check_result` still rereads
the raw report and requires equality with the recorded native summary. The
direct summary helper is not a replacement for those report and provenance
checks.

This review establishes policy wiring and consistency with previously obtained
native evidence. It is not a fresh native rerun, physical PCB validation,
broader pad-shape qualification, or a solution to the separate unresolved
thermal topology certificate. The reviewed source hashes and exact runnable
audit script are retained here. Repeating the script should use a new directory
because its scratch fixture deliberately refuses an existing directory.
