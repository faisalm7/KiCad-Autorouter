# Netclass preferred dimensions versus hard rules

This is a source review and support-policy proposal. It does not alter existing receipts or accept the rejected interf002 candidate.

KiCad's 10.0 manual distinguishes default/optimal track and via dimensions from minimum/maximum constraints. A different netclass width or regular-via size alone is not a DRC violation. Original board Constraints and custom-rule limits remain authoritative; tuning-profile geometry has its own configured severity. The live 10.0 manual currently identifies itself as based on 10.0.7, so the installed 10.0.0 source was checked separately. [Official manual](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html)

Pinned KiCad 10.0.0 corroboration, fetched and hash-recorded in `kicad-source-access.json`:

* `drc_engine.cpp:172–190` generates board minima using `SetMin`.
* `drc_engine.cpp:293–308` gives a netclass track the board minimum and the class width as `SetOpt`.
* `drc_engine.cpp:363–394` does the same for non-microvia diameter and drill: board minima plus class `SetOpt` values.
* `drc_test_provider_track_width.cpp:104–113` tests explicit minimum/maximum values, not optimal width equality.
* Clearance is different: `drc_engine.cpp:283–285` sets class clearance with `SetMin`. Do not generalize preferred width semantics to clearance. Microvia diameter also has distinct source behavior and remains unsupported here.

[KiCad 10.0.0 implicit rules](https://github.com/KiCad/kicad-source-mirror/blob/10.0.0/pcbnew/drc/drc_engine.cpp#L293), [track-width DRC](https://github.com/KiCad/kicad-source-mirror/blob/10.0.0/pcbnew/drc/drc_test_provider_track_width.cpp#L104).

For interf002, the preserved project's board minimum track width is 0.2 mm. `/BIT5` has a preferred Default width of 0.4 mm and generated 0.3 mm segments. The exact-target gate rejects them as a declared support-policy mismatch; this is not by itself a native width error or proof of inadequate current capacity. Existing diagnosis artifacts also retain a distinct new `starved_thermal` native violation, which remains a blocker irrespective of target policy. Do not relabel that run accepted.

Proposed policy, before any wider experiment:

1. Keep exact-target mode available as an explicitly conservative scope. Preserve class membership/targets and original board/rule files. Disable Freerouting automatic neckdown, fanout, and explicit neck-width retry uniformly for all arms in that mode. Describe failures as `strict-target policy mismatch`, separate from actual native DRC.
2. Introduce a separately qualified native-rules mode only through a versioned protocol/code change and real controls. Continue exporting the unchanged preferred DSN widths/vias and verifying effective class mappings. Do not reduce preferred dimensions to ease routing. Permit preference deviations only when the original supported rules, native refill/connectivity, immutable geometry, and fresh bound DRC all pass. Unknown constraints remain unsupported. This changes our support policy, not the source design's rules.
3. Record every deviation's net/class, item UUID, width or via dimensions, preferred values, affected length, source of effective hard limits, native report identity, and selected support mode. Call it `different from preferred target and allowed by checked native rules`; do not infer a justified electrical neckdown, impedance adequacy, or current rating. Human/electrical review remains separate.
4. Before qualifying native-rules mode, run a positive above-floor/below-preference native control, below-floor and violated-custom-minimum negatives, class-mapping/DSN-target tamper controls, via annulus/drill negatives, and a retained new thermal blocker. Verify original rule bytes and exact final hashes for every control. No mocks establish qualification. Apply the same frozen policy to B0/B1/B2/C, with previous strict-mode failures retained in coverage.

The lead may finish conservative no-neckdown qualification first. The broader policy should be justified by source semantics and controls, never introduced solely to convert one failed board into a pass.
