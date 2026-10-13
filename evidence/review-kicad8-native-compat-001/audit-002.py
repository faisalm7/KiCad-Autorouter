"""Read-only audit of recorded KiCad8 compatibility processes and source diagnosis.
No native/JVM/Git/network process or production admission is performed here.
"""
from pathlib import Path
from collections import Counter
import ast,copy,hashlib,json,sys,time,subprocess
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'experiments/kicad8_native_compat_v1')];sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,floor_route as f,placement_clearance as pc,config as c
from experiments.kicad8_native_compat_v1 import driver as control
import fixture
run=ROOT/'.runs/kicad8-native-compat-001/run';outer=run.parent;start=time.monotonic();cpu=time.process_time();checks=[]
def must(value,label):
 if not value:raise AssertionError(label)
 checks.append(label)
def inventory(path):return pc.inventory(path,max_bytes=20*1024**2,max_files=2000,max_entries=4000)
def forbidden(*args,**kwargs):raise RuntimeError('review forbids child processes')
before=inventory(outer);record=f.read_json(run/'summary.json');execution=f.read_json(outer/'execution.json');protocol=f.read_json(run/'code/experiments/kicad8_native_compat_v1/PROTOCOL.json')
originals={rel:inventory(ROOT/rel) for rel in protocol['original_trees']}
acquisition_path=ROOT/protocol['acquisition_receipt'];must(p.sha(acquisition_path)==protocol['acquisition_receipt_sha256'],'exact acquisition receipt binding')
acquisition=f.read_json(acquisition_path);acquired=[row for row in acquisition['files'] if row['repository']=='sparkfun/SparkFun_Ideal_Diode_Breakout']
must(len(acquired)==6,'all six acquired ideal source/notice files present')
for row in acquired:
 payload=pc.read_bytes(ROOT/row['local_path'],20*1024**2);blob=hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
 must(row['commit']=='c950f439b55c08009e14fecc60f0fecd5832a42e' and len(payload)==row['bytes'] and hashlib.sha256(payload).hexdigest()==row['sha256'] and blob==row['git_blob_sha1'],'exact acquired revision/length/SHA/blob '+row['local_path'])

must(record['status']=='failed' and record['observations_complete'] is False,'whole experiment remains failed')
must(all(record[key] is False for key in control.FALSE_FLAGS),'all qualification/admission flags remain false')
must(p.sha(run/'code/experiments/kicad8_native_compat_v1/PROTOCOL.json')==record['protocol_sha256'],'actual protocol binding')
must(inventory(run/'code')==record['code_inventory'],'retained full controller code inventory')
for rel,digest in record['runtime_sources'].items():must(p.sha(run/'code'/rel)==digest,'retained runtime '+rel)
for rel,expected in protocol['original_trees'].items():must(originals[rel]==expected,'original project/notices '+rel)
must(execution['git_head']==record['tools']['git_head']=='28da8928557434bb6f53876ddb44e248fff5ab74','actual code checkpoint binding')
must(p.sha(outer/'command.log')==execution['log_sha256'],'outer log binding')
pins=f.read_json(ROOT/'toolchain.lock.json')['tools']
for pin in pins.values():must(record['tools']['files'][str(c.resolve_tool_path(pin['path']))]==pin['sha256'],'recorded pinned tool '+pin['path'])
processes=[];total_child=total_monitor=total_step_wall=0.;steps=record['steps']
for step in steps:
 folder=Path(step['cwd']);name=step['name'];process=f.read_json(folder/(name+'-process.json'))
 must(all(step.get(k)==v for k,v in process.items()),'exact retained process '+folder.name+'/'+name)
 must(step['argv'][:len(f.SANDBOX)]==f.SANDBOX and step['cleanup_complete'] is True and step['log_truncated'] is False,'network/cleanup/log bound '+folder.name+'/'+name)
 must(len(pc.read_bytes(Path(step['log']),1024**2))==step['log_bytes'],'retained log bytes '+folder.name+'/'+name)
 total_child+=step['cpu_seconds'];total_monitor+=step['monitor_cpu_seconds'];total_step_wall+=step['wall_seconds']
 processes.append({'case':folder.name,'name':name,'status':step['status'],'exit_code':step['exit_code'],'wall_seconds':step['wall_seconds'],'cpu_seconds':step['cpu_seconds'],'process_sha256':p.sha(folder/(name+'-process.json')),'log_sha256':p.sha(Path(step['log']))})
