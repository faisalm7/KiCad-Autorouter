import time,resource
START=time.monotonic();r=resource.getrusage(resource.RUSAGE_SELF);CPU0=r.ru_utime+r.ru_stime
rc=resource.getrusage(resource.RUSAGE_CHILDREN);CHILD0=rc.ru_utime+rc.ru_stime
import json,hashlib,re,sys,subprocess,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'.runs/installation-040';CLONE=BASE/'checkout';OUT=ROOT/'.runs/current-installation040-review-005'
sys.path.insert(0,str(CLONE))
sys.dont_write_bytecode=True
def forbidden(*a,**kw):raise AssertionError('installed audit forbids workers; only exact read-only installed Git HEAD allowed')
real_run,real_popen=subprocess.run,subprocess.Popen
git_active=False
safe_git=['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','rev-parse','HEAD']
def readonly_run(argv,*args,**kw):
 global git_active
 # tool_manifest's exact read-only provenance observation, never a worker.
 assert argv==['git','rev-parse','HEAD'] and not args and Path(kw.get('cwd',''))==CLONE
 assert set(kw)=={'cwd','capture_output','text','check'} and all(kw[k] is True for k in ('capture_output','text','check'))
 assert not git_active
 git_active=True
 try:return real_run(safe_git,**kw)
 finally:git_active=False
def controlled_popen(argv,*args,**kw):
 assert git_active and argv==safe_git and not args and Path(kw.get('cwd',''))==CLONE
 return real_popen(argv,**kw)
subprocess.run=readonly_run;subprocess.Popen=controlled_popen
from scripts import install_smoke as install
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,config as c,padless_alias as alias,padless_alias_native,native_edge as edge,schematic_field_evidence as fields,netclass,netclass_native,strategy,placement_strategy
from experiments.universal_shift_recovery_v1 import b2
from scripts import fetch_led_demo,experiment_quality
checks={};failures=[]
def read(x):return f.read_json(x)
def sha(x):return hashlib.sha256(pc.read_bytes(x,128*1024**2)).hexdigest()
def step(name,action):
 print('starting',name,'peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 try:
  checks[name]=action()
  print('completed',name,'peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 except BaseException as exc:failures.append({'check':name,'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(limit=4)})
R=read(BASE/'result.json');EX=read(ROOT/'.runs/installation-040-execution/execution.json');PLAN=read(ROOT/'.runs/installation040-preparation-001/protocol.json');HEAD=PLAN['git_head'];RP=Path(R['native_receipt']['path']);N=read(RP);fixture=CLONE/R['selected_qualification']['fixture'];pin=sha(BASE/'result.json');npin=sha(RP)
PINSET=read(OUT/'input-pins.json');PINSET_SHA=sha(OUT/'input-pins.json')
assert PINSET['kind']=='installation040-reader-inputs-v1' and PINSET['git_head']==HEAD=='6bd0d57b596c1d55dd7df281d5d6904723cead10'
assert all(sha(ROOT/name)==digest for name,digest in PINSET['files_sha256'].items())

def context():
 assert all(sha(ROOT/name)==pin for name,pin in PLAN['controller_sha256'].items())
 assert all(sha(ROOT/name)==sha(CLONE/name)==pin for name,pin in PLAN['source_sha256'].items())
 assert PLAN['status']=='frozen_for_lead_execution'
 assert all(sha(ROOT/name)==digest for name,digest in PINSET['files_sha256'].items())
 assert all(Path(module.__file__).resolve()==CLONE/'autorouter'/(module.__name__.split('.')[-1]+'.py') for module in (alias,padless_alias_native))
 assert N['tools']['normal_native_export_alias_policy']==PLAN['tools']['normal_native_export_alias_policy']==alias.POLICY
 assert c.ROOT==CLONE and Path(p.__file__).resolve().is_relative_to(CLONE) and Path(install.__file__).resolve().is_relative_to(CLONE)
 assert Path(sys.executable)==CLONE/'.venv/bin/python'
 assert Path(sys.prefix).resolve()==CLONE/'.venv' and sys.prefix!=sys.base_prefix
 assert sys.version_info[:2]==(3,11)
 return {'passed':True,'module_root':str(c.ROOT),'python':sys.executable,'version':sys.version,'sys_prefix':sys.prefix,'base_prefix':sys.base_prefix,'pipeline_module':str(Path(p.__file__)),'install_module':str(Path(install.__file__)),'git_head':R['git_head']}
step('real_installed_context',context)

