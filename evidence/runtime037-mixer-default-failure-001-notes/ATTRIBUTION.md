# Multichannel Mixer source and derived routing

The original Multichannel Mixer demo comes from the KiCad project,
`demos/multichannel`, official tag10.0.7, commit
69cafb907ebc09e7722a2a464b1d466fc2e3608d:
https://gitlab.com/kicad/code/kicad/-/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/multichannel
Mirror: https://github.com/KiCad/kicad-source-mirror/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/multichannel

KiCad's retained source LICENSE.README explicitly assigns all demos/* files to
Creative Commons Attribution-ShareAlike4.0 International. The exact license
and notice are physically retained under source-license/. The original source
and library credits, including embedded CERN Author/License properties, remain
unchanged. No new authorship of the original demo is claimed. The source
schematic explicitly warns that this is a demo, not a working audio mixer.

Generated candidate PCB/DSN/SES and copied/refilled design files in this packet
derive from that source and remain CC-BY-SA-4.0. Changes comprise the declared
whole-board unlocked-routing task, engine-generated routing and Native refill;
the unchanged original and exact source hashes are linked in files.json. The
candidate failed actual Native checks and is not an approved design. No KiCad,
CERN or original-contributor endorsement is implied.

Authored router/controller code remains governed by its repository GPL notice;
that license is not substituted for the demo and derived design license.
