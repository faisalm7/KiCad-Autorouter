# Fresh-checkout installation test

Status: prepared; no execution result is claimed by this document. The lead runs
this after the sequential quality experiment and after committing the exact
installation-test implementation. Native and engine tests must remain sequential.

```sh
python3 scripts/install_smoke.py --output .runs/installation-001
```

Use Python 3.11 and a new output directory. The source checkout must have no
tracked changes or nonignored untracked files. The script refuses an existing
output and preserves partial outputs and command logs on failure or cancellation.
It never removes or modifies the original checkout's tracked files, Git identity,
global Git configuration, installed applications or private preferences.

The test clones the exact committed local HEAD into the output directory with
`--no-local --no-hardlinks`, checks out that commit detached, and compares every
tracked file against a source hash inventory. This is a disposable test fixture,
not a competing development checkout or managed worktree. Git hooks are disabled
for these commands; no user/global Git configuration is written. A newly created
Python virtual environment uses interpreter copies and no pip installation;
the coordinator has only standard-library dependencies.

The official Freerouting JAR is copied from the existing verified cache and
checked for the pinned hash and independent file identity. The copied checkout's
`setup_engine.py` runs with network denied and must verify that cached asset.
The test then runs doctor, the full lightweight unit suite, a real native route
of the project-owned smoke fixture, and `check-result`. The native receipt must
bind to the tested commit and unchanged source. Final tracked inventories,
clean status and HEAD are checked for both checkouts.

`result.json` records every command's arguments, working directory, exit/status,
time, CPU, RSS, log path and log hash; it also records the source inventory,
virtual-environment identity, dependency reuse, doctor and native results.
Raw command logs and native artifacts remain under the output. The script uses
a 10-minute overall command budget, 2 MB capped command logs, 4 GiB process-group
RSS polling and a 512 MiB scratch ceiling. Polling can overshoot; it is not an OS
filesystem or memory quota. Nested native workers also use the pipeline's own
bounds. Source verification overhead and the final receipt write are small but
are not a hard real-time or kernel resource guarantee.

Passing establishes relocation into a fresh checkout and virtual environment
on this Mac. The installed KiCad, bundled pcbnew, Java and base Python are reused;
the engine download is reused after verification. It does not establish a fresh
Mac installation, independent dependency acquisition, package installation,
GUI support on a new host, or broad routing correctness. No formal package or
release is produced. Failed steps must remain reported as failed rather than
editing the disposable checkout to make its original commit appear to pass.
