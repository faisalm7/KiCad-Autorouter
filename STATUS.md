# Current status

Updated October 12, 2026. **Active local reconstruction; not release-ready.** Durable Mac checkout: `/Users/faisal/Projects/KiCad-Autorouter-local`, branch `rebuild/local-20261010-015447`. No cloud environment or competing worktree was used.

## Latest actual result

Preview001 rejected the observed SVG1.1 declaration. Compatibility/substitution/active-content fixes passed independent controls atc3fa13f, but actual002 then exposed KiCad creating a PRL in the advertised original copy; exact-copy guard rejected, with source/accepted run unchanged. The new fix uses private per-plot project copies, binds their exact file sets through publication, and keeps the generic existing-PRL guard strict. Native003 and actual tampering/SIGTERM controls are next; no ready preview is claimed yet. [Failures](evidence/review-render-fixture-002/review.json).

PAW3395 diagnostic001 completed export (56pads/16nets/220routes) and original-rule nonsaving DRC, then rejected because KiCad changed the existing disposable PRL. Original14files remain exact; only the DRC copy's PRL changed. Separate posthoc readback finds0opens/0blocking/17librarywarnings/0exclusions, but the original controller never published a stage-two binding. It remains failed, not production-qualified or newly routed. Do not repeat completed native stages. [Raw failure](evidence/paw3395-native-diagnostic-001/summary.json), [diagnosis](evidence/paw3395-native-diagnosis-001/REPORT.md).

Low-via diagnostic001 at **467f7bb9f2fb751a17a3560d2531225b6f6eb676** used25/3 instead50/5 via costs under the same180second caps and unchanged original constraints. Actual KiCad still reports **5opens/0blocking/41warnings/0exclusions**,0vias,1,803.155205mm. The hypothesis did not improve completion; rejected lengths are not usable-quality gains. All8compile/engine/native stages finished; strict335segment transport and original15files pass independent readback. Stored15.882477wall/19.651377CPU, outer16.179195wall/19.897275CPU. [Exact evidence](evidence/pic-low-via-routing-001/summary.json), [review](evidence/review-pic-low-via-actual-001/REVIEW.md). Candidate `ff59099f8a3752f97d1c26e30a1427b01015b9911d1b0ec8059615a7f04a0739`; final report `f5c1975531ed696060ce6522e905c964514e79e7c7db2557c6df44ddf3983929`. This is B2-style tuning on an exposed input, not a new mechanism or paired population result.

Corrected-adapter native001 at **2199621ed938bb6db2c0565059754c66f4a93979** completed all six KiCad stages using saved routing001 output. No compiler, solver or SES writer was repeated. The candidate is **rejected: 5 opens, 0 blocking findings, 41 library warnings, 0 exclusions**. Missing connections involve `/VPP/MCLR`, `/CLOCK-RB6` and `/DATA-RB7`. Original project files and nonrouting geometry remain preserved. Native track length is1,803.123465mm with0vias; rejected length is not a usable-quality gain.

Candidate SHA256: `05e980f795d7722206c9cf9075b72abcffaa5febda6f6864e13a1da15cc39f79`.
Original-rule report SHA256: `132339ce6ab18b78902c7da90b0cea0491c8992fafba3aff1b65f10bb7d07c1f`.
Stored continuation cost:10.848156wall/8.948096fullCPU seconds; outer11.113877wall/9.187081waitedCPU. Prior solver001 cost6.452533wall/11.280382CPU stays separate. Raw evidence: `.runs/pic-corrected-adapter-native-001`; [independent readback](evidence/review-pic-adapter-native-001/REPORT.md) and [public evidence](evidence/pic-corrected-adapter-native-001/summary.json) are complete. ROOT independently verified all237frozen artifacts, the exact candidate, report and original design.

The B1 adapter added19 conservative text keepouts and suppressed only the engine plane, preserving the native zone. The prior diagnostic had1open/3copper-text clearances/41warnings; the new result removes those blocking findings but leaves more opens. These are exposed diagnostic attempts, not a fair population comparison or new routing mechanism. PIC remains production-unsupported.

Original corrected-adapter solver001 remains failed on its internal GND/VCC numbering check. A separate corrected checker normalizes cross-import numbers by net name while retaining same-instance IDs, terminal and constraint checks. Exact337segment engine→SES transport passes; all513corners are integer, so the new RationalPoint capture branch remains unexercised. Twenty-two targeted software tests pass. Native acceptance is false.

## Usable experimental workflow

Pinned tools: KiCad10.0.0, Freerouting2.5.0, Java25.0.2. The offline CLI snapshots complete projects, routes in isolation, imports/refills, checks original rules and semantic invariants, and emits separate candidates with actual findings and hashes. Unsupported, stale, corrupt or incomplete validation rejects.

```sh
python3 -B -m autorouter doctor
python3 -B -m autorouter settings-init --output routing-settings.json
python3 -B -m autorouter preview /path/to/board.kicad_pcb --settings routing-settings.json
python3 -B -m autorouter route /path/to/board.kicad_pcb --settings routing-settings.json --output .runs/my-route-001
python3 -B -m autorouter review-copy .runs/my-route-001/result.json --output .runs/my-review-001
```

