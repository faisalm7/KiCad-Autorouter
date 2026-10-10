# Ignored feedback-pruning draft

Prepared against the source hashes in receipt.json. No tracked edits and no native/engine runs were performed. feedback.patch changes only autorouter/strategy.py and tests/test_strategy.py. `git apply --check` passed. Parent must coordinate applying it after current frozen experiments and before a new audited checkpoint.

API: `prune(source, output, seconds=120, *, proposal_policy="single")`; policies are `single` (default/current whole-net then individual behavior) and `feedback`. Root receipt records the explicit policy. The CLI flag and prospective five-arm experiment entry/summary contract remain lead integration work: require the actual root receipt policy to match C_single/C_feedback, plus the existing adapter/profile/incumbent checks. Do not overwrite quality001/002/003.

Run draft controls without modifying tracked modules:

```sh
python3 .runs/compound-deletion-draft-001/run_controls.py
```

31 controls pass. These exercise real copied project files, proposal ownership and accounting but substitute native stages in control-flow cases; they prove no native acceptance. The actual stored quality002 trial0001 candidate/report hashes were verified, and the pure helper selected exactly the two native-identified stubs plus the preceding removed segment. stored-trial-proposal.json is only proposal evidence; the compound deletion has not been run through KiCad.

Each cleanup is a new ordinary attempt, counts against MAX_TRIALS and all wall/CPU accounting, and gets full refill/DRC/metrics. At most two feedback stages and eight additionally removed tracks per initial proposal. Failed receipts are immutable; decision files bind parent trial, candidate/report/base hashes and selected UUIDs. New warning identities must consist exclusively of track_dangling. Every referenced UUID must be present exactly once across all board objects and resolve to an eligible segment/arc on the same original zone net. Protected, missing, other-net, nonroute, repeated or ambiguous references refuse feedback. Original source/snapshot and the failed candidate/report/current best are checked for staleness. Acceptance and final validation remain unchanged.

Risks and limitations: valid native geometry and a shorter proxy do not establish electrical suitability; generic dangling cleanup can delete intentional unprotected stubs. New compound attempts may displace more valuable later singleton attempts within the fixed budget; this needs the prospective five-arm ablation. Candidate roundtrips must retain the warning UUID mapping; missing mapping refuses the operator rather than guessing. Current signature policy compares warning type plus item UUID set, inherited unchanged from existing C. A caller can supply malformed helper data but receives a refused proposal for the checked schema errors. Any non-dangling new warning blocks feedback. Independent agent review could not be spawned because the team thread limit was reached; lead/engine-agent review remains pending.
