"""Read-only independent AI evidence consistency audit; no native rerun."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
BASE=ROOT/'.runs/quality-comparison-002'
load=lambda path:json.loads(path.read_text())
protocol=load(BASE/'protocol.json');summary=load(BASE/'summary.json');freeze=protocol['freeze']
assert p.sha(BASE/'protocol.json')==summary['protocol_sha256']
head=freeze['tools']['git_head']; source=Path(protocol['source'])
assert p.tree_hash(source.parent)==freeze['source_hashes']
for name,digest in freeze['files_sha256'].items():
    assert p.sha(BASE/'frozen-code'/name)==digest
    raw=subprocess.run(['git','show',head+':'+name],cwd=ROOT,check=True,capture_output=True).stdout
    assert hashlib.sha256(raw).hexdigest()==digest
rows=[]
for row in summary['results']:
    run=BASE/row['id'];result=load(run/'result.json');candidate=Path(result['candidate'])
    assert p.sha(run/'result.json')==row['result_sha256']
    assert result['tools']==freeze['tools'] and result['source_hashes']==freeze['source_hashes']
    assert p.tree_hash(run/'snapshot')==freeze['source_hashes']
    assert p.immutable(sx.read(candidate))==p.immutable(sx.read(source))
    assert p.sha(candidate)==result['candidate_sha256']==row['candidate_sha256']
    assert p.sha(run/'final-drc.json')==result['native_report_sha256']==row['native_report_sha256']
    assert p.parse_report(run/'final-drc.json',candidate.name)==result['native']
    binding=load(run/'final-drc-binding.json')
    assert binding['before'][candidate.name]==result['candidate_sha256']
    assert p.tree_hash(run/'final-drc-input')==binding['after']
    for relative,digest in result['tools']['implementation_sha256'].items():
        assert p.sha(run/'code'/Path(relative).name)==digest
    assert result['budget_seconds']==result['cpu_budget_seconds']==120
    assert result['wall_seconds']<=120 and result['total_cpu_seconds']<=120
    assert row['invocation_wall_seconds']<=120 and row['invocation_cpu_seconds']<=120
    assert abs(sum(step['cpu_seconds'] for step in result['steps'])-result['child_cpu_seconds'])<1e-6
    assert abs(sum(step['monitor_cpu_seconds'] for step in result['steps'])-result['monitor_cpu_seconds'])<1e-6
    if result['accepted']:assert p.check_result(run/'result.json')['current']
    rows.append({key:row[key] for key in ('id','accepted','opens','blocking','warnings','length_mm','vias','invocation_wall_seconds','invocation_cpu_seconds')})
c=load(BASE/'C/result.json');counts={}
for item in c['trials']:
    record=load(Path(item['receipt']));counts[record['status']]=counts.get(record['status'],0)+1
    if record.get('candidate_sha256'):
        trial=Path(item['receipt']).parent;candidate=trial/'candidate'/source.name
        assert p.sha(candidate)==record['candidate_sha256']
        assert p.immutable(sx.read(candidate))==p.immutable(sx.read(source))
        assert p.sha(trial/'final-drc.json')==record['native_report_sha256']
        assert p.parse_report(trial/'final-drc.json',source.name)==record['native']
        if record['accepted']:assert not(record['native']['opens'] or record['native']['blocking'] or record['native']['exclusions'])
for item in c['checkpoints']:
    checkpoint=load(BASE/'C'/item);assert p.sha(checkpoint['candidate'])==checkpoint['candidate_sha256']
threshold=p.optimizer_threshold_audit(BASE/'B2/engine.log',0.1)
assert threshold['observed_stop_threshold_percent']==[0.1]
print(json.dumps({'passed':True,'reviewer':'AI subagent engine_research; not human PCB review','native_rerun':False,
 'frozen_head':head,'frozen_files':len(freeze['files_sha256']),'arms':rows,'C_trial_counts':counts,
 'C_checkpoints':len(c['checkpoints']),'B2_threshold':threshold,
 'commands':'PYTHONDONTWRITEBYTECODE=1 python3 .runs/review-quality002-001/audit.py',
 'checked':'Protocol hash; frozen code bytes and committed Git blobs; original/snapshot source inventories; tool and per-arm implementation manifests; candidate immutable geometry and hashes; final native report hashes/parsed summaries/input bindings; child and monitoring CPU sums; receipt and invocation wall/CPU ceilings; accepted receipt consistency; all C trial native bindings; all checkpoints; B2 logged threshold',
 'interpretation':'C is 126.216474 mm shorter than B1/B2, same vias as B1, one more than B2. No Pareto win against B2, no speedup, one exposed family only. Original docs table uses receipt timings; invocation timings above include call overhead. No electrical or physical validation claim.'},indent=2))
