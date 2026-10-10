# Roller Encoder source-closure review

The Roller Encoder remains the smallest development support candidate in this
batch, but this bounded review does **not** fully close its dependencies, asset
rights or family ancestry. No production support gate changed; no native/engine,
installer, dataset code or third-party contact ran. Five primary API pages were
requested; four succeeded and one wrong directory spelling returned404. All saved
new payloads are JSON metadata. Originals were rehashed against acquisition records.

## New checked evidence

The board is SparkFun Roller Encoder Breakout at
`9aeb5e878ea6ae5c3becabfbdb2607528404c4b3`. Its complete observed reachable history
contains three commits: initial `d54c9fc1358dcebeddf3058d1d723cdddfe12f5a`, README
addition `9fd49bae91c8c9bb70f393d035ae39413fa329a5`, then the pinned README change,
all on2025-04-28. The initial commit has no parents. That establishes the published
Git ancestry, not how the hardware or imported assets were created before publication.
[Primary history](https://api.github.com/repos/sparkfun/SparkFun_Roller_Encoder_Breakout/commits?sha=9aeb5e878ea6ae5c3becabfbdb2607528404c4b3&per_page=100)

The complete, nontruncated SparkFun library tree at already recorded pin
`25af7faf567c3c6627d5065acf771ba0ff883103` has1054 entries. It contains
`3dmodels/Electromechanical.3dshapes/Roller_Encoder.step`, Git blob
`5d1d7b5d15e7e33cff1a52977a76cac11bb9c218`,552428bytes, and all four named
nut/screw model leads. The five model blobs total1807151bytes; none was fetched.
The custom `RollerEncoder:RollerEncoder` footprint has no matching named file in
that tree. The electromechanical footprint directory itself contains nine other
parts. This pin is a source lead, not a proven matching dependency snapshot.
[Complete pinned tree](https://api.github.com/repos/sparkfun/SparkFun-KiCad-Libraries/git/trees/25af7faf567c3c6627d5065acf771ba0ff883103?recursive=1)

History of the board's old model path identifies introduction
`61dfcfcea753a004b6bf6164578e6eb80973fffb` on2025-01-28, whose message names the roller
encoder, and folder rename `6dbab669c783daca89a69d3c60fdbb0fb667e35a` on2025-10-16.
This yields a much narrower historical acquisition target than downloading today's
entire library. Metadata alone does not prove old/new blob equality, original model
authorship, or license rights for that individual model.
[Old-path history](https://api.github.com/repos/sparkfun/SparkFun-KiCad-Libraries/commits?sha=25af7faf567c3c6627d5065acf771ba0ff883103&path=Footprints%2FSparkFun-3D-models%2FElectromechanical%2FRoller_Encoder.step&per_page=100)

The saved five-page URLs, dates, SHA256s, unsuccessful404 and byte counts are in
`fetch-receipt.json`; source SHA256s and candidate model blob IDs are in `closure.json`.
Web reader failed to access the initial three API URLs; bounded direct HTTPS GETs of
those same URLs supplied the retained raw responses. No credentials were requested.

## Existing rights evidence, carefully scoped

The pinned board's own [LICENSE.md](https://raw.githubusercontent.com/sparkfun/SparkFun_Roller_Encoder_Breakout/9aeb5e878ea6ae5c3becabfbdb2607528404c4b3/LICENSE.md)
is already retained and rechecked locally: it explicitly assigns the hardware
CC-BY-SA-4.0 and code MIT separately. Preserve SparkFun attribution, license link,
change notices and applicable share-alike terms for board derivatives. This is
actual publisher permission evidence, not a finding that the publisher owns every
third-party item embedded or referenced by the project.

The separately pinned library README is already retained under the earlier audit;
it grants CC-BY-4.0 and explicitly describes a mixture of KiCad stock, SparkFun and
open-source model assets. Keep that notice, but trace exact footprint/model origin
and any asset-specific notice before public redistribution. No model headers or
upstream model-vendor licenses were inspected in this five-page task. The custom
RollerEncoder namespace and exact historical footprint remain unresolved. Do not
claim the board's root license automatically licenses that external collection.

All six schematic symbol identities have embedded definitions, without external
extends or sheet files; the board preserves its embedded footprint geometry. Thirteen
labels identify FreddySpark-Regular in generator metadata. The previous audit holds
its SIL-OFL-1.1 notice and KiBuzzard's MIT notice. An installed generator/font is not
needed to preserve already embedded polygon artwork; editable regeneration and
font redistribution are distinct scopes and need their own provenance. Do not
install plugins or fonts merely to read this board.

## Ancestry: narrower evidence, still not independence

The previously observed shared footprint UUIDs were resolved against the actual
unchanged acquired boards. With VEML7700 and SFA40, Roller shares a zero-pad SparkFun
logo and the ST4 standoff; with full-size LIS3DH it shares only ST4. Exact UUIDs,
identities and pad counts are in `shared-object-classification.json`. This supports
common template/branding reuse, not demonstrated reuse of the encoder circuit.
Conversely, different function and lack of matching active-component UUIDs do not
prove independent circuit ancestry. Public Git starts from an initial import.

The smallest defensible split decision now is to keep Roller and the related
SparkFun template group development-exposed, never label this board an independent
holdout family. A later circuit graph audit should compare connected terminals,
active topology, repeated subcircuits and footprint poses across the considered
projects, excluding neither inconvenient relationships nor whole-board transforms.
No human reference tracks should enter features or candidate generation.

## Smallest concrete path to closure

1. In a separately bounded metadata follow-up, inspect introduction61dfcfce and
   its pre-renaming historical library tree. Resolve the exact Roller model blob,
   the five other footprint identities, and the custom RollerEncoder source. Seek
   file headers/history and exact notices; absence remains unresolved rather than
   being filled by a current snapshot guess. No contact is required for that step.
2. After rights evidence is sufficient, acquire only the required pinned assets
   into a new ignored dependency directory, with expected blob/size/SHA256 and all
   applicable notices. The present five model leads total about1.81MB; do not fetch
   a full library or silently replace the historical asset. Verify any earlier
   model version against the exact board references and record differences.
3. Keep native originals byte-for-byte. A separately recorded project-local
   dependency map or sandbox environment may resolve original namespaces/old model
   paths only after exact identity is proved. No global path settings, source
   relinking, footprint replacement or severity changes. Exporting embedded parts
   to a cache is not evidence that they match upstream libraries; do not suppress
   library mismatch checks by presenting such a cache as authentic vendor data.
4. Once closed, let the lead schedule native complete-project load, library/model
   resolution diagnostics, schematic/board parity, refill and export controls.
   Separately qualify inactive5mil class semantics, text_on_edge_cuts and the
   declared B.Cu jumper layer under unchanged rules. Padstack policy has evolved
   since the old static audit; its historical rejection is not a current native
   result. No route experiment is justified by this research alone.

A narrower embedded-2D routing-replay scope might eventually be possible while
editing/3D dependencies remain incomplete, but it must be explicitly specified and
native-tested as such. This review does not relabel it full project closure.
If exact custom/model origin cannot be established from public evidence, retain
this source as unsupported and investigate another licensed candidate; do not
manufacture certainty or remove it from the population denominator.
