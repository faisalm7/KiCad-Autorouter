"""Unexecuted owned Windows transport, not the POSIX router or product acceptance."""
import argparse,contextlib,copy,hashlib,json,os,subprocess,time,uuid
from pathlib import Path
from windows_process import run,preserved,digest,safe
ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--install',required=True);ap.add_argument('--java',required=True);ap.add_argument('--jar',required=True);ap.add_argument('--output',required=True);ap.add_argument('--firewall-manifest',required=True);a=ap.parse_args()
REPO=Path(a.repo).resolve();ROOT=Path(os.environ['RUNNER_TEMP']).resolve();OUT=safe(a.output,ROOT);OUT.mkdir();sysroot=Path(os.environ['SystemRoot']);started=time.monotonic()
import sys
sys.path.insert(0,str(REPO))
from autorouter import sexpr as sx,adapter
from experiments.free_angle_baseline_v1 import fixture
install=safe(a.install,ROOT);candidates=list(install.glob('bin/python.exe'));cli=install/'bin/kicad-cli.exe';java=Path(a.java).resolve();jar=safe(a.jar,ROOT)
if len(candidates)!=1 or not cli.is_file() or digest(jar)!='f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7':raise RuntimeError('owned Native Python/CLI or pinned JAR absent')
python=candidates[0];worker=Path(__file__).with_name('native_worker.py');tools={str(p):digest(p) for p in [python,cli,java,jar,worker,Path(__file__),Path(__file__).with_name('windows_process.py')]};steps=[]
manifest=safe(a.firewall_manifest,ROOT);manifest_pin=digest(manifest);gate=Path(__file__).with_name('firewall_gate.ps1');tools[str(manifest)]=manifest_pin;tools[str(gate)]=digest(gate)
def firewall(exe,sha):
 if digest(manifest)!=manifest_pin:raise RuntimeError('owned firewall manifest changed')
 result=subprocess.run([str(sysroot/'System32/WindowsPowerShell/v1.0/powershell.exe'),'-NoProfile','-NonInteractive','-File',str(gate),'-Manifest',str(manifest),'-Program',str(exe),'-Sha256',sha],capture_output=True,timeout=12)
 if result.returncode or len(result.stdout)>16384:raise RuntimeError('effective owned per-program firewall block unavailable: '+result.stderr.decode(errors='replace')[:300])
 return json.loads(result.stdout)
def call(argv,name,seconds=30,cancel_after=None):
 if time.monotonic()-started>240:raise RuntimeError('whole slice wall exceeded240')
 record=run(argv,cwd=OUT,log=OUT/(name+'.log'),root=ROOT,firewall_check=firewall,seconds=seconds,cancel_after=cancel_after);steps.append(record)
 if cancel_after is None and (record['status']!='success' or record['exit_code']):raise RuntimeError('worker failed: '+name)
 return record
def native(action,board,output,session=None):
 args=[str(python),'-B',str(worker),'--repo',str(REPO),'--action',action,'--board',str(board),'--output',str(output)]
 if session:args+=['--session',str(session)]
 return call(args,output.stem+'-'+action)
def project(folder,boardbytes):
 folder.mkdir();material=fixture.files()
 for name,raw in material.items():(folder/name).write_bytes(boardbytes if name.endswith('.kicad_pcb') else raw)
 return folder/(fixture.STEM+'.kicad_pcb')
def immutable(tree):
 tree=copy.deepcopy(tree);tree[:]=[n for n in tree if not isinstance(n,list) or not n or n[0] not in {'segment','arc','via'}]
 for zone in sx.children(tree,'zone'):zone[:]=[n for n in zone if not isinstance(n,list) or not n or n[0] not in {'filled_polygon','fill_segments'}]
 return tree