must(len(steps)==13 and len({(x['cwd'],x['name']) for x in steps})==13,'all13 unique recorded process entries')
must({str(Path(x['cwd'])/(x['name']+'-process.json')) for x in steps}=={str(x) for x in run.rglob('*-process.json')},'complete worker file population accounted')
must(total_child+total_monitor<=record['total_cpu_seconds'] and total_step_wall<=record['wall_seconds'],'all recorded worker costs included')
case_results=[]
with patch.object(subprocess,'run',side_effect=forbidden),patch.object(subprocess,'Popen',side_effect=forbidden):
 for row in record['cases']:
  case=row['case'];folder=run/case;source=control.SOURCE if case=='ideal_diode' else run/'owned-sources'/case/'fixture.kicad_pcb';hashes=inventory(source.parent);original=sx.read(source)
  must(row==f.read_json(folder/'case.json'),'stored case/index equality '+case)
  must(hashes==row['source_hashes'] and p.sha(source)==row['source_sha256'],'exact case source '+case)
  must(sx.one(original,'version')==['version','20240108'],'actual source grammar version '+case)
  if case=='ideal_diode':
   must(inventory(folder/'observe-input')==hashes,'failed export untouched complete original copy')
   missing=[name for name in ('original-export-context.json','original-export.dsn','original-native.kicad_pcb','refill-drc.json','final-drc.json') if not (folder/name).exists()]
   must(len(missing)==5 and row['status']=='failed' and row['observations_complete'] is False,'failed ideal outputs absent; no fabricated binding')
   f.process_check(folder,{'steps':steps},'original-export',f.context_argv('export',folder/'observe-input'/source.name,folder/'original-export-context.json',folder/'original-export.dsn'),allowed=(1,))
   case_results.append({'case':case,'status':row['status'],'source_sha256':row['source_sha256'],'steps':len(row['steps']),'error':row['error'],'missing_outputs':missing,'posthoc_copy_currently_exact':True,'historical_success_context_binding_available':False});continue
  must(pc.read_bytes(source)==fixture.board(case),'exact authored old grammar recipe '+case)
  candidate=Path(row['candidate']);p.verify_candidate_files(candidate,hashes,row['candidate_sha256'])
  saved=folder/'refill'/source.name;refill=f.check_drc_stage(folder,row,'refill-drc',saved,saved,True,hashes)
  final=f.check_drc_stage(folder,row,'final-drc',candidate,folder/'final-drc-input'/source.name,False,{**hashes,source.name:row['candidate_sha256']})
  must(refill==row['saved_drc']['native']==final==row['final_drc']['native'],'exact saved/final raw findings '+case)
  must(p.sha(folder/'refill-drc.json')==row['saved_drc']['report_sha256'] and p.sha(folder/'final-drc.json')==row['final_drc']['report_sha256'],'raw native report hashes '+case)
  must(p.sha(folder/'refill-drc-binding.json')==row['saved_drc']['binding_sha256'] and p.sha(folder/'final-drc-binding.json')==row['final_drc']['binding_sha256'],'raw native binding hashes '+case)
  shell=control.old_shell(original,sx.read(saved));must((sx.dump(shell)+'\n').encode()==pc.read_bytes(candidate),'exact original shell/derived fill reconstruction '+case)
  must(p.immutable(sx.read(candidate))==p.immutable(original) and p.routes(sx.read(candidate))==p.routes(original),'original format/nonfill/routes preserved '+case)
  passed,hits=fixture.expected(case,final);must(passed and hits==row['targeted_findings'],'exact actual positive/criticalinvalid target '+case)
  if case=='positive':
   contexts={}
   for name,board in (('original-export',folder/'observe-input'/source.name),('saved-export',saved),('shell-export',candidate)):
    context=f.read_json(folder/(name+'-context.json'));dsn=folder/(name+'.dsn');f.context_binding(context,board,inventory(board.parent),'export',p.sha(dsn));f.process_check(folder,row,name,f.context_argv('export',board,folder/(name+'-context.json'),dsn));contexts[name]=context
   must(control.geometry(contexts['original-export'])==control.geometry(contexts['saved-export'])==control.geometry(contexts['shell-export']),'all3 same-load native geometry/rules equal')
   emissions=[]
   for name,board in (('original-native',folder/'observe-input'/source.name),('saved-native',saved),('shell-native',candidate)):
    f.process_check(folder,row,name,[*f.SANDBOX,str(c.PYTHON),str(ROOT/'autorouter/native.py'),'roundtrip',str(board),str(folder/(name+'.kicad_pcb'))]);emissions.append(sx.read(folder/(name+'.kicad_pcb')))
   must(control.emission_equal(emissions[0],emissions[1])==row['native_serialization_equivalence'],'full native nonfill AST/routes original-vs-refill emission')
   must(control.emission_equal(emissions[0],emissions[2])==row['shell_serialization_equivalence'],'full native nonfill AST/routes original-vs-oldshell emission')
   must(control.digest(f.canonical(control.geometry(contexts['original-export'])).encode())==row['native_geometry_sha256'],'native geometry digest')
  must(all(row[key] is False for key in control.FALSE_FLAGS),'control case does not imply admission '+case)
  case_results.append({'case':case,'status':row['status'],'native_counts':{k:final[k] for k in ('opens','blocking','warnings','exclusions')},'ignored_checks':final['ignored_checks'],'source_sha256':row['source_sha256'],'candidate_sha256':row['candidate_sha256'],'native_report_sha256':row['final_drc']['report_sha256'],'steps':len(row['steps']),'targeted_findings':hits,'full_nonfill_native_emissions_equal':case=='positive'})

