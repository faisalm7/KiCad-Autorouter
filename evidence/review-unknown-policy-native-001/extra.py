"""Pure retained-execution and public-copy checks for announced completed run."""
import ast, math
from pathlib import Path

def audit_extra(ROOT,RUN,data,read,sha,inventory,ok):
    execution_path=ROOT/'.runs/unknown-policy-native-001-execution.json'
    wrapper=ROOT/'.runs/run-unknown-policy-native-001.py'
    command=ROOT/'.runs/unknown-policy-native-001-command.log'
    execution=read(execution_path);external_before={str(p):sha(p)for p in (execution_path,wrapper,command)}
    expected=['python3','-B','-m','autorouter','route','evidence/placement-area-native-001/allowed_placement/candidate/fixture.kicad_pcb','--guidance','placement-clearance-v1','--adapter','both','--profile','completion-only','--seconds','60','--output','.runs/unknown-policy-native-001']
    ok('actual measured controller exit0 and exact planned argv',execution['argv']==expected and execution['exit_code']==0 and execution['cwd']==str(ROOT) and execution['git_head']==data['tools']['git_head'] and execution['cleanup_signals']==[])
    ok('exact external wrapper and command log',sha(wrapper)==execution['wrapper_sha256'] and sha(command)==execution['log_sha256'] and command.stat().st_size==execution['log_bytes'])
    tree=ast.parse(wrapper.read_text());declared=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='argv'for t in n.targets))
    ok('wrapper source exact argv matches execution',ast.literal_eval(declared)==expected)
    ok('outer actual durationCPU compatible with stored beforepublication sample',0<data['wall_seconds']<=execution['wall_seconds']<60 and 0<data['total_cpu_seconds']<=execution['waited_child_cpu_seconds']<60)
    emitted=read(command);ok('controller stdout summary matches canonical result',all(emitted[k]==data[k]for k in ('status','accepted','candidate','metrics','wall_seconds','total_cpu_seconds')))
    processes=[]
    for step in data['steps']:
        name=step['name'];raw=read(RUN/(name+'-process.json'));log=Path(raw['log'])
        ok(name+' process record exact retained step subset',all(step.get(k)==v for k,v in raw.items()))
        ok(name+' exact log length/nottruncated/cleanup',log.parent==RUN and log.stat().st_size==raw['log_bytes'] and raw['log_truncated'] is False and raw['cleanup_complete'] is True and raw['status']=='success' and raw['exit_code']==0)
        ok(name+' explicit networkdeny all actualworker argv',raw['argv'][:3]==['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)'])
        guard=raw['resource_guards']
        ok(name+' bounded sampled resource observations',guard['max_group_rss_bytes']==4*1024**3 and guard['max_workdir_bytes']==512*1024**2 and raw['sampled_peak_group_rss_bytes']<=guard['max_group_rss_bytes'] and raw['sampled_peak_workdir_bytes']<=guard['max_workdir_bytes'] and guard['os_enforced'] is False)
        if name.endswith('drc'):
            ok(name+' actual log zero violations and opens',b'Found 0 violations' in log.read_bytes() and b'Found 0 unconnected items' in log.read_bytes())
        processes.append({'name':name,'process_sha256':sha(RUN/(name+'-process.json')),'log_sha256':sha(log),'log_bytes':log.stat().st_size,'exit_code':0,'wall_seconds':raw['wall_seconds'],'cpu_seconds':raw['cpu_seconds']})
    final_log=(RUN/'floor-final.log').read_text()
    ok('retained finalobserver GetWidth diagnostic truthfully recorded','PCB_VIA::GetWidth called without a layer argument' in final_log)
    source=Path(data['source']);project=read(source.with_suffix('.kicad_pro'));severities=project['board']['design_settings']['rule_severities']
    explicit=sorted(k for k,v in severities.items()if v=='ignore');native=sorted(x['key']for x in data['native']['ignored_checks'])
    ok('native ignored defaults noncritical and originalexplicitignored retained',set(explicit)<=set(native))
    public=ROOT/'evidence/unknown-policy-native-001';before=inventory(public);selection=read(public/'public-copy.json');total=0;names=[]
    for row in selection['files']:
        raw=ROOT/row['source'];dest=public/row['destination']
        ok('public exact original bytes '+row['destination'],sha(raw)==sha(dest)==row['sha256'] and raw.stat().st_size==dest.stat().st_size==row['bytes'])
        names.append(row['destination']);total+=row['bytes']
    ok('public exact census total and no unexpectedpayload',len(names)==len(set(names))==selection['count']==27 and total==selection['bytes']==128676 and set(before)==set(names)|{'public-copy.json','PUBLIC_SCOPE.md'})
    for license in ('LICENSE.README','LICENSE.CC-BY-SA-4.0'):
        ok('public original grantnotice '+license,sha(public/'_licenses'/license)==data['source_hashes']['_licenses/'+license])
    ok('all external/public bytes stable after checks',before==inventory(public) and external_before=={s:sha(s)for s in external_before})
    return {'external_execution_sha256':sha(execution_path),'external_wall_seconds':execution['wall_seconds'],'external_waited_child_cpu_seconds':execution['waited_child_cpu_seconds'],'controller_exit_code':0,'processes':processes,'source_explicit_ignored':explicit,'native_effective_ignored':native,'extra_default_ignored_absent_source':sorted(set(native)-set(explicit)),'public_selection_sha256':sha(public/'public-copy.json'),'public_selected_files':27,'public_selected_bytes':total,'public_inventory':before,'floor_final_nonfatal_log':'PCB_VIA::GetWidth called without a layer argument; observed exit0, complete context, raw log preserved; not a DRC finding or waived native finding.'}
