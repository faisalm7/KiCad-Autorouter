"""Correct only an unexecuted plan's stale descriptive ordinal; reuse doctor."""
from pathlib import Path
import copy,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv
old=ROOT/'.runs/runtime055-native-qualification-001';out=ROOT/'.runs/runtime055-native-qualification-002';assert not out.exists()
head='38e193cdf94a814ee50baacb786e7f64214f02b8';assert pv.git_head(ROOT)==head
frozen=f.read_json(old/'frozen.json');assert frozen['source_head']==head and len(frozen['protocols'])==7
assert f.read_json(old/'doctor.json')['ready'] and f.read_json(old/'doctor-process.json')['exit_code']==0
out.mkdir(mode=0o700);rows=[]
for name in ('doctor.json','doctor-process.json','tools-defaults.json','tools-defaults-process.json'):
 shutil.copyfile(old/name,out/name)
for row in frozen['protocols']:
 source=Path(row['protocol']);assert p.sha(source)==row['protocol_sha256'] and not (source.parent/'execution.json').exists()
 plan=copy.deepcopy(f.read_json(source));assert 'Fresh installed053 ' in plan['scope'] and plan['kind']=='runtime055-six-stage-route-or-improve-CLI'
 assert not Path(plan['output']).exists() and p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
 folder=out/row['case'];folder.mkdir();shutil.copyfile(source.parent/'settings.json',folder/'settings.json')
 assert p.sha(folder/'settings.json')==plan['settings_sha256']
 plan['scope']=plan['scope'].replace('Fresh installed053 ','Fresh installed055 ')
 protocol=folder/'protocol.json';p.save_json(protocol,plan);rows.append(dict(row,protocol=str(protocol),protocol_sha256=p.sha(protocol)))
record=dict(frozen,protocols=rows,controller_sha256=p.sha(Path(__file__)),executed=False,
 preparation_correction='Only stale explanatory ordinal installed053 corrected to installed055 before any seven-case dispatch. All runtime/head/manifest/constraints/settings/budgets/output bindings unchanged. Original unexecuted001 kept. Doctor/query evidence reused, not rerun.',
 prior_frozen_sha256=p.sha(old/'frozen.json'),reused_doctor_sha256=p.sha(old/'doctor.json'),Native_executed=False)
p.save_json(out/'frozen.json',record);print(json.dumps(dict(frozen_cases=7,Native_executed=False,reused_doctor=True)))