# Primary source diagnosis uses already acquired pinned material and the
# installed wrapper text, not an imported native API or a new source fetch.
source=control.SOURCE;board=sx.read(source);fp=[]
for item in sx.children(board,'footprint'):
 references=[x for x in sx.children(item,'property') if x[1]=='"Reference"'];must(len(references)==1,'static original reference field '+sx.unquote(sx.one(item,'uuid')[1]))
 fp.append({'uuid':sx.unquote(sx.one(item,'uuid')[1]),'reference':sx.unquote(references[0][2]),'pads':len(sx.children(item,'pad')),'attributes':sx.one(item,'attr')})
refs=Counter(x['reference'] for x in fp);duplicates={name:[x for x in fp if x['reference']==name] for name,n in refs.items() if n>1};vias=[x for x in p.routes(board) if x[0]=='via']
log=pc.read_bytes(run/'ideal_diode/original-export.log').decode();warnings=log.count('Warning: PCB_VIA::GetWidth called without a layer argument')
must(len(vias)==warnings==12,'static12via census equals actual12 assertion warnings')
must('ValueError: DSN export failed' in log,'actual export Boolean failure reached after warnings')
must(set(duplicates)=={'kibuzzard-6765D292','kibuzzard-6765D25C'} and all(len(rows)==2 and all(x['pads']==0 for x in rows) for rows in duplicates.values()),'two exact original padless duplicated references')
wrapper=Path(c.PYTHON).parents[1]/'lib/python3.9/site-packages/pcbnew.py';wrapper_text=pc.read_bytes(wrapper,20*1024**2).decode();class_node=next(x for x in ast.parse(wrapper_text).body if isinstance(x,ast.ClassDef) and x.name=='PCB_VIA');width_node=next(x for x in class_node.body if isinstance(x,ast.FunctionDef) and x.name=='GetWidth');width_doc=ast.get_docstring(width_node)
must('GetWidth(PCB_VIA self, PCB_LAYER_ID aLayer) -> int' in width_doc,'installed wrapper explicit layer width signature')
research=ROOT/'.runs/lipo-export-failure-research-001';manifest=f.read_json(research/'manifest.json');primary={}
for rel in ('source/pcbnew/pcb_track.cpp','source/pcbnew/specctra_import_export/specctra_export.cpp','source/pcbnew/python/scripting/pcbnew_scripting_helpers.cpp'):
 path=research/rel;raw=pc.read_bytes(path,20*1024**2);expected=manifest['files'][rel];digest=p.sha(path);must(digest==(expected['sha256'] if isinstance(expected,dict) else expected),'cached primary source pin '+rel);primary[rel]={'sha256':digest,'bytes':len(raw)}
