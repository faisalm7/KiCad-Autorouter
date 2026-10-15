import time,resource
START=time.monotonic();r=resource.getrusage(resource.RUSAGE_SELF);CPU0=r.ru_utime+r.ru_stime
rc=resource.getrusage(resource.RUSAGE_CHILDREN);CHILD0=rc.ru_utime+rc.ru_stime
import json,hashlib,re,sys,subprocess,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'.runs/installation-043';CLONE=BASE/'checkout';OUT=ROOT/'.runs/current-installation043-review-001'
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
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as pc,sexpr as sx,config as c,padless_alias as alias,padless_alias_native,native_edge as edge,schematic_field_evidence as fields,netclass,netclass_native,strategy,placement_strategy,local_settings as ls
from experiments.universal_shift_recovery_v1 import b2
from scripts import fetch_led_demo,experiment_quality
checks={};failures=[]
def read(x):return f.read_json(x)
def sha(x):return hashlib.sha256(pc.read_bytes(x,128*1024**2)).hexdigest()
def step(name,action):
 try:checks[name]=action()
 except BaseException as exc:failures.append({'check':name,'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(limit=4)})
R=read(BASE/'result.json');EX=read(ROOT/'.runs/installation-043-execution/result.json');PLAN=read(ROOT/'.runs/installation043-preparation-001/protocol.json');HEAD=PLAN['git_head'];RP=Path(R['native_receipt']['path']);N=read(RP);fixture=CLONE/R['selected_qualification']['fixture'];pin=sha(BASE/'result.json');npin=sha(RP)
PINSET=read(OUT/'input-pins.json');PINSET_SHA=sha(OUT/'input-pins.json')
assert PINSET['kind']=='installation043-reader-inputs-v1' and PINSET['git_head']==HEAD
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
 missing_plan=read(ROOT/'.runs/installation043-missing-preparation-001/protocol.json')
 assert missing_plan['kind']=='installation043-missing-preparation-v1' and missing_plan['git_head']==HEAD
 assert missing_plan['status']=='frozen_for_lead_execution' and missing_plan['tools']==PLAN['tools']
 assert missing_plan['source_sha256']==PLAN['source_sha256'] and missing_plan['target_modules']==PLAN['target_modules']
 assert all(sha(ROOT/name)==digest for name,digest in missing_plan['controller_sha256'].items())
 rows=[];methods_by_attempt=[]
 for suffix,plan,count,successful in (('001',PLAN,62,False),('002',missing_plan,7,True)):
  folder=ROOT/('.runs/installation043-targeted-'+suffix);row=read(folder/'result.json');worker=row['process'];text=pc.read_bytes(folder/'tests.log').decode()
  assert row['accepted'] is False and row['passed'] is successful and row['status']==('completed' if successful else 'failed')
  # Original001 remains failed/source_current=False; current source is separately verified in groups1/4/7.
  assert row['source_current'] is successful and row['git_head']==HEAD
  assert f.evidence_inventory(folder)==row['completed_evidence']
  controller=ROOT/('.runs/run-installation043-targeted'+('002' if successful else '')+'-001.py')
  assert sha(controller)==row['controller_sha256']
  protocol=ROOT/('.runs/installation043-'+('missing-' if successful else '')+'preparation-001/protocol.json')
  assert row['protocol_sha256']==sha(protocol) and row['modules']==plan['target_modules']
  assert worker['argv']==[*install.NETWORK_DENIAL,str(CLONE/'.venv/bin/python'),'-B','-c',plan['target_bootstrap']]
  assert worker['cwd']==str(folder) and worker['status']==('success' if successful else 'nonzero_exit') and worker['exit_code']==(0 if successful else 2)
  assert worker['cleanup_complete'] is True and worker['log_truncated'] is False
  assert worker['resource_guards']['max_group_rss_bytes']==1024**3 and worker['resource_guards']['max_workdir_bytes']==16*1024**2
  assert sha(folder/'tests.log')==row['log_sha256'] and worker['log_bytes']==(folder/'tests.log').stat().st_size
  population=read(folder/'population.json')
  assert population==row['population'] and sha(folder/'population.json')==row['population_sha256']
  assert population['modules']==plan['target_modules'] and population['selectors']==plan['target_selectors']
  assert population['successful'] is successful and population['skipped']==0
  expected={name:str(CLONE/(name.replace('.','/')+'.py')) for name in plan['new_shipped_modules']}
  assert population['shipped_modules']==expected
  assert population['planned']==population['ran']==plan['expected_target_method_count']==count
  methods=re.findall(r'^test_\S+ \(([^)]+)\) \.\.\. (ok|ERROR|FAIL)$',text,re.M)
  assert len(methods)==len({name for name,status in methods})==count
  footer=r'(?m)^Ran '+str(count)+r' tests in [0-9.]+s\n\n'+('OK' if successful else r'FAILED \(failures=2, errors=5\)')+r'\s*$'
  assert len(list(re.finditer(footer,text)))==1
  assert row['whole_delivery_within_budget'] is True and row['publication_allowance_seconds']==2
  assert max(row['wall_seconds'],row['full_cpu_seconds'])+2<=plan['limits']['targeted_whole_wall_full_cpu_seconds']==92
  assert plan['historical_test_supplement'] is None and row['historical_test_supplement'] is None
  assert not (folder/'supplement.json').exists() and not (folder/'supplement.json').is_symlink()
  methods_by_attempt.append(dict(methods))
  rows.append(dict(attempt=suffix,original_passed=row['passed'],original_status=row['status'],population=population,population_sha256=row['population_sha256'],receipt_sha256=sha(folder/'result.json'),sample_wall_seconds=row['wall_seconds'],sample_full_cpu_seconds=row['full_cpu_seconds'],publication_allowance_seconds=2))
 first,second=methods_by_attempt;failed={n for n,s in first.items() if s!='ok'}
 assert len(failed)==7 and sum(s=='ERROR' for s in first.values())==5 and sum(s=='FAIL' for s in first.values())==2
 assert set(second)==failed==set(missing_plan['target_selectors']) and all(s=='ok' for s in second.values())
 assert len({n for n,s in first.items() if s=='ok'}|set(second))==62
 old=ROOT/'.runs/installation043-targeted-001'
 assert missing_plan['retained_failure']['receipt_sha256']==sha(old/'result.json') and missing_plan['retained_failure']['material']==f.evidence_inventory(old)
 assert missing_plan['retained_failure']['prior_attempts']==62 and missing_plan['retained_failure']['prior_successful']==55
 observations=rows[1]['population']['read_only_git_observations']
 assert len(observations)==2 and all(x==dict(argv=safe_git,cwd=str(CLONE),head=HEAD,returncode=0) for x in observations)
 assert rows[1]['population']['scratch_parent_created']==str(CLONE/'.local-backups') and (CLONE/'.local-backups').is_dir() and not (CLONE/'.local-backups').is_symlink()
 return dict(passed=True,current_targeted_material_and_publication_qualified=True,unique_successful_methods=62,attempts=69,initial_successes=55,initial_errors=5,initial_failures=2,missing_only_successes=7,skipped=0,attempts_detail=rows,historical_test_supplement=None,modules=PLAN['target_modules'],cost_scope='Both immutable delivered cohorts retained separately,92s each; no single62-pass run or cumulative92s claim.')
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
 assert install.SOURCE_MAX_FILES==22500 and install.SOURCE_MAX_BYTES==384*1024**2
 for root,branch in ((ROOT,R['source_branch']),(CLONE,None)):
  assert install.git_identity(root,HEAD,branch)==R['git_identity_witnesses'][str(root)]
 for name,expected in R['venv_files_sha256'].items():assert sha(Path(name))==expected
 assert sha(Path(R['python']['resolved_path']))==R['python']['sha256']
 return {'passed':True,'complete_original_source_files':len(original),'installed_distribution_files':len(selected),'source_inventory_sha256':R['source_inventory_sha256'],'source_and_installed_subset_exact':True,'historical_test_supplement_file_count':0,'historical_test_supplement_bytes':0,'source_file_cap':22500,'source_byte_cap':384*1024**2,'source_and_clone_git_identity_witnesses_current':True,'independent_venv_files_unchanged':True,'complete_source_listing_sha256':sha(BASE/'03-source-files.log'),'clone_index_listing_sha256':sha(BASE/'09-clone-files.log')}
step('complete_source_and_installed_inventory',inventory)

def native():
 install.verify_native_contract(N,R['selected_qualification'],fixture,HEAD)
 evidence=pc.evidence_inventory(RP.parent)
 current=p.check_result(RP);assert current['current'] is True
 original=sx.read(fixture);candidate=RP.parent/'candidate'/fixture.name
 assert p.tree_hash(fixture.parent)==N['source_hashes']
 assert p.immutable(original)==p.immutable(sx.read(candidate))
 protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
 from autorouter.local_settings import check_normal_policy
 contract=p.normal_import_contract(RP.parent,N,check_normal_policy(RP.parent,N),input_policy='native',original=original)
 assert contract=={}
 alias_checks=alias.check_exports(RP.parent,N,pc.inventory(RP.parent))
 assert len(alias_checks)==1 and alias_checks[0]['alias_count']==0
 assert not fixture.with_suffix('.kicad_sch').exists()  # Current owned PCB-only smoke, no fullSCH claim.
 p.check_preferences_record(RP.parent,N)
 p.check_protected_import(RP.parent,N,original,candidate,protected,**contract);p.check_resource_accounting(N)
 before=dict(N['source_hashes']);before[fixture.name]=N['candidate_sha256']
 observed=f.check_drc_stage(RP.parent,N,'final-drc',candidate,RP.parent/'final-drc-input'/fixture.name,False,before,schematic_parity=False,sandboxed=False)
 assert observed==N['native'] and p.sha(RP.parent/'final-drc.json')==N['native_report_sha256']
 refill_binding=read(RP.parent/'refill-drc-binding.json')
 refill=f.check_drc_stage(RP.parent,N,'refill-drc',RP.parent/'refill'/fixture.name,RP.parent/'refill'/fixture.name,True,refill_binding['before'],schematic_parity=False,sandboxed=False)
 assert refill['opens']==refill['blocking']==refill['warnings']==refill['exclusions']==0
 for worker in N['steps']:
  process=f.process_check(RP.parent,N,worker['name'],worker['argv'],allowed=(0,5))
  assert process['cleanup_complete'] is True and process['log_truncated'] is False
  assert Path(process['log']).stat().st_size==process['log_bytes']
 assert observed['opens']==observed['blocking']==observed['warnings']==observed['exclusions']==0
 assert N['metrics']==read(RP.parent/'metrics.json')
 p.check_refill_route_nets(sx.read(candidate),sx.read(RP.parent/'refill'/fixture.name))
 assert '18GiB total cache checked before task' in N['resource_limitations'] and '10GiB' not in N['resource_limitations']
 assert p.sha(candidate)==N['candidate_sha256'] and sha(RP)==R['native_receipt']['sha256']
 for relative,digest in N['tools']['implementation_sha256'].items():
  assert p.sha(CLONE/relative)==digest and p.sha(RP.parent/'code'/Path(relative).name)==digest
 for name,digest in N['tools']['files'].items():assert p.sha(Path(name))==digest
 copied=CLONE/'.tools'/Path(R['cached_dependency']['path']).name
 assert p.sha(copied)==p.sha(Path(R['cached_dependency']['path']))==R['cached_dependency']['sha256'] and copied.stat().st_ino!=Path(R['cached_dependency']['path']).stat().st_ino
 assert pc.evidence_inventory(RP.parent)==evidence
 import importlib.util
 planpath=ROOT/'.runs/installation043-angle-preparation-001/protocol.json';angleplan=read(planpath)
 outerpath=ROOT/'.runs/installation043-angle-complete-001/result.json';angleouter=read(outerpath)
 work=CLONE/'.runs/installation043-angle';nativeout=work/'native';childpath=nativeout/'result.json'
 assert angleplan['kind']=='installation043-owned-v2-free-angle-v1' and angleplan['git_head']==HEAD
 assert angleouter['accepted'] is False and angleouter['passed'] is True and angleouter['status']=='completed' and angleouter['git_head']==HEAD
 assert angleouter['child_completed_evidence_bound'] is True and angleouter['protocol_sha256']==sha(planpath)
 process=angleouter['process']
 assert process['argv']==[*install.NETWORK_DENIAL,str(CLONE/'.venv/bin/python'),'-B',str(work/'installed_angle.py'),'--mode','worker','--source-head',HEAD,'--protocol-sha256',sha(planpath)]
 assert process['cwd']==str(work) and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
 assert sha(Path(process['log']))==angleouter['log_sha256'] and Path(process['log']).stat().st_size==process['log_bytes']
 assert process['resource_guards']['max_group_rss_bytes']==4*1024**3 and process['resource_guards']['max_workdir_bytes']==128*1024**2
 assert max(angleouter['wall_seconds'],angleouter['full_cpu_seconds'])+2<=180
 assert f.evidence_inventory(outerpath.parent)==angleouter['completed_evidence']
 assert p.tree_hash(work)==angleouter['installed_work_material'] and sha(childpath)==angleouter['child_receipt_sha256']
 assert sha(Path(angleplan['controller_source']))==angleouter['controller_sha256']==angleplan['controller_sha256']==sha(work/'installed_angle.py')==angleplan['companion_sha256']
 spec=importlib.util.spec_from_file_location('installed_angle_reader',work/'installed_angle.py');companion=importlib.util.module_from_spec(spec);spec.loader.exec_module(companion)
 qualified=companion.read_transport(angleplan,sha(planpath));child=read(childpath);literal=f.canonical(child)
 assert child['passed'] is True and child['status']=='completed' and child['accepted'] is False and child['tools']==angleplan['installed_tools'] and child['transport']==qualified
 assert child['protocol_sha256']==sha(planpath) and child['git_head']==HEAD
 assert literal==angleouter['child_literal'] and f.canonical(read(childpath))==literal
 assert f.evidence_inventory(nativeout)==child['transport']['material']==child['completed_evidence']
 assert p.tree_hash(work)==angleouter['installed_work_material'] and max(child['wall_seconds'],child['full_cpu_seconds'])+2<=176
 assert qualified['complete_field_components']==6 and qualified['protected_routes']==1 and qualified['non45_route_segments']
 return dict(passed=True,native_outer_publication_completed=True,fresh_installed_child_and_material_qualified=True,installed_owned_v2_free_angle=dict(transport=qualified,outer_sample_wall_seconds=angleouter['wall_seconds'],outer_sample_full_cpu_seconds=angleouter['full_cpu_seconds'],outer_receipt_sha256=sha(outerpath)),receipt_sha256=sha(RP),candidate_sha256=N['candidate_sha256'],report_sha256=N['native_report_sha256'],native_counts={k:observed[k] for k in ('opens','blocking','warnings','exclusions')},metrics=N['metrics'],native_worker_count=len(N['steps']),baseline_source_has_schematic=False,baseline_schematic_parity_claimed=False,native_alias_export_checks=alias_checks,source_and_original_constraints_unchanged=True,exact_implementation_snapshots_and_tool_bytes=True,independent_pinned_engine_copy=True)

step('installed_actual_native_smoke_and_current_readback',native)

def outer():
 proc=EX['process'];assert EX['passed'] is True and EX['status']=='completed'
 assert f.evidence_inventory(ROOT/'.runs/installation-043-execution')==EX['completed_evidence']
 assert EX['source_current'] is True and EX['whole_delivery_within_budget'] is True and EX['publication_allowance_seconds']==2
 assert max(EX['wall_seconds'],EX['full_cpu_seconds'])+2<=600
 assert proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True and proc['log_truncated'] is False
 assert sha(Path(proc['log']))==EX['log_sha256'] and proc['log_bytes']==Path(proc['log']).stat().st_size
 assert sha(ROOT/'.runs/run-installation-043.py')==EX['wrapper_sha256']
 assert sha(BASE/'result.json')==pin and sha(RP)==npin
 timing={}
 for stage in ('base','targeted-prepare','targeted','targeted-missing-prepare','targeted-missing','native-prepare','native'):
  path=ROOT/('.runs/installation-043-outer-timing/'+stage+'-time.log');text=pc.read_bytes(path,64*1024).decode()
  values={name:float(value) for name,value in re.findall(r'(?m)^(real|user|sys) ([0-9.]+)$',text)}
  assert set(values)=={'real','user','sys'} and all(value>=0 for value in values.values())
  timing[stage]=dict(whole_command_wall_seconds=values['real'],whole_command_full_cpu_seconds=values['user']+values['sys'],time_log_sha256=sha(path),scope='External process-exit timing; two-decimal rounded. Separate stage, not a routing gain measurement.')
 return {'passed':True,'whole_command_costs':timing,'actual_installation_foreground_wall_seconds':EX['wall_seconds'],'actual_installation_foreground_full_cpu_seconds':EX['full_cpu_seconds'],'receipt_wall_seconds':R['wall_seconds'],'receipt_total_cpu_seconds':R['total_cpu_seconds'],'command_cpu_seconds':R['command_cpu_seconds'],'scratch_bytes':R['scratch_bytes'],'outer_execution_sha256':sha(ROOT/'.runs/installation-043-execution/result.json'),'installation_receipt_sha256':pin,'publication_and_native_receipt_unchanged':True,'scope':EX['scope']}
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
 assert not (ROOT/'.runs/installation043-targeted-001/supplement.json').exists() and not (ROOT/'.runs/installation043-targeted-001/supplement.json').is_symlink()
 for root,branch in ((ROOT,R['source_branch']),(CLONE,None)):
  assert install.git_identity(root,HEAD,branch)==R['git_identity_witnesses'][str(root)]
 for name,digest in N['tools']['files'].items():assert sha(Path(name))==digest
 assert sha(BASE/'result.json')==pin and sha(RP)==npin
 planpath=ROOT/'.runs/installation043-angle-preparation-001/protocol.json';angleplan=read(planpath)
 angleouter=read(ROOT/'.runs/installation043-angle-complete-001/result.json');work=Path(angleplan['native_output']).parent;child=read(work/'native/result.json')
 assert child['status']=='completed' and child['passed'] is True and child['git_head']==HEAD
 assert sha(work/'native/result.json')==angleouter['child_receipt_sha256'] and f.canonical(child)==angleouter['child_literal'] and p.tree_hash(work)==angleouter['installed_work_material']
 assert f.evidence_inventory(work/'native')==child['transport']['material']==child['completed_evidence']
 ls.check_normal_policy(RP.parent,N,max_bytes=128*1024**2,max_files=2048)
 ls.check_normal_policy(work/'native/route',read(work/'native/route/result.json'),max_bytes=128*1024**2,max_files=2048)
 return dict(passed=True,installed_owned_v2_prl_metadata_current=True,input_pins_sha256=PINSET_SHA,file_count=len(PINSET['files_sha256']),source_and_complete_distribution_unchanged=True)

step('late_complete_material_and_source',late_material)

r=resource.getrusage(resource.RUSAGE_SELF);rc=resource.getrusage(resource.RUSAGE_CHILDREN);wall=time.monotonic()-START;child_cpu=rc.ru_utime+rc.ru_stime-CHILD0;cpu=r.ru_utime+r.ru_stime-CPU0+child_cpu
result={'schema':1,'kind':'independent installed043 retained actual readback','passed':not failures and max(wall,cpu)+2<=60,'new_native_execution':False,'new_jvm_execution':False,'network_access':False,'read_only_git_head_allowed':True,'checks':checks,'failures':failures,'cost':{'active_wall_seconds':wall,'active_full_cpu_seconds':cpu,'child_cpu_seconds':child_cpu,'bootstrap_allowance_seconds':1,'emission_allowance_seconds':1,'charged_wall_seconds':wall+2,'charged_full_cpu_seconds':cpu+2,'scope':'from first audit-script line before installed project imports through checks; explicit1s bootstrap/1s emission; review preparation separately unmeasured development inspection'},'limits':{'audit_wall_full_cpu_seconds':60,'selected_output_bytes':16*1024**2},'limitations':['Same Mac and installed pinned tools/cache; ordinary default60mm PCB-only baseline plus one new owned-v2 fullSCH tuned-free-angle transport, no1007/4Cu/root loader/short repeats','Original targeted001 remains failed:62attempts/55successes/5errors/2failures; missing-only0027successes yields69attempts/62unique, not a single62-pass run','No full installed suite, freshOS,GUI,physical,comparative quality or default promotion claim; all stage costs separately retained','Samples+explicit allowances are not exact process-exit costs; external time logs retained independently','Local mutable evidence consistency, not adversarial authentication']}
CHILD=OUT/'checks';CHILD.mkdir();owner={};h.capture_destination(owner,CHILD)
result.update(accepted=False,status='completed' if result['passed'] else 'failed',completed_evidence=f.evidence_inventory(CHILD))
initial_passed=result['passed']
def audit_cpu():
 values=[resource.getrusage(k) for k in (resource.RUSAGE_SELF,resource.RUSAGE_CHILDREN)]
 return sum(x.ru_utime+x.ru_stime for x in values)-CPU0-CHILD0
def remaining():return min(58-(time.monotonic()-START),58-audit_cpu())
def stable():
 h.owned_destination(owner)
 if f.evidence_inventory(CHILD)!=result['completed_evidence']:raise p.Rejected('audit child material changed')
 late_material()
 if remaining()<=0:raise p.Rejected('audit whole delivery budget exhausted')
def account():
 wall=time.monotonic()-START;full=audit_cpu()
 result['cost'].update(active_wall_seconds=wall,active_full_cpu_seconds=full,charged_wall_seconds=wall+2,charged_full_cpu_seconds=full+2)
 result['passed']=bool(initial_passed and result['status']=='completed' and remaining()>0)
f.publish(CHILD,result,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
stored=read(CHILD/'result.json')
print(json.dumps({'passed':stored['passed'],'status':stored['status'],'failures':stored['failures'],'cost':stored['cost'],'checks':list(stored['checks'])}))
raise SystemExit(0 if stored.get('passed') is True and stored.get('status')=='completed' else 2)
