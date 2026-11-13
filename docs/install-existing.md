# Install the current artifact into another local folder

The tested runtime088 root is `.runs/runtime088 fresh install 001`, source `67672390912789234c87441992d4c5eea636ee7b`, manifest `b3b5b4ef9dd5a281c23ef6f6014bce263589de240478411b2ff1fd2f706d6f12`. Its [Native group/full260 record](../evidence/runtime088-installed-group-milestone-001.json) includes installation/doctor, actual headless group delivery and complete relevant regression. ActualGUI114/startup remains pending.087 is the last finite GUI-tested build; its command-based prepared startup was observed. Existing installation users should follow [Start here](../START_HERE.md), without making another copy.

For a genuinely needed new installation, the existing installer copies83verified immutable files and records the new root. Old jobs, settings, environments and launchers are excluded. It downloads or relocates no external dependency. Choose one unused owned destination with an existing real parent and first check free space against peak temporary allocation plus the fixed3GiB reserve:

```sh
(
  set -eu
  AUTOROUTER_PROJECT="$PWD"
  AUTOROUTER_INSTALL="$AUTOROUTER_PROJECT/.runs/Autorouter user install 001"
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source "$AUTOROUTER_PROJECT/.runs/runtime088 fresh install 001" \
    --expected-manifest-sha256 b3b5b4ef9dd5a281c23ef6f6014bce263589de240478411b2ff1fd2f706d6f12 \
    --output "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m venv --copies --without-pip "$AUTOROUTER_INSTALL/.venv"
  cd "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run `prepare_runtime.py` from the checkout; that installer is not shipped in the curated runtime. Enter the new runtime before `-m autorouter`. Preserve its manifest/process records. Changed/missing/extra files, unsafe links, stale pins and destination collisions refuse. Failure preserves partial output; use a fresh destination rather than overwriting it. Another root needs its own qualification. This documented command does not claim an independent clean installation or authorize automatic retirement of historical copies.

Current qualification uses the same Mac/account, copied no-pip Python3.11.9 and pinned external KiCad10.0.7/Java25.0.2/Freerouting2.5.0. GUI imports use that KiCad app's Python3.9.13/wx. Global KiCad10.0.0 is unchanged. No cleanOS, independent user, relocated dependencies, standalone package or Windows Native installation is qualified.

New prepared launchers bind config/documents/cache and `KICAD10_3RD_PARTY` inside the owned session. They verify PCM directory identity and reject unsafe links. A replaced/restored launcher directory needs new preparation; old launchers are not silently upgraded. This cooperative launch boundary is not an operating-system sandbox. Personal plugins/settings are not disabled or changed.087's boundary and correctly sequenced command startup were observed together; the absent override alone was not isolated as the cause of the old GUI112 stall. Observe the prepared process before a GUI tool attaches, since app selection may itself launch a default process.

Every final retains fresh Native refill/full-schematic/original-rule, immutable/protected, class/field and local-settings proofs. Warnings remain visible. Sources remain closed/saved, delivery is a separate project, and live apply/undo is unavailable. Genuine changed-warning GUI, exact queued timing, every cancellation phase, broader usefulness, independent installation/full recovery, Windows Native and human/physical review remain open. Raw080–087beyond the last compact archive cutoff is currently on this Mac only; old subset restoration does not prove current recovery. [Platform matrix](supported-platforms.md) · [Requirements](../REQUIREMENTS.md).