track=pc.read_bytes(research/'source/pcbnew/pcb_track.cpp').decode();exporter=pc.read_bytes(research/'source/pcbnew/specctra_import_export/specctra_export.cpp').decode();script=pc.read_bytes(research/'source/pcbnew/python/scripting/pcbnew_scripting_helpers.cpp').decode()
must('m_padStack.Size( PADSTACK::ALL_LAYERS ).x' in track and 'return m_padStack.Size( aLayer ).x;' in track,'pinned via width return meaning')
must('for( FOOTPRINT* footprint : aBoard->Footprints() )' in exporter and 'STRINGSET_PAIR refpair = refs.insert' in exporter and 'Multiple footprints have the reference' in exporter,'pinned exporter all-footprint duplicate rejection')
must('catch( ... )\n    {\n        return false;' in script,'pinned scripting wrapper suppresses caught export reason')
for rel,expected in originals.items():must(inventory(ROOT/rel)==expected,'review original preservation '+rel)
must(inventory(outer)==before,'review entire original run unchanged')
must(execution['wall_seconds']<90 and execution['full_cpu_seconds']<90 and execution['process']['cleanup_complete'] is True and execution['process']['sampled_peak_workdir_bytes']<20*1024**2,'actual outer full resource/cleanup limits')
result={'schema':1,'status':'audit_passed','original_experiment_status':'failed','native_reexecuted':False,'subprocess_executed':False,'guard_count':len(checks),'guards':checks,'case_results':case_results,'processes':processes,'process_count':len(processes),'summed_worker_cpu_seconds':total_child,'summed_monitor_cpu_seconds':total_monitor,'summed_step_wall_seconds':total_step_wall,'stored_wall_seconds':record['wall_seconds'],'stored_full_cpu_seconds':record['total_cpu_seconds'],'outer_wall_seconds':execution['wall_seconds'],'outer_full_cpu_seconds':execution['full_cpu_seconds'],'originals_unchanged':True,'diagnosis':{'source_sha256':p.sha(source),'source_format':sx.one(board,'version')[1],'footprint_count':len(fp),'route_counts':dict(Counter(x[0] for x in p.routes(board))),'duplicate_references':duplicates,'actual_no_layer_width_warning_count':warnings,'installed_wrapper_sha256':p.sha(wrapper),'installed_width_doc':width_doc,'primary_source_commit':'0feeca2a807f428ad2b3fa7c1e39625cb769f02c','primary_sources':primary,'export_failure_cause':'Source-backed duplicate-reference inference; native all-footprint census/exception unavailable, not proven by the Boolean failure alone. Via API warnings are a separate demonstrated observer defect.','recommended_width_meaning':'For an ordinary two-layer through via use explicit copper-layer size.x as diameter and require F/B equality where one scalar width is expected; unsupported asymmetric padstacks must fail closed.','remaining_observation':'Fresh final-mode same-load context and original/native-save/refill/old-shell native emissions only on unchanged ideal source; no DSN retry/normalization or production/SES admission.'},'bindings':{'summary_sha256':p.sha(run/'summary.json'),'execution_sha256':p.sha(outer/'execution.json'),'protocol_sha256':record['protocol_sha256'],'acquisition_receipt':protocol['acquisition_receipt'],'acquisition_sha256':protocol['acquisition_receipt_sha256'],'original_inventories':originals,'run_inventory':before},'audit_wall_seconds':time.monotonic()-start,'audit_parent_cpu_seconds':time.process_time()-cpu,'scope':'Actual13recorded processes and owned compatibility controls only; ideal export failed, format/SES/routing admission remains closed.'}
p.save_json(HERE/'audit-002.json',result);print(json.dumps({k:result[k] for k in ('status','original_experiment_status','native_reexecuted','guard_count','process_count','summed_worker_cpu_seconds','outer_wall_seconds','outer_full_cpu_seconds','audit_wall_seconds')}))
