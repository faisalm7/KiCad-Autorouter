"""Retain shared public-sanitized facts and exact protocol/cost metadata; no new validation."""
from pathlib import Path
import ast,json,datetime,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
from scripts.report_current_comparison import complete_cost
notes=ROOT/'evidence/runtime050-devobordo-development-001-notes';target=ROOT/'evidence/runtime050-devobordo-development-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='retain'];assert len(nodes)==1
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared-retention','exec'),globals())
frame=ROOT/'.runs/runtime050-devobordo-development-followup-001';facts=ROOT/'.runs/runtime050-devobordo-facts-public-001';report=json.loads((facts/'report.json').read_text());children=json.loads((frame/'frozen-children.json').read_text());population=json.loads((frame/'population.json').read_text())
assert report['public_sanitize'] is True and report['record_is_authoritative'] is False and report['accepted'] is False
assert report['source_head']==population['source_head']=='aa0072c6b3d8090de2603e5ecb42a95968fb873b'
assert report['runtime_manifest_sha256']==population['runtime_manifest_sha256']=='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
assert report['population_sha256']==p.sha(frame/'population.json')=='37392f9ede3a012eb1d89d33308050263c0b91f3c8cde932c66bf272dbdc8e9e'
assert report['frozen_children_sha256']==p.sha(frame/'frozen-children.json')=='c9117c695ee580e60ef06e28f0a5a29c18ef47f0411bb5d0e6a1886d72e573c5'
assert report['complete_external_totals']==dict(CPU_seconds=832.92,wall_seconds=751.09)
assert len(report['rows'])==6 and not any(row['workflow_delivered'] for row in report['rows'])
assert [row['arm'] for row in report['rows']]==population['planned_arm_order']
assert [row['evidence_classification'] for row in report['rows']].count('validated_completed_negative')==5
assert population['administration_head']==report['administration_head']=='1dadb9d380c33f8810fb0fa9494931af78bc08be'
for row in population['families'].values():assert p.tree_hash(Path(row['source']).parent)==row['source_hashes']
queue=[]
def add(path,name):queue.append((Path(path),Path(name)))
for name in ('report.json','files.json'):add(facts/name,Path('facts')/name)
for name in ('population.json','frozen-children.json','sources.json','native-only-prerequisites.json','tools-defaults.json','tools-defaults-process.json'):add(frame/name,Path('frame')/name)
for arm,item in children['protocols']['devobordo'].items():
 folder=Path(item['path']).parent;assert p.sha(Path(item['path']))==item['sha256']
 for name in ('protocol.json','outer-time.log'):add(folder/name,Path('frame/devobordo')/arm/name)
 # Raw child/Native/engine logs and findings intentionally remain local; generated public facts retain their hashes and classifications.
for name in ('freeze-runtime050-devobordo-followup-001.py','run-runtime050-devobordo-freeze-001.py','runtime050-devobordo-freeze-001.log','runtime050-devobordo-freeze-001-time.log','runtime050-devobordo-facts-public-001.log','runtime050-devobordo-facts-public-001-time.log','runtime050-devobordo-freezer-review-001.json','runtime050-devobordo-final-review-001.json'):
 add(ROOT/'.runs'/name,Path('controllers-and-costs')/name)
add(ROOT/'.runs/runtime050-devobordo-freeze-enclosure-001/execution.json',Path('controllers-and-costs/setup-execution.json'))
add(ROOT/'.runs/runtime050-devobordo-freeze-enclosure-001/process.json',Path('controllers-and-costs/setup-process.json'))
add(Path(__file__),Path('controllers-and-costs')/Path(__file__).name)
sealed={str(path):p.sha(path) for path,_ in queue}
assert len(queue)<2000 and sum(path.stat().st_size for path,_ in queue)<12*1024**2
for path,_ in queue:
 raw=io.read_bytes(path,4*1024**2);assert b'\0' not in raw;raw.decode('utf8')
for path,name in queue:retain(path,name)
assert all(p.sha(Path(path))==pin for path,pin in sealed.items())
setup=complete_cost(ROOT/'.runs/runtime050-devobordo-freeze-001-time.log');reporting=complete_cost(ROOT/'.runs/runtime050-devobordo-facts-public-001-time.log')
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
local_reviews={name:p.sha(ROOT/'.runs'/name) for name in ('runtime050-devobordo-initial-negative-review-001.json','runtime050-devobordo-open-classification-001.json')}
record=dict(schema=1,kind='runtime050-six-arm-exposed-development-Devobordo-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=report['source_head'],runtime_manifest_sha256=report['runtime_manifest_sha256'],administration_head=report['administration_head'],actual_GUI=False,human_review=False,project_complete=False,accepted=False,source_rights=report['source_rights'],population_sha256=report['population_sha256'],frozen_children_sha256=report['frozen_children_sha256'],methods=report['rows'],complete_external_totals=report['complete_external_totals'],additional_setup_cost=setup,additional_reporting_cost=reporting,local_review_sha256=local_reviews,
 result='All six frozen methods executed sequentially without board/policy/code/budget changes. No delivered board: five qualified completed negatives including three-score portfolio, one unqualified/non-delivered thermal method. Cdefault/B1/tuned have66opens/1blocking/74warnings; stock48/26/76. No gain or route-quality ranking among invalid boards.',
 diagnosis='Narrow NPTH keepout support reaches the engine; all four circle subtrees preserved. Default65of66opens are non-zone across actual net membership; zero graphic obstacles were added. Source0opens is not whole-reroute0demand:619routeitems and75fillpolygons were stripped in task. The final single thermal is at a different pad from source conflict; source board-only warnings are not directly comparable to final full-schematic findings. Detailed raw findings/diagnosis stay local.',
 decision='Retain qualified exact-form NPTH interchange repair. No measured completion superiority. Do not reopen graphics/zone-only hypotheses from this evidence; pursue broader ordinary non-zone completion diagnosis and actual current GUI gates. Keep all failures and original049 results unchanged. No board-specific tuning stitched into this run.',
 limitations='One already exposed family, no independent ancestry/holdout/GUI/optionalImprove comparison/electrical/cleanup/speed/release claim. B0 keeps common fidelity/Native safeguards and is not untouchedvanilla; API baselines and CLI method workloads differ. Every raw candidate remains rejected/unadopted. Ten ignored checks remain visible. Research/authoring/AI review/GUI/curation costs additional or unknown, notzero; nested samples count once.',
 backup_scope='Owned sanitized facts/protocol/controller/cost metadata for auditedGit. No CAD/DSN/SES/plots/rawfindings/engine downloaded binaries; full unique raw remains Mac-only/outside010. No new restoration claim.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
p.save_json(target,record);print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total)))
