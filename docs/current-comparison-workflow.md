# Freeze a fresh installed-workflow comparison

`scripts/freeze_current_comparison.py` prepares a comparison without routing a board. It replaces the historical, path-specific freezer for new experiments. It reads only the supplied projects, qualification packet, selected runtime and seven administration files; it does not scan the research archive. It is administration tooling, outside the shipped runtime.

The current contract is deliberately narrow: this Mac, the selected KiCad10.0.7 runtime042 artifact, and its explicit fresh-root installation qualification. That qualification records actual native CLI delivery and one actual new-root GUI vertical slice. It does not transfer all GUI081 roles, qualify another platform or establish a clean-OS installation. The freezer checks the exact manifest, complete immutable population, tools and actual defaults. It cannot create missing native, GUI, legal or human evidence.

Before executing a new comparison, state the failure or support gap, proposed general mechanism, fixed population, budgets and integrate/revise/defer decision rule. Develop on exposed inputs. This preparation is not a confirmation protocol or proof that family labels have independent ancestry.

## Inputs

Use a fresh absolute output directly beneath this checkout's `.runs`, with a lowercase slug of at most64 characters. Existing outputs and conflicting copied controllers refuse; partial outputs remain for diagnosis and must not be automatically deleted or reused. Commit the seven administration files and keep that exact HEAD stable throughout every arm.

Supply a SHA256-pinned JSON object with this shape:

```json
{
  "schema": 1,
  "split": "development-exposed",
  "families": {
    "example-family": {
      "source": "/absolute/complete-project/example.kicad_pcb",
      "source_hashes": {
        "example.kicad_pcb": "<sha256>",
        "example.kicad_pro": "<sha256>",
        "example.kicad_sch": "<sha256>"
      },
      "source_rights": {
        "family": "example-family-exposed",
        "license": "Exact local-use grant and redistribution limitations",
        "provenance": "Publisher, exact revision, acquisition and notice evidence; exposure and unresolved rights"
      },
      "publication": "hashes_only"
    }
  }
}
```

The hashes must cover **every file** in the source project directory, including rule files, libraries, schematic children and notices. The three files shown above are only the minimum paired names. Use one to four families, at most2000 files/32MiB per project, matching the unchanged controllers. Paths must be absolute/canonical and the source external to the runtime; links, special files, incomplete inventories and duplicate board bytes/family labels refuse. Rights strings are caller declarations, not an automated legal clearance. The tool never downloads or executes project scripts.

## Preparation and execution

The following is a parameterized reproduction command, not a command to rerun any completed experiment. Replace the paths and digests with the exact newly prepared inputs. Use the checked source checkout's virtual environment; keep all Python invocations in bytecode-free mode.

```sh
cd /absolute/KiCad-Autorouter-local
.venv/bin/python -B scripts/freeze_current_comparison.py \
  --runtime '/absolute/current qualified runtime' \
  --expected-manifest-sha256 '<runtime-distribution.json sha256>' \
  --sources /absolute/new-sources.json \
  --sources-sha256 '<new-sources.json sha256>' \
  --qualification /absolute/evidence/runtime042-install-existing-001.json \
  --qualification-sha256 '<qualification sha256>' \
  --expected-administration-head '<audited committed HEAD>' \
  --output /absolute/KiCad-Autorouter-local/.runs/new-comparison-namespace \
  --enclosure /absolute/KiCad-Autorouter-local/scripts/enclose_current_comparison.py \
  --enclosure-sha256 9a77bdc832988f45d3bd920dfeeed09288700569db8da7788d043308deb478e4
```

Measure that complete setup command with `/usr/bin/time -l`; setup is additional cost. Successful preparation writes `population.json`, `frozen-children.json`, six protocols per family, the bounded tools-query process record and pinned input copies. It also installs or verifies the exact public current-method controller in the runtime's `.runs`. Preparation does not start Native routing or qualify future outcomes.

Verify all frozen protocol hashes before starting any arm. Follow `planned_family_order` and `planned_arm_order` exactly. For **one** arm, use its protocol path/digest from `frozen-children.json`:

```sh
(set -C
/usr/bin/time -l .venv/bin/python -B scripts/enclose_current_comparison.py \
  --protocol /absolute/new-comparison-namespace/FAMILY/ARM/protocol.json \
  --protocol-sha256 '<that protocol sha256>' \
  > /absolute/new-comparison-namespace/FAMILY/ARM/outer.log \
  2> /absolute/new-comparison-namespace/FAMILY/ARM/outer-time.log)
```

Run one supervised Native worker at a time. Check actual disk headroom and process cleanup between arms. Do not restart an arm under its old identifier, change a board or policy during a batch, move administration HEAD, or present a repaired continuation as an unattended first attempt. Capture terminal failures and unsupported inputs as well as successes. No background or automatic resume facility is provided.

