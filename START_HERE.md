# Use the local autorouter

This is the existing local project at `~/Projects/KiCad-Autorouter-local`. Keep this folder and its prepared environment. Routing runs locally without Codex, an AI subscription or internet.

The graphical launcher has been tested on this Mac within the scope below. In the prepared checkout, close other KiCad applications, then create a fresh local launcher once:

```sh
.venv/bin/python -B scripts/install_gui.py --output .runs/autorouter-launcher-001
```

Double-click `Launch Autorouter.command` in that folder. Open a saved project in its KiCad window, open PCB Editor and click the green autorouter icon. The routing window lets you choose scope/protection, supported layers, preferences and budget; preview support; start/cancel; review findings; record accept/reject intent; and export a freshly validated separate project. Save and close the source PCB/schematic editors before confirming their exact paths. The launcher uses local settings and requires this checkout and pinned tools to stay in place. Prepare a new launcher after a source update. [Workflow and qualification limits](docs/gui-workflow.md).

The CLI remains available. Open Terminal in this folder and check the installed tools:

```sh
cd ~/Projects/KiCad-Autorouter-local
.venv/bin/python -B -m autorouter doctor
```

Follow the [local demo](docs/quickstart.md) for a small public board, or the [ArcDice demo](docs/arcdice-demo.md) for the qualified class-parent workflow. Only the explicit public demo download needs internet. Each routing attempt uses a fresh output folder and preserves the complete original project.

Use [saved preferences](docs/routing-preferences.md) for routing scope, permitted new layers, time limits and optimization. Use `--keep-existing` to protect existing copper during partial completion; locked copper remains protected. Unsupported constraints are explained and blocked.

The [KiCad workflow](docs/gui-workflow.md) creates before/after copper plots and a separate review project. Inspect it through KiCad Project Manager. Acceptance records intent, then a fresh native-validated export creates another separate project. Rejection records rejection. Press Control-C to cancel. Save editor changes first: this external workflow cannot inspect unsaved buffers or apply verified live-editor undo.

This is an experimental tool. Development comparisons show configuration-specific length gains, ties and failures against corrected and tuned/restart baselines under the recorded budgets. They do not establish added completion or general superiority; independent circuit ancestry and unexposed confirmation remain unproved. The cited comparisons retain their original warnings, recorded in their native evidence. Native acceptance is separate from electrical, manufacturing or human PCB approval. [Actual status and limits](STATUS.md), [local handoff qualification](docs/experimental-rc.md).

Source and small sanitized evidence are backed up on the authorized GitHub branch. Private boards, raw experiments, downloaded tools and references stay out of Git. Their tested archives remain on this Mac by your current choice. No formal release or package has been published.

The original preparation instructions are [preserved as history](docs/history/2026-10-14-4b1e871/START_HERE.md). They are not instructions to restart this checkout.

An additional [temperature-interface example](docs/ds18b20-demo.md) now has actual generated-routing/full-schematic qualification. C ties its tuned baseline; no extra gain is claimed.

The current prepared candidate is [runtime008](.runs/runtime-directory-008/runtime/RUNTIME_README.txt), built from source76d2c666. Protected4Cu Route,2Cu Improve and fresh separate Native exports pass. [Actual GUI059](evidence/gui-runtime008-059-native-opening-001.json) launched from KiCad and completed preview, routing, rendered review, test intent, export and checked opening. Opening subsequently changed project metadata; the next check visibly refused it as stale. [Current qualification](evidence/runtime008-export-accounting-integration-001.json) preserves every warning/control and the earlier export-accounting failure. This is a local directory artifact, not a published package or completed release.

**Constraint scope:** archived006 wrongly accepted a schematic/PCB class mismatch. Current008 explicitly refuses schematic class directives and hierarchies until their complete inputs and class equivalence are verified. The exact old counterexample now refuses; no original rule was repaired or weakened. [Coverage](evidence/corpus-population015-class-guard-cohort-001/SCOPE.md) retains both newly refused hierarchical projects.
