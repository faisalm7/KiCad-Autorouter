"""Finite owned-scene diagnostic; requires a separately reviewed frozen protocol.

Protocol keys: schema=1, kind=owned-solderjumper-ses-native-v1,
runtime_manifest_sha256, preparation_sha256, helpers_sha256 (exact HELPERS map),
tools (exact selected tool records plus javac and sandbox), continuation
(producer, prior_inventory, custody_pins). This one-off execution002 consumes
the exact retained failed compile receipt; no implicit retry or Native replay.
"""
import time, resource
ENTERED=time.monotonic()
CPU_ENTERED=sum(v.ru_utime+v.ru_stime for v in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
import argparse, fcntl, json, os, sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
RUNTIME=ROOT/'.runs/runtime-directory-058/runtime'
BASE=ROOT/'.runs/solderjumper-ses-native-vertical-slice-002'
MANIFEST='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'
PREP='60b89ade3e6fe477afbe9e4dc77ef79cee0d61aa51a5b0c5f93cef83d7161203'
CASES=('back90-positive','back90-false_hull');BOARD='pic_programmer.kicad_pcb'
OLD=ROOT/'.runs/solderjumper-ses-native-vertical-slice-001'
PRIOR_ROOTS=(OLD/'execution001',BASE/'execution001')
HELPERS=tuple('experiments/'+name for name in (
 'solderjumper_ses_v1/controller.py','solderjumper_ses_v1/transform.py','solderjumper_ses_v1/native_context.py',
 'solderjumper_ses_v1/SesBridge.java','custom_pad_area_probe_v1/AreaContactProbe.java',
 'custom_pad_area_probe_v1/driver.py','custom_pad_area_probe_v1/derive.py','custom_pad_area_probe_v1/checks.py',
 'pic_mixed_transport_probe_v1/MixedClassProbe.java','pic_mixed_transport_probe_v1/ExactPointWitness.java',
 'pic_mixed_transport_probe_v1/ses_checks.py','pic_custom_native_controls_v1/worker.py'))+tuple(
 'evidence/pic-custom-native-controls-002/'+case+'/recipe.json' for case in CASES)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true')
 ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
 if not a.execute:ap.error('--execute required; no implicit Native/Java execution')
 sys.dont_write_bytecode=True;sys.path[:0]=[str(RUNTIME),str(ROOT/'experiments/custom_pad_area_probe_v1'),str(ROOT)]
 from autorouter import config as c,pipeline as p,floor_route as floor,sexpr as sx,runner,local_settings as ls,handoff as h
 from experiments.custom_pad_area_probe_v1 import driver as base
 from experiments.solderjumper_ses_v1 import transform as t
 from checks import integer_coordinate_witness
 if c.ROOT!=RUNTIME or Path(p.__file__).resolve().parent.parent!=RUNTIME or c.NATIVE_VERSION!='10.0.7':raise ValueError('original058 runtime imports required')
 digest=lambda path:base.content(Path(path),128*1024**2,digest=True)['sha256']
 protocol=base.real(a.protocol);raw=base.content(protocol,1024**2)
 if digest(protocol)!=a.protocol_sha256:raise ValueError('explicit protocol pin differs')
 plan=base.decode(raw);prep=base.decode(base.content(BASE/'preparation.json',1024**2))
 if (set(plan)!={'schema','kind','runtime_manifest_sha256','preparation_sha256','helpers_sha256','tools','continuation'}
     or type(plan['schema']) is not int or plan['schema']!=1 or plan['kind']!='owned-solderjumper-ses-native-v1'
     or plan['runtime_manifest_sha256']!=MANIFEST or plan['preparation_sha256']!=PREP
     or set(plan['helpers_sha256'])!=set(HELPERS)):raise ValueError('exact finite protocol required')
 manifest=base.decode(base.content(RUNTIME/'runtime-distribution.json',256*1024))
 if manifest['build_source']['git_head']!='8f5e96b88dd22cd25919bb71ce47711612994efa':raise ValueError('058 source identity differs')
 tools={name:dict(pin,path=str(c.resolve_tool_path(pin['path']))) for name,pin in p.selected_tool_pins().items()}
 tools.update(javac=dict(path=str(c.JAVA.parent/'javac'),bytes=70464,sha256='c977cb93886f87d04f451b163c11f5bb2d100398cf48d57c680c8102237e5704'),
  sandbox=dict(path='/usr/bin/sandbox-exec',**base.content(Path('/usr/bin/sandbox-exec'),1024**2,digest=True)))
 if plan['tools']!=tools:raise ValueError('protocol must bind actual selected tools, javac and sandbox')
 pins={protocol:a.protocol_sha256,BASE/'preparation.json':PREP,RUNTIME/'runtime-distribution.json':MANIFEST}
 pins.update({ROOT/name:pin for name,pin in plan['helpers_sha256'].items()})
 pins.update({RUNTIME/name:pin for name,pin in manifest['immutable_files_sha256'].items()})
 pins.update({ROOT/name:pin for name,pin in prep['input_sha256'].items()})
 pins.update({Path(pin['path']):pin['sha256'] for pin in tools.values()})
 continuation=plan['continuation'];producer=base.real(Path(continuation['producer']))
 custody={BASE/'execution001/result.json':'f36179fff2fd208e887a9552c3bb4e45e1a58edc04123dea09e38771ecc2100a',
  BASE/'protocol.json':'090f3df7ce81cbfa0de3d5a4634724f171ea7f7b37037d60a1341de55b18374b',
  BASE/'complete-execution001.log':'e0567c310775430f3a3a93f173efd194a1f9dc39449d461adfe0609b0725b9bd',
  BASE/'complete-execution001-time.log':'25784da3f52b24dc37e7d2fabbb845bdd98c66416ede4b96227e879a937889fe',
  OLD/'complete-execution001.log':'4436149c01c658c9904fff5d469f7cbd956cea70e406e98b868359d0189ec741',
  OLD/'complete-execution001-time.log':'11bc37648128005e3464957d9eb5fe226d1bf4db816ff94a03acc07e20866e71',
  producer:'cd1c558bd1e4e6ae1e11069432023e247f6359067a7573252ce3c96a9470ad3d'}
 if (set(continuation)!={'producer','prior_inventory','custody_pins'} or not producer.is_relative_to(ROOT/'.runs')
     or continuation['custody_pins']!={str(k):v for k,v in custody.items()}
     or set(continuation['prior_inventory'])!={str(path) for path in PRIOR_ROOTS}):raise ValueError('exact one-off continuation custody required')
 pins.update(custody)
 if prep['status']!='PREPARED_ONLY' or tuple(row['case'] for row in prep['cases'])!=CASES:raise ValueError('paired preparation differs')
 for row in prep['cases']:
  if Path(row['source'])!=BASE/('source-'+row['case']):raise ValueError('fixed owned source path differs')
  for name,pin in row['source_files'].items():pins[Path(row['source'])/name]=pin['sha256']
 owners={}
 def owned(path):
  base.real(path)
  if path not in owners:
   if not path.is_dir() or path.stat().st_uid!=os.getuid():raise ValueError('owned directory required')
   owners[path]={};h.capture_destination(owners[path],path)
  h.owned_destination(owners[path])
  if path.stat().st_uid!=os.getuid():raise ValueError('directory ownership changed')
 for path in (ROOT,OLD,BASE,RUNTIME,protocol.parent,producer.parent,*PRIOR_ROOTS,*(Path(r['source']) for r in prep['cases'])):owned(path)
 def inputs():
  for path,pin in pins.items():
   if digest(path)!=pin:raise ValueError('captured input changed: '+str(path))
  for path in tuple(owners):owned(path)
  for path in PRIOR_ROOTS:
   if base.inventory(path)!=continuation['prior_inventory'][str(path)]:raise ValueError('prior retained execution inventory changed')
  for row in prep['cases']:ls.check_current_metadata(Path(row['source'])/Path(BOARD).with_suffix('.kicad_prl'))
 inputs()                         # Every required pin is checked before output or heavy work.
 started=ENTERED;cpu_started=CPU_ENTERED;out=BASE/'execution002'
 record=dict(schema=1,kind=plan['kind'],status='running',accepted=False,production_admitted=False,
  whole_project_drc_clean=False,workflow_qualified=False,Cheapino_eligible=False,
  protocol_sha256=a.protocol_sha256,runtime=str(RUNTIME),runtime_manifest_sha256=MANIFEST,preparation_sha256=PREP,
  continuation=continuation,prior_complete_wall_seconds=5.64,prior_complete_CPU_seconds=4.85,
  limits=dict(wall=180,full_CPU=180,return_reserve=25,engine=30,bytes=10*1024**2,files=1024,entries=2048,log=262144,RSS=1024**3),
  scope='Two same-CONTACT owned custom-pad scenes; not Cheapino different-net separation or product admission.',
  accounting='Parent plus waited-child CPU; complete external exit/authoring cost additional. Polled resource limits may overshoot.',cases=[],steps=[])
 frozen={}
 def remaining(work=True):
  value=min(174.36-(time.monotonic()-started),175.15-(base.cpu()-cpu_started))-(25 if work else 0)
  if value<=0:raise ValueError('original wall/full-CPU budget exhausted')
  return value
 def stable(*,prl=True):
  inputs();inventories=[base.inventory(path) for path in (OLD,BASE)]
  total=sum(v['bytes'] for files in inventories for v in files.values())
  if total>10*1024**2 or sum(map(len,inventories))>1024 or sum(1 for path in (OLD,BASE) for _ in path.rglob('*'))>2048:raise ValueError('aggregate original/prior/current resource quota exceeded')
  for name,pin in frozen.items():
   if base.content(out/name,digest=True)!=pin:raise ValueError('retained evidence changed: '+name)
  if prl:
   for root in (*PRIOR_ROOTS,out):
    for path in root.rglob('*.kicad_prl'):ls.check_current_metadata(path)
  return total
 def capture():
  stable();frozen.update(base.inventory(out))
 def account():record.update(continuation_wall_seconds=time.monotonic()-started,continuation_CPU_seconds=base.cpu()-cpu_started,wall_seconds=5.64+time.monotonic()-started,total_cpu_seconds=4.85+base.cpu()-cpu_started)
 def copy_project(source,destination):
  import shutil
  stable();shutil.copytree(source.parent,destination);os.chmod(destination,0o700)
  for path in destination.iterdir():os.chmod(path,0o600)
  board=destination/source.name;p.verify_candidate_files(board,p.tree_hash(source.parent));return board
 class Job(p.Job):
  def __init__(self,path):
   super().__init__(path,180,protect_local_settings=True);owned(self.out);self.remaining=remaining
   for key in tuple(self.env):
    if key in ('PYTHONPATH','PYTHONHOME') or key.startswith('KICAD_') and key not in ('KICAD_CONFIG_HOME','KICAD_CACHE_HOME','KICAD_DOCUMENTS_HOME'):self.env.pop(key)
   for key,name in (('HOME','home'),('TMPDIR','tmp')):(self.out/name).mkdir();self.env[key]=str(self.out/name)
   self.env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
  def step(self,name,argv,allowed=(0,),*,cap=30,already_sandboxed=False):
   used=stable(prl=False);p.experimental_native_version(None)
   argv=list(map(str,argv if already_sandboxed else [*floor.SANDBOX,*argv]))
   result=runner.run(argv,cwd=self.out,log=self.out/(name+'.log'),timeout=min(cap,remaining()),env=self.env,
    max_log_bytes=262144,max_group_rss_bytes=1024**3,max_workdir_bytes=10*1024**2-used+sum(v['bytes'] for v in base.inventory(self.out).values()))
   result['name']=name;self.steps.append(result);record['steps'].append(dict(result,job=str(self.out)))
   p.save_json(self.out/(name+'-process.json'),result)
   if result['status']=='cancelled':raise KeyboardInterrupt('shared worker cancellation')
   if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result['cleanup_complete'] is not True or result['log_truncated'] is not False:raise ValueError('bounded child failed: '+name)
   stable(prl=False);remaining();return result
 def native_counts(job,name,native,negative=False):
  report=floor.read_json(job.out/(name+'.json'));opens=report['unconnected_items']
  if negative:
   if len(opens)!=1 or opens[0].get('type')!='unconnected_items' or opens[0].get('severity')!='error' or opens[0].get('excluded',False) or not any(i.get('uuid')=='4915a982-bb17-52b4-bbe6-f66f4a60b95a' for i in opens[0]['items']):raise ValueError('exact concave-notch negative absent')
   clean=dict(native,opens=0,findings=[f for f in native['findings'] if f!=opens[0]])
  else:clean=native
  if native['opens']!=int(negative) or native['blocking'] or native['exclusions'] or not p.native_accepted(clean):raise ValueError('unexpected Native/full-SCH/field/ignored-check result')
  return native
 def reused_baselines():
  prior=floor.read_json(BASE/'execution001/result.json');old_plan=floor.read_json(BASE/'protocol.json')
  if (prior['status']!='failed' or prior['error']!='ValueError: bounded child failed: javac' or prior['accepted'] is not False
      or prior['runtime_manifest_sha256']!=MANIFEST or prior['preparation_sha256']!=PREP or prior['protocol_sha256']!=custody[BASE/'protocol.json']
      or old_plan['tools']!=tools or [s['name'] for s in prior['steps']]!=['source-drc','source-drc','javac']
      or {name for name in HELPERS if old_plan['helpers_sha256'][name]!=plan['helpers_sha256'][name]}!={'experiments/solderjumper_ses_v1/controller.py','experiments/solderjumper_ses_v1/SesBridge.java'}):raise ValueError('exact failed compile/source producer differs')
  sources={};contexts=[]
  for row,old in zip(prep['cases'],prior['cases']):
   case=row['case'];folder=BASE/'execution001'/('source-'+case);source=folder/'snapshot'/BOARD;expected={k:v['sha256'] for k,v in row['source_files'].items()}
   for path in (folder,source.parent,folder/'source-drc-input'):owned(path)
   if old['case']!=case or p.tree_hash(source.parent)!=expected:raise ValueError('retained baseline source copy differs')
   binding=floor.read_json(folder/'source-drc-binding.json');process=floor.read_json(folder/'source-drc-process.json')
   matches=[s for s in prior['steps'] if s['name']=='source-drc' and s['cwd']==str(folder)]
   if len(matches)!=1 or any(process.get(k)!=v for k,v in matches[0].items() if k!='job'):raise ValueError('old producer step/process differs')
   # Readback-only context. These two post-DRC fields were absent in the old
   # copied global steps; derive them from exact binding, never rewrite history.
   checker=dict(steps=[dict(process,validated_input_sha256=binding['before'][BOARD],emitted_candidate=binding['source'])])
   native=floor.check_drc_stage(folder,checker,'source-drc',source,folder/'source-drc-input'/BOARD,False,expected,schematic_parity=True)
   native_counts(SimpleNamespace(out=folder),'source-drc',native,case.endswith('false_hull'))
   if native!=old['source_native']:raise ValueError('retained baseline summary differs')
   sources[case]=source;record['cases'].append(dict(old,source_baseline_reused=True))
   contexts.append(dict(case=case,readback_only=True,derived_fields=['validated_input_sha256','emitted_candidate'],process_sha256=p.sha(folder/'source-drc-process.json'),binding_sha256=p.sha(folder/'source-drc-binding.json')))
  if len(prior['cases'])!=2:raise ValueError('exact two retained baselines required')
  record.update(reconstructed_checker_context=contexts,prior_steps=prior['steps']);stable();return sources
 def observe(job,source,case,count):
  context,raw_dsn=job.out/'context.json',job.out/'native.dsn'
  job.step('context',[c.PYTHON,HERE/'native_context.py',RUNTIME,MANIFEST,BASE/'preparation.json',PREP,case,source,p.sha(source),count,context,raw_dsn])
  value=floor.read_json(context);derived,expected=t.derive(base.content(raw_dsn),value,value,
   floor.read_json(ROOT/'evidence/pic-custom-native-controls-002'/case/'recipe.json'),base.content(source.with_suffix('.kicad_pro')),generated=count==0)
  path=job.out/('task.dsn' if count==0 else case+'.dsn');path.write_bytes(derived);p.save_json(job.out/'expected.json',expected)
  return path,expected,value
 def manager_state(path,expected):
  value=floor.read_json(path);row=value['case'];state=row['state']
  if value['status']!='observed' or row['post_load_awaited'] is not True or state!=row['state_after_ses'] or row['route_geometry']!=row['route_geometry_after_ses']:raise ValueError('bound nonrouting manager state changed')
  for settings in (row['settings_before'],row['settings_after']):
   if settings['router_enabled'] is not False or settings['optimizer_enabled'] is not False or settings['plane_as_obstacle'] is not True:raise ValueError('nonrouting settings differ')
  census=state['census']
  if any(census[k]!=v for k,v in dict(pins=4,areas=2,components=4,layers=2,max_net_number=2,vias=0).items()) or len(state['nets'])!=2:raise ValueError('manager census differs')
  if {n['name'] for n in state['nets']}!={'CONTACT','FOREIGN'} or any(n['contains_plane'] is not False or n['width_um']!=[500,500] for n in state['nets']):raise ValueError('source targets/no-plane differ')
  for area in state['areas']:
   if area['fixed']!='USER_FIXED' or area['nets']!=['CONTACT'] or area['layer']!='bottom_layer' or area['holes'] or not integer_coordinate_witness(area,state,area=True):raise ValueError('fixed area witness differs')
  if Counter(t.area.canonical_ring(x['ring_um']) for x in state['areas'])!=Counter(t.area.canonical_ring(x['ring_um']) for x in expected['areas']):raise ValueError('area contours differ')
  for n in state['nets']:
   for area in state['areas']:
    rows=[x for x in state['matrix'] if x['a']==n['trace_clearance_class'] and x['b']==area['clearance_class_index'] and x['layer']==1]
    if len(rows)!=1 or rows[0]['raw_um']!=250:raise ValueError('source clearance target differs')
  return dict(observations_sha256=p.sha(path),settings_before=row['settings_before'],settings_after=row['settings_after'],state_before=state,state_after=row['state_after_ses'])
 def final(job,source,dsn,expected,context,session,negative=False):
  filtered,proof=t.import_session(base.content(session,4*1024**2),base.content(dsn),expected)
  ses=job.out/'import.ses';ses.write_bytes(filtered);p.save_json(job.out/'transport.json',proof)
  import_source=copy_project(source,job.out/'import-input')
  original=sx.read(source);empty=p.routing_task(original,'whole_board_unlocked_routing')
  if p.routes(empty) or p.immutable(empty)!=p.immutable(original):raise ValueError('import task is not exact route-empty source')
  sx.write(import_source,empty);import_hashes=p.tree_hash(import_source.parent)
  imported=job.out/'imported.kicad_pcb';job.native('import','import',import_source,imported,ses)
  if p.tree_hash(import_source.parent)!=import_hashes:raise ValueError('Native import changed its complete input project')
  paths,vias=Counter(),Counter();tree=sx.parse(filtered.decode())
  for net in sx.children(sx.one(sx.one(tree,'routes'),'network_out'),'net'):
   name=sx.unquote(net[1])
   for wire in sx.children(net,'wire'):
    path=sx.one(wire,'path');paths.update(t.ses.segments(name,sx.unquote(path[1]),t.ses.number(path[2])/10,t.ses.pairs(path[3:],10)))
   for via in sx.children(net,'via'):vias[(name,tuple(t.ses.number(v)/10 for v in via[2:4]),t.ses.number(1600),t.ses.number(600))]+=1
  if t.ses.source_routes(sx.read(imported))!=(paths,vias):raise ValueError('Native import changed exact final SES routes')
  candidate=copy_project(source,job.out/'candidate');rebuilt=p.transplant_routes(original,sx.read(imported),protected=())
  if p.immutable(rebuilt)!=p.immutable(original):raise ValueError('source intent changed')
  sx.write(candidate,rebuilt);source_hashes=p.tree_hash(source.parent);p.verify_candidate_files(candidate,source_hashes)
  before=p.audit_route_dimensions(rebuilt,(),context['mapping'])
  refill=copy_project(candidate,job.out/'refill');job.drc('refill-drc',refill,save=True,schematic_parity=True)
  p.check_refill_route_nets(rebuilt,sx.read(refill));sx.write(candidate,p.transplant_fill(rebuilt,sx.read(refill)))
  if p.immutable(sx.read(candidate))!=p.immutable(original):raise ValueError('refill changed source intent')
  mapping=job.out/'final-netclasses.json';job.native('final-netclasses','netclasses',candidate,mapping);native_map=floor.read_json(mapping)
  if native_map['source']!=str(candidate) or native_map['board_sha256']!=p.sha(candidate) or native_map['project_sha256']!=p.sha(source.with_suffix('.kicad_pro')) or native_map['board_saved'] is not False:raise ValueError('final native map is stale')
  t.targets(t._parse_dsn(base.content(job.out/'native.dsn').decode()),native_map,base.content(source.with_suffix('.kicad_pro')))
  after=p.audit_route_dimensions(sx.read(candidate),(),native_map);pin=p.sha(candidate)
  native=native_counts(job,'final-drc',job.drc('final-drc',candidate,schematic_parity=True),negative)
  p.verify_candidate_files(candidate,source_hashes,pin)
  return dict(candidate=str(candidate),candidate_sha256=pin,final_native=native,dimension_audit_before=before,dimension_audit_after=after,import_input_hashes=import_hashes,import_seed_routes=0,
   final_report_sha256=p.sha(job.out/'final-drc.json'),final_binding_sha256=p.sha(job.out/'final-drc-binding.json'),transport=proof,production_admitted=False)
 with base.cancellation(),base.real(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);inputs();out.mkdir(mode=0o700);owned(out)
  try:
   sources=reused_baselines();capture()
   compile_job=Job(out/'compile');classes=compile_job.out/'classes';classes.mkdir()
   java_sources=[ROOT/name for name in HELPERS if name.endswith('.java')]
   compile_job.step('javac',[tools['javac']['path'],'-J-Xmx256m','-J-XX:ActiveProcessorCount=1','-J-Duser.home='+compile_job.env['HOME'],'-J-Djava.io.tmpdir='+compile_job.env['TMPDIR'],'-proc:none','-classpath',c.JAR,'-d',classes,*java_sources]);capture()
   for case,row in zip(CASES,record['cases']):
    job=Job(out/('roundtrip-'+case));source=copy_project(sources[case],job.out/'snapshot');dsn,expected,context=observe(job,source,case,2)
    bridge=job.out/'bridge';job.step('bridge',[c.JAVA,'-Xmx256m','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-Duser.home='+job.env['HOME'],'-Djava.io.tmpdir='+job.env['TMPDIR'],'-cp',str(classes)+os.pathsep+str(c.JAR),'SesBridge',case,dsn,bridge])
    row['manager']=manager_state(bridge/'observations.json',expected);row['roundtrip']=final(job,source,dsn,expected,context,bridge/'raw.ses',case.endswith('false_hull'));capture()
   job=Job(out/'positive-generated');source=copy_project(sources[CASES[0]],job.out/'task');sx.write(source,p.routing_task(sx.read(source),'whole_board_unlocked_routing'))
   if p.routes(sx.read(source)):raise ValueError('reference routes reached generated task')
   dsn,expected,context=observe(job,source,CASES[0],0)
   settings=p.engine_profile_settings('standard',30+p.ENGINE_NATIVE_RESERVE_SECONDS+p.ENGINE_GRACE_RESERVE_SECONDS,strict_class_targets=True)
   argv=p.engine_argv(job.out,[*settings['argv'],'--router.plane_as_obstacle=true']);argv[argv.index('-Xmx2g')]='-Xmx256m'
   argv[argv.index('-jar'):argv.index('-jar')]=['-Duser.home='+job.env['HOME'],'-Djava.io.tmpdir='+job.env['TMPDIR']]
   record['engine_settings']=settings;job.step('engine',argv,already_sandboxed=True,cap=30)
   record['generated']=final(job,source,dsn,expected,context,job.out/'routes.ses');capture()
   record.update(status='completed_diagnostic',observations_complete=True,internal_graph_qualification=False)
  except (Exception,KeyboardInterrupt) as exc:
   record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',observations_complete=False,error=type(exc).__name__+': '+str(exc))
  result=floor.publish(out,record,stable,account,lambda:remaining(False),owned=lambda:owned(out),final_check=lambda:(stable(),remaining(False)))
 print(json.dumps({k:result.get(k) for k in ('status','accepted','observations_complete','wall_seconds','total_cpu_seconds','error')}))
 return 0 if result['status']=='completed_diagnostic' else 1

if __name__=='__main__':raise SystemExit(main())
