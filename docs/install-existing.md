# Install the current artifact into another local folder

The current tested runtime is `.runs/runtime092 fresh install 001`, source `95f540f8d519956f6b9d8e0ec6ba348373950c45`, manifest `0f823fa7b91ab66766f6aca09a56fc0a889a870592c39e9737acc1758ca95708`. Its [Native delivery/full264](../evidence/runtime092-licensed-placement-delivery-001.json) and [actual GUI117 workflow](../evidence/runtime092-GUI117-core-001.json) include installation/doctor, automatic selected placement, protected routing, review, acceptance/rejection, cancellation and checked export opening on this Mac. Existing users should follow [Start here](../START_HERE.md), without making another copy. Runtime093 is a separate routing experiment, not the qualified product installation.

For a genuinely needed new installation, the existing installer copies the 87 verified immutable runtime092 files and records the new root. Old jobs, settings, environments and launchers are excluded. It downloads or relocates no external dependency. Choose one unused owned destination with an existing real parent and first check free space against peak temporary allocation plus the fixed 3 GiB reserve:

```sh
(
  set -eu
  AUTOROUTER_PROJECT="$PWD"
  AUTOROUTER_INSTALL="$AUTOROUTER_PROJECT/.runs/Autorouter user install 001"
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source "$AUTOROUTER_PROJECT/.runs/runtime092 fresh install 001" \
    --expected-manifest-sha256 0f823fa7b91ab66766f6aca09a56fc0a889a870592c39e9737acc1758ca95708 \
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

Every final retains fresh Native refill/full-schematic/original-rule, immutable/protected, class/field and local-settings proofs. Warnings remain visible. Sources remain closed/saved, delivery is a separate project, and live apply/undo is unavailable. Genuine changed-warning GUI, exact queued timing, every cancellation phase, broader usefulness, independent installation/full recovery, Windows Native and human/physical review remain open. New raw evidence beyond the last compact archive cutoff is currently on this Mac only; old subset restoration does not prove current recovery. [Platform matrix](supported-platforms.md) · [Requirements](../REQUIREMENTS.md).
