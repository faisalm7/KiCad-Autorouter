# Thermal comparison fairness review

Independent AI review at frozen `cbae1254f00d3470d98ba18d24a09e99874f0cc2`.
No native/engine jobs or production edits. The recommendation was fixed while
thermal-paired-001 was running, without reading its final outcomes. `bindings.json`
binds the actual protocol, unchanged source inventory and reviewed code.

## What the current pair establishes

The predeclared pair has equal 120-second total wall and measured-CPU acceptance
caps, identical original projects/rules/strict-target policy, combined adapter,
sequential workers, independently acquired candidates and no reference-route use.
Enclosing invocation accounting plus the entire shared overhead charged to each arm
includes unsuccessful attempts, setup, native checks, selection and publication.
It is a defensible comparison of these two allocation policies on this exposed
family. Equal caps need not mean equal consumption or identical engine settings.
No fairness blocker was found in this declared scope.

It is not a thermal-repair-only ablation. B2 uses the tuned optimizer and fixed
three search-cost variants, each paying the shared portfolio budget. It can exhaust
its allowance before all three variants execute; this must be reported as the
actual attempted population. C starts a fresh completion-only, default-cost
incumbent, withholds 40 seconds for recovery/finalization, and charges fresh geometry,
bridge search, every trial and final validation. At 120 seconds this assigns about
80 seconds to the incumbent; the shared route helper additionally withholds 30
seconds of cooperative engine grace plus 10 seconds native-finalization planning,
leaving roughly 35–39 seconds internal job allowance after preparation. B2's first
trial gets roughly 105 seconds and a larger internal job allowance. These are real
allocation differences, not free compute. The reserves are plans, not completion
guarantees or OS CPU quotas.

The B2 portfolio is a tuned baseline; this pair alone cannot claim the strongest
possible Freerouting allocation. Disabling optimization is a legitimate comparator,
especially because retained older interf003/004 show that completion-only can emit
a fully connected candidate sooner, while both outputs still fail a native thermal
check. Those older results were at another code version and are contextual leads,
not same-code benchmark substitutes. A B2 timeout by itself would not prove the
bridge mechanism beats a completion-first baseline.

## Smallest prospective addition

The single most valuable missing arm is **B1_completion120**: a new source-to-output
`pipeline.route(source, fresh_output, 120, False, 'both', 'completion-only')` under
the same frozen implementation, source, strict targets and full enclosing 120 wall/
CPU caps. Do not reuse C's incumbent or old interf003 as this baseline. This tests
whether completion-first allocation alone suffices without any repair. It gets the
full available ceiling and no C recovery reserve, so it is not artificially weakened.
Its earlier exit leaves unused budget honestly; do not silently turn repeated runs
into a free best-of-N comparator.

For an explicit same-code B0/B1/B2/C statement on interf, the minimum comparator
extension is three new arms, in predeclared order:

1. **B0_standard120**: `route(..., 120, False, 'none', 'standard')`.
2. **B1_standard120**: `route(..., 120, False, 'both', 'standard')`.
3. **B1_completion120**: `route(..., 120, False, 'both', 'completion-only')`.

B0 versus B1 estimates representation effects; B1_standard versus B1_completion
estimates optimizer/allocation effects; C versus B1_completion and the retained B2
portfolio addresses the added recovery policy. B0 still uses the project's common
strict-target/runtime safety wrapper, so label it stock DSN representation under
this wrapper, not every aspect of the vendor's default GUI workflow. Treat every
arm as a separate 120-second policy. Their union is not a single 120-second baseline.
A portfolio containing completion-first is a later predeclared allocation ablation,
not a retrospective replacement for the running B2 trial.

Run these only after the current paired job and review have ended. Freeze the exact
driver/hash and arm definitions before execution. Preserve cbae125 core/protocol
bytes and source if executing as a separately hash-bound reviewed diagnostic driver.
If adding a committed harness or changing implementation, use a new common checkpoint
and rerun C and B2 there before claiming a same-HEAD prospective comparison; do not
rewrite thermal-paired-001. A same-core-byte cross-HEAD diagnostic can be identified
honestly, but is not silently called the original frozen comparison.

## Separate the mechanism evidence

C's fresh incumbent is already a useful within-run no-repair observation, with
native failure, exact candidate/report bindings and charged acquisition. Compare
its failure category and geometry against C's final candidate, including the exact
added segment and preserved pads/zones/rules. This is conditional evidence on that
one incumbent, not an independently sampled full-budget baseline.

The accepted full C run, if one exists, is the positive native control. On a separate
complete disposable copy, remove only its recorded added bridge and rerun the audited
native refill/class/DRC control under unchanged project settings. Require the expected
thermal to reappear on the same pad/zone with all original invariants retained. Keep
both reports and exact input/final hashes. The already executed geometric positive
and bridge-removal negative support the mechanism on earlier exposed candidates;
a new removal control on the exact production candidate gives the strongest local
attribution. It is diagnostic cost, reported separately, and cannot rescue an
out-of-budget C delivery or be billed as zero-cost comparison evidence.

If a full allocation-matched no-repair experiment is later needed, expose a reviewed
repair-enabled switch while retaining the same incumbent/reserve/finalization path,
then predeclare fresh C_on/C_off arms at one new checkpoint. Do not fake this ablation
by patching an existing receipt or excluding the repair's failed native trials.
For this narrow first result, full-budget B1_completion plus exact bridge removal
is the smaller useful experiment.

## Required scoring and honest limits

Every accepted delivery needs pinned actual KiCad refill/DRC, raw JSON bound to the
final candidate, original project and severity/exclusion preservation, semantic
invariants, exact class targets and native map/provenance, unchanged code/source,
strict `check_result`, and full enclosing wall/CPU caps including final publication.
Use original acceptance policy on all arms; a zero-open candidate with a thermal
error is rejected. Keep unsupported, timeout, crash, incomplete and invalid results,
all native warnings/exclusions, raw metrics and rejected candidates. Do not compare
rejected route length with accepted quality as if they are equivalent outputs.

Report native-valid completion first. Compare length/vias and the retained B2 Pareto
front only among accepted outputs; disclose frontier and selected point. Record
quiet-host order, UTC/monotonic timing and child/group RSS. No extra native checks
run concurrently. The primary endpoint is one exposed board's outcome under these
policies, not a completion-rate percentage, statistically independent board sample,
novel algorithm claim, general superiority, human cleanup time or electrical proof.
