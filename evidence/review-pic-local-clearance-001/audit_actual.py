"""Read-only saved-native readback through the existing control helpers."""
from pathlib import Path
from collections import Counter
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'experiments/pic_custom_native_controls_v1'),str(ROOT)]
import driver as d
import clearance_controls as cc
RUN=ROOT/'.runs/pic-local-clearance-native-001'
PUBLIC=ROOT/'evidence/pic-local-clearance-native-001'
before=d.inventory(RUN);summary=d.read(RUN/'summary.json')
original_before,total=d.source_binding();original=d.sx.read(d.SOURCE)
project=d.read(d.SOURCE.with_suffix('.kicad_pro'))
assert original_before==summary['source_hashes'] and total==summary['source_bytes']==1366598
assert summary['source_file_count']==15
assert {k:v for k,v in before.items() if k!='summary.json'}==summary['completed_evidence']
assert summary['status']=='controls_passed' and summary['controls_passed'] is True
assert summary['suite']==cc.SUITE and summary['protocol']==d.protocol(cc.SUITE)
assert summary['protocol_sha256']==d.digest(d.HERE/'CLEARANCE_PROTOCOL.json')
assert all(summary[key] is value for key,value in d.FALSE_CLAIMS.items())
assert [(row['variant'],row['case']) for row in summary['cases']]==list(cc.ORDER)
assert summary['source_explicit_ignored_checks']==sorted(k for k,v in project['board']['design_settings']['rule_severities'].items() if v=='ignore')
ignored=summary['original_observed_effective_ignored_checks']
assert ignored==list(d.OBSERVED_IGNORED)
assert set(ignored)-set(summary['source_explicit_ignored_checks'])=={'track_not_centered_on_via'}

# One read-only Git process checks exact retained snapshot bytes against the run's
# committed source, without executing any worker or rerunning native validation.
runtime=summary['runtime_sources'];head=summary['tools']['git_head']
proc=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,input=''.join(head+':'+path+'\n' for path in runtime).encode(),capture_output=True,check=True)
remaining=proc.stdout
for rel,expected in runtime.items():
    line,remaining=remaining.split(b'\n',1);_,kind,size=line.split();size=int(size)
    raw,remaining=remaining[:size],remaining[size+1:]
    assert kind==b'blob' and hashlib.sha256(raw).hexdigest()==expected
    assert d.digest(ROOT/rel)==expected==d.digest(RUN/'code'/rel)
assert not remaining
assert all(d.p.sha(Path(path))==sha for path,sha in summary['tools']['files'].items())
assert d.digest(d.WRAPPER)==d.WRAPPER_SHA

cases=[];steps=[]
for row in summary['cases']:
    path=RUN/(row['variant']+'-'+row['case'])
    raw,scene=cc.prepare(original,row['case'],row['variant'])
    expected=dict(original_before);expected[d.SOURCE.name]=d.sha_bytes(raw)
    assert row['input_hashes']==expected==d.inventory(path/'observe-input')
    assert d.f.canonical(scene)==d.f.canonical(row['scene'])==d.f.canonical(d.read(path/'recipe.json'))
    observed=d.observation_binding(path,expected,row['scene'],project,cc.observe)
    assert observed==row['observation'] and row['geometry_verified'] is True
    d.f.process_check(path,{'steps':row['steps']},'observe',d.observe_argv(path))
    native=d.p.parse_report(path/'original-drc.json',d.SOURCE.name)
    assert native==row['native']
    assert d.drc_binding(path,row['steps'],expected,native)==row['native_binding']
    passed,hits=cc.predicate(row['case'],native,d.read(path/'original-drc.json'),row['scene'],ignored)
    assert passed is True and hits==row['target_findings']
    assert row['control_passed'] is True and row['paired_positive_passed'] is True
    prior=next(x for x in summary['cases'] if x['case']==cc.POSITIVE[row['case']])
    assert prior['control_passed'] is True and cc.CASES[prior['case']][2]
    for stage,entries in row['stages'].items():
        assert all(d.digest(path/name)==sha for name,sha in entries.items())
    assert all(d.digest(path/name)==sha for name,sha in row['binding_evidence'].items())
    assert row['native_dsn_sha256']==d.digest(path/'native.dsn') and row['dsn_export_succeeded'] is True
    warnings=Counter(x['type'] for x in native['findings'] if x['severity']=='warning')
    assert warnings=={'missing_courtyard':4,'track_dangling':1}
    assert (native['opens'],native['blocking'],native['warnings'],native['exclusions'])==(0,0 if cc.CASES[row['case']][2] else 1,5,0)
    assert len(row['steps'])==2
    for step in row['steps']:
        assert step['cleanup_complete'] is True and step['log_truncated'] is False
        assert step['exit_code']==(0 if step['name']=='observe' else 5)
        assert step['resource_guards']['max_group_rss_bytes']==2*1024**3
        assert step['resource_guards']['max_workdir_bytes']==d.LIMIT
        assert step['wall_seconds']<30
        steps.append({k:step[k] for k in ('name','exit_code','wall_seconds','cpu_seconds','max_rss_bytes')})
    cases.append({'case':row['case'],'counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},
        'warnings':dict(warnings),'target_findings':hits,'native_binding':row['native_binding'],
        'native_classes':observed['native_nets'],'paired_positive':cc.POSITIVE[row['case']]})

