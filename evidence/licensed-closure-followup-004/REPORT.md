# Closure follow-up004: exact models acquired, one upstream rights chain resolved

Three exact originally referenced model blobs are now in **research staging only**:510,932bytes, individually Git-blob/SHA-256 verified. No model was added to `.data`, published, loaded into KiCad or executed. All81 original project files remain byte-identical. The full follow-up used20HTTP requests and952,778response-body bytes, within the20-request/2MiB ceiling; network work stopped at the request cap. Every request had a30-second timeout and bounded response read.

| Model | Original pinned Git blob | Actual header/provenance finding |
|---|---|---|
|SM04B-SRSS-TB.STEP|5167178f7b0fa44d9595431b7ec2fa3727b6d124|Header names an Adafruit-Feather-M7-1011-PCB module path; author/organization are blank. Autodesk/ST-Developer export metadata is not a rights grant. Exact repository-name search returned no match; that is not proof of absence or authorship.|
|S2B-PH-SM4-TB.step|7bfe9f28cc256f423bc691e3937777a1ca22f6db|Header points to Gregory Davill's gsd-kicad-libs. The original source and original MIT notice were found at the same immutable commit; detailed chain below.|
|Jumper_2_P2.54mm.step|8002c3ae73ffaf8c30050b986fa1d57e8debe65b|Header gives a generic desktop filename, blank author/organization and Autodesk/ST-Developer export metadata. Its exact import commit and repository MIT notice are available; independent model authorship is not identified.|

All three have concrete arturo182 MIT2019 notices both at the already pinned module revision and at their exact introduction commits: [SM04 introduction](https://github.com/arturo182/kicad-modules/commit/4e46778b73a1d9077e2d3960f56c79fcf9d3555e), [S2B introduction](https://github.com/arturo182/kicad-modules/commit/76f8be030d91e6b123b37f3898e09f0f66331049), [jumper introduction](https://github.com/arturo182/kicad-modules/commit/922fb3252cfddcb4b2e2b85c2cefef36fa95bd9a). Each introduction's actual LICENSE bytes match MIT blob b72430dd28b649c004e6e82ecfa008ae4cecdb48. Import authorship is not automatically geometry authorship. Complete nontruncated pinned module trees have no model-local license or README; their sole notice is root LICENSE. No rights conclusion relies on absent notices.

## Exact S2B origin and additional notice

[Gregory Davill's original model](https://github.com/gregdavill/gsd-kicad-libs/blob/47107d92f4ad33e915fb0a173a66457c68952ca6/packages3d/gkl_conn.3dshapes/S2B-PH-SM4-TB.STEP) has Git blob5ab7029db9def9c8106da4ec36a5118cf6bdfc43 and156,771bytes. Replacing its3,210CRLF pairs with LF yields **every byte** of the153,561-byte arturo182 model. No geometric equivalence approximation was used. The model and [MIT2018Gregory Davill notice](https://github.com/gregdavill/gsd-kicad-libs/blob/47107d92f4ad33e915fb0a173a66457c68952ca6/LICENSE) were both retrieved at commit47107d92f4ad33e915fb0a173a66457c68952ca6. Notice blob8c33ecef42299f787fc7733fb8fa6e7ca02162c6 is verified.

This establishes an upstream notice chain for that asset. If the lead later adds the exact model to a dependency package, retain Gregory Davill's MIT2018 notice **in addition to** arturo182's MIT2019 notice. The current original project lacks this extra notice because the model itself was not acquired there. Preserve original source trees and attach such provenance in a separate audited dependency package. No model publication is authorized by this follow-up.

## Stock library identity remains unresolved

Neither original project names a stock-library Git revision. Their pinned-library lists are empty, no sym-lib-table exists, and fp-lib-table defines only the local Symbols_Extra directory. Actual schematic references use Connector_Generic and power; PCB references use Connector_JST and Connector_PinHeader_2.54mm. Model aliases `${KISYS3DMOD}` and `${KICAD6_3DMODEL_DIR}` specify environments, not exact library commits. Bare `pcbnew` generator strings, board format versions, embedded symbol/footprint copies and uninterpreted cache header numbers do not uniquely identify historical libraries.

Accordingly no installed/latest stock library was substituted, no aliases were renamed, and no exact historical match was invented. The PMOD symbol repository remains present but unlinked to actual stock schematic identifiers. Three staged local models do not complete stock footprint/symbol/model closure. The population remains16acquired boards,7complete/9incomplete and3eligible/13unsupported. Production and diagnostic acceptance counts remain unchanged.

## Smallest next compatibility step

Prioritize LiPo for a bounded **diagnostic**, because its current static rejection is only PCB format20220621. Keep the original files immutable and the current source gate closed.

1. Resolve an authentic stock-library identity or explicitly retain the dependency-unqualified classification. Assemble only verified named dependencies and their original notices in a separate ignored package; do not silently substitute embedded footprints or omit the hidden jumper model.
2. On a disposable complete copy, first observe pinned KiCad10's loaded geometry, original project rules/severities, effective Default class, pad/net identities and native DRC without saving the board. Record the known unsupported input scope; a successful load or clean report is not routing admission.
3. Compare every effective constraint and identity against the unchanged original source. Establish old-format positive and deliberate width/clearance/via/drill/exclusion invalid controls before proposing any narrow format support. If a conversion is needed, preserve both files and prove semantic invariants; never manually relabel the version or normalize rules to make it pass.
4. Only a separately reviewed implementation and fresh native qualification could open that scope. PMOD's legacy Power binding, five unknown severity keys and below-floor class width make it a later compatibility task.

The staged STEP files and raw model API responses stay ignored. `findings.json` records exact notices, body hashes, metadata pins, header observations, unresolved stock references and the original-tree guard. `analyze.py` performs only pure readback checks. No source gate, original rule, alias or application installation was changed.