def commands():
 assert R['status']=='passed' and R['passed'] is True and R['git_head']==HEAD and EX['git_head']==HEAD
 assert R['installed_test_scope']==list(install.DISTRIBUTION_TESTS)
 rows=[]
 for i,row in enumerate(R['commands']):
  assert row['status']=='success' and row['exit_code']==0 and row['cleanup_complete'] is True and row['log_truncated'] is False
  assert row['argv'][:3]==install.NETWORK_DENIAL
  log=Path(row['log']);assert sha(log)==row['log_sha256'] and log.stat().st_size==row['log_bytes']
  assert str(log).startswith(str(BASE)+'/') and log.name.startswith(f'{i:02d}-')
  assert row['resource_guards']['max_group_rss_bytes']==4*1024**3
  rows.append({'name':row['name'],'log_sha256':row['log_sha256'],'log_bytes':row['log_bytes'],'wall_seconds':row['wall_seconds'],'cpu_seconds':row['cpu_seconds'],'cleanup_complete':True,'network_denied':True})
 names=[x['name'] for x in rows]
 assert len(names)==len(set(names)) and {'tests','doctor','route','check-result','setup-engine-offline','fetch-pinned-local-source'}<=set(names)
 for row in R['commands']:
  if row['name'] in ('venv-identity','setup-engine-offline','doctor','tests','route','check-result'):
   assert row['argv'][3]==str(CLONE/'.venv/bin/python')
 text=Path(next(row['log'] for row in R['commands'] if row['name']=='tests')).read_text();match=re.search(r'Ran (\d+) tests in ([0-9.]+)s\n\nOK\s*$',text)
 import unittest
 distribution_planned=unittest.defaultTestLoader.loadTestsFromNames(list(install.DISTRIBUTION_TESTS)).countTestCases()
 assert match and distribution_planned>0 and int(match.group(1))==distribution_planned and len(rows)==22
 scoring=[line for line in text.splitlines() if '(tests.test_pruning_scoring.' in line]
 assert scoring and all(line.endswith(' ... ok') for line in scoring)
 check=read(BASE/'17-check-result.log');assert check['current'] is True and check['candidate_sha256']==N['candidate_sha256']
 freshness=[]
 for path in sorted(BASE.glob('freshness-*.json')):
  row=read(path);assert row['status']=='success' and row['exit_code']==0 and row['cleanup_complete'] is True and row['log_truncated'] is False
  assert row['argv'][:3]==install.NETWORK_DENIAL and sha(Path(row['log']))==row['log_sha256']
  freshness.append({'receipt_sha256':sha(path),'log_sha256':row['log_sha256'],'cleanup_complete':True})
 assert len(freshness)==8
 return {'passed':True,'offline_command_count':len(rows),'commands':rows,'freshness_process_count':len(freshness),'freshness':freshness,'installed_test_count':int(match.group(1)),'installed_test_log_seconds':float(match.group(2)),'scoring_control_count':len(scoring),'scoring_controls':scoring,'installed_test_scope':R['installed_test_scope'],'check_result_candidate_sha256':check['candidate_sha256'],'no_network_or_auth_workflow':True}
step('actual_commands_and_selected_tests',commands)

