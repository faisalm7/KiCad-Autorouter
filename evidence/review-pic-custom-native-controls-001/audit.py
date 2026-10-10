"""Independent read-only audit of retained actual six-case native001; no native calls."""
from pathlib import Path
import collections
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
import os
import stat
import subprocess
import sys

ROOT=Path(__file__).absolute().parents[2]
OUT=Path(__file__).absolute().parent
RUN=ROOT/'.runs/pic-custom-native-controls-001'
HEAD='34665498a2a4e3a0c017f7120f1352fa9e4f7d5e'
SOURCE=ROOT/'.data/boards/kicad-pic-programmer'
checks=[]
def check(name, condition):
    checks.append(name)
    if not condition:raise AssertionError(name)
def raw(path, cap=32*1024**2):
    check('real bounded file '+str(path),not path.is_symlink() and path.is_file() and path.stat().st_size<=cap)
    with path.open('rb') as stream:value=stream.read(cap+1)
    check('read bounded '+str(path),len(value)<=cap)
    return value
def digest(path):
    return hashlib.sha256(raw(path)).hexdigest()
def read(path):
    return json.loads(raw(path))
def tree(path):
    result={};total=0;stack=[path];n=0
    while stack:
        with os.scandir(stack.pop())as entries:
            for e in entries:
                n+=1;check('entry ceiling',n<=4096 and not e.is_symlink())
                p=Path(e.path)
                if e.is_dir(follow_symlinks=False):stack.append(p)
                else:
                    value=raw(p);total+=len(value)
                    check('tree ceiling',len(result)<2048 and total<=32*1024**2)
                    result[str(p.relative_to(path))]=hashlib.sha256(value).hexdigest()
    return result

summary=read(RUN/'summary.json');initial=tree(RUN);source_before=tree(SOURCE)
check('failed batch truth',summary['status']=='failed_controls' and summary['controls_passed'] is False)
false=('routing_accepted','geometry_qualified','format_support_qualified','dependency_complete','custom_routing_support_qualified','nondefault_resolution_qualified','new_severity_enforcement_qualified','arbitrary_reflection_qualified','new_engine_execution','board_saved')
for key in false:check('scope '+key,summary[key] is False)
check('head',summary['tools']['git_head']==HEAD)
check('completed retained evidence',summary['completed_evidence']=={k:v for k,v in initial.items()if k!='summary.json'})
check('original full source',source_before==summary['source_hashes'] and len(source_before)==15)
check('source bytes',sum((SOURCE/n).stat().st_size for n in source_before)==1366598==summary['source_bytes'])
manifest=read(ROOT/'data/sources.json')
check('acquisition manifest',digest(ROOT/'data/sources.json')==summary['acquisition_receipt_sha256'])
for row in manifest['files']:
    if row.get('project_id')!='kicad-pic-programmer':continue
    source=ROOT/'.data'/row['destination'];value=raw(source)
    check('original Git blob '+str(source),hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()==row['git_blob_sha1'])
    check('original SHA/size '+str(source),hashlib.sha256(value).hexdigest()==row['sha256'] and len(value)==row['bytes'])
for name,expected in summary['runtime_sources'].items():
    check('saved source '+name,digest(RUN/'code'/name)==expected)
    committed=subprocess.run(['git','show',HEAD+':'+name],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3,check=True).stdout
    check('source commit '+name,hashlib.sha256(committed).hexdigest()==expected)
check('code complete',tree(RUN/'code')==summary['runtime_sources'])
for name,expected in summary['tools']['files'].items():
    path=Path(name);check('tool regular '+name,path.is_file() and not path.is_symlink() and path.stat().st_size<512*1024**2)
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(256*1024):h.update(block)
    check('current pinned binary '+name,h.hexdigest()==expected)
