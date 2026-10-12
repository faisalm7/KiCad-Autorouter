"""Retained-run consistency audit using frozen shared parsers; no native/JVM."""
from pathlib import Path
import collections,hashlib,importlib.util,json,math,sys
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;D=R/'.runs/pic-mixed-transport-probe-005';CODE=D/'code'
sys.dont_write_bytecode=True;sys.path.insert(0,str(CODE));sys.path.insert(0,str(CODE/'experiments/pic_mixed_transport_probe_v1'))
from autorouter import placement_clearance as io,sexpr as sx
from experiments.pic_custom_observer_v1 import mapping
from experiments.pic_mixed_transport_probe_v1 import driver,transport
read=lambda p:io.read_bytes(p,16*1024**2)
sha=lambda p:hashlib.sha256(read(p)).hexdigest()
load=lambda p:json.loads(read(p))
inv=lambda p:io.inventory(p,max_bytes=64*1024**2,max_files=2000,max_entries=4000)
before=inv(D);s=load(D/'summary.json');o=load(D/'observations.json');e=load(D/'expectations.json');runtime=s['runtime'];source=R/'.data/boards/kicad-pic-programmer'
original=inv(source);assert len(original)==15 and original==runtime['original']==inv(D/'observe-input')
assert all(before.get(k)==v for k,v in s['frozen_evidence'].items())
assert runtime==load(D/'runtime.json')
for n,pin in runtime['sources'].items():assert sha(CODE/n)==pin['sha256'] and (CODE/n).stat().st_size==pin['bytes'],n
for n,pin in runtime['basis'].items():assert sha(R/n)==pin['sha256'] and (R/n).stat().st_size==pin['bytes'],n
sourcepins=len(runtime['sources']);basispins=len(runtime['basis'])
assert s['status']=='failed' and s['observations_complete'] is False and s['native_process_executed'] is True and s['import_process_executed'] is True
for key in ['routing_accepted','routing_executed','ses_executed','custom_pad_support_qualified','mixed_clearance_equivalence_qualified']:assert s[key] is False
steps=[]
for step in s['steps']:
 receipt=load(D/(step['name']+'-process.json'));assert {k:v for k,v in step.items() if k!='name'}==receipt
 assert receipt['status']=='success' and receipt['exit_code']==0 and receipt['cleanup_complete'] is True
 assert receipt['cwd']==str(D) and receipt['log']==str(D/(step['name']+'.log')) and not receipt['log_truncated']
 assert receipt['argv'][:3]==driver.base.SANDBOX
 steps.append({k:step[k] for k in ('name','status','exit_code','wall_seconds','cpu_seconds','monitor_cpu_seconds','max_rss_bytes','cleanup_complete')})