def targeted():
 folder=ROOT/'.runs/installation040-targeted-001';row=read(folder/'execution.json');worker=row['process'];text=pc.read_bytes(folder/'tests.log').decode()
 assert row['passed'] is True and row['source_current'] is True and row['git_head']==HEAD
 assert sha(ROOT/'.runs/run-installation040-targeted-001.py')==row['controller_sha256']
 assert row['modules']==PLAN['target_modules']==['tests.test_native_toolchain', 'tests.test_native_parser_context', 'tests.test_experimental_route_context', 'tests.test_experimental_route_publication', 'tests.test_field_local_settings_event', 'tests.test_native_import_toolchain', 'tests.test_native_schematic_transport_fixture']
 assert row['protocol_sha256']==sha(ROOT/'.runs/installation040-preparation-001/protocol.json')
 assert worker['argv']==[*install.NETWORK_DENIAL,str(CLONE/'.venv/bin/python'),'-B','-c',PLAN['target_bootstrap']]
 assert worker['cwd']==str(folder) and worker['status']=='success' and worker['exit_code']==0 and worker['cleanup_complete'] and not worker['log_truncated']
 assert sha(folder/'tests.log')==row['log_sha256'] and worker['log_bytes']==(folder/'tests.log').stat().st_size
 population=read(folder/'population.json');summaries=list(re.finditer(r'(?m)^Ran (\d+) tests in [0-9.]+s\n\nOK$',text))
 assert len(summaries)==1;match=summaries[0];assert not text[match.end():].strip()
 methods=re.findall(r'^test_\S+ \(([^)]+)\) \.\.\. (ok|ERROR|FAIL)$',text,re.M)
 assert len(methods)==len({name for name,status in methods})==46 and all(status=='ok' for name,status in methods)
 assert population==row['population'] and sha(folder/'population.json')==row['population_sha256']
 assert population['modules']==PLAN['target_modules'] and population['successful'] is True and population['skipped']==0
 assert row['whole_delivery_within_budget'] is True and row['publication_allowance_seconds']==2
 assert max(row['wall_seconds'],row['full_cpu_seconds'])+2<=PLAN['limits']['targeted_whole_wall_full_cpu_seconds']==92
 expected={name:str(CLONE/(name.replace('.','/')+'.py')) for name in PLAN['new_shipped_modules']}
 assert population['shipped_modules']==expected
 assert population['planned']==population['ran']==int(match.group(1))==PLAN['expected_target_method_count']==46
 assert PLAN['historical_test_supplement'] is None and row['historical_test_supplement'] is None
 assert not (folder/'supplement.json').exists() and not (folder/'supplement.json').is_symlink()
 return {'passed':True,'retained_targeted_current_material_qualified':True,'historical_target_writer_final_publication_qualified':False,'unique_successful_methods':46,'attempts':46,'skipped':0,'historical_test_supplement':None,'population_sha256':row['population_sha256'],'actual_wall_seconds':row['wall_seconds'],'actual_full_cpu_seconds':row['full_cpu_seconds'],'shipped_modules':expected,'modules':PLAN['target_modules']}
step('installed_targeted_current_changes',targeted)

def inventory():
 listing=pc.read_bytes(BASE/'03-source-files.log',2_000_000).decode()
 assert pc.read_bytes(BASE/'09-clone-files.log',2_000_000).decode()==listing
 original=read(BASE/'source-tracked.json');assert sha(BASE/'source-tracked.json')==R['source_inventory_sha256']
 assert install.tracked_inventory(ROOT,listing)==original
 installed_listing=install.distribution_listing(listing);selected={name:original[name] for name in installed_listing.split('\0') if name}
 assert install.tracked_inventory(CLONE,installed_listing)==selected
 assert len(original)==R['complete_source_tracked_files'] and len(selected)==R['installed_tracked_files']
 assert PLAN['historical_test_supplement'] is None
 expected_evidence={name.removeprefix('evidence/'):digest for name,digest in selected.items() if name.startswith('evidence/')}
 assert pc.inventory(CLONE/'evidence')==expected_evidence
 assert R['source_installation_mode']=='distribution' and R['historical_evidence_omitted_from_installation'] is True
 assert install.SOURCE_MAX_FILES==22000 and install.SOURCE_MAX_BYTES==384*1024**2
 for root,branch in ((ROOT,R['source_branch']),(CLONE,None)):
  assert install.git_identity(root,HEAD,branch)==R['git_identity_witnesses'][str(root)]
 for name,expected in R['venv_files_sha256'].items():assert sha(Path(name))==expected
 assert sha(Path(R['python']['resolved_path']))==R['python']['sha256']
 return {'passed':True,'complete_original_source_files':len(original),'installed_distribution_files':len(selected),'source_inventory_sha256':R['source_inventory_sha256'],'source_and_installed_subset_exact':True,'historical_test_supplement_file_count':0,'historical_test_supplement_bytes':0,'source_file_cap':22000,'source_byte_cap':384*1024**2,'source_and_clone_git_identity_witnesses_current':True,'independent_venv_files_unchanged':True,'complete_source_listing_sha256':sha(BASE/'03-source-files.log'),'clone_index_listing_sha256':sha(BASE/'09-clone-files.log')}
step('complete_source_and_installed_inventory',inventory)