# Import ONLY the saved project-owned pure parsers/recipe checks; no driver/worker import.
sys.dont_write_bytecode=True
sys.path[:0]=[str(RUN/'code'),str(RUN/'code/experiments/pic_custom_native_controls_v1')]
from autorouter import pipeline as p, sexpr as sx
import fixture,checks as frozen_checks
project=read(SOURCE/'pic_programmer.kicad_pro');original=sx.parse(raw(SOURCE/'pic_programmer.kicad_pcb').decode())
explicit=sorted(k for k,v in project['board']['design_settings']['rule_severities'].items()if v=='ignore')
effective=summary['original_observed_effective_ignored_checks']
check('explicit3/effective4',explicit==summary['source_explicit_ignored_checks'] and len(explicit)==3 and len(effective)==4 and set(effective)-set(explicit)=={'track_not_centered_on_via'})
check('baseline original DRC',digest(ROOT/summary['original_native_report']['path'])==summary['original_native_report']['sha256'])
order=[(v,c)for v in ('front0','back90')for c in ('positive','false_hull','foreign_intrusion')]
check('allsix fixed order',[(r['variant'],r['case'])for r in summary['cases']]==order)
cli='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
python='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9'
worker=str(ROOT/'experiments/pic_custom_native_controls_v1/worker.py')
sandbox=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)']
records=[];stage_cpu=0
for row in summary['cases']:
    name=row['variant']+'-'+row['case'];folder=RUN/name;scene=row['scene'];back=row['variant']=='back90'
    board,prepared=fixture.prepare(original,row['case'],row['variant'])
    check(name+' pure recipe exact',json.loads(json.dumps(prepared))==scene)
    check(name+' saved recipe',read(folder/'recipe.json')==scene)
    check(name+' board exact derivation',raw(folder/'observe-input/pic_programmer.kicad_pcb')==board)
    expected=dict(source_before);expected['pic_programmer.kicad_pcb']=hashlib.sha256(board).hexdigest()
    check(name+' complete observer copy',tree(folder/'observe-input')==expected==row['input_hashes'])
    binding=read(folder/'original-drc-binding.json')
    check(name+' complete DRC copy',tree(folder/'original-drc-input')==binding['after'] and binding['before']==expected and all(binding['after'].get(k)==v for k,v in expected.items()) and set(binding['after'])-set(expected)<={'pic_programmer.kicad_prl'})
    check(name+' no save original rules',binding['saved'] is False and binding['source']==str(folder/'observe-input/pic_programmer.kicad_pcb') and binding['input']==str(folder/'original-drc-input/pic_programmer.kicad_pcb'))
    for stage,entries in row['stages'].items():
        for key,value in entries.items():check(name+' stage frozen '+key,digest(folder/key)==value)
    for key,value in row['binding_evidence'].items():check(name+' binding frozen '+key,digest(folder/key)==value)
    obs=read(folder/'observation.json');custom=read(folder/'custom-pads.json');dsn=raw(folder/'native.dsn')
    check(name+' floor/custom shared fields',all(obs[k]==custom[k]for k in ('context_schema','native_version','units','mode','source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after')))
    check(name+' same-load source/DSN',obs['source']==str(folder/'observe-input/pic_programmer.kicad_pcb') and obs['board_sha256']==expected['pic_programmer.kicad_pcb'] and obs['project_sha256']==expected['pic_programmer.kicad_pro'] and obs['dsn_sha256']==hashlib.sha256(dsn).hexdigest()==row['native_dsn_sha256'])
    check(name+' context input unchanged',obs['input_hashes_before']==obs['input_hashes_after']==expected)
    check(name+' same BOARD before after',custom['same_loaded_board'] is True and custom['observation_before_export']==custom['observation_after_export'] and custom['floor_context_sha256']==digest(folder/'observation.json'))
    observed=frozen_checks.observe(obs,custom,dsn,scene,project)
    check(name+' independently rederive frozen geometry audit',observed==row['observation'])
    # Independently compare the actual native ring to fixed recipe's world points.
    pads={q['uuid']:q for q in scene['pads']}
    for pad in custom['observation_before_export']['pads']:
        for key in ('transformed_world','effective_world'):
            shape=pad[key];points=shape['outlines'][0]['outline']['points_nm']
            check(name+' native actual world ring '+key,fixture.poly_ring(points)==fixture.poly_ring(pads[pad['uuid']]['polygon']))
            check(name+' actual noholes/arcs',shape['arc_count']==0 and shape['outlines'][0]['holes']==[] and shape['outlines'][0]['outline']['closed'] is True)
        check(name+' explicit native flipped angle',pad['orientation_degrees']==(90 if back else 0) and pad['pad_flipped'] is back and pad['size_nm']==[300000,300000] and pad['drill_nm']==[0,0])
    for q in row['observation']['correspondence']['custom_pads']:
        check(name+' DSN back270/front0',q['placement_ast'][4:6]==(['back','270']if back else ['front','0']))
    native_raw=read(folder/'original-drc.json');native=p.parse_report(folder/'original-drc.json','pic_programmer.kicad_pcb')
    check(name+' summary parser exact',native==row['native'])
    check(name+' native schema source',native_raw['$schema']=='https://schemas.kicad.org/drc.v1.json' and native_raw['kicad_version']=='10.0.0' and native_raw['source']=='pic_programmer.kicad_pcb' and native_raw['coordinate_units']=='mm' and native_raw['schematic_parity']==[])
    findings=native_raw['violations']+native_raw['unconnected_items']
    check(name+' findings complete',native['findings']==findings)
    check(name+' direct raw counts',native['opens']==len(native_raw['unconnected_items']) and native['blocking']==sum(r['severity']=='error'for r in native_raw['violations']) and native['warnings']==sum(r['severity']=='warning'for r in findings) and native['exclusions']==0 and not any(r.get('excluded',False)for r in findings))
    check(name+' effective ignored preserved',sorted(r['key']for r in native_raw['ignored_checks'])==effective)
    passed,hits=frozen_checks.predicate(row['case'],native,native_raw,scene,effective)
    check(name+' frozen predicate unchanged',passed is row['expected_predicate_met'] and hits==row['target_findings'] and row['paired_positive_passed'] is True)
    check(name+' pass truth',row['control_passed'] is (row['case']!='foreign_intrusion') and passed is (row['case']!='foreign_intrusion'))
    padids={r['id']:r['uuid']for r in scene['pads']};trackids={r['id']:r['uuid']for r in scene['tracks']}
    errors=[r for r in findings if r['severity']=='error']
    warnings=collections.Counter(r['type']for r in findings if r['severity']=='warning')
    check(name+' warnings exact',warnings==({'missing_courtyard':4,'track_dangling':1}if row['case']=='false_hull'else {'missing_courtyard':4}))
    if row['case']=='foreign_intrusion':
        check(name+' exact copper and companion mask',collections.Counter(r['type']for r in errors)=={'shorting_items':1,'solder_mask_bridge':1} and all({i['uuid']for i in r['items']}=={padids['CONCAVE'],trackids['FOREIGN_TRACK']}for r in errors))
    elif row['case']=='false_hull':
        check(name+' actual notch open exact pair',len(errors)==1 and errors[0]['type']=='unconnected_items' and {i['uuid']for i in errors[0]['items']}=={padids['CONCAVE'],trackids['CONTACT_TRACK']})
    else:check(name+' actual positive no error',not errors)
    check(name+' final report bound',row['native_binding']=={'board_sha256':expected['pic_programmer.kicad_pcb'],'project_sha256':expected['pic_programmer.kicad_pro'],'report_sha256':digest(folder/'original-drc.json'),'binding_sha256':digest(folder/'original-drc-binding.json')})
    check(name+' exactly two stages',[s['name']for s in row['steps']]==['observe','original-drc'])
    for step in row['steps']:
        stage=step['name'];proc=read(folder/(stage+'-process.json'))
        expected_step=dict(proc)
        if stage=='original-drc':expected_step.update(validated_input_sha256=expected['pic_programmer.kicad_pcb'],emitted_candidate=str(folder/'observe-input/pic_programmer.kicad_pcb'))
        check(name+' raw process augmentation '+stage,step==expected_step)
        argv=sandbox+([python,worker,str(folder/'observe-input/pic_programmer.kicad_pcb'),str(folder/'observation.json'),str(folder/'native.dsn'),str(folder/'custom-pads.json')]if stage=='observe'else [cli,'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(folder/'original-drc.json'),str(folder/'original-drc-input/pic_programmer.kicad_pcb')])
        check(name+' exact bounded argv '+stage,proc['argv']==argv and proc['cwd']==str(folder))
        check(name+' captured native exit '+stage,proc['exit_code']==(0 if stage=='observe'else 5) and proc['status']==('success'if stage=='observe'else 'nonzero_exit') and proc['cleanup_complete'] is True)
        check(name+' process bounds '+stage,0<proc['wall_seconds']<=30 and proc['cpu_seconds']>=0 and proc['sampled_peak_group_rss_bytes']<=2*1024**3 and proc['sampled_peak_workdir_bytes']<=32*1024**2 and proc['log_truncated'] is False and proc['log_bytes']==(folder/(stage+'.log')).stat().st_size)
        stage_cpu+=proc['cpu_seconds']
    records.append({'name':name,'predicate':passed,'native':{k:native[k]for k in ('opens','blocking','warnings','exclusions')},'warning_types':dict(warnings),'errors':[{'type':r['type'],'uuid_pair':[i['uuid']for i in r['items']]}for r in errors],'board_sha256':expected['pic_programmer.kicad_pcb'],'original_drc_sha256':digest(folder/'original-drc.json'),'geometry_verified':True})
check('all12 native stages',len(summary['cases'])==6 and sum(len(r['steps'])for r in summary['cases'])==12)
check('stage CPU readback',abs(stage_cpu-summary['child_step_cpu_seconds'])<1e-9 and summary['total_cpu_seconds']>=stage_cpu)
check('finite stored full budgets',all(isinstance(summary[k],(int,float))and math.isfinite(summary[k])and 0<summary[k]<180 for k in ('wall_seconds','total_cpu_seconds'))and summary['within_budget'] is True)
execution=read(ROOT/'.runs/pic-custom-native-controls-001-execution.json')
check('outer measured controller failure',execution['controller_exit_code']==2 and execution['git_head']==HEAD and execution['outer_cleanup_signals']==[])
check('outer accounting greater',execution['outer_wall_seconds']>=summary['wall_seconds'] and execution['outer_waited_child_cpu_seconds']>=summary['total_cpu_seconds'])
check('outer wrapper/log pins',digest(ROOT/'.runs/run-pic-custom-controls-001.py')==execution['wrapper_sha256'] and digest(ROOT/execution['stdout_stderr'])==execution['log_sha256'])
check('review unchanged source',tree(SOURCE)==source_before)
check('review unchanged rawrun',tree(RUN)==initial)
# Propose only rights-audited small raw files, without copying to public evidence.
selected=[]
def select(path,destination,rights):
    selected.append({'original':str(path.relative_to(ROOT)),'proposed_destination':destination,'sha256':digest(path),'bytes':path.stat().st_size,'rights':rights})
select(RUN/'summary.json','summary.json','project-authored factual diagnostic receipt; names/geometry derivative attribution retained')
select(ROOT/'.runs/pic-custom-native-controls-001-execution.json','execution.json','project-authored execution metadata')
select(ROOT/'.runs/pic-custom-native-controls-001-command.log','command.log','project-authored process output')
select(ROOT/'.runs/run-pic-custom-controls-001.py','execution-wrapper.py','project-owned wrapper source')
for row in summary['cases']:
    name=row['variant']+'-'+row['case'];folder=RUN/name
    for leaf in ('recipe.json','observation.json','custom-pads.json','native.dsn','observe-process.json','observe.log','original-drc.json','original-drc-process.json','original-drc.log','original-drc-binding.json'):
        select(folder/leaf,name+'/'+leaf,'owned diagnostic fixture/native derivative of official KiCad pic_programmer demo at69cafb907ebc09e7722a2a464b1d466fc2e3608d; CC-BY-SA4.0, attribution+notices required')
    for leaf in ('pic_programmer.kicad_pcb','pic_programmer.kicad_pro'):
        select(folder/'observe-input'/leaf,name+'/observe-input/'+leaf,'official KiCad demo project or owned derived fixture; CC-BY-SA4.0; original project unchanged')
for leaf in ('LICENSE.README','LICENSE.CC-BY-SA-4.0'):
    select(SOURCE/'_licenses'/leaf,'_licenses/'+leaf,'original upstream license/attribution notice, retain verbatim')
(OUT/'selected-public-proposal.json').write_text(json.dumps({'schema':1,'status':'selection_only_not_copied','files':selected,'file_count':len(selected),'bytes':sum(r['bytes']for r in selected),'omitted':'repeated full source schematics/libraries/models, personal-free generated KiCad config, duplicated DRC project, repeated source/runtime payload; complete original raw remains local and hash-bound','attribution':'KiCad official demos/pic_programmer at69cafb907ebc09e7722a2a464b1d466fc2e3608d, CC-BY-SA4.0; owned modified four-pad diagnostic fixtures at34665498, no manufacturer endorsement.'},indent=2)+'\n')
result={'schema':1,'status':'audit_passed_failed_controls_preserved','checks':len(checks),'checks_names':checks,'git_head':HEAD,'summary_sha256':digest(RUN/'summary.json'),'execution_sha256':digest(ROOT/'.runs/pic-custom-native-controls-001-execution.json'),'cases':records,'actual_native_stages':12,'native_invoked_by_audit':False,'network_requests':0,'source_before_after_equal':True,'raw_before_after_equal':True,'source_file_count':15,'source_bytes':1366598,'stored_wall_seconds':summary['wall_seconds'],'stored_total_cpu_seconds':summary['total_cpu_seconds'],'outer_wall_seconds':execution['outer_wall_seconds'],'outer_waited_child_cpu_seconds':execution['outer_waited_child_cpu_seconds'],'stored_accounting_point':summary['accounting_point'],'false_scope_flags':list(false),'selected_public_file_count':len(selected),'selected_public_bytes':sum(r['bytes']for r in selected)}
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k not in ('checks_names','cases','false_scope_flags')},indent=2))
