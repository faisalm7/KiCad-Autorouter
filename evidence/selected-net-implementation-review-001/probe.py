"""Synthetic full-checker receipt controls only; no native or solver execution.
Authored minimal legacy board and fabricated process/report/code metadata are
NOT native qualification. All production checks remain unpatched.
"""
import copy,hashlib,json,shutil,sys,uuid
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, preferences as pref, routing_scope as rs, sexpr as sx
from autorouter import review_export as e
OWN=Path(__file__).resolve().parent
SOURCE_FILES=['autorouter/routing_scope.py','autorouter/preferences.py','autorouter/pipeline.py','autorouter/floor_route.py','autorouter/review_export.py','autorouter/__main__.py']
initial={f:p.sha(ROOT/f) for f in SOURCE_FILES}
base=OWN/'synthetic';base.mkdir();source_dir=base/'source';source_dir.mkdir();run=base/'run';run.mkdir()
source=source_dir/'board.kicad_pcb'
def route(net,ident,locked=False):
 row=['segment',['start','1','1'],['end','2','1'],['width','0.2'],['layer','"F.Cu"'],['net',str(net)],['uuid','"'+str(uuid.UUID(int=ident))+'"']]
 if locked:row.append(['locked','yes'])
 return row
original=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal']],['net','0','""'],['net','1','"SEL"'],['net','2','"OTHER"'],['footprint','"fixture"',['at','10','10']],route(1,1),route(1,2,True),route(2,3)]
sx.write(source,original);source.with_suffix('.kicad_pro').write_text('{}\n');source.with_suffix('.kicad_sch').write_text('fabricated schematic seam; no native parse\n')
shutil.copytree(source_dir,run/'snapshot');shutil.copytree(source_dir,run/'candidate');candidate=run/'candidate'/source.name
final=copy.deepcopy(original);final.remove(final[-3]);final.append(route(1,4));sx.write(candidate,final)
shutil.copytree(candidate.parent,run/'final-drc-input');native_input=run/'final-drc-input'/candidate.name
native=run/'final-drc.json';p.save_json(native,{'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':source.name,'included_severities':['error','warning','exclusion'],'ignored_checks':[],'violations':[],'unconnected_items':[],'schematic_parity':[]})
metrics={'version':'10.0.0','track_length_mm':3.0,'vias':0};p.save_json(run/'metrics.json',metrics)
code=run/'code';code.mkdir();implementation={}
for name in ['pipeline.py','native.py','runner.py','sexpr.py']:
 file=code/name;file.write_text('# Fabricated code provenance seam; never executed.\n');implementation['autorouter/'+name]=p.sha(file)