assert [x['name'] for x in steps]==['native-observe','compile','import']
assert 0<s['wall_seconds']<180 and sum(x['cpu_seconds']+x['monitor_cpu_seconds'] for x in steps)<=s['total_cpu_seconds']<180
notes=mapping.source_notes(sx.parse(read(source/'pic_programmer.kicad_pcb').decode()),load(source/'pic_programmer.kicad_pro'))
derived,expected,native=driver.verify_native(D,original,notes)
assert derived==read(D/'mixed.dsn') and expected==e and native==s['native']
try:transport.validate(o,e)
except ValueError as exc:error=str(exc)
else:raise AssertionError('original failed checker unexpectedly passed')
assert error=='engine original class/width differs' and s['error']=='ValueError: '+error
casefacts=[]
for setting,c in zip((False,True),o['cases']):
 assert c['requested_obstacle'] is setting and c['status']=='observed' and c['input_sha256']==e['derived_dsn_sha256']==sha(D/'mixed.dsn')
 assert c['post_load_awaited'] is True and c['parser_result_class']=='app.freerouting.io.BoardReadResult$Success'
 assert c['argv']==['--router.autorouter.enabled=false','--router.optimizer.enabled=false','--router.plane_as_obstacle='+str(setting).lower()]
 for stage in ('settings_before','settings_after'):
  assert c[stage]['plane_as_obstacle'] is setting and c[stage]['router_enabled'] is False and c[stage]['optimizer_enabled'] is False
 st=c['state'];nets={n['name']:n for n in st['nets']};assert len(nets)==len(st['nets'])==111 and set(nets)==set(e['nets'])
 classdiff=[{'net':n,'expected':e['nets'][n]['class'],'actual':nets[n]['class']} for n in e['nets'] if nets[n]['class']!=e['nets'][n]['class']]
 widthdiff=[n for n in e['nets'] if nets[n]['width_um']!=[e['nets'][n]['width_um']]*2]
 assert len(classdiff)==109 and {tuple((x['expected'],x['actual'])) for x in classdiff}=={('kicad_default','default')} and widthdiff==[]
 pins={(p['reference'],p['number']):p for p in st['pins']};placed={(p['reference'],p['number']):p for p in e['dsn_pins']}
 assert len(pins)==len(st['pins'])==st['census']['pins']==e['dsn_pin_count']==240 and set(pins)==set(placed)
 pinmismatch=[list(k) for k in pins if pins[k]['nets']!=placed[k]['nets'] or pins[k]['position_um']!=placed[k]['position_um']]
 assert pinmismatch==[]
 assigned={k:p for k,p in pins.items() if p['nets']};terms={(p['reference'],p['number']):p for p in e['terminals']}
 assert len(assigned)==236 and set(assigned)==set(terms)
 assert all(p['nets']==[terms[k]['net']] and p['position_um']==terms[k]['position_um'] for k,p in assigned.items())
 matrix={(x['a'],x['b'],x['layer']):x for x in st['matrix']};scale=st['board_units_per_um'];assert scale==10
 assert len(matrix)==len(st['matrix'])==50 and set(matrix)=={(a,b,l) for a in range(5) for b in range(5) for l in (0,1)}
 for m in matrix.values():
  assert m['raw_board_units']/scale==m['raw_um'] and m['compensated_board_units']/scale==m['compensated_um']
  assert m['compensated_board_units']-m['raw_board_units']==16
 bodies=[]
 for want in e['areas']:
  matches=[a for a in st['areas'] if a['nets']==[want['net']] and a['layer']==want['layer'] and transport.canonical_ring(a['ring_um'])==transport.canonical_ring(want['ring_um'])]
  assert len(matches)==1;a=matches[0];p=pins[(want['reference'],want['number'])]
  assert p['padstack_name']==want['padstack_name'] and a['fixed']=='USER_FIXED' and a['holes']==0 and a['obstacle'] is setting
  origin=st['board_origin_dsn_um'];exact=[[q[0]/scale+origin[0],q[1]/scale+origin[1]] for q in a['ring_board_integer']]
  assert transport.canonical_ring(exact)==transport.canonical_ring(want['ring_um'])
  mrows=[]
  for name in ('VCC','/pic_sockets/VCC_PIC'):
   n=nets[name];layer=e['layer_order'].index(want['layer']);ac=matrix[(a['clearance_class_index'],n['trace_clearance_class'],layer)];pc=matrix[(p['clearance_class_index'],n['trace_clearance_class'],layer)]
   mrows.append({'trace_class':n['class'],'area_to_trace_raw_um':ac['raw_um'],'compensated_um':ac['compensated_um'],'pin_to_trace_raw_um':pc['raw_um']})
  bodies.append({'pad_uuid':want['uuid'],'net':want['net'],'pin_id':p['id'],'area_id':a['id'],'pin_class':p['clearance_class_index'],'area_class':a['clearance_class_index'],
   'own_contacts_reciprocal':a['id'] in p['contacts'] and p['id'] in a['contacts'],'pin_contacts':p['contacts'],'area_contacts':a['contacts'],'integer_area_um2':want['area_um2'],'reported_api_area_um2':a['area_api_um2'],'clearances':mrows})
 casefacts.append({'setting':setting,'census':st['census'],'settings_before':c['settings_before'],'settings_after':c['settings_after'],'post_load_awaited':True,'parser_warnings':c['parser_warnings'],
  'class_label_mismatches':len(classdiff),'class_label_mapping_observed':{'kicad_default':'default','POWER':'POWER'},'width_mismatches':widthdiff,'first_class_mismatch':classdiff[0],
  'assigned_pins':len(assigned),'unassigned_pins':[list(k) for k,p in pins.items() if not p['nets']],'pin_position_net_mismatches':pinmismatch,'layers':st['layers'],
  'matrix_classes':st['clearance_class_names'],'matrix_cells':len(matrix),'all_matrix_safety_margin_board_units':16,'bodies':bodies,'ignore_conduction':st['ignore_conduction']})
log=read(D/'import.log').decode();assert '287 pre-existing clearance violation(s)' in log and log.count('Loading board file...')==2
assert before==inv(D) and original==inv(source)
result={'schema':1,'audit_passed':True,'run_status':'failed','checker_error_reproduced':error,'scope':'Retained-run consistency only; original validator remains failed. No native/JVM rerun, normalization fix, or routing acceptance.',
 'git_head':runtime['git']['head'],'source_files':15,'frozen_run_files':len(before),'source_code_pins_verified':sourcepins,'basis_pins_verified':basispins,
 'bound_artifacts':{n:sha(D/n) for n in ('summary.json','observations.json','expectations.json','native.dsn','mixed.dsn','context.json','custom.json','clearance-observation.json','native-observe.log','compile.log','import.log')},
 'steps':steps,'stored_wall_seconds':s['wall_seconds'],'stored_full_cpu_seconds':s['total_cpu_seconds'],'outer':load(R/'.runs/pic-mixed-transport-probe-005-execution.json'),
 'native_observation':native,'cases':casefacts,'engine_log_warning':{'count':287,'scope':'pre-existing fixed trace/via clearance violations reported after second plane=true load','parser_warning_arrays_empty':True,'is_KiCad_verdict':False},
 'all_original_and_run_bytes_unchanged':True,'native_jobs':0,'jvm_jobs':0}
(H/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'audit_passed':True,'original_check_failed':error,'cases':len(casefacts),'pins_per_case':240,'assigned_per_case':236,'class_label_mismatches_per_case':109}))
