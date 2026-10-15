"""Prospective exposed C-only follow-up; prepare/native/worker/read/qualify modes.
Draft only. Native mode alone invokes a new adaptive solve; read is pure replay.
Historical source/tool/HEAD records remain literal, separately pinned references.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,copy,hashlib,json,sys,subprocess,shutil,fcntl,os,stat,contextlib
sys.dont_write_bytecode=True
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT))

class PureReaderViolation(RuntimeError):pass

READ_ONLY_GIT=(('git','rev-parse','HEAD'),('git','status','--porcelain=v1','--untracked-files=normal'))
GIT_READ_PREFIX=('git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null')
CONTROLLED_GIT={GIT_READ_PREFIX+command[1:]:command for command in READ_ONLY_GIT}
_PURE_GUARD_ACTIVE=False

def check_pure_launch(executable,argv,cwd,env=None):
 if (executable!='git' or type(argv) not in (list,tuple) or tuple(argv) not in READ_ONLY_GIT
     or cwd is None or Path(cwd)!=ROOT or env is not None):
  raise PureReaderViolation('pure reader refuses subprocess outside exact read-only Git whitelist')

def pure_audit(event,args):
 if event=='subprocess.Popen':
  executable,argv,cwd,env=args
  if type(argv) not in (list,tuple) or tuple(argv) not in CONTROLLED_GIT:raise PureReaderViolation('pure reader refuses uncontrolled process audit')
  check_pure_launch(executable,CONTROLLED_GIT[tuple(argv)],cwd,env)
 elif event in {'os.system','os.fork','os.forkpty','os.posix_spawn','os.posix_spawnp','os.exec','os.spawn','pty.spawn'}:
  raise PureReaderViolation('pure reader refuses process creation: '+event)

@contextlib.contextmanager
def pure_reader_guard(*,audit=False):
 # Install before project imports in read mode. The audit hook persists for this
 # dedicated reader process; tests use the reversible wrapper and audit checker.
 global _PURE_GUARD_ACTIVE
 if _PURE_GUARD_ACTIVE:
  yield
  return
 _PURE_GUARD_ACTIVE=True
 original=subprocess.Popen;replaced={}
 def guarded(argv,*args,**kwargs):
  if args or set(kwargs)-{'cwd','stdout','stderr','text','universal_newlines','encoding','errors'}:
   raise PureReaderViolation('pure reader refuses subprocess execution options')
  if kwargs.get('stdout') not in (None,subprocess.PIPE) or kwargs.get('stderr') not in (None,subprocess.PIPE,subprocess.STDOUT):
   raise PureReaderViolation('pure reader refuses subprocess output redirection')
  check_pure_launch('git' if type(argv) in (list,tuple) and argv else None,argv,kwargs.get('cwd'))
  return original([*GIT_READ_PREFIX,*argv[1:]],**kwargs)
 def refused(*args,**kwargs):raise PureReaderViolation('pure reader refuses direct process creation')
 subprocess.Popen=guarded
 for name in ('system','popen','fork','forkpty','posix_spawn','posix_spawnp','spawnl','spawnle','spawnlp','spawnlpe','spawnv','spawnve','spawnvp','spawnvpe','execl','execle','execlp','execlpe','execv','execve','execvp','execvpe'):
  if hasattr(os,name):replaced[name]=getattr(os,name);setattr(os,name,refused)
 if audit:sys.addaudithook(pure_audit)
 try:yield
 finally:
  _PURE_GUARD_ACTIVE=False
  subprocess.Popen=original
  for name,value in replaced.items():setattr(os,name,value)

def parse_cli():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('mode',choices=['prepare','native','worker','read','qualify'])
 parser.add_argument('--prospective',type=Path,required=True)
 parser.add_argument('--case',choices=['ir','arc']);parser.add_argument('--output-prefix',type=Path)
 parser.add_argument('--strategy-delta-reviewed',action='store_true')
 parser.add_argument('--cache-ceiling-delta-reviewed',action='store_true')
 return parser.parse_args()

_ENTRY_ARGS=parse_cli() if __name__=='__main__' else None
if _ENTRY_ARGS is not None and _ENTRY_ARGS.mode=='read':
 _pure_lifetime_guard=pure_reader_guard(audit=True)
 _pure_lifetime_guard.__enter__()

from autorouter import pipeline as p,floor_route as f,handoff as h,config as c,local_settings as ls,sexpr as sx,strategy
from autorouter.runner import run
from scripts import experiment_quality as q,experiment_paired as paired
from experiments.native_paired_v1 import readback as shared
from experiments.native_paired_v1.observations import require,number,inventory,workers,candidate,resource_failure
ARMS=['B0','B1','B2_portfolio','C_feedback','C_chains']
ADAPTIVE=dict(id='C_adaptive',adapter='both',engine_profile='tuned',operation='prune',proposal_policy='adaptive')
CASES={
 'ir':dict(matrix='.runs/ir-chain-fivearm-001',qualification='.runs/ir-chain-fivearm-readback-execution-002/execution.json',delivered=240,reader=60),
 'arc':dict(matrix='.runs/arcdice-chain-native300-002',qualification='.runs/arcdice-chain-native300-readback-execution-002/execution.json',delivered=300,reader=90)}
DEPENDENCIES=['experiments/native_paired_v1/observations.py','experiments/native_paired_v1/readback.py']
NATIVE_CAP=150.;PUBLICATION=2.;STARTUP=1.;READER_TAIL_GUARD=15.

CACHE_BEFORE='.runs/retained-cache-pipeline-before-001.py'
CACHE_BEFORE_SHA256='8c4f3b0bcb87349a52ae94538af7650636b7e7b79b51c4f9f9e8956dea1a3eea'
IR_PREDECESSOR_PINS={'.runs/ir-adaptive-001-protocol.json': '30ebf12518b4c6c33f197975b7a15a98ece6285144375a884b27780fcfb504e1', '.runs/ir-adaptive-001-native/execution.json': '17e56a2b0a505ea651b43da7c3eb84db7484f59e7cf7be1984fab19a6f0e8e61', '.runs/ir-adaptive-001-native/invocation.json': 'e1a718d23aee23fe54320ca17c152b4968dba4b9d223085257ae3ee8c23b8789', '.runs/ir-adaptive-001-native/C_adaptive/result.json': 'd62f6ac0857fef0f33a0a43245927c750453e951d0958956340fddc8d87f08ef', '.runs/ir-adaptive-001-native/C_adaptive/pruning-preferences.json': '46ed0bc7d4fb2e5ea031f4f69440bf94fce55b855eccfc8730ccbd1ed04a0f87', '.runs/ir-adaptive-001-native/controller.py': '4fc95c256845d7d529292ce3b6741e47d6e4ab06b86a1a5f6fb3df7414c44fbe', '.runs/ir-adaptive-001-native/prospective-protocol.json': '30ebf12518b4c6c33f197975b7a15a98ece6285144375a884b27780fcfb504e1', '.runs/ir-adaptive-001-native/command.log': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}

def elapsed():return time.monotonic()-START,cpu()-CPU0

def real(value,existing=True):
 path=h.real_path(value,existing=existing)
 require(Path(value).is_absolute() and str(path)==str(value) and ROOT/'.runs' in path.parents,'canonical .runs path required')
 return path

def digest(value):return hashlib.sha256(f.canonical(value).encode()).hexdigest()

def clean():return subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=normal'],cwd=ROOT)==b''

def files_pin(names):
 result={}
 for n in names:
  path=h.real_path(n);require(ROOT in path.parents,'pin outside selected repository');result[str(path)]=p.sha(path)
 return result

def read_spec(path):
 path=real(path);spec=f.read_json(path)
 require(spec['schema']==1 and spec['status']=='frozen' and spec['arm']==ADAPTIVE,'wrong C-only protocol')
 require(spec['limits']==dict(native=150,reader=CASES[spec['case']]['reader'],inner_ceiling=120,delivered=CASES[spec['case']]['delivered'],output=128*1024**2),'limits differ')
 require(spec['controller_source']==str(Path(__file__).resolve()) and p.sha(Path(__file__))==spec['controller_sha256'],'controller differs')
 require(spec.get('cache_ceiling_delta_reviewed') is True and spec.get('operational_pipeline_delta') is not None and 'predecessor' in spec,'operational review or predecessor record missing')
 return path,spec,p.sha(path)

def cache_ceiling_bytes(before,after):
 require(type(before) is bytes and type(after) is bytes,'pipeline bytes required')
 require(before.count(b'16*1024**3')==1 and before.count(b'16 GiB')==2,'preserved pipeline ceiling shape differs')
 expected=before.replace(b'16*1024**3',b'18*1024**3').replace(b'16 GiB',b'18 GiB')
 require(after==expected,'pipeline differs beyond exact16-to18GiB operational ceiling')
 return hashlib.sha256(after).hexdigest()

def cache_ceiling_delta(current,old):
 source=ROOT/CACHE_BEFORE;before=source.read_bytes()
 require(p.sha(source)==CACHE_BEFORE_SHA256==old['implementation_sha256']['autorouter/pipeline.py'],'preserved pre-ceiling pipeline pin differs')
 after=(ROOT/'autorouter/pipeline.py').read_bytes();pin=cache_ceiling_bytes(before,after)
 require(pin==current['implementation_sha256']['autorouter/pipeline.py'],'current pipeline manifest differs')
 return dict(source=str(source),source_sha256=CACHE_BEFORE_SHA256,current_sha256=pin,transformation="before.replace('16*1024**3','18*1024**3').replace('16 GiB','18 GiB')",scope='finite operational cache/data ceiling only; routing and Native validation unchanged')

def compatibility(current,old,operational=None):
 require(set(current)==set(old),'tool manifest schema changed')
 require({k:v for k,v in current.items() if k not in ('git_head','implementation_sha256')}
     =={k:v for k,v in old.items() if k not in ('git_head','implementation_sha256')},'Native/tool/policy bytes changed')
 now=current['implementation_sha256'];prior=old['implementation_sha256'];allowed={'autorouter/strategy.py'}
 if operational is not None:
  require(operational==cache_ceiling_delta(current,old),'operational pipeline delta differs');allowed.add('autorouter/pipeline.py')
 require(set(now)==set(prior) and all(now[n]==prior[n] for n in now if n not in allowed),'non-strategy Native implementation changed')
 return {'autorouter/strategy.py':dict(reference=prior['autorouter/strategy.py'],current=now['autorouter/strategy.py'])}

def failed_predecessor(case):
 require(case in CASES,'unknown predecessor case')
 if case=='arc':return None
 pins={str(ROOT/name):pin for name,pin in IR_PREDECESSOR_PINS.items()}
 for name,pin in pins.items():require(p.sha(h.real_path(name))==pin,'failed IR001 predecessor pin changed: '+name)
 protocol=ROOT/'.runs/ir-adaptive-001-protocol.json';prior=f.read_json(protocol)
 root=ROOT/'.runs/ir-adaptive-001-native';outer=f.read_json(root/'execution.json');raw=f.read_json(root/'invocation.json');data=f.read_json(root/'C_adaptive/result.json')
 require(prior['case']=='ir' and prior['arm']==ADAPTIVE and prior['paths']['native']==str(root),'failed IR001 identity differs')
 require(p.sha(root/'prospective-protocol.json')==p.sha(protocol)==outer['protocol_sha256'] and outer['invocation_sha256']==p.sha(root/'invocation.json'),'failed IR001 enclosure linkage differs')
 require(raw['result']==str(root/'C_adaptive/result.json') and raw['result_sha256']==p.sha(root/'C_adaptive/result.json'),'failed IR001 result linkage differs')
 require(data['source']==prior['source'] and data['budget_seconds']==data['cpu_budget_seconds']==prior['assigned_inner_seconds'],'failed IR001 source/allocation differs')
 reason='Rejected: 16 GiB project cache/data ceiling exceeded'
 require(data['accepted'] is False and raw['accepted'] is False and raw['accepted_in_receipt'] is False and data['status']==raw['status']=='rejected' and data['reason']==raw['reason']==reason,'failed IR001 outcome differs')
 require(data['steps']==[] and data['trials']==[] and data['checkpoints']==[] and not data.get('incumbent') and not data.get('candidate_sha256') and not data.get('native_report_sha256') and not raw.get('candidate_sha256') and not raw.get('native_report_sha256'),'failed IR001 unexpectedly contains Native/routing work')
 material=inventory(root);before={n:v for n,v in material[0].items() if n!='execution.json'}
 require(f.canonical((before,material[1]))==f.canonical(outer['material']),'failed IR001 material changed')
 process=outer['process'];require(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process.get('log_truncated') is False,'failed IR001 cleanup/enclosure differs')
 cost={key:number(prior['preparation_cost'][key])+number(outer[key])+2*STARTUP+2*PUBLICATION for key in ('wall_seconds','full_cpu_seconds')}
 return dict(protocol=str(protocol),pins=pins,cost=cost,accepted=False,new_native_execution=False,new_engine_execution=False,reason=reason,operations=2,scope='IR only: actual failed preparation plus whole Native enclosure and two startup1/publication2 allowances; no reader existed; all six rows pay uniformly')

def predecessor_common(spec):
 expected=failed_predecessor(spec['case'])
 require('predecessor' in spec and spec['predecessor']==expected,'required failed predecessor record differs')
 if expected is None:return dict(wall_seconds=0.,full_cpu_seconds=0.)
 prior=f.read_json(expected['protocol'])
 require(spec['source']==prior['source'] and spec['source_hashes']==prior['source_hashes'] and spec['assigned_inner_seconds']==prior['assigned_inner_seconds'],'failed predecessor source/allocation differs')
 return expected['cost']

def uniform_reference_common(rows):
 require([r['id'] for r in rows]==ARMS,'reference population differs')
 common={}
 for field,inv,out in [('charged_wall_seconds','invocation_wall_seconds','wall_seconds'),('charged_cpu_seconds','invocation_cpu_seconds','full_cpu_seconds')]:
  values=[number(r[field])-number(r[inv]) for r in rows]
  require(min(values)>=0 and all(abs(x-values[0])<=1e-9 for x in values),'reference shared costs not uniform')
  common[out]=values[0]
 return common


def charged_rows(reference_rows,raw,outer,common,preparation,reader_cost,cap,valid,*,predecessor_cost=None):
 """Pure replacement accounting; historical solver work is never recharged to peers."""
 actual=uniform_reference_common(reference_rows)
 require(all(abs(number(common[k])-actual[k])<=1e-9 for k in actual),'reference common cost changed')
 added={};predecessor_cost=predecessor_cost if predecessor_cost is not None else dict(wall_seconds=0.,full_cpu_seconds=0.)
 require(set(predecessor_cost)=={'wall_seconds','full_cpu_seconds'},'both predecessor costs required')
 for key,inv in [('wall_seconds','invocation_wall_seconds'),('full_cpu_seconds','invocation_cpu_seconds')]:
  enclosing=number(outer[key]);own=number(raw[inv]);require(own<=enclosing,'outer costs omit adaptive invocation')
  added[key]=enclosing-own+number(preparation[key])+number(reader_cost[key])+3*STARTUP+3*PUBLICATION+number(predecessor_cost[key])
 rows=copy.deepcopy(reference_rows)
 for row in rows:
  row['charged_wall_seconds']=number(row['charged_wall_seconds'])+added['wall_seconds']
  row['charged_cpu_seconds']=number(row['charged_cpu_seconds'])+added['full_cpu_seconds']
 fresh=copy.deepcopy(raw);fresh.update(charged_wall_seconds=number(raw['invocation_wall_seconds'])+common['wall_seconds']+added['wall_seconds'],charged_cpu_seconds=number(raw['invocation_cpu_seconds'])+common['full_cpu_seconds']+added['full_cpu_seconds']);rows.append(fresh)
 return apply_delivered_caps(rows,cap,valid),added


def apply_delivered_caps(rows,cap,valid):
 number(cap)
 for row in rows:
  require(type(row['accepted']) is bool,'nonboolean arm acceptance')
  row['within_delivered_wall_full_cpu_caps']=max(number(row['charged_wall_seconds']),number(row['charged_cpu_seconds']))<=cap
  row['accepted']=valid and row['accepted'] and row['within_delivered_wall_full_cpu_caps']
  for observation in row.get('observations',[]):observation['final_delivery_accepted']=row['accepted']
 return rows


def replace_reader_cost(rows,sampled,enclosed,cap):
 result=copy.deepcopy(rows);delta={}
 for key in ('wall_seconds','full_cpu_seconds'):
  low=number(sampled[key]);high=number(enclosed[key]);require(high+1e-6>=low,'whole reader costs omit sampled work');delta[key]=max(0.,high-low)
 for row in result:
  row['charged_wall_seconds']+=delta['wall_seconds'];row['charged_cpu_seconds']+=delta['full_cpu_seconds']
 return apply_delivered_caps(result,cap,True)


def check_tail(now,sampled,cap,guard):
 require(len(now)==len(sampled)==2,'both wall and CPU samples required')
 require(all(number(a)<=number(b)+number(guard) for a,b in zip(now,sampled)) and max(now)<=number(cap),'publication callbacks exceeded wall/fullCPU guard')


def finish_publication(path,record,stable_callback,sampled,cap,guard):
 expected=f.canonical(record)
 require(f.canonical(f.read_json(path))==expected,'publication changed before callbacks')
 stable_callback()
 require(f.canonical(record)==expected and f.canonical(f.read_json(path))==expected,'publication changed during callbacks')
 check_tail(elapsed(),sampled,cap,guard)


def event_replay(rows):
 for worker in rows:
  cwd=Path(worker['cwd']);name=worker['name'];proc=f.read_json(cwd/(name+'-process.json'))
  require(proc['cleanup_complete'] is True and p.sha(cwd/(name+'-process.json'))==worker['process_sha256'],'retained worker changed')
  argv=proc['argv'];cmd=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
  if cmd[:3]==[str(c.CLI),'pcb','drc']:
   failed=proc['status']!='success' and not(proc['status']=='nonzero_exit' and proc.get('exit_code')==5)
   ls.check_event(cwd,f.read_json(cwd/(name+'-binding.json')),proc,allow_worker_failure=failed)

def reference(spec):
 if 'case' in spec:predecessor_common(spec)
 ref=spec['reference']
 for name,pin in ref['pins'].items():require(p.sha(h.real_path(name))==pin,'reference pin changed: '+name)
 for name,pin in ref['inventories'].items():require(digest(inventory(h.real_path(name)))==pin,'reference material changed: '+name)
 old=f.read_json(ref['spec']);qual=f.read_json(ref['qualification']);proof=f.read_json(ref['result']);execution=f.read_json(ref['reader_execution'])
 require(qual['passed'] is True and qual['source_current'] is True and proof['status']=='completed' and proof['comparison_eligible'] is True,'reference no longer qualified')
 require(qual['result_sha256']==p.sha(ref['result'])==execution['result_sha256'] and qual['reader_execution_sha256']==p.sha(ref['reader_execution']),'reference qualification linkage differs')
 rows=qual['final_charged_results'];require([x['id'] for x in rows]==ARMS,'reference population differs')
 require(uniform_reference_common(rows)==ref['common'],'reference shared costs differ')
 oldprotocol=f.read_json(Path(ref['matrix'])/'run/protocol.json')
 require(number(spec['assigned_inner_seconds'])==number(oldprotocol['inner_allowance_seconds']) and 30<=spec['assigned_inner_seconds']<=120,'inherited assigned allowance changed')
 require(spec['source']==old['source'] and spec['source_hashes']==old['source_hashes'],'reference source differs')
 require(compatibility(spec['tools'],old['tools'],spec.get('operational_pipeline_delta'))==spec['additive_strategy_delta'],'unreviewed implementation delta')
 for name,pin in old.get('pins',{}).items():
  target=Path(name) if Path(name).is_absolute() else ROOT/name
  # Historical live strategy is separately declared; retained captured strategy
  # and every original proof/source/helper pin remain unchanged.
  require(p.sha(target)==pin,'historical original source/proof pin changed: '+name)
 event_replay(proof['workers'])
 return old,qual,proof

def stable(path,spec,pin,*,new_workers=()):
 require(p.sha(path)==pin,'new protocol changed');q.verify_freeze(spec['freeze'],Path(spec['source']))
 require(clean(),'current tracked checkpoint changed')
 for name,pin in spec['dependencies'].items():require(p.sha(ROOT/name)==pin,'reader dependency changed')
 require(p.sha(spec['controller_source'])==spec['controller_sha256'],'controller changed')
 reference(spec);event_replay(new_workers)
 require(callable(getattr(strategy,'check_adaptive_policy',None)),'adaptive marker checker missing')

def prepare(args):
 require(args.strategy_delta_reviewed,'explicit additive strategy review declaration required')
 require(args.cache_ceiling_delta_reviewed,'explicit operational cache ceiling review declaration required')
 require(clean() and callable(getattr(strategy,'check_adaptive_policy',None)),'commit reviewed additive strategy/checker before preparation')
 case=CASES[args.case];matrix=ROOT/case['matrix'];qualpath=ROOT/case['qualification'];qual=f.read_json(qualpath)
 require(qual['passed'] is True and qual['source_current'] is True,'reference qualification failed')
 argv=qual['process']['argv'];proofdir=real(argv[argv.index('--output')+1]);proof=f.read_json(proofdir/'result.json')
 oldspec=matrix/'prospective-protocol.json';old=f.read_json(oldspec);oldprotocol=f.read_json(matrix/'run/protocol.json')
 board,family=q.selected_source(old['project']);require(str(board)==old['source'] and p.tree_hash(board.parent)==old['source_hashes'],'source differs')
 frozen=q.freeze(board);operational=cache_ceiling_delta(frozen['tools'],old['tools']);delta=compatibility(frozen['tools'],old['tools'],operational)
 prefix=real(args.output_prefix,False);protocol=real(args.prospective,False)
 paths={name:str(prefix.with_name(prefix.name+'-'+name)) for name in ('native','read','qualification')}
 require(not protocol.exists() and not prefix.exists() and len(set(paths.values()))==3 and all(not Path(n).exists() for n in paths.values()),'fresh exclusive destinations required')
 for a in paths.values():
  require(board.parent not in Path(a).parents and matrix not in Path(a).parents and Path(a) not in matrix.parents,'output overlaps original/reference')
 rows=qual['final_charged_results'];require([r['id'] for r in rows]==ARMS,'reference five-arm rows differ')
 common=uniform_reference_common(rows)
 pinpaths=[oldspec,matrix/'execution.json',matrix/'run/protocol.json',matrix/'run/paired-summary.json',qualpath,proofdir/'result.json',proofdir/'execution.json']
 for name in old.get('pins',{}):pinpaths.append(Path(name) if Path(name).is_absolute() else ROOT/name)
 original=old['original_native_report'];pinpaths.append(Path(original['path']))
 # Freeze original folder without inventing an Arc-style gate or replaying
 # absent historical stages. The old qualified proof and its pins are retained.
 material=[matrix,qualpath.parent,proofdir,Path(original['path']).parent.parent,board.parent]
 inventories={str(x):digest(inventory(x)) for x in material}
 spec=dict(schema=1,status='frozen',case=args.case,project=old['project'],family=family,source=str(board),source_hashes=p.tree_hash(board.parent),
  arm=ADAPTIVE,assigned_inner_seconds=number(oldprotocol['inner_allowance_seconds']),tools=frozen['tools'],git_head=frozen['tools']['git_head'],freeze=frozen,
  additive_strategy_delta=delta,strategy_delta_reviewed=True,operational_pipeline_delta=operational,cache_ceiling_delta_reviewed=True,predecessor=failed_predecessor(args.case),paths=paths,controller_source=str(Path(__file__).resolve()),controller_sha256=p.sha(__file__),
  dependencies={n:p.sha(ROOT/n) for n in DEPENDENCIES},limits=dict(native=150,reader=case['reader'],inner_ceiling=120,delivered=case['delivered'],output=128*1024**2),
  reference=dict(spec=str(oldspec),matrix=str(matrix),qualification=str(qualpath),result=str(proofdir/'result.json'),reader_execution=str(proofdir/'execution.json'),pins=files_pin(pinpaths),inventories=inventories,common=common),
  claims_limits=['Exposed C-only development against frozen historical controls; no fresh matched batch/new family/confirmation.','Fresh own incumbent; no historical route initialization or runtime board-identity oracle.','All old failures/costs retained; development/research CPU unknown and outside this frozen operation.'])
 require(30<=spec['assigned_inner_seconds']<=120,'invalid inherited inner allowance')
 reference(spec);require(clean() and q.selected_source(spec['project'])==(board,family),'source/checkpoint changed during preparation')
 spec['preparation_cost']=dict(zip(('wall_seconds','full_cpu_seconds'),elapsed()))
 spec['preparation_cost']['scope']='Actual preparation from module entry plus separately charged startup1/publication2; development/research separate.'
 p.save_json(protocol,spec)
 require(f.canonical(f.read_json(protocol))==f.canonical(spec) and all(a<=b+PUBLICATION for a,b in zip(elapsed(),(spec['preparation_cost']['wall_seconds'],spec['preparation_cost']['full_cpu_seconds']))),'preparation publication changed/exceeded reserve')
 print(json.dumps(dict(protocol=str(protocol),sha256=p.sha(protocol))))

def worker(path,spec,pin):
 root=Path(spec['paths']['native']);directory=root/'C_adaptive';stable(path,spec,pin)
 t=time.monotonic();ct=cpu();data=strategy.prune(Path(spec['source']),directory,spec['assigned_inner_seconds'],proposal_policy='adaptive')
 raw=q.summarize(ADAPTIVE,directory,data,time.monotonic()-t,cpu()-ct)
 raw.update(invocation_wall_seconds=time.monotonic()-t,invocation_cpu_seconds=cpu()-ct)
 raw['accepted']=raw['accepted'] and max(raw['invocation_wall_seconds'],raw['invocation_cpu_seconds'])<=120
 cancelled=q.cancelled(data) or q.cancelled(raw) or raw.get('cancelled') is True
 if cancelled:raw.update(accepted=False,status='cancelled',cancelled=True)
 stable(path,spec,pin);p.save_json(root/'invocation.json',raw)
 require(f.canonical(f.read_json(root/'invocation.json'))==f.canonical(raw),'invocation publication changed')
 return 130 if cancelled else 0

def native(path,spec,pin):
 root=Path(spec['paths']['native']);stable(path,spec,pin);require(not root.exists(),'native destination exists')
 lockpath=ROOT/'.runs/quality-experiment.lock';fd=os.open(lockpath,os.O_RDWR|os.O_NOFOLLOW);lock=os.fdopen(fd,'r+')
 require(stat.S_ISREG(os.fstat(lock.fileno()).st_mode),'invalid shared lane lock');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 root.mkdir();owner={};h.capture_destination(owner,root);record=dict(schema=1,passed=False,clean_before=True,source_current=False,protocol_sha256=pin,tools=spec['tools'],git_head=spec['git_head'])
 try:
  shutil.copyfile(path,root/'prospective-protocol.json');shutil.copyfile(spec['controller_source'],root/'controller.py')
  argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',spec['controller_source'],'worker','--prospective',str(path)]
  proc=run(argv,cwd=root,log=root/'command.log',timeout=max(.001,NATIVE_CAP-PUBLICATION-elapsed()[0]),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
  record['process']=proc;stable(path,spec,pin);h.owned_destination(owner)
  record.update(source_current=True,clean_after=clean(),invocation_sha256=p.sha(root/'invocation.json'))
  require(proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True and proc.get('log_truncated') is False,'adaptive process failed')
  record['passed']=True
 except (Exception,KeyboardInterrupt) as exc:record['reason']=type(exc).__name__+': '+str(exc)
 finally:
  try:record['material']=inventory(root)
  except Exception as exc:record.update(passed=False,material_error=str(exc))
  record.update(zip(('wall_seconds','full_cpu_seconds'),elapsed()))
  if max(elapsed())+PUBLICATION>NATIVE_CAP:record.update(passed=False,budget_exceeded=True)
  p.save_json(root/'execution.json',record)
  try:
   stable(path,spec,pin);h.owned_destination(owner)
   current=inventory(root);require(f.canonical(({n:v for n,v in current[0].items() if n!='execution.json'},current[1]))==f.canonical(record['material']),'native material changed during publication')
   require(all(a<=b+PUBLICATION for a,b in zip(elapsed(),(record['wall_seconds'],record['full_cpu_seconds']))) and max(elapsed())<=NATIVE_CAP,'native publication exceeded reserve')
   require(f.canonical(f.read_json(root/'execution.json'))==f.canonical(record),'native execution publication changed')
  except (Exception,KeyboardInterrupt) as exc:
   record.update(passed=False,reason=type(exc).__name__+': '+str(exc));p.save_json(root/'execution.json',record)
  lock.close()
 require(record['passed'],'native enclosure failed');return 0

def comparisons(rows):
 new=next(r for r in rows if r['id']=='C_adaptive');answer=[]
 mapped=[copy.deepcopy(r) for r in rows if r['id'] in ('B0','B1','B2_portfolio')]+[dict(new,id='C_feedback')]
 for item in paired.comparisons(mapped):item['system']='C_adaptive';answer.append(item)
 for name in ('C_feedback','C_chains'):
  old=next(r for r in rows if r['id']==name)
  if new['accepted'] and old['accepted']:
   answer.append(dict(baseline=name,system='C_adaptive',length_delta_mm=new['length_mm']-old['length_mm'],via_delta=new['vias']-old['vias']))
 return answer

def read(path,spec,pin):
 reader_cap=spec['limits']['reader']
 out=Path(spec['paths']['read']);require(not out.exists(),'reader destination exists');out.mkdir();owner={};h.capture_destination(owner,out)
 root=Path(spec['paths']['native']);outer=f.read_json(root/'execution.json');raw=f.read_json(root/'invocation.json');directory=root/'C_adaptive';board=Path(spec['source']);original=p.preflight(board);hashes=spec['source_hashes']
 old,qual,refproof=reference(spec);baseline=old['original_native_report']['summary'];proofs=[];seen_workers=[]
 material=inventory(root);result=dict(schema=1,status='incomplete',accepted=False,comparison_eligible=False,new_native_execution=False,new_engine_execution=False,protocol_sha256=pin,results=[],workers=[],final_candidates=[],claims_limits=spec['claims_limits'],reader_tail_guard_seconds=READER_TAIL_GUARD,inherited_failed_predecessor=spec['predecessor'],accounting='Every method inherits all historical reference shared/qualification cost, the explicit case-specific failed predecessor cost, plus actual new preparation, Native outer common and complete reader enclosure. Fixed startup/publication allowances are added; the15s inner publication guard is an acceptance reserve, not omitted work. Final enclosing receipt replaces sampled reader cost with actual whole reader cost.')
 def stable_read():
  stable(path,spec,pin,new_workers=result['workers']);h.owned_destination(owner)
  require(inventory(root)==material and max(elapsed())<reader_cap,'new material changed or reader cap exceeded')
 def check_one(label,folder,data,parent=None):
  err=resource_failure(folder,data,parent)
  if data.get('candidate_sha256') and data.get('native_report_sha256'):
   proofs.append(dict(id=label,status=data['status'],**candidate(folder,data,board,original,hashes,baseline,parent=parent,resource_error=err)))
  else:result.setdefault('incomplete_candidates',[]).append(dict(id=label,status=data.get('status')))
 def account():
  wall,full=elapsed()
  valid=result['status']=='completed' and outer['passed'] is True and outer['source_current'] is True and outer.get('clean_before') is True and outer.get('clean_after') is True and max(elapsed())<reader_cap
  rows,added=charged_rows(qual['final_charged_results'],raw,outer,spec['reference']['common'],spec['preparation_cost'],dict(wall_seconds=wall,full_cpu_seconds=full),spec['limits']['delivered'],valid,predecessor_cost=predecessor_common(spec))
  result.update(results=rows,comparison_eligible=valid,comparisons=comparisons(rows) if valid else [],observed_reader_wall_seconds=wall,observed_reader_full_cpu_seconds=full,new_common_wall_seconds=added['wall_seconds'],new_common_full_cpu_seconds=added['full_cpu_seconds'])

 try:
  with p.validation_readback_session():
   stable_read();require(outer['protocol_sha256']==pin and outer['invocation_sha256']==p.sha(root/'invocation.json'),'new enclosure pins differ')
   before={n:v for n,v in material[0].items() if n!='execution.json'};require(f.canonical(outer['material'])==f.canonical((before,material[1])),'new enclosing material differs')
   data=f.read_json(directory/'result.json');require(data['tools']==spec['tools'] and data['source_hashes']==hashes and data['source']==str(board) and data['budget_seconds']==data['cpu_budget_seconds']==spec['assigned_inner_seconds'],'adaptive identity/allocation differs')
   authoritative=q.summarize(ADAPTIVE,directory,data,raw['invocation_wall_seconds'],raw['invocation_cpu_seconds'])
   for k,v in authoritative.items():
    if k!='accepted':require(f.canonical(raw.get(k))==f.canonical(v),'adaptive comparison row differs: '+k)
   require(not raw['accepted'] or authoritative['accepted'],'unqualified adaptive row accepted')
   strategy.check_adaptive_policy(directory,data);strategy.check_chain_context(directory,data)
   if data['accepted']:p.check_result(directory/'result.json')
   result['workers']=workers(directory,data,board,hashes,original);check_one('C_adaptive',directory,data)
   if data.get('incumbent'):
    incdir=directory/'incumbent';inc=f.read_json(incdir/'result.json');marker=data['incumbent']
    require(marker['receipt']==str(incdir/'result.json') and all(marker.get(k)==inc.get(k) for k in ('accepted','status','metrics','wall_seconds')),'own incumbent marker differs')
    require([dict(x,phase='incumbent') for x in inc['steps']]==[x for x in data['steps'] if x.get('phase')=='incumbent'],'own incumbent workers differ')
    if data['accepted']:shared.pruning_incumbent_readback(directory,data,board,original,hashes)
    check_one('C_adaptive/incumbent',incdir,inc)
   for trial in data.get('trials',[]):
    child=directory/'trials'/trial['id'];record=f.read_json(child/'result.json')
    require(trial['receipt']==str(child/'result.json') and all(trial[k]==record[k] for k in ('id','accepted','status')),'trial parent binding differs')
    check_one('C_adaptive/'+trial['id'],child,record,data)
   # Reuse old full qualification plus every retained final observation with
   # the shared validators; never call its historical freeze as current.
   for proof in refproof['final_candidates']:
    folder=Path(proof['path']).parent.parent;record=f.read_json(folder/'result.json');label=proof['id'];parent=None
    if '/trial-' in label:parent=f.read_json(folder.parent.parent/'result.json')
    check_one('reference/'+label,folder,record,parent)
    if '/incumbent' not in label and '/trial-' not in label:
     seen_workers.extend(workers(folder,record,board,hashes,original))
   require({(x['cwd'],x['name']) for x in seen_workers}=={(x['cwd'],x['name']) for x in refproof['workers']},'historical worker population differs')
   event_replay(refproof['workers']);result.update(status='completed',final_candidates=proofs,reference_workers=len(seen_workers))
 except (Exception,KeyboardInterrupt) as exc:result.update(status='failed',reason=type(exc).__name__+': '+str(exc))
 def final_bound():
  stable_read()
  require(all(not r['accepted'] or max(r['charged_wall_seconds'],r['charged_cpu_seconds'])+READER_TAIL_GUARD<=spec['limits']['delivered'] for r in result['results']),'reader callback guard exceeds delivered cap')
 f.publish(out,result,stable_read,account,lambda:reader_cap-max(elapsed()),owned=lambda:h.owned_destination(owner),final_check=final_bound)
 require(f.canonical(f.read_json(out/'result.json'))==f.canonical(result),'reader result differs')
 result_pin=p.sha(out/'result.json')
 p.save_json(out/'execution.json',dict(zip(('wall_seconds','full_cpu_seconds'),elapsed()),result_sha256=result_pin))
 execution_pin=p.sha(out/'execution.json');stable_read()
 check_tail(elapsed(),(result['observed_reader_wall_seconds'],result['observed_reader_full_cpu_seconds']),reader_cap,READER_TAIL_GUARD)
 require(p.sha(out/'result.json')==result_pin and p.sha(out/'execution.json')==execution_pin,'reader receipts changed during final callbacks')
 return 0 if result['status']=='completed' and result['comparison_eligible'] else 2

def qualify(path,spec,pin):
 reader_cap=spec['limits']['reader'];new_workers=[]
 out=Path(spec['paths']['qualification']);require(not out.exists(),'reader enclosure exists');stable(path,spec,pin);out.mkdir();record=dict(schema=1,passed=False,protocol_sha256=pin,new_native_execution=False,new_engine_execution=False)
 try:
  proc=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',spec['controller_source'],'read','--prospective',str(path)],cwd=out,log=out/'command.log',timeout=max(.001,reader_cap-PUBLICATION-elapsed()[0]),max_log_bytes=256*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=4*1024**3)
  record['process']=proc;require(proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True and proc.get('log_truncated') is False,'pure reader failed')
  result=f.read_json(Path(spec['paths']['read'])/'result.json');new_workers=result['workers'];stable(path,spec,pin,new_workers=new_workers)
  require(result['status']=='completed' and result['comparison_eligible'] is True,'pure reader did not qualify')
  wall,full=elapsed();rows=replace_reader_cost(result['results'],dict(wall_seconds=result['observed_reader_wall_seconds'],full_cpu_seconds=result['observed_reader_full_cpu_seconds']),dict(wall_seconds=wall,full_cpu_seconds=full),spec['limits']['delivered'])
  require(max(wall,full)+PUBLICATION<=reader_cap,'whole reader enclosure cap exceeded')
  record.update(passed=True,wall_seconds=wall,full_cpu_seconds=full,final_charged_results=rows,comparisons=comparisons(rows),result_sha256=p.sha(Path(spec['paths']['read'])/'result.json'))
 except (Exception,KeyboardInterrupt) as exc:record.update(reason=type(exc).__name__+': '+str(exc),wall_seconds=elapsed()[0],full_cpu_seconds=elapsed()[1])
 p.save_json(out/'execution.json',record)
 try:
  finish_publication(out/'execution.json',record,lambda:stable(path,spec,pin,new_workers=new_workers),(record['wall_seconds'],record['full_cpu_seconds']),reader_cap,PUBLICATION)
 except (Exception,KeyboardInterrupt) as exc:
  record.update(passed=False,comparisons=[],reason=type(exc).__name__+': '+str(exc))
  for row in record.get('final_charged_results',[]):
   row['accepted']=False
   for observation in row.get('observations',[]):observation['final_delivery_accepted']=False
  p.save_json(out/'execution.json',record)
 return 0 if record['passed'] else 2

def main():
 args=_ENTRY_ARGS if _ENTRY_ARGS is not None else parse_cli()
 if args.mode=='prepare':require(args.case is not None and args.output_prefix is not None,'prepare requires case/output-prefix');prepare(args);return 0
 if args.mode=='read':
  with pure_reader_guard():
   path,spec,pin=read_spec(args.prospective);return read(path,spec,pin)
 path,spec,pin=read_spec(args.prospective);return globals()[args.mode](path,spec,pin)
if __name__=='__main__':raise SystemExit(main())
