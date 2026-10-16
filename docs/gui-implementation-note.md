# External graphical workflow implementation

`autorouter.gui` is a wx wrapper around the existing typed CLI. It provides labelled routing/protection, profile, adapter, layer, budget, via preference and exact selected-net controls, plus explicit preset loading and exclusive preset saving. Defaults come from `preferences.DEFAULTS`; optional improvement is explicit and retains the existing pruning-scope restrictions.

From the checkout, launch with the pinned KiCad wx-enabled interpreter:

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9 -B -m autorouter.gui
```

The product KiCad entry point is a separately packaged IPC `exec` plugin launcher, owned by the lead integration. It only starts this external process. No IPC client, source-buffer access or editor mutation is claimed. `register_kicad_action()` is an unqualified legacy compatibility hook, not the preferred installation path.

The user selects the exact saved PCB and an existing output folder outside the source directory, then acknowledges that both PCB and schematic editors were saved and closed. Matching project and schematic files are required. The UI captures a bounded complete source inventory (32 MiB, 2,000 files, 4,000 entries), source directory and output inode identity, and exact validated settings. Changed source, settings or destination refuses continuation. This acknowledgment is explicit user information; the UI cannot inspect unsaved editor buffers.

Preview, route/improve, checked disposable review, accept/reject intent, fresh export and current export readback are separate steps. CPU-intensive work uses the checkout's existing CLI interpreter in a child process, outside KiCad and outside the wx event thread. Review/export CLI readers retain authority for validation; a UI label or test mock is no substitute. Opened review/export projects remain separate. There is no live apply, automatic overwrite or undo claim. Accept intent requires manual review acknowledgment and remains distinct from electrical, physical or manufacturing approval.

Cancel and the per-action watchdog request SIGINT once. The existing CLI runner owns Native/JVM cleanup. The GUI waits for CLI exit, preserves bounded logs and process metadata, and rejects cancellation even if the child exits zero. Closing while busy requests cancellation and waits. The GUI does not independently certify descendant cleanup or impose a new process-tree kill policy. Forced application termination remains outside this cooperative guarantee. Source collection and readback use existing bounded file helpers; the watchdog covers the child invocation, not an OS hard quota for the entire UI.

Implementation controls are portable software tests only. At authoring, no tests, GUI window, routing, Native worker or JVM were run by the author. Direct import established that checkout Python lacks `_tkinter`; wx is the chosen backend, not a new dependency install. Lead independently reported a successful pinned wx import. Actual GUI qualification remains required: start through the project-scoped KiCad exec launcher; inspect all labelled controls and preset round-trip; verify exact saved/closed source acknowledgment; exercise successful preview/review/fresh export and all findings; cancel during real work and verify cleanup and unchanged source; test stale source and refusal. Existing installed046 evidence does not qualify this new interface.
