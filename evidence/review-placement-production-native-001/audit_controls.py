"""Audit completed five native controls from retained bytes only; no native work."""
from pathlib import Path
import collections,copy,hashlib,json,math,subprocess
import audit_fixture as a
from autorouter import pipeline as p,sexpr as sx,floor_route as f,board_floor as g,config as c
ROOT,HERE=a.ROOT,a.HERE
RUN=ROOT/'.runs/placement-production-controls-native-002'
HEAD='eab7540924b5c8d68263fb68eb4bce6ab9540783'
CASES=('positive','narrow_track','small_via','missing_via','changed_rule')
REASONS={'narrow_track':'generated track differs from derived guidance','small_via':'generated via differs from derived guidance/floor','changed_rule':'native context/source/DSN byte binding mismatch'}
def uid(node):return sx.unquote(sx.one(node,'uuid')[1])
def derive(case,original,project,row):
    tree=copy.deepcopy(original);pr=copy.deepcopy(project);expected=row['expected']
    routes=p.routes(tree);via=[x for x in routes if x[0]=='via'];a.ok(case+': actual exactlyone expectedvia',len(via)==1 and uid(via[0])==expected['positive_via_uuid'])
    if case=='narrow_track':
        target=[x for x in routes if uid(x)==expected['target_uuid']]
        a.ok(case+': exact widthold',len(target)==1 and sx.one(target[0],'width')==['width','0.3'])
        sx.one(target[0],'width')[1]='0.2'
    elif case=='small_via':
        a.ok(case+': exact diameterold',sx.one(via[0],'size')==['size','1.5']);sx.one(via[0],'size')[1]='0.6'
    elif case=='missing_via':tree.remove(via[0])
    elif case=='changed_rule':
        a.ok(case+': original width severityerror',pr['board']['design_settings']['rule_severities']['track_width']=='error');pr['board']['design_settings']['rule_severities']['track_width']='warning'
    return tree,pr

def process(run,name,record,allsteps,board,native=None,saved=False,before=None):
    raw=a.read(run/(name+'-process.json'));matches=[x for x in allsteps if x['cwd']==str(run) and x['name']==name]
    a.ok(str(run.relative_to(RUN))+': '+name+' uniqueprocess bound',len(matches)==1 and all(matches[0].get(k)==v for k,v in raw.items()) and raw['cleanup_complete'] is True)
    if native is not None:
        copied=run/'refill'/board.name if saved else run/(name+'-input')/board.name
        binding=a.read(run/(name+'-binding.json'));expected_before=a.inventory(board.parent) if before is None else before
        a.ok(name+': native stage exact source/copy/pre-input',binding['source']==str(board) and binding['input']==str(copied) and binding['saved'] is saved and binding['before']==expected_before)
        a.ok(name+': all original rules unchanged innativeinput',all(binding['after'].get(k)==v for k,v in expected_before.items() if not saved or k!=board.name) and set(binding['after'])-set(expected_before)<={board.with_suffix('.kicad_prl').name} and a.inventory(copied.parent)==binding['after'])
        argv=[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(run/(name+'.json'))]
        if saved:argv.append('--save-board')
        argv.append(str(copied));exitcode=5 if native['findings'] else 0
        a.ok(name+': actualCLIargv status andinputhash',raw['argv']==argv and raw['exit_code']==exitcode and raw['status']==('success' if exitcode==0 else 'nonzero_exit') and matches[0]['validated_input_sha256']==expected_before[board.name] and matches[0]['emitted_candidate']==str(board))
    return raw

