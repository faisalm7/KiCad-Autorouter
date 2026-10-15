"""Adapt successful installed035 shared checks to current036; no Native/test rerun."""
from pathlib import Path
import sys,ast
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
old=R/'.runs/current-installation035-review-002';out=R/'.runs/current-installation036-review-001'
plan=f.read_json(R/'.runs/installation036-preparation-001/protocol.json');head=plan['git_head']
s=(old/'audit.py').read_text().replace('installation-035','installation-036').replace('installation035','installation036').replace('installed035','installed036').replace('current-installation036-review-002','current-installation036-review-001').replace('e78f5343ec401ee7df82957eaced84fc96f2b9f3',head)
a=s.index('def targeted():');b=s.index("step('installed_targeted_current_changes',targeted)",a)
s=s[:a]+'''def targeted():
 folder=ROOT/'.runs/installation036-targeted-001';row=read(folder/'execution.json');worker=row['process'];text=pc.read_bytes(folder/'tests.log').decode()
 assert row['passed'] is True and row['source_current'] is True and row['git_head']==HEAD
 assert sha(ROOT/'.runs/run-installation036-targeted-001.py')==row['controller_sha256']
 assert row['modules']==PLAN['target_modules']==['tests.test_chain_proposals','tests.test_strategy','tests.test_paired']
 assert row['protocol_sha256']==sha(ROOT/'.runs/installation036-preparation-001/protocol.json')
 assert worker['argv']==[*install.NETWORK_DENIAL,str(CLONE/'.venv/bin/python'),'-B','-c',PLAN['target_bootstrap']]
 assert worker['cwd']==str(folder) and worker['status']=='success' and worker['exit_code']==0 and worker['cleanup_complete'] and not worker['log_truncated']
 assert sha(folder/'tests.log')==row['log_sha256'] and worker['log_bytes']==(folder/'tests.log').stat().st_size
 population=read(folder/'population.json');match=re.search(r'Ran (\\d+) tests in [0-9.]+s\\n\\nOK\\s*$',text)
 assert match and population==row['population'] and sha(folder/'population.json')==row['population_sha256']
 assert population['modules']==PLAN['target_modules'] and population['successful'] is True and population['skipped']==0
 assert row['whole_delivery_within_budget'] is True and row['publication_allowance_seconds']==2
 assert max(row['wall_seconds'],row['full_cpu_seconds'])+2<=PLAN['limits']['targeted_whole_wall_full_cpu_seconds']==92
 expected={name:str(CLONE/(name.replace('.','/')+'.py')) for name in PLAN['new_shipped_modules']}
 assert population['shipped_modules']==expected
 assert population['planned']==population['ran']==int(match.group(1))==PLAN['expected_target_method_count']==78
 assert PLAN['historical_test_supplement'] is None and row['historical_test_supplement'] is None
 assert not (folder/'supplement.json').exists() and not (folder/'supplement.json').is_symlink()
 return {'passed':True,'unique_successful_methods':78,'attempts':78,'skipped':0,'historical_test_supplement':None,'population_sha256':row['population_sha256'],'actual_wall_seconds':row['wall_seconds'],'actual_full_cpu_seconds':row['full_cpu_seconds'],'shipped_modules':expected,'modules':PLAN['target_modules']}
''' + s[b:]
extra=" extra=read(ROOT/'.runs/installation036-missing-policy-followup-001/fixture-preparation.json')['fixture_files']\n expected_evidence.update({name.removeprefix('evidence/'):item['sha256'] for name,item in extra.items()})\n"
assert s.count(extra)==2;s=s.replace(extra,'')
s=s.replace("'historical_test_supplement_file_count':1,'historical_test_supplement_bytes':67060", "'historical_test_supplement_file_count':0,'historical_test_supplement_bytes':0")
s=s.replace('actual fixed distribution tests plus current field/edge/composite/netclass/quality controls with one explicitly declared historical source test supplement after initial242successes/twoerrors; not full installed suite or fresh OS','actual fixed distribution tests plus78 current chain/strategy/paired methods, no historical supplements; not full installed suite or fresh OS')
ast.parse(s)
run=(old/'run.py').read_text().replace('installation035','installation036').replace('installation-035','installation-036').replace('current-installation036-review-002','current-installation036-review-001')
run=run.replace("adapted_reader_source_sha256=p.sha(ROOT/'.runs/current-installation036-review-001/audit.py')","adapted_reader_source_sha256=p.sha(ROOT/'.runs/current-installation035-review-002/audit.py')")
a=run.index("    scope='") if "    scope='" in run else run.index(" scope='")
b=run.index("')\np.save_json",a)
run=run[:a]+" scope='Successful035 complete installed reader adapted to current036 source and78 changed-area installed controls with no historical supplements; same existing seven groups and Native/source/tool/PRL/process/complete-inventory/late-material checks. Pure installed interpreter audit refuses all subprocess/network/Native/JVM/tests. No full installed suite/freshOS/fullSCH/GUI/benchmark/human claim."+run[b:]
ast.parse(run);out.mkdir();(out/'audit.py').write_text(s);(out/'run.py').write_text(run)
names=['.runs/installation-036/result.json','.runs/installation-036/source-tracked.json','.runs/installation-036-execution/execution.json','.runs/installation-036-execution/command.log','.runs/installation036-targeted-001/execution.json','.runs/installation036-targeted-001/population.json','.runs/installation036-targeted-001/tests.log','.runs/installation036-preparation-001/protocol.json','.runs/current-installation035-review-002/audit.py','.runs/prepare-installation036-readback-001.py']
pins={name:p.sha(R/name) for name in names};pins.update(plan['controller_sha256']);pins.update(plan['source_sha256'])
pins.update({str(x.relative_to(R)):p.sha(x) for x in (out/'audit.py',out/'run.py')})
p.save_json(out/'input-pins.json',dict(kind='installation036-reader-inputs-v1',git_head=head,files_sha256=pins,scope='Existing seven complete installed checks, changed-area78controls, no supplements. Immutable currentsource/native/process/distribution/PRL/tool pins; no prior failures relabelled.'))
print(f.canonical(dict(prepared=True,git_head=head,files=len(pins),tests_executed=False,new_native_execution=False)))
