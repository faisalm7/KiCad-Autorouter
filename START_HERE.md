# Use the local autorouter

This is the existing local project at `~/Projects/KiCad-Autorouter-local`. Keep this folder and its prepared environment. Routing runs locally without Codex, an AI subscription or internet.

Open Terminal in this folder and check the installed tools:

```sh
cd ~/Projects/KiCad-Autorouter-local
.venv/bin/python -B -m autorouter doctor
```

Follow the [local demo](docs/quickstart.md) for a small public board, or the [ArcDice demo](docs/arcdice-demo.md) for the qualified class-parent workflow. Only the explicit public demo download needs internet. Each routing attempt uses a fresh output folder and preserves the complete original project.

Use [saved preferences](docs/routing-preferences.md) for routing scope, permitted new layers, time limits and optimization. Use `--keep-existing` to protect existing copper during partial completion; locked copper remains protected. Unsupported constraints are explained and blocked.

The [KiCad workflow](docs/gui-workflow.md) creates before/after copper plots and a separate review project. Inspect it through KiCad Project Manager. Acceptance records intent, then a fresh native-validated export creates another separate project. Rejection records rejection. Press Control-C to cancel. Save editor changes first: this external workflow cannot inspect unsaved buffers or apply verified live-editor undo.

This is an experimental tool. Nine exposed development circuits show shorter native-accepted routing than the corrected and tuned/restart baselines under equal budgets within each comparison. Independent circuit ancestry remains unproved, so these results do not establish general superiority. The cited comparisons retain their original warnings, recorded in their native evidence. Native acceptance is separate from electrical, manufacturing or human PCB approval. [Actual status and limits](STATUS.md), [local handoff qualification](docs/experimental-rc.md).

Source and small sanitized evidence are backed up on the authorized GitHub branch. Private boards, raw experiments, downloaded tools and references stay out of Git. Their tested archives remain on this Mac by your current choice. No formal release or package has been published.

The original preparation instructions are [preserved as history](docs/history/2026-10-14-4b1e871/START_HERE.md). They are not instructions to restart this checkout.

An additional [temperature-interface example](docs/ds18b20-demo.md) now has actual generated-routing/full-schematic qualification. C ties its tuned baseline; no extra gain is claimed.