def main():
    before=a.inventory(RUN);record=a.read(RUN/'summary.json');freeze=record['freeze'];positive=a.read(a.RUN/'result.json');source=Path(record['source']);source_before=a.inventory(source.parent);original=sx.read(source);candidate=Path(positive['candidate']);base=sx.read(candidate);project=a.read(candidate.with_suffix('.kicad_pro'));task=g.task_from_source(original)
    a.ok('complete fiveexpectedcontrols and no routing/comparisonclaim',record['status']=='completed' and record['controls_passed'] is True and [x['case'] for x in record['cases']]==list(CASES) and all(record[k] is False for k in ('routing_accepted','comparison_eligible','new_engine_execution','physical_electrical_validation')))
    a.ok('new helper HEAD and unchanged qualified core/tools',freeze['tools']['git_head']==HEAD and {k:v for k,v in freeze['tools'].items() if k!='git_head'}=={k:v for k,v in positive['tools'].items() if k!='git_head'})
    a.ok('earlier positive receipt andcomplete tree exact',record['positive_result']==str(a.RUN/'result.json') and record['positive_result_sha256']==a.sha(a.RUN/'result.json') and record['positive_candidate_sha256']==a.CANDIDATE and freeze['positive']==a.inventory(a.RUN))
    a.ok('owned original eight reference routes strippedtask distinction',len(p.routes(original))==8 and p.routes(task)==[] and g.sha((sx.dump(task)+'\n').encode())==positive['task_sha256'])
    a.ok('fullsource andpositivecandidate preservedcopies',freeze['source']==source_before==a.inventory(RUN/'source') and freeze['candidate']==a.inventory(candidate.parent)==a.inventory(RUN/'positive-candidate'))
    a.ok('entire retained code exactfreeze',a.inventory(RUN/'code')==freeze['code'])
    for rel,digest in freeze['tools']['implementation_sha256'].items():
        blob=subprocess.run(['git','show',HEAD+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=5).stdout
        a.ok('committed currentandcopied core '+rel,hashlib.sha256(blob).hexdigest()==digest==a.sha(ROOT/rel)==a.sha(RUN/'code'/rel))
    for name,digest in freeze['helpers'].items():
        rel='experiments/placement_production_controls_v1/'+name;blob=subprocess.run(['git','show',HEAD+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=5).stdout
        a.ok('committed diagnostichelper '+name,hashlib.sha256(blob).hexdigest()==digest==a.sha(ROOT/rel)==a.sha(RUN/'code'/name))
    for filename,digest in freeze['tools']['files'].items():a.ok('installed binaryexact '+Path(filename).name,a.sha(filename)==digest)
    results=[]
    for row in record['cases']:
        case=row['case'];directory=RUN/case;diagnostic=directory/'diagnostic';validation=directory/'validation';db=diagnostic/'candidate'/candidate.name;vb=validation/'candidate'/candidate.name
        a.ok(case+': completed case byteinventoryandrow',a.inventory(directory)==record['completed_evidence'][str(directory)] and a.read(directory/'case.json')==row)
        expected,expected_project=derive(case,base,project,row)
        a.ok(case+': sole declaredboard mutation inbothcopies',sx.read(db)==expected==sx.read(vb) and p.immutable(expected)==p.immutable(base))
        a.ok(case+': exactproject mutation onlyifdeclared',a.read(db.with_suffix('.kicad_pro'))==expected_project==a.read(vb.with_suffix('.kicad_pro')))
        hashes={**freeze['candidate'],candidate.name:a.sha(db),candidate.with_suffix('.kicad_pro').name:a.sha(db.with_suffix('.kicad_pro'))}
        a.ok(case+': all other files exactpositiveproject',a.inventory(db.parent)==hashes==a.inventory(vb.parent) and row['expected']['board_sha256']==a.sha(db) and row['expected']['project_sha256']==a.sha(db.with_suffix('.kicad_pro')))
        native=p.parse_report(diagnostic/'diagnostic-drc.json',db.name);a.ok(case+': actualraw native countersand originalignored/exclusions',native==row['native'] and native['ignored_checks']==positive['native']['ignored_checks'] and native['exclusions']==0)
        process(diagnostic,'diagnostic-drc',row,record['steps'],db,native)
        binding=a.read(diagnostic/'diagnostic-drc-binding.json')
        a.ok(case+': diagnosticreceipt exactbindings',row['diagnostic_binding']=={'candidate_sha256':a.sha(db),'native_report_sha256':a.sha(diagnostic/'diagnostic-drc.json'),'native_binding_sha256':a.sha(diagnostic/'diagnostic-drc-binding.json'),'input_hashes':binding['after']})
        types=collections.Counter((x['type'],x['severity']) for x in native['findings'])
        expected_types={'positive':{},'narrow_track':{('track_width','error'):1,('connection_width','warning'):1},'small_via':{('annular_width','error'):1,('via_diameter','error'):1},'missing_via':{('unconnected_items','error'):1,('track_dangling','warning'):2},'changed_rule':{}}
        a.ok(case+': complete actualfinding census',types==expected_types[case])
        if case in ('narrow_track','small_via'):
            targetkind='track_width' if case=='narrow_track' else 'via_diameter';hits=[x for x in native['findings'] if x['type']==targetkind and x['severity']=='error' and row['expected']['target_uuid'] in {y['uuid'] for y in x['items']}]
        elif case=='missing_via':hits=[x for x in native['findings'] if x['type']=='unconnected_items' and set(row['expected']['adjacent_route_uuids'])<={y['uuid'] for y in x['items']}]
        else:hits=[]
        a.ok(case+': targeted native exactitemidentity',hits==row['targeted_native_findings'] and (bool(hits) if case not in ('positive','changed_rule') else not hits))
        for name in ('floor-policy.json','floor-export-context.json','native.dsn','floor-guided.dsn'):a.ok(case+': originalguidancecontract retained '+name,a.sha(validation/name)==a.sha(a.RUN/name))
        contract=a.read(validation/'floor-policy.json')
        if case in REASONS:
            try:f.validate_contract(original,vb,source_before,[],contract,validation)
            except (ValueError,p.Rejected) as exc:a.ok(case+': reproduced pureproduction refusal',str(exc)==REASONS[case] and row['production_rejection']==type(exc).__name__+': '+str(exc))
            else:raise AssertionError(case+' incorrectlyaccepted')
            a.ok(case+': productionrefuses before anynative validation',row['production_native_accepted'] is False and row['production_steps']==[] and not list(validation.glob('*-process.json')))
        else:
            f.validate_contract(original,vb,source_before,[],contract,validation);a.CHECKS.append(case+': productionexactfloorcontract passesgeometry')
            final=p.parse_report(validation/'final-drc.json',vb.name);a.ok(case+': freshproduction native equalsdiagnostic',row['production_native']==final==native and row['production_native_accepted']==p.native_accepted(final)==(case=='positive'))
            stage_before={**source_before,candidate.name:row['expected']['board_sha256']};refill=validation/'refill'/candidate.name;refill_native=p.parse_report(validation/'refill-drc.json',vb.name)
            process(validation,'refill-drc',row,record['steps'],refill,refill_native,True,stage_before)
            a.ok(case+': savedrefill exactcandidate reconstruction',(sx.dump(p.transplant_fill(expected,sx.read(refill)))+'\n').encode()==vb.read_bytes())
            process(validation,'final-drc',row,record['steps'],vb,final)
            final_context=a.read(validation/'floor-final-context.json');f.context_binding(final_context,vb,{**source_before,candidate.name:a.sha(vb)},'final')
            context=g.qualify(project,final_context,task);audit={'candidate_sha256':a.sha(vb),'native_context_sha256':a.sha(validation/'floor-final-context.json'),'generated':g.audit_generated_routes(sx.read(vb),context),'native_routes':g.audit_native_routes(sx.read(vb),final_context)}
            a.ok(case+': finalnative effectivegeometry audited',a.read(validation/'floor-final-audit.json')==audit)
            nativeproc=process(validation,'floor-final',row,record['steps'],vb)
            a.ok(case+': finalnative observation exactargv',nativeproc['argv']==f.context_argv('final',vb,validation/'floor-final-context.json') and nativeproc['status']=='success' and nativeproc['exit_code']==0)
            b=a.read(validation/'final-drc-binding.json');a.ok(case+': finalproduction summarybound',row['production_binding']=={'candidate_sha256':a.sha(vb),'native_report_sha256':a.sha(validation/'final-drc.json'),'native_binding_sha256':a.sha(validation/'final-drc-binding.json'),'input_hashes':b['after']} and row['candidate_sha256']==a.sha(vb)==row['expected']['board_sha256'])
            a.ok(case+': exactthree retained productionsteps',[x['name'] for x in row['production_steps']]==['refill-drc','floor-final','final-drc'] and all(x in record['steps'] for x in row['production_steps']))
        a.ok(case+': declarationmatches independentlyconfirmed outcome',all(row[k] is True for k in ('passed','diagnostic_passed','production_validation_invoked','production_expected_outcome')))
        results.append({'case':case,'candidate_sha256':a.sha(db),'diagnostic_report_sha256':a.sha(diagnostic/'diagnostic-drc.json'),'native':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'findings':[{'type':x['type'],'severity':x['severity'],'items':[y['uuid'] for y in x['items']]} for x in native['findings']],'production_native_accepted':row['production_native_accepted'],'production_rejection':row.get('production_rejection'),'production_native_steps':len(row['production_steps'])})
    steps=record['steps'];a.ok('eleven realnative stages exactlyonce noengine',len(steps)==11 and len({(x['cwd'],x['name']) for x in steps})==11 and all(x['name'] in ('diagnostic-drc','refill-drc','floor-final','final-drc') for x in steps))
    a.ok('all native childCPU andwalls within shared60secondcap',record['budget_seconds']==record['cpu_budget_seconds']==60 and record['within_budget'] is True and 0<record['wall_seconds']<=60 and 0<record['total_cpu_seconds']<=60 and math.isclose(sum(s['cpu_seconds'] for s in steps),record['child_step_cpu_seconds'],abs_tol=1e-8) and math.isclose(sum(s['monitor_cpu_seconds'] for s in steps),record['monitor_cpu_seconds'],abs_tol=1e-8) and record['total_cpu_seconds']>=record['child_step_cpu_seconds'] and record['wall_seconds']>=sum(s['wall_seconds'] for s in steps))
    old=ROOT/'.runs/placement-production-controls-native-001/summary.json';old_audit=a.read(HERE/'cancellation-audit.json')['pre_native_failed_control']
    a.ok('first failed001 remainsunaltered andprenative',a.sha(old)==old_audit['summary_sha256'] and a.read(old)['native_executed'] is False and a.read(old)['cases']==[])
    a.ok('all original/source/positive/newnativeevidence unchanged',before==a.inventory(RUN) and source_before==a.inventory(source.parent) and freeze['positive']==a.inventory(a.RUN))
    result={'schema':1,'audit_passed':True,'check_count':len(a.CHECKS),'checks':a.CHECKS,'native_engine_network_executed':False,'head':HEAD,'summary_sha256':a.sha(RUN/'summary.json'),'cases':results,'wall_seconds':record['wall_seconds'],'total_cpu_seconds':record['total_cpu_seconds'],'native_step_cpu_seconds':record['child_step_cpu_seconds'],'run_inventory':before,'source_inventory':source_before,'scope':'Five stored-candidate controls, fresh actual native reports; no new engine route, population board or comparison. Rule-severity mutation refused by provenance, not a nativeDRC finding. Raw001 pre-native failure retained. Timings sampled before publication with finalcaps in frozen source; no independent time instrumentation.'}
    with (HERE/'controls-audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','run_inventory','source_inventory')},indent=2))
if __name__=='__main__':main()
