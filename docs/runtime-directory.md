# Curated local runtime directory

Current **runtime058**, source `8f5e96b88dd22cd25919bb71ce47711612994efa`, manifest `4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74`, contains49autorouter modules/54immutable files and the pinned local engine. Full209/[eleven Native workflows and three invalid controls](../evidence/runtime058-native-milestone-001.json), [IR Improve](../evidence/runtime058-ir-delivery-001.json) and [EEPROM Improve](../evidence/runtime058-eeprom-improve-regression-001.json) pass in their scopes. [GUI092 ordinary](../evidence/gui-runtime058-092-ordinary-001.json)/[observations](../evidence/gui-runtime058-092-observations-001.json) and [installed GUI093](../evidence/gui-runtime058-install093-observations-002.json) are actual functional evidence; fullGUI/release remain open.

Original runtime:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-058/runtime
```

Enter that directory before `.venv/bin/python -B -m autorouter`; an absolute interpreter alone can import checkout code from the wrong CWD. Code/resources/licences/manifest are immutable; `.runs` and `.venv` are mutable and unattested. Source projects remain separate. Normal jobs need no AI account, Git, network or research archive. Documentation/administration changes do not require rebuilding this unchanged artifact.

[Explicit existing-artifact installation](install-existing.md) preserves the immutable census/build source/lock/engine and changes only the absolute root. Current fresh root `/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime058 fresh install 001` has manifest `19bdfe08169624f49a3b2bee1b789258f2ccaac63ad24a1e06c1d6ba371788f2`. [Two actual partial90 CLI slices](../evidence/runtime058-install-existing-001.json) deliver0all/protected4 under default/high costs. [One actual installed GUI093 slice](../evidence/gui-runtime058-install093-observations-002.json) completes ordinary delivery through checked opening and post-editor stale refusal. Other combinations, fullGUI and independent installation are not inferred.

The existing launcher is `/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime058 fresh install 001/.runs/gui-launcher093/Launch Autorouter.command`. Its isolated project/preset/jobs are under that runtime's `.runs/gui-session093`. Use the child-only Edge override in [GUI steps](gui-workflow.md), or manually open review HTML in Edge; leave Chrome/default settings unchanged. Do not move/edit a launcher or copy old jobs/venvs to simulate installation. Original058 GUI092 remains separate.

For intentional development builds only, choose a fresh destination from reviewed committed source:

```sh
cd /Users/faisal/Projects/KiCad-Autorouter-local
.venv/bin/python -B scripts/prepare_runtime.py --output /absolute/NEW-runtime --copy-local-engine --native-version 10.0.7
.venv/bin/python -B -m venv --copies --without-pip /absolute/NEW-runtime/.venv
cd /absolute/NEW-runtime
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output /absolute/NEW-runtime/.runs/NEW-launcher
```

These are build reproduction commands, not instructions to rebuild058. The destination parent must exist and be real/owned; collisions refuse and partial output remains after failure. A different source/root needs its own evidence. Doctor proves readiness, not board acceptance; launcher creation is not GUI qualification.

Nothing downloads. Existing official KiCad10.0.7/macOS arm64, Java25.0.2, Python3.11.9 base and Freerouting2.5.0 remain pinned. Copy-local-engine copies that existing JAR only. Without explicit `--native-version`, build preparation selects historical10.0.0. The install-existing mode instead preserves the artifact's selection unchanged. Copied interpreters/`-B` avoid immutable bytecode; unexpected files/symlinks refuse.

Same Mac/account/basePython/fixed dependencies is not standalone, cleanOS/account, relocation, Windows or independent-user support. Manifest consistency is not hostile-user/power-loss protection or a raw backup. Review/export never overwrites originals; transactional apply/undo remains unavailable. [Installation limits](install-test.md) · [Preferences](routing-preferences.md) · [Status](../STATUS.md). [Historical057 installation](../evidence/runtime057-install-existing-001.json)/[GUI091](../evidence/gui-runtime057-install091-delivery-001.json) retain their exact scope. [Restoration capacity](../evidence/backups/runtime041-receipt-capacity-001.json) remains blocked; new raw050–058 stays Mac-only/outside010. No formal release/tag/package publication.
