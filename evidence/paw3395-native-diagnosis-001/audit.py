"""Read-only retained PAW001 evidence diagnosis; no worker or Git execution."""
from pathlib import Path
import collections,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'.runs/paw3395-native-diagnostic-001'
OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
# Reuse the exact captured parser/binding helpers, independent of later core edits.
sys.path.insert(0,str(RUN/'code/experiments/lipo_native_diagnostic_v1'))
sys.path.insert(0,str(RUN/'code'))
from autorouter import pipeline as p,floor_route as f,placement_clearance as io,sexpr as sx
import driver as d

def read(path):return f.read_json(path)
def digest(path):return hashlib.sha256(io.read_bytes(path)).hexdigest()
def inventory(path):return io.inventory(path,max_bytes=20*1024*1024,max_files=512,max_entries=1024)
def delta(left,right,path=''):
    if type(left)!=type(right):return [{'path':path,'before':left,'after':right}]
    if isinstance(left,dict):
        result=[]
        for key in sorted(left.keys()|right.keys()):
            q=path+'/'+key
            if key not in left:result.append({'path':q,'added':right[key]})
            elif key not in right:result.append({'path':q,'removed':left[key]})
            else:result+=delta(left[key],right[key],q)
        return result
    return [] if left==right else [{'path':path,'before':left,'after':right}]

before=inventory(RUN);summary=read(RUN/'summary.json');source=Path(summary['source']);original=inventory(source.parent)
assert original==summary['source_hashes'] and len(original)==14
receipt=Path(summary['source_spec']['receipt']);assert digest(receipt)==summary['source_spec']['receipt_sha256']
acquired=read(receipt);expected={}
for row in acquired['files']:
    path=ROOT/row['local_path'];raw=io.read_bytes(path);assert path.is_relative_to(source.parent)
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha1']
    expected[str(path.relative_to(source.parent))]=row['sha256']
