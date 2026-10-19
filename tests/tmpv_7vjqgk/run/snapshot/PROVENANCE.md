# Owned board-floor consistency test seeds

These small seeds derive from the project-owned forced-via diagnostic geometry and actual KiCad observations in `board-floor-forced-via-001`. Test code rebinds all paths, source hashes and process receipts synthetically. Passing these tests is evidence of consistency checks, never a new native validation run.

The board geometry and generated routes are original project work under this repository's GPL-3.0 license. `fixture.kicad_pro` is the unchanged KiCad multichannel demo settings file, SHA-256 `ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538`, from the repository's already audited/pinned KiCad source manifest. Original notice and CC-BY-SA-4.0 license copies remain in `_licenses`. This project-settings file is separately attributable third-party material, not relabelled as project-owned geometry.

The DSN root display name is normalized to `owned-floor-fixture.dsn`; no routing/net/pad/rule geometry changes. Transient original absolute paths and input hashes are removed from context seeds and reconstructed in each test's disposable project. The final native DRC seed is an empty-report schema sample from the same development control. All seeds are development exposed.
