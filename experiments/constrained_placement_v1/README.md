# Constrained placement search prototype

This experiment reuses the **MIT-licensed DTU-EKB/KiCad-Autoplace annealer** at commit `12bb5556fc5c1db287285425aea49a1d79dc8ffa`. Eight upstream modules and the complete copyright/license notice are retained unchanged in `vendor/`; `upstream.json` records their official paths, Git blobs, SHA-256 hashes and imports. No upstream KiCad writer, serializer, remote service or installation hook is used. This prototype is outside the installed routing product.

`prototype.propose(facts, seed=0, steps=200, alternatives=2, seconds=2)` returns source-bound transforms. `constraints.validate_alternative(facts, candidate)` independently checks each proposal. The exact input example is in `tests/test_constrained_placement_prototype.py`. Facts must come from a trusted project capture; a model must never invent or replace their constraints.

The first scope is an **initially feasible rectangular layout**, with at least two selected movable components and a fixed/unselected anchor. Fixed, locked, unselected and all components on any tracked net remain immovable. Allowed rectangular regions, quarter-turn orientations, unchanged front/back side, rectangular keepouts and a declared rectangle gap are enforced. Pad identities and supplied connectivity remain exact. Net labels become opaque tokens inside the search, disabling upstream name-based electrical heuristics. Changing side, rigid groups, polygon outlines, cutouts, initial overlaps and unrestricted full-board placement are explicitly unsupported. Track geometry is not modeled; routing corridors require explicit rectangular keepouts. Rectangular extents below one nanometre are refused.

The host reuses upstream moves, annealing and connectivity cost. It rolls back a move that violates the independent constraints and verifies every returned alternative again. Limits are 32 components, 256 pads, 1,000 steps per alternative, three alternatives and five seconds of cooperative wall/CPU checking. Cancellation or budget exhaustion returns no proposals. These are cooperative limits, not an OS resource quota. A smaller proxy cost is not proof of easier routing, better electrical design or less human cleanup.

Run the small deterministic and adversarial controls:

```sh
.venv/bin/python -B -m unittest discover -s tests -p test_constrained_placement_prototype.py -v
```

The original 14-test evidence is retained. Independent review reproduced an oversized-integer error and numerically collapsed tiny rectangles; both now have refusal regressions, with 16 controls passing on Python 3.11.9. Native project capture/application, KiCad validation, useful graphical alternatives and subsequent routing remain separate gates. No proposal authorizes execution, acceptance or PCB manufacture.