def report(board,name):
 before={p.name:digest(p) for p in board.parent.iterdir()};path=OUT/(name+'.json');step=call([str(cli),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--schematic-parity','--output',str(path),str(board)],name)
 if before!={p.name:digest(p) for p in board.parent.iterdir()}:raise RuntimeError('DRC input project changed')
 step.update(input_sha256=before,native_report_sha256=digest(path))
 value=json.loads(path.read_text());return value
def counts(value):return dict(opens=len(value['unconnected_items']),blocking=sum(v['severity']=='error' for v in value['violations']),warnings=sum(v['severity']=='warning' for v in value['violations']))
source=project(OUT/'original',fixture.files()[fixture.STEM+'.kicad_pcb']);original=sx.read(source);frozen={p.name:digest(p) for p in source.parent.iterdir()};result=dict(schema=1,passed=False,accepted=False,product_support=False,tool_sha256=tools,source_sha256=frozen,steps=steps)
try:
 with contextlib.ExitStack() as guards:
  for path in source.parent.iterdir():guards.enter_context(preserved(path,ROOT))
  call([str(java),'-XshowSettings:properties','-version'],'java-version');version=(OUT/'java-version.log').read_text(errors='replace')
  if 'java.version = 25.0.2' not in version or 'java.vendor = Eclipse Adoptium' not in version:raise RuntimeError('exact official Temurin25.0.2 required')
  original_report=report(source,'original-drc');need=counts(original_report)
  if need['opens']!=1 or need['blocking']:raise RuntimeError('original Native control not1open/0blocking')
  raw=OUT/'task.dsn';native('export',source,raw);dsn=OUT/'corrected.dsn';dsn.write_bytes(raw.read_bytes());changes=adapter.adapt_dsn(dsn,'both',[])
  ses=OUT/'routes.ses';engine=[str(java),'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(jar),'--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(OUT/'engine-config'),'--logging.file.enabled=false','-mp','2','--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0','-de',str(dsn),'-do',str(ses)];call(engine,'engine',120)
  imported=OUT/'imported.kicad_pcb';native('import',source,imported,ses);tree=sx.read(imported)
  netmap={n[1]:sx.unquote(n[2]) for n in sx.children(tree,'net') if len(n)==3};new=[]
  for route in tree:
   if not isinstance(route,list) or not route or route[0] not in {'segment','arc','via'}:continue
   net=sx.one(route,'net');name=netmap.get(net[1],sx.unquote(net[1])) if net else None
   if name=='ROUTE':row=copy.deepcopy(route);sx.one(row,'net')[1:]=['"ROUTE"'];new.append(row)
  if not new:raise RuntimeError('no newly generated ROUTE copper')
  merged=copy.deepcopy(original);merged.extend(new);candidate=project(OUT/'candidate',(sx.dump(merged)+'\n').encode())
  for path in candidate.parent.iterdir():
   if path.suffix!='.kicad_pcb':guards.enter_context(preserved(path,ROOT))
  filled=OUT/'filled.kicad_pcb';native('fill',candidate,filled)
  # Native serialization remains derived only: transplant filled_polygon records by exact zone UUID.
  filledtree=sx.read(filled);zones={sx.one(z,'uuid')[1]:z for z in sx.children(filledtree,'zone')}
  for zone in sx.children(merged,'zone'):
   nativezone=zones[sx.one(zone,'uuid')[1]];zone.extend(copy.deepcopy(sx.children(nativezone,'filled_polygon')))
  sx.write(candidate,merged)
  if immutable(original)!=immutable(merged) or not all(n in merged for n in sx.children(original,'segment')):raise RuntimeError('original shell or protected source copper changed')
  final=report(candidate,'final-drc')
  if counts(final)['opens'] or counts(final)['blocking']:raise RuntimeError('final Native not0/0')
  warning=lambda x:sorted(json.dumps(v,sort_keys=True) for v in x['violations'] if v['severity']=='warning')
  if warning(final)!=warning(original_report):raise RuntimeError('Native warning identities changed')
  disconnected=copy.deepcopy(merged);disconnected[:]=[n for n in disconnected if n not in new];bad=project(OUT/'invalid-disconnect',(sx.dump(disconnected)+'\n').encode())
  for path in bad.parent.iterdir():
   if path.suffix!='.kicad_pcb':guards.enter_context(preserved(path,ROOT))
  negative=report(bad,'disconnect-drc')
  if counts(negative)['opens']<1:raise RuntimeError('deliberate disconnect did not fail Native')
  cancel_engine=list(engine);cancel_engine[cancel_engine.index('-do')+1]=str(OUT/'cancel.ses');cancelled=call(cancel_engine,'cancel-engine',30,.2)
  if cancelled['status']!='cancelled' or not cancelled['cleanup_complete']:raise RuntimeError('live engine cancellation/cleanup unproved')
  if {p.name:digest(p) for p in source.parent.iterdir()}!=frozen or any(digest(p)!=v for p,v in tools.items()):raise RuntimeError('source/tool bytes changed')
  result.update(native_transport_observed=True,original=counts(original_report),final=counts(final),invalid=counts(negative),candidate_sha256=digest(candidate),final_report_sha256=digest(OUT/'final-drc.json'),network_live_checked=True,job_object_cancel_observed=True,whole_cpu_qualification=False,reason='Partial substrate observation; PowerShell guard-query CPU and outer complete exit need qualification, not product support.')
except BaseException as exc:result.update(native_transport_observed=False,cancelled=isinstance(exc,KeyboardInterrupt),error=type(exc).__name__+': '+str(exc))
finally:
 # Retain actual owned Native reports AND failed tool logs before ephemeral cleanup.
 import base64
 paths=[OUT/name for name in ('original-drc.json','final-drc.json','disconnect-drc.json','task.dsn','task.dsn.classes.json','corrected.dsn','routes.ses','imported.kicad_pcb.ses-proof.json')]
 paths += [OUT/'candidate'/(fixture.STEM+'.kicad_pcb')]+[Path(step['log']) for step in steps]
 total=0
 for path in paths:
  if not path.is_file():continue
  raw=path.read_bytes();total+=len(raw)
  if len(raw)>256*1024 or total>2*1024**2:
   result.update(native_transport_observed=False,error='owned CI proof/log publication bound');break
  print('KICAD_NATIVE_PAYLOAD '+json.dumps(dict(path=str(path.relative_to(OUT)),sha256=hashlib.sha256(raw).hexdigest(),encoding='base64',data=base64.b64encode(raw).decode())))
 result.update(wall_seconds_before_publication=time.monotonic()-started,job_cpu_seconds=sum(x['full_job_cpu_seconds'] for x in steps));(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('KICAD_NATIVE_RESULT '+json.dumps(result))
raise SystemExit(130 if result.get('cancelled') else 0 if result.get('native_transport_observed') and result['wall_seconds_before_publication']<240 else 2)