choice={'scope':'selected_nets','nets':['SEL'],'profile':'completion-only'}
request={'captured':None,'snapshot':pref.snapshot(overrides=choice),'effective':pref.resolve(overrides=choice)}
settings=p.engine_profile_settings('completion-only',100);settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
engine={'name':'engine','status':'success','exit_code':0,'cleanup_complete':True,'argv':p.engine_argv(run,settings['argv']),'cwd':str(run),'wall_seconds':0.1,'cpu_seconds':0.1,'monitor_cpu_seconds':0.1}
process={'name':'final-drc','status':'success','exit_code':0,'cleanup_complete':True,'argv':[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--schematic-parity','--exit-code-violations','--output',str(native),str(native_input)],'cwd':str(run),'wall_seconds':1,'cpu_seconds':1,'monitor_cpu_seconds':0.1}
p.save_json(run/'engine-process.json',engine);p.save_json(run/'final-drc-process.json',process)
pins=json.loads((ROOT/'toolchain.lock.json').read_text())['tools']
data={'schema':1,'accepted':True,'status':'routing_accepted','source':str(source),'source_hashes':p.tree_hash(source_dir),'candidate':str(candidate),'candidate_sha256':p.sha(candidate),'native_report_sha256':p.sha(native),'native':p.parse_report(native,source.name),'scope':'selected_nets','schematic_parity':'checked by final native DRC','invariants_unchanged':True,'whole_project_drc_clean':True,'metrics':metrics,'steps':[engine,dict(process,validated_input_sha256=p.sha(candidate),emitted_candidate=str(candidate))],'wall_seconds':2,'budget_seconds':120,'cpu_budget_seconds':120,'parent_cpu_seconds':0.2,'child_cpu_seconds':1.1,'monitor_cpu_seconds':0.2,'total_cpu_seconds':1.5,'tools':{'kicad':'10.0.0','implementation_sha256':implementation,'files':{str(p.c.resolve_tool_path(pin['path'])):pin['sha256'] for pin in pins.values()}},'adapter':'none','engine_profile':'completion-only','scoring_variant':None,'engine_budget':settings,'selected_net_binding':rs.bind(source.read_bytes(),['SEL']),'selected_net_audit':rs.audit(original,final,['SEL'])}
data['task_sha256']=data['selected_net_binding']['task_sha256'];p.capture_preferences(data,run,request)
for file,field in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
 (run/file).write_text('Synthetic retained export; NOT a native DSN.\n');data[field]=p.sha(run/file)
receipt=run/'result.json'
def bind_final(d):
 d['candidate_sha256']=p.sha(candidate);expected=dict(d['source_hashes']);expected[candidate.name]=d['candidate_sha256']
 native_input.write_bytes(candidate.read_bytes());p.save_json(run/'final-drc-binding.json',{'source':str(candidate),'input':str(native_input),'saved':False,'before':expected,'after':expected})
 d['steps'][-1]['validated_input_sha256']=d['candidate_sha256']
bind_final(data);p.save_json(receipt,data)
# No native/process execution is permitted. Any unexpected process call fails.
results=[]
def check(label,mutation=None,expect='reject'):
 d=copy.deepcopy(data); candidate.write_bytes((sx.dump(final)+'\n').encode());native_input.write_bytes(candidate.read_bytes())
 (run/'routing-preferences.json').write_bytes(request['snapshot']);p.save_json(run/'final-drc-process.json',process)
 if mutation:mutation(d)
 bind_final(d);p.save_json(receipt,d)
 try:
  with patch('subprocess.run',side_effect=AssertionError('forbidden subprocess')),patch('subprocess.Popen',side_effect=AssertionError('forbidden subprocess')):
   value=p.check_result(receipt)
  outcome='current'
 except (p.Rejected,ValueError,KeyError,FileNotFoundError) as exc:
  outcome='reject';value={'type':type(exc).__name__,'reason':str(exc)}
 entry={'case':label,'expected':expect,'outcome':outcome,'matched':outcome==expect,'detail':value};results.append(entry);print(json.dumps(entry,sort_keys=True))
check('complete legacy Default selected/parity synthetic positive',expect='current')
check('missing source task hash',lambda d:d.pop('task_sha256'))
check('rehashed incorrect source task hash',lambda d:d.update(task_sha256='0'*64))
check('missing selected binding',lambda d:d.pop('selected_net_binding'))
check('missing selected audit',lambda d:d.pop('selected_net_audit'))
check('downgraded whole scope retaining selection markers',lambda d:d.update(scope='whole_board_unlocked_routing'))
check('downgraded schema',lambda d:d.update(schema=2))
check('rehashed bogus binding',lambda d:d['selected_net_binding'].update(protected_count=0,binding_sha256='0'*64))
check('rehashed bogus audit',lambda d:d['selected_net_audit'].update(protected_count=0))
def bogus_pref(d):
 record=json.loads(request['snapshot']);record['effective']['nets']=['OTHER'];raw=json.dumps(record).encode();(run/'routing-preferences.json').write_bytes(raw);d['routing_preferences'].update(effective=record['effective'],sha256=hashlib.sha256(raw).hexdigest())
check('rehashed captured selection disagreement',bogus_pref)
def copper(d,kind):
 tree=sx.read(candidate)
 if kind=='protectedloss':tree.remove(next(row for row in p.routes(tree) if sx.one(row,'net')==['net','2']))
 elif kind=='changednetlist':sx.one(tree,'net')[2]='"ALTERED"'
 else:tree.append(route(2 if kind=='unselected' else 999,5))
 sx.write(candidate,tree)
check('extra unselected copper with all final hashes rebound',lambda d:copper(d,'unselected'))
check('extra unknown copper with all final hashes rebound',lambda d:copper(d,'unknown'))
check('protected loss with all final hashes rebound',lambda d:copper(d,'protectedloss'))
check('changed netlist with all final hashes rebound',lambda d:copper(d,'changednetlist'))
check('false schematic parity declaration',lambda d:d.update(schematic_parity='unavailable: no native schematic in source project'))
def no_flag(d):
 current=copy.deepcopy(process);current['argv'].remove('--schematic-parity');p.save_json(run/'final-drc-process.json',current);d['steps'][-1].update(argv=current['argv'])
check('final native parity argv missing despite copied schematic',no_flag)
def absent_dsn(d):d.pop('native_dsn_sha256');d.pop('task_dsn_sha256')
check('selected DSN provenance downgraded by removing both retained hash fields',absent_dsn,expect='reject')
p.save_json(OWN/'results.json',{'kind':'synthetic consistency controls only','native_validation_performed':False,'subprocesses_executed':0,'source_sha256_before':initial,'source_sha256_after':{f:p.sha(ROOT/f) for f in SOURCE_FILES},'results':results})
