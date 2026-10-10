# Current status

Updated October 9, 2026 (America/Los_Angeles).

This is an active experimental reconstruction, not a completed routing improvement or release.

G0 passed: macOS27.0.1 arm64,16GiB RAM; exact selected checkout and rebuild/local-20261010-015447 branch. Initial push683e41aab756cfb5c6a0c7c0f0ed37b8e18dc704 independently read back by remote Git SHA and GitHub README bytes. Receipt: evidence/backups/G0.json. Existing Git identity retained. No cloud environment or global protection/settings changed.

Working: a real offline CLI uses installed KiCad10.0.0 bundled Python, Freerouting2.5.0 JAR and Java25.0.2. Source projects and rules are copied and hashed. Native export/import/refill/DRC run on isolated copies. Output acceptance binds the final candidate hash and immutable content. Network is denied at the engine process boundary. Cancellation, ordinary descendant cleanup and bounded logs have real subprocess controls.

Fresh exploratory results (not a fair comparative experiment):

- Diagnostic smoke004: accepted, zero opens/blocking findings;2 routed signals plus a ground zone,6 pads,60mm tracks,0vias.6.721s end-to-end,3.784s total CPU. Native refill/connectivity is real.
- Licensed KiCad sonde stock002: rejected,3opens,7blocking findings,1library mismatch warning;566.454mm tracks,4vias.9.903s end-to-end,9.781s total CPU. This recovers the historical failure pattern on a different toolchain/source revision; no adapter improvement demonstrated yet.

Small raw reports/process logs are in evidence/runs. Full copied projects,DSN/SES,early crashes and exploratory evidence remain in ignored .runs; originals are .data and independently hash-verifiable. A new tested local archive is pending the next clean checkpoint. Those non-Git files currently have no independent off-Mac backup. Public sources can be refetched; unique experiment outputs cannot be reconstructed merely from a manifest.

G1 underway: real positive route exists; native negative control suite being rerun after tightening rules/file-set checks. Source-drc initially crashed with only an isolated config variable; all three official config/cache/documents variables work. Exact crash cause remains unknown. KiCad creates .kicad_prl during checks; validation now uses disposable identical copies. Adversarial review fixed malformed ignored-check reports and rule/file-set integrity gaps. Further resource polling and native controls are in progress.

G2 incomplete; G3–G8 unmet. B1/B2/C,30–50-family audit,untouched final evaluation,GUI qualification,fresh install,model,human review and physical validation do not exist as completed evidence. Custom rules/pads,netclass mappings,net ties,advanced vias and exclusions are blocked. Selected-net routing and schematic parity are not implemented. No superiority or speedup claim.

Continuation in this exact checkout:

```sh
python3 -m autorouter doctor
python3 data/fetch.py --verify
python3 -m unittest discover -s tests -v
```

Read PLANS.md and latest results; finish native controls, implement and measure graphics/planes/both adapter variants, then bounded equal-budget baselines and alternate-engine spike. Do not reuse run directories or erase failures. No background work is scheduled.
