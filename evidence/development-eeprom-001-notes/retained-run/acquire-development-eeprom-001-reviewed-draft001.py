"""DRAFT: four pinned EEPROM originals, then read-only syntax observations.

Thin port of acquire-development-ina2xx-001 and its worker: unchanged shared
HTTP/blob/inventory, process runner and S-expression helpers. No Native, engine,
GUI, acceptance/preflight reader, script/model acquisition or publication.
Each phase is a single bounded attempt; failures and partial originals remain.
"""
import argparse,hashlib,json,math,os,re,resource,stat,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'.runs/development-eeprom-001'
PROTOCOL=ROOT/'.runs/acquire-development-eeprom-001-protocol.json'
PROTOCOL_SHA='8be9c174946aff7d4f0f90bfa537f16246befcc67c43696198ca65dc8fab88d9'
LEAD=ROOT/'.runs/development-eeprom-lead-001.json'
LEAD_SHA='69f18043c8f3173d2659bfb49b8f6c8a72d48059db7413fc9fe186344643a1d4'
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))

def owned(path,identity=None,directory=False):
 from experiments.licensed_acquisition_v1 import fetch as f
 f.contained(ROOT,path);s=path.lstat()
 if s.st_uid!=os.getuid() or getattr(s,'st_flags',0)!=0 or not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode) and s.st_nlink==1):raise ValueError('owned ordinary material required')
 value=(s.st_dev,s.st_ino,s.st_uid)
 if identity is not None and value!=identity:raise ValueError('owned identity replaced')
 return value

