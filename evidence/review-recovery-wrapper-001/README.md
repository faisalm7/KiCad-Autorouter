# Recovery wrapper review

This is independent AI review of the wrapper/CLI/accounting, not human PCB review
or native routing evidence. `controls.py` substitutes all native and engine stages,
including receipt validation. The SIGTERM reproductions use a real bounded Python
subprocess and actual signal; they run no native KiCad or routing engine. Accepted
flags inside synthetic case folders must never enter a board benchmark.

Thirteen controls pass: incumbent and shared repair CPU are counted once; metadata
child CPU is included; missing/invalid incumbent and repair candidates are rejected;
cleanup/cancellation blocks acceptance; final hash changes are rejected; source/code
staleness before finalization and during publication is rejected; signal handlers
are restored; failed invalidation publication cannot leave a canonical accepted
receipt; and final-publication wall/CPU overruns and KeyboardInterrupt clear
acceptance. Helper step registration was confirmed with its author and modeled
explicitly; its actual geometry validity belongs to separate native helper controls.

R1 is resolved. Without operation-wide SIGTERM handling, a signal after the second
accepted publication killed Python and left canonical `result.json` accepted=true.
`sigterm-reproduction.json` retains this finding. The lead added scoped SIGINT/SIGTERM
handling with restoration and archives invalidated canonical receipts before
rewriting. `sigterm-fixed.json` retains the first successful retest;
`sigterm-final.json` confirms the final reviewed wrapper responds to the same real
signal with return code 0 and a canonical rejected/cancelled receipt.

R2 is resolved. A source or code change injected during the second accepted
publication originally left accepted=true even though state changed during the
operation. See `postpublication-staleness.json`. The lead added a complete receipt
and source/code freshness recheck after that write. Both injected changes now
invalidate in `postpublication-staleness-fixed.json`. The earlier untriggered
harness is retained as `postpublication-staleness-untriggered.json`; its relative
path hook never fired and is not evidence either for or against the finding.

No remaining blocker was found within the wrapper review scope. Stored resource
measurements precede the final publication and freshness recheck, which the receipt
now discloses. Acceptance caps include this cost, and enclosing comparison arms
must charge the full invocation. This review does not qualify actual thermal repair
or whole-board completion, does not promise immunity to arbitrary repeated signals
or process kills, and does not authenticate mutable receipts cryptographically.

`test_recovery.py` is the promotable copy for `tests/test_recovery.py`; root lookup
works in both locations and temporary files remain project-local. `controls.py`
retains the original review harness. Both intentionally mock receipt/native stages.
Run `python3 -B .runs/review-recovery-wrapper-001/test_recovery.py` for the pure
controls; `--sigterm-repro <fresh-project-local-directory>` reproduces the real
signal in a separately bounded Python child. Exact files and hashes are in
`review.json`. No tracked files were changed by this reviewer.
