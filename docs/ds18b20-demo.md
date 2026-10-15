# Temperature-interface example

This exposed public DS18B20 design has four footprints, ten pads and no copper zones. The exact source is already downloaded in this checkout. Run from the project folder:

```sh
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B -m autorouter route \
  ".data/ds18b20-demo-001/native-project/D18BS20.kicad_pcb" \
  --seconds 120 --adapter both --profile tuned \
  --output .runs/my-ds18b20-route-001
```

Use a new output name for every attempt; Control-C cancels. Inspect the actual result. [Saved preferences](routing-preferences.md) customize scope, layers, time and optimization. [Preview and export](gui-workflow.md) describes explicit review intent and a separate fresh native-validated project. No live editor file is overwritten.

On another installation, first download the fixed source into a fresh directory:

```sh
.venv/bin/python -B scripts/fetch_led_demo.py --project ds18b20 --fetch
```

The [publisher source](https://github.com/ampnics/DS18B20/tree/c5420f538a77e0af03974031a5ee1c36a5b5e0a1) includes an explicit design grant and attribution in README; no standalone license is supplied or invented. The fetch retains all five originals including PRL and one exact README notice copy. Models, images, firmware and upstream scripts are not fetched. Third-party CAD stays outside public Git.

The [recorded four-arm comparison](../evidence/ds18b20-native240-actual-001.json) passes original constraints and complete-schematic native checks for stock, corrected, three-setting tuned baseline and C. Best B2 and C tie at35.511106mm/zero vias, retaining11warnings and seven ignored checks. No zones means no C pruning moves: this is additional supported scope, not a new quality gain. Equal delivered240-second wall/fullCPU caps include source qualification, all attempts and independent readback; the normal120-second command above does not reproduce that whole protocol.

Native routing acceptance is separate from whole-project cleanliness, human PCB review and electrical/physical validation. KiCad's saved source migration changes text caches/metadata; the product retains the exact original shell and checks the actual final candidate.