## Fixed policy and interpretation

All families receive B0 stock adapter, B1 corrected adapter, B2 tuned single, B2 fixed three-score portfolio, C shipped default and C optional thermal recovery. Execution order is Cdefault, B0, B1, B2single_tuned, B2_portfolio, Cthermal. Corrected-standard/B1 remains the shipped default; the freezer does not select a different policy per board.

Every method has420 seconds routing allocation,450 whole-method wall/fullCPU,600 complete-delivery wall/fullCPU and120 export validation. Recovery's420 includes incumbent acquisition, repair, selection and parent validation. The portfolio shares420 across ordered via_default/via_low/via_high trials with30 seconds readback reserve inside each trial and15 seconds root finalization reserve. Selection uses valid(vias,length,index), never hard violations exchanged for length. Source placement, original constraints, protected routing and allowed source layers stay unchanged.

B0 retains common fidelity/protection/native safeguards and identical native/task DSN bytes; it is not an untouched official-plugin test. Baselines use the sealed comparison API and library delivery; C uses actual installed CLI workflows. Those authority-checking workloads differ. Count all actual conversion/startup/attempt/selection/validation/delivery steps and full external exit costs, but do not infer a generic speed advantage from this comparison. Setup, research, authoring, review and curation are separate costs; nested samples count once. Desktop contention and unknown interactive costs must remain visible.

Each accepted final still requires its **own** native refill/full-schematic/original-rule/candidate-hash and protected-copper proof. A completed qualified negative is different from timeout, cancellation, unsupported input or harness failure. Expected source opens are routing demand. Warnings, exclusions, ignored checks, source conflicts and whole-project cleanliness remain separate. No native result establishes current, return-path, impedance, timing, physical suitability or measured engineer cleanup.

The output is local evidence, not a publication bundle. `hashes_only` does not sanitize files automatically. Keep source CAD, generated CAD/DSN/SES, plots and input copies local when redistribution title is unresolved; publish only reviewed facts, hashes and owned code. The4GiB startup check and per-worker polling guards are not an aggregate future-job disk reservation. Existing full-restoration capacity limits still apply.

## Report completed stored evidence

[`scripts/report_current_comparison.py`](../scripts/report_current_comparison.py) reports an entire frozen population after every planned arm has a terminal enclosure. Supply the original `population.json` and `frozen-children.json` with their exact SHA256 digests. Missing arms refuse reporting; unsupported inputs, cancellations, cap failures and harness failures remain unqualified rather than becoming completed routing negatives.

The reporter checks frozen source/runtime/manifest/administration pins, sealed method and portfolio material, all portfolio attempts, and stored own-final source/candidate/report/process/full-schematic bindings. It preserves warnings, exclusions, ignored-check codes, protected counts and numeric metrics, including Native `track_length_mm`, alongside the producer version. Complete external exit wall/CPU costs are counted once; nested method/Native samples are not added again. These are stored-evidence checks, **not** new Native execution, central-reader replay or GUI revalidation.

Use a fresh absolute output directory. It writes generated `report.json` and `files.json`; existing outputs refuse and partial outputs must not be automatically reused. This parameterized command does not rerun any comparison arm:

```sh
.venv/bin/python -B scripts/report_current_comparison.py \
  --population '/absolute/frozen-comparison/population.json' \
  --population-sha256 '<exact population.json sha256>' \
  --children '/absolute/frozen-comparison/frozen-children.json' \
  --children-sha256 '<exact frozen-children.json sha256>' \
  --output '/absolute/KiCad-Autorouter-local/.runs/new-comparison-facts' \
  --public-sanitize
```

Without `--public-sanitize`, output is local and includes bounded original failure text and ignored-check metadata; audit it before sharing. With the flag, safe ignored-check key codes and counts remain visible, while descriptions and free-form reasons become hashes plus exact local receipt/field references. Classification, warnings and failure counts do not change. Source CAD, generated CAD/DSN/SES, plots, logs and raw findings are not copied into the report. Sanitization does not clear redistribution rights or publish anything.

The reporter's 11 constructed tests passed in 0.18 seconds wall/0.12 CPU; they establish reporting controls, not Native correctness. Its actual six-row IR043 stored-evidence report completed in 1.79 seconds wall/1.23 CPU, additional to the comparison costs. The native-only IR043 follow-up used an explicitly reviewed local wrapper. The public freezer above still requires its runtime042 GUI-installation qualification contract: do not fabricate that qualification or treat this report as portable runtime043 GUI support or a fully closed evaluation.

[Current measured results](benchmark-runtime042.md) · [Supported scope and release gates](../REQUIREMENTS.md)
