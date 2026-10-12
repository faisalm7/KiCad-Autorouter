# Reject active tuning profiles before Default fast path

Real preflight on owned copied projects wrongly admitted an active missing profile in the sole Default class and an unused nonempty project profile definition. The existing multi-class qualification guard was bypassed. Completed native severity002 separately showed that a Default missing profile can be omitted from the native warning report, so absence of a finding cannot replace source rejection.

The shared reject_tuning_intent guard now runs before the fast return in netclass_policy and inside qualify_project. It rejects nonempty assignments, definitions and malformed recognized fields while preserving absent/empty settings and ordinary meander preferences. Existing source preflight, immutable project-file checks and candidate/readback netclass_policy calls reuse the guard. No new severity keys or supported-board scope is admitted and no original file is modified.

Root8focused tests pass0.142seconds; full616tests pass14.967seconds. Four original accepted receipts remain current (saved-evidence checks only). Actual fresh native compatibility follows independent source review and audited checkpoint. This is a correctness fix, not a routing improvement or provider qualification. Author's old-fail/new-pass observations and exact prospective pipeline patch are retained with their original chronology.
