# Mixer hierarchy diagnostic001 — completed once, production deferred

The final reviewed controller002 ran once against source HEAD
`0cf76553dc2439a001219a173b0c72f4e2289f6a`. The earlier controller001 was
preserved without execution. Both source folders below are verbatim copies.
Their historical “Unexecuted” docstrings/SCOPE headings are retained, not edited
into a retrospective claim. Do not run these copied controllers in place: their
ROOT calculation and fixed output refer to the original `.runs` layout, and the
completed output must not be reused.

Actual KiCad10.0.0 original-rule fullSCH DRC returned **232findings:24blocking
clearance errors,208warnings,0opens,0exclusions**. The raw report is copied
byte-for-byte as `native-original-fullsch.json`. Its115actual parity warnings
comprise114footprint-identifier differences and one J6value difference. Another
81warnings are footprint-library mismatches; the remaining12are other retained
warnings. These are actual source/native findings, not prototype path errors.
Original severities, ignored checks, source/library bytes and constraints were
preserved. No Native finding was removed or waived.

The prototype recorded114instance defers because its model required the source
root UUID in exported Native sheetpaths. The actual export uses `/` for the10root
components and `/sheetUUID/` for26components in each of four channel instances.
All114stored source expectations equal that actual path with the root prefix
added. This is a prototype model error, not evidence that114source components
need repair. Correcting that assumption would not establish the subsequent
UUID/PCB identity checks, and would not remove the115separate Native parity
warnings.

The prototype also recorded31numbered-pad membership defers: each has an empty
PCB net and no corresponding exported net node. All280other numbered-terminal
comparisons matched. Native reported zero opens. No new NoNet exemption, pad
removal, net renaming or source repair follows from this observation.

The effective-field prerequisite remained false: `other symbol mismatch or
malformed finding`. The Default-class prerequisite independently stopped at
`Class parameter below original board floor: width_nm`: actual/configured
Default width200,000nm versus the original300,000nm board minimum. All80actual
PCB class rows and all80explicit exported schematic class encodings were
Default, but that observation does not override floor checks or establish
hierarchical class membership/inheritance. No rule or dimension was changed.

The bounded root/leaf closure and five pure falsifiers passed. That establishes
only this captured two-file/four-instance closure. All production flags remain
false. Current preflight still rejects schematic hierarchy dependency closure
and class intent as unverified. No routing, engine, JVM, source save, GUI,
human PCB review, electrical/physical validation or generalized improvement
was performed or established by this diagnostic.

Complete external timing was1.48s wall/1.57s CPU preparation plus12.51s
wall/12.02s CPU for the one run: **13.99s wall/13.59s CPU total**. The separate
published budget counter is14.322210291982628s wall/13.682693s CPU, including
a2s preparation-publication allowance and sampled invocation totals. It is not
a second experiment or a substitute for complete external timing. The declared
whole budget was120s; per-process logs256KiB, sampled group RSS2GiB, complete
scratch128MiB and captured source16MiB/40files. Polling can overshoot; these
are not OS-enforced quotas. Read-only curation cost is separate from that run.

During curation, the existing shared `check_drc_stage` and normal-policy readers
were applied to the saved absolute source/input/report paths. They matched the
recorded native summary. Current17-file source and retained original match the
protocol; the18-file Native input matches shared `binding.after`, whose only
addition is the allowed generated PRL. Current implementation hashes match the
recorded code. This readback did not launch Native/JVM or import either draft.
The consumed class-map/netlist/observer/report/process hashes and all original
source/tool/helper pins are in the public summary/protocol/consumed-inputs record.

The original source is KiCad's `demos/multichannel` at commit
`69cafb907ebc09e7722a2a464b1d466fc2e3608d`, recorded in `data/sources.json`.
KiCad and the original demo/library contributors retain their source rights.
Pinned LICENSE.README assigns demos/* to CC BY-SA4.0. The reproduced diagnostic
findings and source-derived comparison data retain that attribution and
CC BY-SA4.0 scope; the complete license is included. The historical embedded
schematic exception is not generalized to PCB artwork. The project-authored
controllers retain their GPL-3.0-or-later SPDX declarations. No original board,
schematic, library, bulk netlist, binary or engine was copied into this evidence
folder.

The historical commands used the original controller002 path with modes
`prepare` and `run`, each with the exact source HEAD above. They are retained in
SCOPE.md as history, not instructions to overwrite/repeat this completed attempt.
Any justified follow-up needs a new version/output, frozen scope and cumulative
prior costs. This diagnostic remains deferred; no source fix is inferred.
