"""Read retained controls through existing Native/process/original-design helpers; no Native execution."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,config as c,sexpr as sx
from experiments.native_components_v1 import controls,fixtures
from experiments.native_components_v1.normalize import normalize
O=R/'.runs/native-components-controls-001';d=f.read_json(O/'result.json');outer=f.read_json(R/'.runs/native-components-controls-execution-001/execution.json')
assert d['status']=='completed' and d['passed'] is True and outer['passed'] is True and outer['source_current'] is True
assert d['tools']==p.tool_manifest()==outer['tools'] and all(p.sha(R/n)==v for n,v in d['source_sha256'].items())
assert f.evidence_inventory(O)==d['completed_material'] and len(d['controls'])==len(fixtures.CASES) and [x['case'] for x in d['controls']]==list(fixtures.CASES)
summary=[]
for row in d['controls']:
 case=row['case'];directory=O/case;source=directory/'original/smoke.kicad_pcb';saved=directory/'saved/smoke.kicad_pcb';candidate=directory/'candidate/smoke.kicad_pcb'
 original,expected=fixtures.recipe(case,sx.read(R/'fixtures/smoke/smoke.kicad_pcb'))
 assert sx.read(source)==original and p.sha(source.with_suffix('.kicad_pro'))==p.sha(R/'fixtures/smoke/smoke.kicad_pro')
 before=p.tree_hash(source.parent);refill=f.check_drc_stage(directory,row,'refill-drc',saved,saved,True,before)
 final=f.check_drc_stage(directory,row,'final-drc',candidate,directory/'final-drc-input/smoke.kicad_pcb',False,p.tree_hash(candidate.parent))
 assert p.immutable(sx.read(candidate))==p.immutable(original) and p.routes(sx.read(candidate))==p.routes(original)
 assert sx.read(candidate)==p.transplant_fill(original,sx.read(saved)) and row['candidate_sha256']==p.sha(candidate) and row['native_report_sha256']==p.sha(directory/'final-drc.json')
 if case=='physical-short':assert controls.intended_short_observed(final)
 else:assert final['blocking']==0 and final['opens']==(1 if case in ('chain-cut','zone-islands','layer-gap') else 0)
 assert row['native_counts']=={k:final[k] for k in ('opens','blocking','warnings','exclusions')}
 request=directory/'request.json';spec=f.read_json(request);hint=f.read_json(directory/'components/result.json')
 process=f.process_check(directory,row,'components',[*f.SANDBOX,str(c.PYTHON),str(R/'experiments/native_components_v1/worker.py'),'--request',str(request),'--output',str(directory/'components')])
 assert hint['status']=='diagnostic_completed' and hint['source_hashes']==spec['project_sha256']==p.tree_hash(candidate.parent)
 assert hint['request_sha256']==p.sha(request) and hint['refill_receipt_sha256']==spec['refill_receipt_sha256']==p.sha(directory/'refill-drc-binding.json')
 assert spec['board']==str(candidate) and spec['refill_receipt']==str(directory/'refill-drc-binding.json')
 assert spec['worker_sha256']==p.sha(R/'experiments/native_components_v1/worker.py') and spec['normalizer_sha256']==p.sha(R/'experiments/native_components_v1/normalize.py') and spec['lock_sha256']==p.sha(R/'toolchain.lock.json') and spec['wrapper_sha256']==controls.WRAPPER
 assert row['component_receipt_sha256']==p.sha(directory/'components/result.json') and row['passed'] is True
 assert all(hint[k] is False for k in ('accepted','routing_accepted','production_admitted','board_saved','native_refill_performed','refill_semantics_checked_by_worker'))
 for key,value in normalize(hint['pad_census'],hint['reachable_pad_uuids']).items():assert hint[key]==value
 refs={r['uuid']:r['reference'] for r in hint['pad_census']};observed=sorted(sorted(refs[u] for u in g['pad_uuids']) for g in hint['components']);assert observed==expected==row['expected_components']==row['observed_components']
 summary.append(dict(case=case,counts=row['native_counts'],ignored_checks=final['ignored_checks'],component_count=len(hint['components']),pad_count=len(refs),candidate_sha256=p.sha(candidate),native_report_sha256=p.sha(directory/'final-drc.json'),worker_receipt_sha256=p.sha(directory/'components/result.json'),native_accepted=p.native_accepted(final)))
assert d['tools']==p.tool_manifest() and f.evidence_inventory(O)==d['completed_material']
result=dict(schema=1,passed=True,native_executed=False,production_admitted=False,routing_accepted=False,receipt_sha256=p.sha(O/'result.json'),controls=summary,checks='Shared saved-refill/final Native process reports/local settings, actual original fixture recipe, exact immutable/routes/original shell, complete request/source/tool/wrapper/hash bindings and normalized full partitions; all original files/current tools/material rechecked. PCB-only diagnostic fixtures, no fullSCH/human/electrical admission.')
P=R/'.runs/native-components-controls-readback-001';P.mkdir();p.save_json(P/'result.json',result);print(json.dumps(result,indent=2))