def native():
 print('native line 136','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 install.verify_native_contract(N,R['selected_qualification'],fixture,HEAD)
 print('native line 137','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 evidence=pc.evidence_inventory(RP.parent)
 print('native line 138','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 current=p.check_result(RP);assert current['current'] is True
 print('native line 139','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 original=sx.read(fixture);candidate=RP.parent/'candidate'/fixture.name
 print('native line 140','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert p.tree_hash(fixture.parent)==N['source_hashes']
 print('native line 141','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert p.immutable(original)==p.immutable(sx.read(candidate))
 print('native line 142','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
 print('native line 143','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 from autorouter.local_settings import check_normal_policy
 print('native line 144','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 contract=p.normal_import_contract(RP.parent,N,check_normal_policy(RP.parent,N),input_policy='native',original=original)
 print('native line 145','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert contract=={}
 print('native line 146','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 alias_checks=alias.check_exports(RP.parent,N,pc.inventory(RP.parent))
 print('native line 147','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert len(alias_checks)==1 and alias_checks[0]['alias_count']==0
 print('native line 148','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert not fixture.with_suffix('.kicad_sch').exists()  # Current owned PCB-only smoke, no fullSCH claim.
 print('native line 149','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 p.check_preferences_record(RP.parent,N)
 print('native line 150','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 p.check_protected_import(RP.parent,N,original,candidate,protected,**contract);p.check_resource_accounting(N)
 print('native line 151','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 before=dict(N['source_hashes']);before[fixture.name]=N['candidate_sha256']
 print('native line 152','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 observed=f.check_drc_stage(RP.parent,N,'final-drc',candidate,RP.parent/'final-drc-input'/fixture.name,False,before,schematic_parity=False,sandboxed=False)
 print('native line 153','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert observed==N['native'] and p.sha(RP.parent/'final-drc.json')==N['native_report_sha256']
 print('native line 154','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 refill_binding=read(RP.parent/'refill-drc-binding.json')
 print('native line 155','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 refill=f.check_drc_stage(RP.parent,N,'refill-drc',RP.parent/'refill'/fixture.name,RP.parent/'refill'/fixture.name,True,refill_binding['before'],schematic_parity=False,sandboxed=False)
 print('native line 156','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert refill['opens']==refill['blocking']==refill['warnings']==refill['exclusions']==0
 print('native line 157','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 for worker in N['steps']:
  process=f.process_check(RP.parent,N,worker['name'],worker['argv'],allowed=(0,5))
  assert process['cleanup_complete'] is True and process['log_truncated'] is False
  assert Path(process['log']).stat().st_size==process['log_bytes']
 print('native line 161','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert observed['opens']==observed['blocking']==observed['warnings']==observed['exclusions']==0
 print('native line 162','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert N['metrics']==read(RP.parent/'metrics.json')
 print('native line 163','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 p.check_refill_route_nets(sx.read(candidate),sx.read(RP.parent/'refill'/fixture.name))
 print('native line 164','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert '18GiB total cache checked before task' in N['resource_limitations'] and '10GiB' not in N['resource_limitations']
 print('native line 165','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert p.sha(candidate)==N['candidate_sha256'] and sha(RP)==R['native_receipt']['sha256']
 print('native line 166','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 for relative,digest in N['tools']['implementation_sha256'].items():
  assert p.sha(CLONE/relative)==digest and p.sha(RP.parent/'code'/Path(relative).name)==digest
 print('native line 168','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 for name,digest in N['tools']['files'].items():assert p.sha(Path(name))==digest
 print('native line 169','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 copied=CLONE/'.tools'/Path(R['cached_dependency']['path']).name
 print('native line 170','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert p.sha(copied)==p.sha(Path(R['cached_dependency']['path']))==R['cached_dependency']['sha256'] and copied.stat().st_ino!=Path(R['cached_dependency']['path']).stat().st_ino
 print('native line 171','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert pc.evidence_inventory(RP.parent)==evidence
 print('native line 172','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 import importlib.util
 print('native line 173','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 ntplanpath=ROOT/'.runs/installation040-native-preparation-001/protocol.json';ntplan=read(ntplanpath)
 print('native line 174','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 outerpath=ROOT/'.runs/installation040-native-001/result.json';outer=read(outerpath)
 print('native line 175','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert outer['accepted'] is False and outer['passed'] is True and outer['status']=='invalidated' and outer['git_head']==HEAD
 print('native line 176','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert outer.get('reason')=='Rejected: unqualified caller-pinned Native command prefix'
 print('native line 177','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert outer['protocol_sha256']==sha(ntplanpath)
 print('native line 178','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 process=outer['process'];work=CLONE/'.runs/installation040-explicit1007'
 print('native line 179','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert process['argv']==[*install.NETWORK_DENIAL,str(CLONE/'.venv/bin/python'),'-B',str(work/'installed1007.py'),'--protocol',str(ntplanpath),'--protocol-sha256',sha(ntplanpath)]
 print('native line 180','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert process['cwd']==str(work) and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
 print('native line 181','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert sha(Path(process['log']))==outer['log_sha256'] and Path(process['log']).stat().st_size==process['log_bytes']
 print('native line 182','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert max(outer['wall_seconds'],outer['full_cpu_seconds'])+2<=180
 print('native line 183','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert p.tree_hash(work)==outer['child_material'] and sha(work/'native/result.json')==outer['child_receipt_sha256']
 print('native line 184','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert sha(ROOT/'.runs/run-installation040-native-001.py')==outer['controller_sha256']==ntplan['controller_sha256']
 print('native line 185','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert sha(work/'installed1007.py')==ntplan['installed_companion_sha256']
 print('native line 186','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 spec=importlib.util.spec_from_file_location('installed1007_audit',work/'installed1007.py');companion=importlib.util.module_from_spec(spec);spec.loader.exec_module(companion)
 print('native line 187','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 def trace_companion(frame,event,arg):
  if frame.f_code.co_filename==str(work/'installed1007.py'):
   if event=='line':print('companion line',frame.f_lineno,'peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
   return trace_companion
  return None
 sys.settrace(trace_companion)
 explicit=companion.read_transport(ntplan)
 sys.settrace(None)
 print('native line 188','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 child=read(work/'native/result.json')
 print('native line 189','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert child['passed'] is True and child['status']=='completed' and child['tools']==ntplan['native_tools'] and child['transport']==explicit
 print('native line 190','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert f.canonical(read(work/'native/result.json'))==f.canonical(child)
 print('native line 191','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert f.evidence_inventory(work/'native')==child['transport']['material']
 print('native line 192','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert explicit['material']==child['transport']['material']
 print('native line 193','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert p.tree_hash(work)==outer['child_material']
 print('native line 194','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 assert max(child['wall_seconds'],child['full_cpu_seconds'])+2<=176
 print('native line 195','peak_rss_bytes',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
 return {'passed':True,'original_native_outer_status':outer['status'],'original_native_outer_reason':outer['reason'],'original_native_outer_publication_completed':False,'retained_installed_child_and_material_qualified':True,'experimental_full_schematic_transport':explicit,'installed1007_outer_wall_seconds':outer['wall_seconds'],'installed1007_outer_full_cpu_seconds':outer['full_cpu_seconds'],'receipt_sha256':sha(RP),'candidate_sha256':N['candidate_sha256'],'report_sha256':N['native_report_sha256'],'native_counts':{k:observed[k] for k in ('opens','blocking','warnings','exclusions')},'refill_native_counts':{k:refill[k] for k in ('opens','blocking','warnings','exclusions')},'refill_native_report_sha256':p.sha(RP.parent/'refill-drc.json'),'metrics':N['metrics'],'native_budget_seconds':N['budget_seconds'],'native_wall_seconds':N['wall_seconds'],'native_full_cpu_seconds':N['total_cpu_seconds'],'native_worker_count':len(N['steps']),'native_process_cleanup_verified':True,'source_has_schematic':False,'schematic_parity_claimed':False,'native_alias_export_checks':alias_checks,'installed_alias_module_files':PLAN['new_shipped_modules'],'source_and_original_constraints_unchanged':True,'resource_description_matches_guard':True,'exact_implementation_snapshots_and_tool_bytes':True,'independent_pinned_engine_copy':True,'evidence_inventory_sha256':hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()}
step('installed_actual_native_smoke_and_current_readback',native)

def outer():
 proc=EX['process'];assert EX['source_current'] is True and EX['whole_delivery_within_budget'] is True and EX['publication_allowance_seconds']==2
 assert max(EX['wall_seconds'],EX['full_cpu_seconds'])+2<=600
 assert proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True and proc['log_truncated'] is False
 assert sha(Path(proc['log']))==EX['log_sha256'] and proc['log_bytes']==Path(proc['log']).stat().st_size
 assert sha(ROOT/'.runs/run-installation-040.py')==EX['wrapper_sha256']
 assert sha(BASE/'result.json')==pin and sha(RP)==npin
 return {'passed':True,'actual_installation_foreground_wall_seconds':EX['wall_seconds'],'actual_installation_foreground_full_cpu_seconds':EX['full_cpu_seconds'],'receipt_wall_seconds':R['wall_seconds'],'receipt_total_cpu_seconds':R['total_cpu_seconds'],'command_cpu_seconds':R['command_cpu_seconds'],'scratch_bytes':R['scratch_bytes'],'outer_execution_sha256':sha(ROOT/'.runs/installation-040-execution/execution.json'),'installation_receipt_sha256':pin,'publication_and_native_receipt_unchanged':True,'scope':EX['scope']}
step('outer_costs_and_publication',outer)

def late_material():
 # Byte-only repetition of the same captured witnesses after all semantic checks.
 assert sha(OUT/'input-pins.json')==PINSET_SHA
 assert all(sha(ROOT/name)==digest for name,digest in PINSET['files_sha256'].items())
 assert all(sha(ROOT/name)==sha(CLONE/name)==digest for name,digest in PLAN['source_sha256'].items())
 listing=pc.read_bytes(BASE/'03-source-files.log',2_000_000).decode()
 original=read(BASE/'source-tracked.json');assert install.tracked_inventory(ROOT,listing)==original
 selected=install.distribution_listing(listing)
 assert install.tracked_inventory(CLONE,selected)=={name:original[name] for name in selected.split('\0') if name}
 expected_evidence={name.removeprefix('evidence/'):original[name] for name in selected.split('\0') if name.startswith('evidence/')}
 assert pc.inventory(CLONE/'evidence')==expected_evidence
 assert not (ROOT/'.runs/installation040-targeted-001/supplement.json').exists() and not (ROOT/'.runs/installation040-targeted-001/supplement.json').is_symlink()
 for root,branch in ((ROOT,R['source_branch']),(CLONE,None)):
  assert install.git_identity(root,HEAD,branch)==R['git_identity_witnesses'][str(root)]
 for name,digest in N['tools']['files'].items():assert sha(Path(name))==digest
 assert sha(BASE/'result.json')==pin and sha(RP)==npin
 ntplan=read(ROOT/'.runs/installation040-native-preparation-001/protocol.json')
 work=Path(ntplan['native_output']).parent;child=read(work/'native/result.json')
 assert child['status']=='completed' and child['passed'] is True
 assert sha(work/'native/result.json')==read(ROOT/'.runs/installation040-native-001/result.json')['child_receipt_sha256']
 assert f.evidence_inventory(work/'native')==child['transport']['material']
 # Last shared metadata replay uses this installed package/Native argv context.
 nt=p.ExperimentalNativeToolchain.from_record(ntplan['native_toolchain'])
 p.check_experimental_local_settings(work/'native/route',read(work/'native/route/result.json'),nt)
 return {'passed':True,'installed_explicit_prl_metadata_current':True,'input_pins_sha256':PINSET_SHA,'file_count':len(PINSET['files_sha256']),'source_and_complete_distribution_unchanged':True}
step('late_complete_material_and_source',late_material)

r=resource.getrusage(resource.RUSAGE_SELF);rc=resource.getrusage(resource.RUSAGE_CHILDREN);wall=time.monotonic()-START;child_cpu=rc.ru_utime+rc.ru_stime-CHILD0;cpu=r.ru_utime+r.ru_stime-CPU0+child_cpu
result={'schema':1,'kind':'independent installed040 retained actual readback','passed':not failures and max(wall,cpu)+2<=60,'new_native_execution':False,'new_jvm_execution':False,'network_access':False,'read_only_git_head_allowed':True,'checks':checks,'failures':failures,'cost':{'active_wall_seconds':wall,'active_full_cpu_seconds':cpu,'child_cpu_seconds':child_cpu,'bootstrap_allowance_seconds':1,'emission_allowance_seconds':1,'charged_wall_seconds':wall+2,'charged_full_cpu_seconds':cpu+2,'scope':'from first audit-script line before installed project imports through checks; explicit1s bootstrap/1s emission; review preparation separately unmeasured development inspection'},'limits':{'audit_wall_full_cpu_seconds':60,'selected_output_bytes':16*1024**2},'limitations':['existing Mac and verified installed tool/engine cache reused; baseline fixture is PCB-only and zeroalias; separate installed explicit1007 owned transport has fullSCH and protected copper','original target pre-write-only writer and Native outer invalidation remain; current retained material/shared installed transport qualify here, no retroactive final-publication/timing claim','actual fixed distribution tests plus46 current explicit-context/import/PRL/field/publication/fixture methods, no historical supplements; not full installed suite or fresh OS','no comparative routing quality claim; preparation/installation costs separate from measured experiments','local mutable evidence consistency, not adversarial authentication']}
(OUT/'checks.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'failures':failures,'cost':result['cost'],'checks':list(checks),'installed_test_count':checks.get('actual_commands_and_selected_tests',{}).get('installed_test_count')}))

raise SystemExit(0 if result['passed'] else 2)
