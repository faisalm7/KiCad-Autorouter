# Owned full-schematic transport qualification

This is a fixed, exposed development experiment for the explicit pinned KiCad10.0.7 API. Production defaults remain10.0.0. This experiment does not establish broader routing quality, installation, GUI support or release readiness.

`fixture.py` creates the new project `owned1007-protected-transport-v1` under GPL-3.0-or-later (see `COPYING`). Its symbols, footprints and design are owned primitives. It uses a different identity/UUID namespace and geometry from the older field controls, which remain unchanged.

The six ordinary through-hole terminals form three two-terminal nets:

- ROUTE has no source copper and needs a new14mm connection.
- KEEP has one exact locked0.3mm F.Cu track.
- GND has an originally unfilled B.Cu zone; native refill must establish connectivity.

The original four-file PCB/SCH/PRO/PRL packet has no DRU from creation. Default targets are0.3mm track,0.2mm clearance and0.8/0.4mm via/drill. Original global floors include0.25mm track/connection and0.3mm edge clearance. Critical checks are blocking, with no exclusions or ignored severities. This is a newly authored source, never removal of custom rules from the earlier design.

The complete flat schematic embeds owned one-pin symbols. PCB Datasheet`~` versus SCH blank deliberately exercises the qualified effective-field bridge; warnings are retained. Exact native finding counts remain experimental outcomes, not prescribed success values.

After software checks and an audited source checkpoint, the one-shot command is:

```sh
.venv/bin/python -B experiments/native_schematic_transport_v1/enclosure.py
```

It requires a fresh `.runs/native-schematic-transport-execution-002`. Never reuse or delete an existing run to repeat completed workers. `driver.py` invokes the ordinary pipeline and its shared uncached result checker with caller-pinned tools and explicit full-schematic opt-in. Eight base workers plus any actual field workers must be accounted for. All export/class/alias/SES/import/refill/metrics/protection/source/PRL/rule checks remain; only Default zero-alias ordinary standard whole-board transport is initially qualified. Unsupported settings reject. Default readers refuse experimental receipts.

The source DRC supplies the actual disconnected native control. Freerouting must create new ROUTE copper; final native validation must remove the open and preserve the original shell and locked copper. No new Native worker repeats the earlier bundle, rule-area or field controls. Those are pinned prerequisites. A failed outcome remains failed.

Route wall/full-CPU allowance is120seconds; the complete child experiment has170seconds and the enclosing process180seconds, including source preparation, tools, failures, readback and guarded publication. These are qualification bounds, not a comparative routing budget or speed claim. Processes reuse the existing bounded runner and shared sequential experiment lock. No paid service or runtime AI is used.

Portable source and context controls are in `tests/test_native_schematic_transport_fixture.py`, `tests/test_experimental_route_context.py`, `tests/test_native_parser_context.py` and `tests/test_experimental_route_publication.py`. Mocked worker tests establish software behavior only. Actual results and failures are stored separately.

Native001 failed at board load, exit3: KiCad rejected the initial SPDX semicolon. No DRC report, export, engine, SES or final candidate was produced. Its immutable source/rules/PRL and69raw files remain frozen. The corrected factory removes only the two PCB/SCH leading comments; exact design ASTs and PRO/PRL are unchanged. Complete GPL text/grant remains here. One before-control fails and all7corrected fixture controls pass. Full1031498 predates this fixture correction; core runtime bytes are unchanged. The fixed002 invocation carries001enclosure17.825710wall/8.990436CPU (including2publication) inside unchanged cumulative170/180bounds. Standalone research/software preparation is separate and does not establish a comparative routing claim.
