# Independent actual forced-via transport review

**607 checks passed, no failures.** The owned fixture's real export → floor guidance → adapter → Freerouting → SES import → refill → final native DRC path completed successfully at frozen production commit `efc174e8ffda7796d56f663d87885b444c7bc729`, reviewed driver SHA `12d4eac8691c8abe8e382e5bbbd593c30c07e038b18d79dc30fd447c981b70cc`.

The original SIGNAL_A terminals are SMD on disjoint front/back copper layers, with no source routes, zones, plated pads or other conductive interlayer objects. Actual completion therefore needs a layer transition. The source/project/native input hashes, exact terminal mapping, unchanged five native floors, all code/helper/tool hashes, raw/guided/adapted DSN receipts, exact engine argv/settings, SES bytes, import command, final candidate, fresh final context and DRC input/report hashes were independently checked.

The exact production completion-only profile used a 60-second internal engine job allowance, optimizer disabled and all three width-reduction controls off. The real process finished without timeout (2.578222917 seconds wall / 1.412575 CPU), saved a nonempty SES and exited successfully. The adapter was an actual no-op for this fixture, with preserved two-net/four-pin mapping.

An independent SES decoder checked its `um 10` scale, Y-coordinate conversion, every net/path segment and the selected `Via[0-1]_1500:300_um` padstack. All seven segment widths are 0.3 mm. The single SIGNAL_A via is 1.5 mm copper diameter with a 0.3 mm drill at (41.645, 13.96) mm. Every segment and via equals the actual imported saved geometry and the final candidate. Fresh native readback independently measures the same copper/drill/layers/net/position. Thus this run supplies the previously missing nonzero-via import evidence for these exact dimensions.

Final candidate SHA `c1a82c6e4749250ce3ce96ac5455bd38f71458bbfeefdf6fd7671eb096e3991a`; final report SHA `6be6649367d9505505fcc0b11be84d561559b5267127170357c6a74c2f13b525`; SES SHA `60b038739ccb4d8c55c5f18f2585e7fc41bc8a1c5b7e638ec1aac02287e62bbe`. Actual final native validation has zero opens, blocking errors, warnings and exclusions under unchanged original project settings. All seven original ignored checks are preserved.

All seven native/engine/import process receipts are registered once. Whole-operation measured cost is 6.759126791 seconds wall / 4.816742 CPU, including preparation and waited children, inside separate 120-second limits. These are cooperative/final measured caps, not an OS aggregate CPU quota. The stored sample precedes final freshness/publication and the driver checks the caps afterward.

This owned exposed fixture is a diagnostic, not a benchmark family. Production eligibility/integration, broader dimension transport, broader-board route completion, physical/electrical validation and human PCB review remain separate. The source-topology object's `engine_via_emission_qualified=false` is a retained pre-execution premise; the actual case records a measured one-via success. Top-level routing/comparison/production-support flags remain false intentionally.

Public subset bytes were independently checked in the companion geometry002 review: all 76 selected raw files match (571,363 bytes). No reviewer native/engine jobs ran; no original evidence, drafts or tracked files were modified.