Use fresh output paths. Persistent choices cover whole/partial scope,5–900second budgets, adapter/profile/via-cost preferences and narrowly qualified two-layer allowed-new-layer lists. Locked/protected copper remains exact. See [preferences](docs/routing-preferences.md) and [GUI procedure](docs/gui-workflow.md).

Open the review copy through its `.kicad_pro` in KiCad project manager, then Tools → PCB Editor. Actual manager entry reproduced all96CLI findings for multichannel; direct PCB opening produced33 extra library warnings. Separate-copy review is qualified narrowly. Live application/undo, plugin-selected nets and complete editor-staleness protection remain unfinished. No human PCB or physical/electrical qualification is claimed.

## Measured contribution and full population

Under separately frozen120second wall/CPU caps, sonde C produced648.045171mm/2vias versus stronger B2's749.441643mm/2vias:101.396471mm shorter with more compute. Interf_u C repaired a sole thermal failure and accepted where tested B0/B1/B2 rejected. These exposed-input, strategy-specific results are in [quality](docs/quality-experiment.md) and [thermal evidence](docs/thermal-experiment.md).

Multichannel's B1 placement/margin correction accepts0opens/0blocking/96warnings,2,647.385729mm/21vias; zero-margin and lower-via-cost variants reject. No pooled completion rate, proven independent-family gain or generalized superiority is established.

Population: **20 acquired development boards,3 statically eligible/17 unsupported,0 proven independent families**. The prior19 retain their recorded7complete/12incomplete dependency categories. Three inputs have accepted production-policy evidence from separate recorded experiments. All are exposed. PAW3395 acquisition005 completed14files/2,163,350bytes; all345previous files unchanged. Mandatory source/project/local footprint are present; optional external library/model identities remain incomplete. Its static blockers are KiCad8format20240108 and zone_has_empty_net severity semantics. [Audit](evidence/paw3395-static-audit-001/REPORT.md). Native diagnostic completed both processes but failed the existing PRL guard as detailed above; production support remains false. Every prior case remains in [qualification](evidence/placement-production-qualification-001/summary.json) and [acquisition004](evidence/licensed-acquisition-004/population-extension.json).

## Testing and installation

Latest full production suite:620tests pass15.513seconds (`.runs/review-render-integration-full-001.log`), including four new preview boundary controls; actual new plotting qualification is pending. The corrected adapter, low-via and shared acquisition integration passes65 targeted controls in9.356seconds; the first invocation retained a mistyped test-module error. Independent reviews preserve and reject demonstrated compiler/argv and late-acquisition-mutation defects. Later experimental-only changes have targeted tests/reviews; test counts are not routing quality. Actual controls cover custom-pad contact/disconnection/intrusion, local clearance, invalid geometry/rules, protected routes, allowed layers and real SIGINT/SIGTERM cleanup. Schematic parity001 and amended area/contact002 are complete; do not rerun interrupted probes.

Installation006 at eae1f39 passed20commands/608then-current tests in a new local checkout/venv, plus actual native0findings/1via/67.933738mm and receipt readback. It reused installed tools/verified cache under network denial: not a fresh Mac or current release package qualification. [Evidence](evidence/installation-006/result.json). Rerun installation at the next major integration/release milestone.

## Checkpoints and backups

Latest independently verified GitHub checkpoint: **c3fa13fee77df16acffe4467daaf69efa7b9540c**; remote SHA and reviewed SVG code bytes match (`.runs/checkpoint-c3fa13f.json`). Preview002/private-copy and shared DRC failure-evidence changes follow this cutoff.

Latest incremental archive at0e8ed9d verifies88,824non-Git files/2,514,749,096bytes,1,126changed/new files/68,970,693bytes,0deletions; chain length3 and delta integrity pass, without a repeated full restore. [Receipt](evidence/backups/incremental-0e8ed9d.json). Last full restoration at e7a948a verifies86,673files/2,358,228,144bytes, allGitrefs and restoredCLIhelp. The retained old chain hit the unchanged128MiB metadata bound; a tested new full base replaced its next-parent role. No evidence was deleted. See [next parent and work](PLANS.md).

GitHub holds audited source/selected licensed evidence. Complete datasets/raw runs/private references/archives remain on this Mac; independent off-Mac protection is unmet. Full restoration cadence: major milestones, backup-system changes and pre-release; incremental snapshots preserve intervening work.

## Remaining gates

G3 representative30–50-family audit, generalized G4 gain beyond B1/B2, full G5 workflow, G7 untouched family-disjoint evaluation and G8 experimental RC remain open. Custom pads, unqualified format/rule semantics, advanced constraints and authentic library closure limit support. Learning is not justified; no model exists. Human/physical review and formal publication require separate authorization.

Continue [PLANS.md](PLANS.md): compatibility review/checkpoint, fresh actual before/after plotting controls, and source-backed PAW PRL/format/severity qualification. No native/engine worker remains after preview001 and PAW diagnostic001. Previous chronological status is preserved byte-for-byte in [history](docs/history/2026-10-12-2199621/STATUS.md); its old pending commands are superseded here.
