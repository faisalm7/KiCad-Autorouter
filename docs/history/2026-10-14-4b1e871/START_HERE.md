# Start on your Mac

This package contains the complete project prompt, persistent instructions, historical references, and a preparation script. It does not contain the old source repository, recovered archives, or a working autorouter.

Use both a local folder and GitHub. The local folder is where Codex runs the tools and saves files. GitHub is the remote history/backup for committed, pushed files. Files ignored by Git need separate preservation. No change to the failed cloud task is required.

## 1. Extract the package

Download `kicad-local-start.zip` to Downloads and double-click it. The extracted folder should be `~/Downloads/kicad-local-start`. Keep that package outside the new repository as a copy of the starting materials.

The bundle includes `payload/MASTER_PROMPT.md` with the full engineering mandate. There is no need to merge the older prompts manually; this version resolves their conflicting cloud, push-approval, and continuation instructions.

## 2. Prepare the local checkout

Open Terminal on your Mac. First run:

```bash
git --version
```

If macOS asks to install its Command Line Tools, complete that Apple installation and run the command again. If Git cannot run, stop and address that prerequisite; do not claim the project was cloned.

Then run:

```bash
bash "$HOME/Downloads/kicad-local-start/prepare_local.sh"
```

The script verifies the supplied payload hashes, clones `faisalm7/KiCad-Autorouter` into `~/Projects/KiCad-Autorouter-local`, creates a new `rebuild/local-<timestamp>` branch, and copies the instruction files. It does not commit, push, install tools, authenticate, change settings, or touch the old cloud task.

At the October 9 preparation check, the existing GitHub repository was empty and public. The script still checks current state rather than assuming this remains true. If it finds existing files with conflicting names, it stops instead of overwriting them. An empty-repository Git warning is expected when the remote is still empty; successful preparation is indicated by the script's final local-checkout message.

If the destination already exists, inspect it rather than deleting it. To deliberately use another new folder, run:

```bash
bash "$HOME/Downloads/kicad-local-start/prepare_local.sh" \
  --destination "$HOME/Projects/KiCad-Autorouter-local-2"
```

If Downloads or the extracted folder has a different name on your Mac, use its actual path. Do not move only `prepare_local.sh`; it needs its adjacent `payload` folder and checksum manifest.

After successful preparation, open the default folder in Finder:

```bash
open "$HOME/Projects/KiCad-Autorouter-local"
```

Use the alternate actual path instead when you chose one.

## 3. Select the correct Codex environment

Open the current ChatGPT/Codex desktop app and select Codex from the top-left experience menu where that menu is present. Open/add the prepared local folder as the project.

Start a new coding task with **Work in > This computer**, then select **Local** rather than a separate managed worktree when those controls are shown. Do not select Cloud, create a cloud environment, or attach the failed task. If labels differ in your installed build, choose the workflow that directly runs commands in the selected local folder. The agent must verify the actual runtime before heavy work.

Grant project-scoped read/write/command access and appropriate network access for public research, dependencies, and GitHub. Do not use unrestricted full-machine access or disable approval controls. Git metadata writes, a browser login, GUI operations, or an installation may need specific approvals.

Use a capable coding model and a high reasoning setting available in your account. Subagent delegation is explicitly requested by the prompt; model branding is not evidence of correctness. Keep this local task running in the app/terminal, with the Mac awake for continuous execution. No automatic background runner is installed.

The local files remain on this Mac, but this is not a claim of offline model inference. The product being built must not upload private board files or require cloud inference by default.

## 4. Launch the engineering assignment

Open `LAUNCH_PROMPT.txt`, copy its entire contents, and paste into the new Codex task. It instructs Codex to read the full master prompt from disk and execute it.

**Important: the launch explicitly authorizes audited development checkpoint pushes to the rebuild branch of your existing PUBLIC repository.** Do not paste it unchanged if you do not approve that. It does not authorize secrets/private boards, indiscriminate data publication, repository setting changes, force pushes, formal release publication, new charges, or contact with third parties.

Codex's first task is to verify the local folder and complete a real initial GitHub push, then read it back. It may need you to finish a browser login. A GitHub connection in this chat does not establish credentials for your Mac's Git tools. Never paste a token or password into a prompt.

Do not approve a long autonomous build until it reports an actual full commit SHA and GitHub branch/commit URL that you can inspect. The preparation script alone has not backed up the instruction files or any new code.

## 5. Let Codex own the toolchain and engineering

Do not manually install several Python, Java, or Rust versions in advance. Codex should inspect what is already available, choose a minimal compatible setup, and pin it. It should prefer an official stable KiCad binary compatible with your Mac, not compile the whole CAD application immediately. The official macOS download page listed 10.0.7 when checked on October 9, 2026; the agent must verify the installed and selected versions itself.

Necessary browser authentication or OS installer approval is a real user action; it cannot be removed safely by a prompt. Everything else that can be decided from code and experiments belongs to the agent.

The assignment continues from bootstrap through native validation, baseline/failure audit, architecture experiments, improvement, data and optional learning, a usable KiCad workflow, held-out evaluation, skeptical review, packaging, and backup restoration. A passed one-board example does not finish the assignment.

## 6. Know what to expect

The first substantive receipt must include the local OS/path, branch, actual remote SHA, and what is or is not backed up. The next evidence should be a real engine/KiCad run and deliberately invalid outputs that are rejected.

The final evidence must distinguish the stock workflow, corrected adapter alone, a strong equal-budget tuned/restart baseline, and the proposed strategy. It must show coverage, gains, regressions, runtime, and route quality, not just a headline percentage.

The instructions request a continuous run but cannot guarantee one uninterrupted session, a research breakthrough, a particular success rate, or human/physical review without outside participation. The workflow is designed to survive interruption without losing work or asking you to rebuild context.

If execution stops, reopen the same local folder, inspect its saved status, and use `CONTINUE_PROMPT.txt`. Do not create a new cloud copy or start the project from scratch. Do not confuse a graceful checkpoint with a completed release.

## What is in the package

`MASTER_PROMPT.md` is the full current mandate. `AGENTS.md` is the concise persistent instruction file. `LAUNCH_PROMPT.txt` starts execution, and `CONTINUE_PROMPT.txt` resumes a real interrupted session. `REVIEW_PROMPT.md` gives a separate reviewer a falsification assignment. `SOURCE_LEDGER.md` distinguishes fresh documentation checks from historical research leads. `.local-reference/` contains the original status and prior prompts, preserved as private historical material and ignored by Git.

The outer `prepare_local.sh` and `PAYLOAD_SHA256SUMS` prepare and verify the checkout. `SETUP_TEST_REPORT.md` reports tests of that preparation package; these are NOT routing results or native macOS qualification.
