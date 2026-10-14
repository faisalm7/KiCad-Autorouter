# Source and acquisition audit scope

Pinned evidence comes from `.local-backups/new-family-leads-20261014-001/leads.json`; native source bodies were read in memory in that task and were not retained as a reusable cache. This draft makes no network request and has no geometry/model payload. Protocol pins5original files347,566B and preserves every source filename and notice.

Static source observation: F/B copper; PCB20241229/SCH20250114; flat schematic; Default-only class;17footprints117circle/oval/rect/roundrectpads;1zone; no observed keepout, padstack, net-tie-group or DRC-exclusion nodes. Native/full-schematic parity, source validity, ordinary-pad DSN conversion, routing, original-shell geometry and actual library warnings remain untested. The source has multiple line/arc Edge.Cuts segments, including near-coincident endpoints; no rectangle adaptation is assumed. Original minimum copper-edge clearance0.5mm remains authority.

MIT hardware scope is explicit in README and the body is supplied in LICENSE. Embedded logo/library ancestry is not independently established. A private-path external model is unresolved; no path/body is copied into this public draft, no STEP/model is fetched, and no source model declaration will be changed. Do not publish raw boards or assume independent third-party asset grants. No electrical/USB/timing/current/thermal/manufacturing conclusion is made.

Existing baseline is the actual complete current .data inventory from the existing bounded shared.inventory helper, captured read/hash-only under unchanged caps. Its capture CPU/wall is retained in protocol.json. No source root was omitted or mutated. The whole source tree must be rechecked by existing shared.inventory before acquisition; unknown entries/collisions/symlinks/drift stay fatal. All acquired/unsupported/rejected sources and reserve dispositions stay intact. The reserved SolderParty CP2102 design was not accessed or reclassified; matching chip/function is an ancestry caveat. This lead is exposed development data, never independent holdout by different-author assumption.

Tests are authored tiny synthetic acquisition controls, not dataset-derived fixtures. Mock Git/transport are explicitly limited to temporary owned roots; actual shared payload/inventory/material/publication logic is exercised. No test was executed in this draft. No native_snapshot/capture/driver registration is included. Before any Native use, require a real acquired_unqualified receipt and exact immutable source verification using existing helpers, then separately qualify original/native/routing gates. Never erase prior errors or treat cache/archive/test growth as routing progress.

Apply-base pins for the seven existing source/test paths (read only during draft; re-review if any move before applying):

- `experiments/licensed_acquisition_v1/fetch.py` SHA256 `56902cfc2b281323801279ba613cd3429b19a51810283aa31e4254d36a5c10c8`
- `experiments/licensed_acquisition_v1/test_fetch.py` SHA256 `eeb9e23d4a47852a3fd6c0249689c8c3873792712cdc40090bf54c8ad8da3fcf`
- `experiments/licensed_acquisition_v3/test_fetch.py` SHA256 `aa70d0be6338d43b586177214a6b0deb9f2815562e96b0d7984652df6836a1fc`
- `experiments/licensed_acquisition_v4/test_fetch.py` SHA256 `d528b79e118d432b9351cc48511667f5400b319f3aa37ecd15815fac35b37492`
- `experiments/licensed_acquisition_v5/test_fetch.py` SHA256 `6062245a93f5feeed3a8e13603ae94f6e632b37858f13c231c35565c2533f3f9`
- `experiments/licensed_acquisition_v6/test_fetch.py` SHA256 `b2c111c847692fd918a78d2a95e95a62f980ead16643ad16439908f685782dd7`
- `experiments/licensed_acquisition_v7/test_fetch.py` SHA256 `e2b5f1bd1ec82b12c89a72a7de493594cf48574b58c9f876a2db4cf443c2e469`

Integration adds ONLY `experiments/licensed_acquisition_v8/{fetch.py,test_fetch.py,protocol.json,existing-data-inventory.json,README.md,STATIC_AUDIT.md}` and applies `patch.diff` to the seven paths above. No capture/native/registry/source-board changes. The six unknown-profile test edits change only the sentinel v8 to v9; no decoder or acceptance assertion is weakened.
