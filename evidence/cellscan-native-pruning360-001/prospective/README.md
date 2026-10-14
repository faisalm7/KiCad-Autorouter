Prepared only; neither operation has started. HEAD965/current source and tools must remain exact. B1 has finished. Launch B2, wait for its exit, then launch C:

```sh
.venv/bin/python -B .runs/cellscan-balanced-pruning360-draft-001/controller.py --method B2
.venv/bin/python -B .runs/cellscan-balanced-pruning360-draft-001/controller.py --method C
```

B2 uses fresh balanced Default/Low/High with263.730088inner seconds. C uses its own fresh explicit Default incumbent and feedback pruning with262.314929inner seconds. Both receive the same corrected-edge adapter as B1. Prior120 failed costs include Source25/Audit15; each adds newAudit15/bootstrap1 and actual new outer wall/fullCPU under360. Old and B1 outputs are metadata pins only, never candidate inputs. No reset, reference-route reuse, untouched or comparative success claim.

After both finish, inspect every retained final candidate with existing shared readers. This runs no new Native/engine. The lead must preserve its output/costs within each charged15audit and independently check aggregate protocol/prefix/outer accounting:

```sh
.venv/bin/python -B - <<'PY'
from pathlib import Path
import json
from autorouter import pipeline as p, floor_route as f
from experiments.native_paired_v1.readback import final_candidate_readback, pruning_incumbent_readback, inherited_trial_accounting
root=Path.cwd(); draft=root/'.runs/cellscan-balanced-pruning360-draft-001'
spec=f.read_json(draft/'C-protocol.json'); board=Path(spec['source']); original=p.preflight(board)
hashes=spec['freeze']['source_hashes']
original_native=f.read_json(Path(spec['original_source_receipt']))['parity_native']
warnings=lambda native:f.canonical([x for x in native['findings'] if x['severity']=='warning'])
observations=[]
def inspect(name,folder,data,parent=None):
    if data.get('candidate_sha256') and data.get('native_report_sha256'):
        checked=final_candidate_readback(folder,data,board,original,hashes,resource_parent=parent)
        checked['unchanged_original209warnings']=warnings(data['native'])==warnings(original_native)
        observations.append(dict(id=name,status=data['status'],**checked))
with p.validation_readback_session():
    b2=root/'.runs/cellscan-b2-balanced-edge-budget360-001/portfolio'
    portfolio=f.read_json(b2/'portfolio-summary.json')
    for row in portfolio['trials']:
        if row.get('result'):
            path=Path(row['result']); data=f.read_json(path)
            if data.get('engine_budget'):p.check_engine_profile_record(data,path.parent)
            inspect('B2/'+row['id'],path.parent,data)
    c=root/'.runs/cellscan-c-default-pruning-edge-budget360-001/trial'
    data=f.read_json(c/'result.json')
    if data.get('incumbent'):
        inc,checked=pruning_incumbent_readback(c,data,board,original,hashes)
        checked['unchanged_original209warnings']=warnings(inc['native'])==warnings(original_native)
        observations.append(dict(id='C/incumbent',status=inc['status'],**checked))
    if data.get('accepted'):p.check_result(c/'result.json')
    inspect('C/final',c,data)
    for row in data.get('trials',[]):
        folder=c/'trials'/row['id']; trial=f.read_json(folder/'result.json')
        inherited_trial_accounting(folder,trial,data)
        inspect('C/'+row['id'],folder,trial,data)
print(json.dumps(dict(accepted=False,comparison_eligible=False,all_B2_variants_attempted=portfolio.get('all_variants_attempted'),observations=observations)))
PY
```

This inspection starts from shared candidate readers; it is not aggregate acceptance. Bind completed input/output witnesses, all209warning identity, missing/rejected Native cases, portfolio ranking/profile coverage and every old/new cost. Missing, stale, unsupported or over-budget proof rejects. Wrapper execution_closed means a terminal process/receipt exists, including expected exit2 rejection; it never means routing acceptance.

Preparation emitted no Native/JVM, test, GET, Git process or backup. A first README shell-heredoc write had a delimiter quoting error before Python launched; the file was then written directly with apply_patch. Controllers/protocols remain unchanged.