outer_path=ROOT/'.runs/pic-local-clearance-native-001-execution.json';outer=d.read(outer_path)
assert outer['git_head']==head and outer['controller_exit_code']==0 and outer['outer_cleanup_signals']==[]
assert outer['wrapper_sha256']==d.digest(ROOT/'.runs/run-pic-local-clearance-native-001.py')
assert outer['log_sha256']==d.digest(ROOT/outer['stdout_stderr'])
assert outer['argv'][1:]==['-B','experiments/pic_custom_native_controls_v1/driver.py','--suite','local-clearance','--run-native','--output','.runs/pic-local-clearance-native-001']
assert 0<summary['wall_seconds']<outer['outer_wall_seconds']<180
assert 0<summary['total_cpu_seconds']<outer['outer_waited_child_cpu_seconds']<180
assert abs(sum(x['cpu_seconds'] for x in steps)-summary['child_step_cpu_seconds'])<1e-9
size=sum((RUN/name).stat().st_size for name in before);assert size<d.LIMIT

manifest=d.read(PUBLIC/'files.json');raw_copy_count=0;raw_copy_bytes=0
for rel,pin in manifest.items():
    dest=PUBLIC/rel;data=dest.read_bytes()
    assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256']
    if rel=='PUBLIC_SCOPE.md':continue
    if rel.startswith('_licenses/'):source=d.SOURCE.parent/rel
    elif rel=='root-readback.json':source=ROOT/'.runs/pic-local-clearance-native-001-root-readback.json'
    elif rel in ('pic-local-clearance-native-001-command.log','pic-local-clearance-native-001-execution.json','run-pic-local-clearance-native-001.py'):source=ROOT/'.runs'/rel
    else:source=RUN/rel
    assert source.read_bytes()==data
    raw_copy_count+=1;raw_copy_bytes+=len(data)
assert d.inventory(RUN)==before and d.source_binding()==(original_before,total)
result={'schema':1,'passed':True,'scope':'Saved-evidence readback; no fresh native, engine, Java or GUI execution.',
    'git_head':head,'summary_sha256':before['summary.json'],'source_original_files':len(original_before),
    'source_original_bytes':total,'source_and_run_unchanged':True,'runtime_committed_files_verified':len(runtime),
    'cases':cases,'steps':steps,'wall_seconds':summary['wall_seconds'],'full_cpu_seconds':summary['total_cpu_seconds'],
    'outer_wall_seconds':outer['outer_wall_seconds'],'outer_waited_cpu_seconds':outer['outer_waited_child_cpu_seconds'],
    'accounting_point':summary['accounting_point'],'raw_run_bytes':size,'raw_run_file_count':len(before),
    'public_manifest_sha256':d.digest(PUBLIC/'files.json'),'public_manifest_files':len(manifest),
    'public_manifest_bytes':sum(x['bytes'] for x in manifest.values()),'public_raw_copies_verified':raw_copy_count,
    'public_raw_copy_bytes':raw_copy_bytes,'additional_public_scope_bytes':manifest['PUBLIC_SCOPE.md']['bytes'],
    'outer_sha256':d.digest(outer_path),'native_rerun':False,'routing_accepted':False}
(OUT/'actual-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'cases':len(cases),'native_stages_read_back':len(steps),'public_raw_copies_verified':raw_copy_count,'native_rerun':False}))
