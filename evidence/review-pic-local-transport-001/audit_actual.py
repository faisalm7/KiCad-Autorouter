"""Read stored local250 results using the same validators; no process rerun."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import driver as d
import transport
RUN=ROOT/'.runs/pic-local-clearance-transport-001'
before=d.inventory(RUN);record=d.base.decode(d.base.content(RUN/'summary.json'))
protocol=d.base.decode(d.base.content(d.HERE/'LOCAL_CLEARANCE_PROTOCOL.json'))
runtime=d.runtime(protocol);saved=record['runtime']
assert {k:v for k,v in runtime.items() if k!='git'}=={k:v for k,v in saved.items() if k!='git'}
assert d.base.decode(d.base.content(RUN/'runtime.json'))==saved
assert record['status']=='completed' and record['observations_complete'] is True
for key in ('routing_accepted','routing_executed','ses_executed','custom_pad_support_qualified','mixed_clearance_equivalence_qualified','native_process_executed'):
    assert record[key] is False
assert record['import_process_executed'] is True
assert {k:v for k,v in before.items() if k!='summary.json'}==record['frozen_evidence']
assert runtime['tools']=={k:{x:v[x] for x in ('bytes','sha256')} for k,v in protocol['tools'].items()}
assert runtime['basis']==protocol['basis']

head=saved['git']['head'];paths=list(saved['sources'])
raw=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,input=''.join(head+':'+p+'\n' for p in paths).encode(),capture_output=True,check=True).stdout
for rel in paths:
    line,raw=raw.split(b'\n',1);_,kind,size=line.split();size=int(size);blob,raw=raw[:size],raw[size+1:]
    pin=saved['sources'][rel]
    assert kind==b'blob' and len(blob)==pin['bytes'] and hashlib.sha256(blob).hexdigest()==pin['sha256']
    assert d.base.content(RUN/'code'/rel)==blob
assert not raw

CACHE=ROOT/protocol['reuse_native'];cached_before=d.inventory(CACHE)
old=d.base.decode(d.base.content(CACHE/'summary.json'))
assert cached_before==saved['cached_native_inventory']
assert old['status']=='failed' and old['error']=='ValueError: engine original class/width differs'
assert all(cached_before.get(k)==v for k,v in old['frozen_evidence'].items())
assert d.base.sha(d.base.content(CACHE/'summary.json'))==record['native_reuse']['summary_sha256']
assert record['native_reuse']['new_native_execution'] is False
assert record['native_reuse']['prior_run_wall_seconds']==old['wall_seconds']
assert record['native_reuse']['prior_run_total_cpu_seconds']==old['total_cpu_seconds']
notes=d.mapping.source_notes(d.sx.read(d.original.SOURCE),d.base.decode(d.base.content(d.original.SOURCE.with_suffix('.kicad_pro'))))
derived,expected,native=d.verify_native(CACHE,saved['original'],notes)
assert derived==d.base.content(CACHE/'mixed.dsn')==d.base.content(RUN/'mixed.dsn')
assert expected==d.base.decode(d.base.content(RUN/'expectations.json')) and native==record['native']
assert d.inventory(RUN/'observe-input')==saved['original']==d.inventory(d.original.SOURCE.parent)
for name in ('context.json','custom.json','clearance-observation.json','native.dsn','summary.json'):
    assert d.base.content(RUN/'cached-native'/name,4*1024**2)==d.base.content(CACHE/name,4*1024**2)
local=d.base.decode(d.base.content(CACHE/'clearance-observation.json',2*1024**2))
assert transport.local_override_basis(local,d.base.decode(d.base.content(d.original.SOURCE.with_suffix('.kicad_pro'))))==record['local_basis']
observed=d.base.decode(d.base.content(RUN/'observations.json',16*1024**2))
assert transport.validate_local(observed,expected)==record['case_comparison']

cases=[]
for row in observed['cases']:
    oldstate=row['state_before_local'];new=row['state'];changes=[]
    olditems={r['id']:r for r in oldstate['items']}
    for item in new['items']:
        olditem=olditems[item['id']]
        if item!=olditem:
            changes.append({'id':item['id'],'old_class':olditem['clearance_class_index'],'new_class':item['clearance_class_index'],'kind':item['kind'],'nets':item['nets']})
    assert {x['id'] for x in changes}=={869,870,1221,1222}
    assert all(x['new_class']==5 for x in changes)
    assert len(oldstate['matrix'])==50 and len(new['matrix'])==72
    assert new['board_units_per_um']==10 and new['clearance_safety_margin_board_units']==16
    assert row['parser_warnings']==[]
    cases.append({'plane_as_obstacle':row['requested_obstacle'],'changes':changes,'targets':row['local_override']['targets'],
        'tree_entry_checks':row['local_override']['tree_entry_checks'],'tree_refresh_completed':row['local_override']['tree_refresh_completed'],
        'census_before':oldstate['census'],'census_after':new['census'],'old_matrix_cells':50,'new_matrix_cells':72,
        'raw_local_clearance_um':250,'compensated_local_clearance_um':251.6,'null_raw_um':0,'null_compensated_um':1.6,
        'parser_warnings':row['parser_warnings'],'routing_disabled':row['settings_after']['router_enabled'] is False and row['settings_after']['optimizer_enabled'] is False})

tools=protocol['tools'];jar=str(ROOT/tools['jar']['path']);code=RUN/'code'/d.HERE.relative_to(ROOT)
argvs={
 'compile':[*d.base.SANDBOX,tools['javac']['path'],'-J-Xmx256m','-J-Duser.home='+str(RUN/'home'),'-proc:none','-classpath',jar,'-d',str(RUN/'classes'),str(code/'MixedClassProbe.java'),str(RUN/'code/experiments/custom_pad_area_probe_v1/AreaContactProbe.java')],
 'import':[*d.base.SANDBOX,tools['java']['path'],'-Xmx256m','-Djava.awt.headless=true','-Duser.home='+str(RUN/'home'),'-Djava.io.tmpdir='+str(RUN/'tmp'),'-cp',str(RUN/'classes')+':'+jar,'MixedClassProbe',str(RUN/'mixed.dsn'),str(RUN/'observations.json'),'local250']}
assert [r['name'] for r in record['steps']]==list(argvs)
for step in record['steps']:
    # This reused controller adds name only to its summary step; the raw runner
    # receipt has no name field, unlike FloorJob.process_check's receipt format.
    process=d.base.decode(d.base.content(RUN/(step['name']+'-process.json')))
    assert process=={k:v for k,v in step.items() if k!='name'}
    assert process['argv']==argvs[step['name']] and process['cwd']==str(RUN)
    assert step['status']=='success' and step['exit_code']==0 and step['cleanup_complete'] is True and step['log_truncated'] is False
    assert step['resource_guards']['max_workdir_bytes']==d.LIMIT and step['resource_guards']['max_group_rss_bytes']==2*1024**3
log=d.base.content(RUN/'import.log').decode()
assert log.count('Board has 287 pre-existing clearance violation(s)')==1
assert '287 fixed trace/via clearance violations' in log
outer_path=ROOT/'.runs/pic-local-clearance-transport-001-execution.json';outer=d.base.decode(d.base.content(outer_path))
assert outer['exit_code']==0 and outer['git_head']==head and outer['cleanup_signals']==[]
assert outer['wrapper_sha256']==d.base.sha(d.base.content(ROOT/'.runs/run-pic-local-clearance-transport-001.py'))
assert outer['log_sha256']==d.base.sha(d.base.content(ROOT/'.runs/pic-local-clearance-transport-001-command.log'))
assert 0<record['wall_seconds']<outer['wall_seconds']<180 and 0<record['total_cpu_seconds']<outer['waited_child_cpu_seconds']<180
assert sum((RUN/path).stat().st_size for path in before)<d.LIMIT
assert d.inventory(RUN)==before and d.inventory(CACHE)==cached_before and d.inventory(d.original.SOURCE.parent)==saved['original']
result={'schema':1,'passed':True,'scope':'Stored experiment readback using existing helpers; no native/JVM rerun.',
    'git_head':head,'summary_sha256':before['summary.json'],'source_and_cached005_unchanged':True,'committed_sources':len(paths),
    'basis_pins':len(runtime['basis']),'original_files':len(saved['original']),'original_bytes':saved['original_bytes'],
    'native_reuse':record['native_reuse'],'cases':cases,'steps':[{k:s[k] for k in ('name','status','exit_code','wall_seconds','cpu_seconds','max_rss_bytes')} for s in record['steps']],
    'wall_seconds':record['wall_seconds'],'full_cpu_seconds':record['total_cpu_seconds'],'outer_wall_seconds':outer['wall_seconds'],
    'outer_waited_cpu_seconds':outer['waited_child_cpu_seconds'],'native_process_executed':False,'observed_log_fixed_trace_via_warnings':287,
    'parser_warnings_empty':True,'accounting_point':record['accounting_point'],'raw_run_files':len(before),
    'raw_run_bytes':sum((RUN/path).stat().st_size for path in before),'routing_accepted':False}
(OUT/'actual-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'cases':len(cases),'stages':len(record['steps']),'source_and_cached005_unchanged':True,'native_jvm_rerun':False}))