assert expected==original
observe=inventory(RUN/'observe-input');after=inventory(RUN/'original-drc-input')
assert observe==original and set(after)==set(original)
changed=[name for name in original if original[name]!=after[name]]
assert changed==['paw3395.kicad_prl']
assert inventory(RUN/'code')==summary['code_inventory']==summary['runtime_sources']
assert all(summary['runtime_sources'][name]==sha for name,sha in summary['tools']['implementation_sha256'].items())
checkpoint=read(ROOT/'.runs/checkpoint-0e8ed9d.json')
assert checkpoint['verified'] is True and checkpoint['git_head']==checkpoint['remote_sha']==summary['tools']['git_head']=='0e8ed9db34405b66e2e2350e48b4e25be248e604'
assert digest(RUN/'code'/checkpoint['file'])==checkpoint['file_sha256']
assert all(digest(RUN/name)==sha for name,sha in summary['stage_one_evidence'].items())
notes=d.source_notes(sx.read(source),read(source.with_suffix('.kicad_pro')),'paw3395')
assert notes==summary['source_notes']
observed=d.observe_binding(RUN,original,notes,'export','paw3395')
assert observed['floors_nm']==summary['native_effective_floors_nm'] and observed['nets']==summary['native_effective_nets']
observe_argv=[*f.SANDBOX,str(d.c.PYTHON),str(ROOT/'autorouter/floor_context.py'),'export',str(RUN/'observe-input'/source.name),str(RUN/'observation.json'),str(RUN/'native.dsn')]
f.process_check(RUN,summary,'observe',observe_argv)
native=p.parse_report(RUN/'original-drc.json',source.name)
f.process_check(RUN,summary,'original-drc',d.drc_argv(RUN,'paw3395'),allowed=(5,))
assert [step['name'] for step in summary['steps']]==['observe','original-drc']
assert summary['status']=='failed' and summary['observations_complete'] is False and summary['dsn_export_succeeded'] is True
assert summary['native_original_pad_route_identities_match'] is True
assert summary['wall_seconds']<30 and summary['total_cpu_seconds']<30
assert not (RUN/'original-drc-binding.json').exists() and 'stage_two_evidence' not in summary and 'native' not in summary
try:p.check_drc_project(original,after,source.name)
except p.Rejected as exc:guard_error=str(exc)
else:raise AssertionError('original strict guard unexpectedly accepted existing PRL mutation')
assert guard_error=='native DRC modified input or rules: paw3395.kicad_prl'
raw=read(RUN/'original-drc.json');counts=collections.Counter((x['type'],x['severity']) for x in native['findings'])
assert (native['opens'],native['blocking'],native['warnings'],native['exclusions'])==(0,0,17,0)
assert counts=={('lib_footprint_issues','warning'):17}
outer=read(ROOT/'.runs/paw3395-native-diagnostic-001-execution.json')
assert outer['git_head']==summary['tools']['git_head'] and outer['exit_code']==2 and outer['cleanup_signals']==[]
assert digest(ROOT/'.runs/run-paw3395-native-diagnostic-001.py')==outer['wrapper_sha256']
assert digest(ROOT/'.runs/paw3395-native-diagnostic-001-command.log')==outer['log_sha256']
prl_name=source.with_suffix('.kicad_prl').name
changes=delta(read(source.parent/prl_name),read(RUN/'original-drc-input'/prl_name))
assert len(changes)==10
source_ignored=sorted(k for k,v in notes['source_design_settings']['rule_severities'].items() if v=='ignore')
native_ignored=sorted(x['key'] for x in native['ignored_checks'])
assert inventory(RUN)==before and inventory(source.parent)==original
result={'schema':1,'audit_passed':True,'scope':'Retained failed diagnostic readback only; no source, native, JVM, Git, or network actions. No acceptance or enforcement qualification.',
 'head':summary['tools']['git_head'],'historical_code_snapshot_exact':True,'checkpoint_receipt_sha256':digest(ROOT/'.runs/checkpoint-0e8ed9d.json'),
 'source_files':original,'source_file_count':len(original),'source_bytes':sum((source.parent/n).stat().st_size for n in original),'originals_unchanged':True,
 'run_inventory_before_after_equal':True,'run_inventory':before,'code_inventory_exact':True,
 'observe_input_exact':True,'drc_input_changed_files':changed,'drc_non_prl_files_exact':13,
 'prl':{'original_sha256':original[prl_name],'observe_sha256':observe[prl_name],'drc_sha256':after[prl_name],
        'original_bytes':(source.parent/prl_name).stat().st_size,'drc_bytes':(RUN/'original-drc-input'/prl_name).stat().st_size,'json_changes':changes},
 'source_format':notes['format'],'pads':len(observed['pads']),'nonempty_nets':len(observed['nets']),'routes':len(observed['routes']),
 'observed_floors_nm':observed['floors_nm'],'observed_class_rows':observed['nets'],
 'native_report':{key:native[key] for key in ('opens','blocking','warnings','exclusions')},'finding_types':{'lib_footprint_issues:warning':17},
 'library_warning_descriptions':dict(collections.Counter(x['description'] for x in native['findings'])),
 'original_ignored_keys':source_ignored,'native_ignored_keys':native_ignored,'native_added_ignored_keys':sorted(set(native_ignored)-set(source_ignored)),
 'zone_has_empty_net_original_severity':notes['source_design_settings']['rule_severities']['zone_has_empty_net'],
 'zone_has_empty_net_enforcement_qualified':False,'report_sha256':digest(RUN/'original-drc.json'),'native_dsn_sha256':digest(RUN/'native.dsn'),
 'historical_failure':summary['error'],'failure_boundary':'Both actual processes completed. Existing-PRL comparison failed before binding JSON save, parse_report return and stage_two/completed evidence publication.',
 'stage_two_binding_present':False,'historical_stage_two_digest_present':False,'posthoc_report_hash_observation_only':True,
 'costs':{'stored_wall_seconds':summary['wall_seconds'],'stored_total_cpu_seconds':summary['total_cpu_seconds'],'outer_wall_seconds':outer['wall_seconds'],'outer_waited_cpu_seconds':outer['waited_child_cpu_seconds'],'outer_exit_code':outer['exit_code'],'steps':[{k:step[k] for k in ('name','status','exit_code','wall_seconds','cpu_seconds','cleanup_complete')} for step in summary['steps']]},
 'routing_accepted':False,'format_support_qualified':False,'no_new_native_processes':True}
(OUT/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'audit_passed':True,'native_report':result['native_report'],'changed_files':changed,'prl_json_changes':len(changes),'source_files':len(original),'run_files':len(before),'no_new_native':True}))