def write(name,data):
 raw=(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
 if len(raw)>1024**2:raise ValueError('one-MiB receipt cap')
 with (HERE/name).open('xb') as stream:stream.write(raw)

def load(expected_helper):
 if not re.fullmatch('[0-9a-f]{64}',expected_helper) or sha(Path(__file__))!=expected_helper:raise ValueError('exact reviewed helper required')
 if sha(PROTOCOL)!=PROTOCOL_SHA or sha(LEAD)!=LEAD_SHA:raise ValueError('frozen protocol/lead changed')
 plan=json.loads(PROTOCOL.read_bytes());pins=plan['material_sha256']
 for name,pin in pins.items():
  path=ROOT/name
  if path.is_symlink() or sha(path)!=pin:raise ValueError('shared implementation changed: '+name)
 from experiments.licensed_acquisition_v1 import fetch as f
 from autorouter import sexpr as sx,runner
 if Path(f.__file__).resolve()!=ROOT/'experiments/licensed_acquisition_v1/fetch.py' or Path(sx.__file__).resolve()!=ROOT/'autorouter/sexpr.py' or Path(runner.__file__).resolve()!=ROOT/'autorouter/runner.py':raise ValueError('shared helper import identity')
 plan=f.decode(f.bounded(PROTOCOL,65536));lead=f.decode(f.bounded(LEAD,65536))
 rows=plan['rows'];data=Path(plan['destination'])
 if plan['repository']!='WestianPKl/pcb-docs' or plan['commit']!=lead['revision'] or data!=ROOT/'.data/development-eeprom-001':raise ValueError('fixed source identity')
 if plan['expected_files']!=4 or plan['expected_bytes']!=360526 or len(rows)!=4 or plan['expected_bytes']!=sum(row['bytes'] for row in rows):raise ValueError('fixed four-file census')
 for row,source in zip(rows,lead['files']):
  expected_source=source['path'];name=Path(expected_source).name
  if name not in {'EEPROM_Board.kicad_pcb','EEPROM_Board.kicad_pro','EEPROM_Board.kicad_sch','README.md'}:raise ValueError('unsupported payload')
  if row['source_path']!=expected_source or row['destination']!='project/'+name or row['raw_url']!=source['url'] or row['bytes']!=source['bytes'] or row['sha256']!=source['sha256'] or row['git_blob_sha1']!=source['git_blob_sha1']:raise ValueError('lead/protocol row differs')
  if row['repository']!=plan['repository'] or row['commit']!=plan['commit'] or row['raw_url']!='https://raw.githubusercontent.com/'+row['repository']+'/'+row['commit']+'/'+row['source_path']:raise ValueError('exact raw URL required')
 if len({row['destination'] for row in rows})!=4 or plan['license_body']['acquire'] is not False:raise ValueError('no additional licence/body payload allowed')
 def stable():
  if sha(Path(__file__))!=expected_helper or sha(PROTOCOL)!=PROTOCOL_SHA or sha(LEAD)!=LEAD_SHA:raise ValueError('captured controller/protocol/lead changed')
  for name,pin in pins.items():
   path=ROOT/f.safe(name);owned(path)
   if f.sha(f.bounded(path))!=pin:raise ValueError('shared implementation changed: '+name)
 stable();return plan,f,sx,runner,stable

def inspect(plan,f,sx,data):
 project=data/'project';pcb=project/'EEPROM_Board.kicad_pcb';sch=pcb.with_suffix('.kicad_sch');pro=pcb.with_suffix('.kicad_pro')
 t=sx.read(pcb);s=sx.read(sch);p=f.decode(f.bounded(pro,1024**2))
 def walk(node):
  if type(node) is list:
   yield node
   for x in node:
    if type(x) is list:yield from walk(x)
 def vals(node,key):return [sx.unquote(x) for x in sx.one(node,key,[])[1:] if type(x) is str]
 fps=sx.children(t,'footprint');pads=[pad for fp in fps for pad in sx.children(fp,'pad')]
 settings=p.get('board',{}).get('design_settings',{});nets=p.get('net_settings',{})
 layers=[row for row in sx.one(t,'layers',[])[1:] if type(row) is list]
 symbols=sx.children(s,'symbol');definitions=sx.children(sx.one(s,'lib_symbols',[]),'symbol')
 defined={sx.unquote(n[1]) for n in definitions if len(n)>1};used={vals(n,'lib_id')[0] for n in symbols if vals(n,'lib_id')}
 sheetfiles=[sx.unquote(n[2]) for n in walk(s) if n and n[0]=='property' and len(n)>2 and sx.unquote(n[1])=='Sheetfile']
 models=[sx.unquote(n[1]) for n in walk(t) if n and n[0]=='model' and len(n)>1]
 requirement_text=[]
 for node in (*walk(t),*walk(s)):
  if node and node[0] in {'gr_text','text','property'}:
   for atom in node[1:]:
    if type(atom) is str:
     text=sx.unquote(atom)
     if re.search(r'(?i)impedance|differential|length.?match|return.?path|kelvin|shunt|current|timing|high.?speed|controlled|voltage',text):requirement_text.append(text)
 outline=[node for node in t if type(node) is list and node and 'Edge.Cuts' in vals(node,'layer')]
 points=[]
 for edge in outline:
  for node in walk(edge):
   if node and node[0] in {'start','mid','end','center','xy'} and len(node)>=3:
    try:points.append((float(node[1]),float(node[2])))
    except ValueError:raise ValueError('nonnumeric declared outline coordinate')
 if any(not all(math.isfinite(v) for v in point) for point in points):raise ValueError('nonfinite declared outline coordinate')
 point_bounds=None
 if points:point_bounds=dict(min_x=min(x for x,y in points),max_x=max(x for x,y in points),min_y=min(y for x,y in points),max_y=max(y for x,y in points))
 controls={key:sum(bool(node and node[0]==key) for node in walk(t)) for key in ('net_tie_pad_groups','keepout','rule_area','tuning_pattern','tuning_pattern_settings','teardrop','teardrop_parameters')}
 rec=dict(pcb_format=vals(t,'version'),schematic_format=vals(s,'version'),generator_versions=dict(pcb=vals(t,'generator_version'),schematic=vals(s,'generator_version')),
  copper_layers=[row for row in layers if len(row)>1 and re.fullmatch(r'(F|B|In[0-9]+)\.Cu',sx.unquote(row[1]))],footprints=len(fps),pads=len(pads),
  pad_types={kind:sum(len(pad)>2 and pad[2]==kind for pad in pads) for kind in sorted({pad[2] for pad in pads if len(pad)>2})},pad_shapes=sorted({pad[3] for pad in pads if len(pad)>3}),custom_pad_count=sum(len(pad)>3 and pad[3]=='custom' for pad in pads),
  route_counts={kind:len(sx.children(t,kind)) for kind in ('segment','arc','via')},locked_route_count=sum('locked' in n or sx.one(n,'locked') in (['locked','yes'],['locked']) for n in t if type(n) is list and n and n[0] in {'segment','arc','via'}),
  zones=len(sx.children(t,'zone')),suspicious_structural_token_counts=controls,schematic_netclass_flags=sum(bool(node and node[0]=='netclass_flag') for node in walk(s)),
  schematic_closure=dict(root_sheet_only=not sx.children(s,'sheet'),child_sheet_files=sheetfiles,root_placed_symbols=len(symbols),embedded_definitions=len(defined),placed_lib_ids=len(used),missing_embedded_lib_ids=sorted(used-defined),embedded_extends_declarations=[node for definition in definitions for node in walk(definition) if node and node[0]=='extends'],Native_parity='NOTRUN'),
  original_net_settings=nets,original_design_settings=settings,original_stackup=sx.one(sx.one(t,'setup',[]),'stackup',[]),
  route_width_declarations=sorted({tuple(vals(node,'width')) for node in t if type(node) is list and node and node[0] in {'segment','arc'}}),via_size_drill_declarations=sorted({(tuple(vals(node,'size')),tuple(vals(node,'drill'))) for node in sx.children(t,'via')}),
  edge_primitive_counts={key:sum(node[0]==key for node in outline) for key in sorted({node[0] for node in outline})},edge_declared_control_point_bounds_mm=point_bounds,dimensions_limit='Declared Edge.Cuts coordinate span only; curved extrema, closed-outline validity, clearance and actual board dimensions are not Native-verified.',
  footprint_library_ids=sorted({sx.unquote(fp[1]) for fp in fps if len(fp)>1}),external_model_declarations=models,external_models_summary=dict(declarations=len(models),unique=len(set(models)),absolute_unique=sum(x.startswith('/') for x in set(models)),acquired=0),
  explicit_source_requirement_text=sorted(set(requirement_text)),sanitization_or_removal_performed=False,production_preflight_or_acceptance_readers_called=False,decision='static_observations_only_eligibility_unproved',eligible_family_count=0,independent_family_established=False,
  remaining_unknowns=['Installed parser/source support, original Native DRC, full-schematic parity, refill and protected final-candidate acceptance are untested.','Electrical/current/voltage/thermal/measurement suitability cannot be inferred from labels, component descriptions, static grammar or future DRC.','Embedded stock-library/model/per-asset title closure, exact library revisions and independent ancestry remain unqualified.','Licence designation is retained in README, but official licence-body acquisition remains separately pending without a predeclared body hash.'])
 return rec

def worker(phase,expected_helper):
 plan,f,sx,runner,stable=load(expected_helper);owned(HERE,directory=True);here_id=owned(HERE,directory=True)
 data=Path(plan['destination']);started=time.monotonic();cpu0=cpu();ids={}
 def remaining():
  left=min((90 if phase=='acquire' else 30)-(time.monotonic()-started),60-(cpu()-cpu0))
  if left<=0:raise TimeoutError('phase wall/fullCPU exhausted')
  return left
 def current():
  stable();owned(HERE,here_id,directory=True)
  for path,identity in ids.items():owned(path,identity,directory=path in (data,data/'project'))
  remaining()
 rec=dict(schema=1,kind=plan['kind'],phase=phase,status='running',accepted=False,Native=False,engine=False,GUI=False,comparison_ready=False,eligible_family_count=0,independent_family_established=False,split='development-exposed',protocol_sha256=PROTOCOL_SHA,controller_sha256=expected_helper,repository=plan['repository'],commit=plan['commit'],destination=str(data),rights=plan['rights'],license_body=plan['license_body'],additional_authoring_research_review_cost='unknown additional, not zero')
 if phase=='acquire':
  rec.update(requests=[],files={},source_exact=False)
  try:
   current();owned(ROOT/'.data',directory=True)
   if os.path.lexists(data):raise ValueError('exclusive source destination already exists')
   data.mkdir(mode=0o700);(data/'project').mkdir(mode=0o700)
   ids.update({path:owned(path,directory=True) for path in (data,data/'project')})
   for row in plan['rows']:
    current()
    if len(rec['requests'])>=4:raise ValueError('four-request cap')
    request={'source_path':row['source_path'],'destination':row['destination']};rec['requests'].append(request)
    received=sum(x.get('received_bytes',0) for x in rec['requests'])
    raw=f.fetch_one(row,request,data/f.safe(row['destination']),plan['caps']['network_bytes']-received,remaining)
    rec['files'][row['destination']]=f.payload(row,raw);ids[data/f.safe(row['destination'])]=owned(data/f.safe(row['destination']))
   expected=dict(schema=1,files=dict(sorted(rec['files'].items())),directories=['project'],file_count=4,bytes=360526)
   f.inventory(data,expected,cap=1024**2);current()
   for name in rec['files']:os.chmod(data/f.safe(name),0o400)
   os.chmod(data/'project',0o500);os.chmod(data,0o500)
   f.inventory(data,expected,cap=1024**2);current();rec.update(status='acquired_unqualified',source_exact=True,source_inventory=expected)
  except BaseException as exc:rec.update(status='failed',error=type(exc).__name__+': '+str(exc));raise
  finally:
   rec.update(wall_seconds=time.monotonic()-started,full_CPU_seconds=cpu()-cpu0,requests_actual=len(rec['requests']),received_bytes=sum(x.get('received_bytes',0) for x in rec['requests']))
   write('acquisition.json',rec)
 else:
  try:
   current();acquisition=f.decode(f.bounded(HERE/'acquisition.json',65536));acquisition_pin=sha(HERE/'acquisition.json')
   if acquisition['status']!='acquired_unqualified' or acquisition['source_exact'] is not True or acquisition['protocol_sha256']!=PROTOCOL_SHA:raise ValueError('complete pinned original acquisition required')
   expected=dict(schema=1,files={row['destination']:dict(bytes=row['bytes'],sha256=row['sha256']) for row in plan['rows']},directories=['project'],file_count=4,bytes=360526)
   if acquisition['source_inventory']!=expected:raise ValueError('original inventory differs from protocol')
   before=f.inventory(data,expected,cap=1024**2)
   ids.update({path:owned(path,directory=path in (data,data/'project')) for path in (data,data/'project',*(data/f.safe(name) for name in before['files']))})
   rec.update(inspect(plan,f,sx,data),acquisition_sha256=acquisition_pin,source_inventory=before)
   current();f.inventory(data,before,cap=1024**2)
   if sha(HERE/'acquisition.json')!=acquisition_pin:raise ValueError('acquisition receipt changed')
   rec.update(status='completed',source_unchanged=True)
  except BaseException as exc:rec.update(status='failed',error=type(exc).__name__+': '+str(exc));raise
  finally:
   rec.update(wall_seconds=time.monotonic()-started,full_CPU_seconds=cpu()-cpu0);write('inspection.json',rec)
 print(json.dumps({key:rec[key] for key in ('phase','status','source_exact','source_unchanged','requests_actual','received_bytes','decision','wall_seconds','full_CPU_seconds') if key in rec}))

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('phase',choices=['acquire','inspect']);ap.add_argument('--expected-helper-sha256',required=True);ap.add_argument('--worker',action='store_true',help=argparse.SUPPRESS);a=ap.parse_args()
 plan,f,sx,runner,stable=load(a.expected_helper_sha256)
 if sys.platform!='darwin':raise ValueError('reviewed local Mac control only')
 if a.worker:return worker(a.phase,a.expected_helper_sha256)
 if a.phase=='acquire':
  if os.path.lexists(HERE):raise ValueError('preserve existing attempt; no retry/overwrite')
  owned(ROOT/'.runs',directory=True);HERE.mkdir(mode=0o700)
 else:owned(HERE,directory=True)
 owner=owned(HERE,directory=True)
 for suffix in ('.log','-process.json'):
  if os.path.lexists(HERE/(a.phase+suffix)):raise ValueError('phase already attempted; preserve evidence')
 started=time.monotonic();receipt=runner.run([sys.executable,'-B',str(Path(__file__)),a.phase,'--expected-helper-sha256',a.expected_helper_sha256,'--worker'],cwd=HERE,log=HERE/(a.phase+'.log'),timeout=90 if a.phase=='acquire' else 30,max_log_bytes=65536,max_group_rss_bytes=512*1024**2,max_workdir_bytes=16*1024**2)
 write(a.phase+'-process.json',receipt);stable();owned(HERE,owner,directory=True)
 print(json.dumps(dict(phase=a.phase,status=receipt['status'],exit_code=receipt['exit_code'],wall_seconds=receipt['wall_seconds'],cpu_seconds=receipt['cpu_seconds'],cleanup_complete=receipt['cleanup_complete'],complete_outer_wall_seconds=time.monotonic()-started,Native=False,engine=False,GUI=False)))
 raise SystemExit(0 if receipt['status']=='success' and receipt['exit_code']==0 and receipt['cleanup_complete'] and not receipt['log_truncated'] else 2)
if __name__=='__main__':main()
