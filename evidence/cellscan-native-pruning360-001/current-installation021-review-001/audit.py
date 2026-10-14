import time,resource
START=time.monotonic();r=resource.getrusage(resource.RUSAGE_SELF);CPU0=r.ru_utime+r.ru_stime
import json,hashlib,re,sys,subprocess,traceback
from pathlib import Path
ROOT=Path('/Users/faisal/Projects/KiCad-Autorouter-local');BASE=ROOT/'.runs/installation-021-current965';CLONE=BASE/'checkout';OUT=ROOT/'.runs/current-installation021-review-001'
sys.path.insert(0,str(CLONE))
def forbidden(*a,**kw):raise AssertionError('pure installed audit forbids subprocess/native/JVM/Git')
subprocess.run=forbidden;subprocess.Popen=forbidden
from scripts import install_smoke as install
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,config as c
checks={};failures=[]
def read(x):return f.read_json(x)
def sha(x):return hashlib.sha256(pc.read_bytes(x,128*1024**2)).hexdigest()
def step(name,action):
 try:checks[name]=action()
 except BaseException as exc:failures.append({'check':name,'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(limit=4)})
R=read(BASE/'result.json');EX=read(ROOT/'.runs/installation-021-current965-execution/execution.json');HEAD='965796670d2835e185938d52ef694333e5752356';RP=Path(R['native_receipt']['path']);N=read(RP);fixture=CLONE/R['selected_qualification']['fixture'];pin=sha(BASE/'result.json');npin=sha(RP)

def context():
 assert c.ROOT==CLONE and Path(p.__file__).resolve().is_relative_to(CLONE) and Path(install.__file__).resolve().is_relative_to(CLONE)
 assert Path(sys.executable)==CLONE/'.venv/bin/python'
 assert Path(sys.prefix).resolve()==CLONE/'.venv' and sys.prefix!=sys.base_prefix
 assert sys.version_info[:2]==(3,11)
 return {'passed':True,'module_root':str(c.ROOT),'python':sys.executable,'version':sys.version,'sys_prefix':sys.prefix,'base_prefix':sys.base_prefix,'pipeline_module':str(Path(p.__file__)),'install_module':str(Path(install.__file__)),'git_head':R['git_head']}
step('real_installed_context',context)

def commands():
 assert R['status']=='passed' and R['passed'] is True and R['git_head']==HEAD and EX['git_head']==HEAD
 assert len(R['commands'])==22
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
 text=(BASE/'15-tests.log').read_text();match=re.search(r'Ran (\d+) tests in ([0-9.]+)s\n\nOK\s*$',text)
 assert match and int(match.group(1))==72
 scoring=[line for line in text.splitlines() if '(tests.test_pruning_scoring.' in line]
 assert scoring and all(line.endswith(' ... ok') for line in scoring)
 check=read(BASE/'17-check-result.log');assert check['current'] is True and check['candidate_sha256']==N['candidate_sha256']
 freshness=[]
 for path in sorted(BASE.glob('freshness-*.json')):
  row=read(path);assert row['status']=='success' and row['exit_code']==0 and row['cleanup_complete'] is True and row['log_truncated'] is False
  assert row['argv'][:3]==install.NETWORK_DENIAL and sha(Path(row['log']))==row['log_sha256']
  freshness.append({'receipt_sha256':sha(path),'log_sha256':row['log_sha256'],'cleanup_complete':True})
 assert len(freshness)==8
 return {'passed':True,'offline_command_count':22,'commands':rows,'freshness_process_count':len(freshness),'freshness':freshness,'installed_test_count':72,'installed_test_log_seconds':float(match.group(2)),'scoring_control_count':len(scoring),'scoring_controls':scoring,'installed_test_scope':R['installed_test_scope'],'check_result_candidate_sha256':check['candidate_sha256'],'no_network_or_auth_workflow':True}
step('actual_commands_and_selected_tests',commands)

def inventory():
 listing=pc.read_bytes(BASE/'03-source-files.log',2_000_000).decode()
 assert pc.read_bytes(BASE/'09-clone-files.log',2_000_000).decode()==listing
 original=read(BASE/'source-tracked.json');assert sha(BASE/'source-tracked.json')==R['source_inventory_sha256']
 assert install.tracked_inventory(ROOT,listing)==original
 installed_listing=install.distribution_listing(listing);selected={name:original[name] for name in installed_listing.split('\0') if name}
 assert install.tracked_inventory(CLONE,installed_listing)==selected
 assert len(original)==20460==R['complete_source_tracked_files'] and len(selected)==505==R['installed_tracked_files']
 assert R['source_installation_mode']=='distribution' and R['historical_evidence_omitted_from_installation'] is True
 assert install.SOURCE_MAX_FILES==22000 and install.SOURCE_MAX_BYTES==320*1024**2
 for root,branch in ((ROOT,R['source_branch']),(CLONE,None)):
  assert install.git_identity(root,HEAD,branch)==R['git_identity_witnesses'][str(root)]
 for name,expected in R['venv_files_sha256'].items():assert sha(Path(name))==expected
 assert sha(Path(R['python']['resolved_path']))==R['python']['sha256']
 return {'passed':True,'complete_original_source_files':len(original),'installed_distribution_files':len(selected),'source_inventory_sha256':R['source_inventory_sha256'],'source_and_installed_subset_exact':True,'source_file_cap':22000,'source_byte_cap':320*1024**2,'source_and_clone_git_identity_witnesses_current':True,'independent_venv_files_unchanged':True,'complete_source_listing_sha256':sha(BASE/'03-source-files.log'),'clone_index_listing_sha256':sha(BASE/'09-clone-files.log')}
step('complete_source_and_installed_inventory',inventory)

def native():
 install.verify_native_contract(N,R['selected_qualification'],fixture,HEAD)
 evidence=pc.evidence_inventory(RP.parent)
 current=p.check_result(RP);assert current['current'] is True
 original=sx.read(fixture);candidate=RP.parent/'candidate'/fixture.name
 assert p.tree_hash(fixture.parent)==N['source_hashes']
 assert p.immutable(original)==p.immutable(sx.read(candidate))
 protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
 p.check_protected_import(RP.parent,N,original,candidate,protected);p.check_resource_accounting(N)
 before=dict(N['source_hashes']);before[fixture.name]=N['candidate_sha256']
 observed=f.check_drc_stage(RP.parent,N,'final-drc',candidate,RP.parent/'final-drc-input'/fixture.name,False,before,schematic_parity=False,sandboxed=False)
 assert observed==N['native'] and p.sha(RP.parent/'final-drc.json')==N['native_report_sha256']
 assert observed['opens']==observed['blocking']==observed['warnings']==observed['exclusions']==0
 assert abs(N['metrics']['track_length_mm']-60)<1e-8 and N['metrics']['vias']==0
 assert p.sha(candidate)==N['candidate_sha256'] and sha(RP)==R['native_receipt']['sha256']
 for relative,digest in N['tools']['implementation_sha256'].items():
  assert p.sha(CLONE/relative)==digest and p.sha(RP.parent/'code'/Path(relative).name)==digest
 for name,digest in N['tools']['files'].items():assert p.sha(Path(name))==digest
 copied=CLONE/'.tools'/Path(R['cached_dependency']['path']).name
 assert p.sha(copied)==p.sha(Path(R['cached_dependency']['path']))==R['cached_dependency']['sha256'] and copied.stat().st_ino!=Path(R['cached_dependency']['path']).stat().st_ino
 assert pc.evidence_inventory(RP.parent)==evidence
 return {'passed':True,'receipt_sha256':sha(RP),'candidate_sha256':N['candidate_sha256'],'report_sha256':N['native_report_sha256'],'native_counts':{k:observed[k] for k in ('opens','blocking','warnings','exclusions')},'metrics':N['metrics'],'native_budget_seconds':N['budget_seconds'],'native_wall_seconds':N['wall_seconds'],'native_full_cpu_seconds':N['total_cpu_seconds'],'native_worker_count':len(N['steps']),'native_process_cleanup_verified':True,'source_and_original_constraints_unchanged':True,'exact_implementation_snapshots_and_tool_bytes':True,'independent_pinned_engine_copy':True,'evidence_inventory_sha256':hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()}
step('installed_actual_native_smoke_and_current_readback',native)

def outer():
 proc=EX['process'];assert proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True and proc['log_truncated'] is False
 assert sha(Path(proc['log']))==EX['log_sha256'] and proc['log_bytes']==Path(proc['log']).stat().st_size
 assert sha(ROOT/'.runs/run-installation-021-current965.py')==EX['wrapper_sha256']
 assert sha(BASE/'result.json')==pin and sha(RP)==npin
 return {'passed':True,'actual_installation_foreground_wall_seconds':EX['wall_seconds'],'actual_installation_foreground_full_cpu_seconds':EX['full_cpu_seconds'],'receipt_wall_seconds':R['wall_seconds'],'receipt_total_cpu_seconds':R['total_cpu_seconds'],'command_cpu_seconds':R['command_cpu_seconds'],'scratch_bytes':R['scratch_bytes'],'outer_execution_sha256':sha(ROOT/'.runs/installation-021-current965-execution/execution.json'),'installation_receipt_sha256':pin,'publication_and_native_receipt_unchanged':True,'scope':EX['scope']}
step('outer_costs_and_publication',outer)
r=resource.getrusage(resource.RUSAGE_SELF);wall=time.monotonic()-START;cpu=r.ru_utime+r.ru_stime-CPU0
result={'schema':1,'kind':'independent installed021 retained actual readback','passed':not failures,'new_native_execution':False,'new_jvm_execution':False,'network_access':False,'checks':checks,'failures':failures,'cost':{'active_wall_seconds':wall,'active_full_cpu_seconds':cpu,'child_cpu_seconds':0,'bootstrap_allowance_seconds':1,'emission_allowance_seconds':1,'charged_wall_seconds':wall+2,'charged_full_cpu_seconds':cpu+2,'scope':'from first audit-script line before installed project imports through checks; explicit1s bootstrap/1s emission; review preparation separately unmeasured development inspection'},'limits':{'audit_wall_full_cpu_seconds':60,'selected_output_bytes':16*1024**2},'limitations':['existing Mac and verified installed tool/engine cache reused','fixed72 installed tests, not full installed suite or fresh OS','no comparative routing quality claim; preparation/installation costs separate from measured experiments','local mutable evidence consistency, not adversarial authentication']}
(OUT/'checks.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':not failures,'failures':failures,'cost':result['cost'],'checks':list(checks),'installed_test_count':checks.get('actual_commands_and_selected_tests',{}).get('installed_test_count')}))
