"""Independent offline audit of announced complete production replay; no engines."""
from pathlib import Path
from collections import Counter
import copy,hashlib,json,math,subprocess
import audit_fixture as a
from autorouter import pipeline as p,sexpr as sx,board_floor as g,placement_clearance as pc,floor_route as f
ROOT,HERE=a.ROOT,a.HERE
RUN=ROOT/'.runs/placement-production-multichannel-001'
OLD=ROOT/'.runs/placement-search-three-arm-001/arm-1'
HEAD='eab7540924b5c8d68263fb68eb4bce6ab9540783'
CANDIDATE='65dd3b0e6e0bfe6bf45a84b58d94eb4388a8b318967c47c40c26714b6777a0ef'
SOURCE='44b7c119a0d05c98e9f294659879184038a5f6c30073c04d9536990429ca413e'
def geometry(board):
    _,resolve=g.source_net_identity(board);segments=[];vias=[]
    for item in p.routes(board):
        net=resolve(sx.one(item,'net'))
        if item[0]=='segment':
            ends=sorted(tuple(a.nm(x) for x in sx.one(item,key)[1:3]) for key in ('start','end'))
            segments.append((net,sx.unquote(sx.one(item,'layer')[1]),a.nm(sx.one(item,'width')[1]),*ends))
        elif item[0]=='via':
            layers=tuple(sx.unquote(x) for x in sx.one(item,'layers')[1:]);position=tuple(a.nm(x) for x in sx.one(item,'at')[1:3])
            vias.append((net,layers,position,a.nm(sx.one(item,'size')[1]),a.nm(sx.one(item,'drill')[1])))
        else:raise AssertionError('unknown route topology')
    return sorted(segments),sorted(vias)
def ses_geometry(directory):
    routes=sx.one(sx.read(directory/'routes.ses'),'routes');a.ok('SES qualifiedum10resolution',sx.one(routes,'resolution')==['resolution','um','10']);segments=[];vias=[]
    padstacks=sx.children(sx.one(routes,'library_out'),'padstack');a.ok('one exactqualified outputviapadstack',len(padstacks)==1 and sx.unquote(padstacks[0][1])=='Via[0-1]_1500:300_um')
    for shape in sx.children(padstacks[0],'shape'):a.ok('SES viapadstack1.5mm coppercircle',shape[1][0]=='circle' and shape[1][2:] == ['15000','0','0'])
    for net in sx.one(routes,'network_out')[1:]:
        name=sx.unquote(net[1])
        for wire in sx.children(net,'wire'):
            path=sx.one(wire,'path');points=[(a.nm(path[i],100),-a.nm(path[i+1],100)) for i in range(3,len(path),2)]
            segments.extend((name,sx.unquote(path[1]),a.nm(path[2],100),*sorted((first,last))) for first,last in zip(points,points[1:]))
        for via in sx.children(net,'via'):
            a.ok('SES exactviastack reference',sx.unquote(via[1])=='Via[0-1]_1500:300_um')
            vias.append((name,('F.Cu','B.Cu'),(a.nm(via[2],100),-a.nm(via[3],100)),1500000,300000))
    return sorted(segments),sorted(vias)
def main():
    before=a.inventory(RUN);old_before=a.inventory(OLD);data=a.read(RUN/'result.json');source=Path(data['source']);source_before=a.inventory(source.parent);candidate=Path(data['candidate']);original=sx.read(source);board=sx.read(candidate);task=g.task_from_source(original)
    root_readback=ROOT/'.runs/placement-production-multichannel-001-root-readback.json';readback_hash=a.sha(root_readback)
    a.ok('exactannounced productionhead candidate source',data['tools']['git_head']==HEAD and data['candidate_sha256']==CANDIDATE==a.sha(candidate) and source_before[source.name]==SOURCE)
    a.ok('accepted newproduction scopedpolicy',data['schema']==3 and data['input_policy']=='placement-clearance-v1' and data['accepted'] is True and data['status']=='routing_accepted' and data['whole_project_drc_clean'] is False and data['physical_electrical_validation'] is False and data['baseline']=='completion_only_probe')
    a.ok('exact17file originalandsnapshot',len(source_before)==17 and source_before==data['source_hashes']==a.inventory(RUN/'snapshot'))
    a.ok('candidate fullproject onlyboardchanged',a.inventory(candidate.parent)=={**source_before,source.name:CANDIDATE})
    a.ok('every immutable originalfield preserved',p.immutable(original)==p.immutable(board))
    strip=lambda tree:[[x for x in zone if not isinstance(x,list) or not x or x[0] not in p.DERIVED_ZONE] for zone in sx.children(tree,'zone')]
    a.ok('all six originalzone definitions exactlypreserved',len(sx.children(original,'zone'))==6 and strip(original)==strip(board))
    zones=pc.narrow_source(original);areas=[x for x in zones if x['is_rule_area']]
    a.ok('four originally allallowed enabledplacementareas',len(areas)==4 and all(x['placement_enabled'] and x['placement_source_type']=='SHEETNAME' and not any(x['disallow'].values()) for x in areas))
    a.ok('originaltask routingstripped exactly',not p.routes(task) and (sx.dump(task)+'\n').encode()==pc.read_bytes(RUN/'floor-export-input'/source.name))
    native=a.read(RUN/'floor-export-context.json');area=a.read(RUN/'placement-area-context.json');final=a.read(RUN/'floor-final-context.json')
    a.ok('same-load floorandarea completebindings',all(native[k]==area[k] for k in ('source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after','board_saved','native_version','units')) and not native['routes'] and area['footprint_zone_count']==area['footprint_rulearea_count']==0)
    a.ok('original nativepads nets preferencesandfloors preserved',all(native[k]==final[k] for k in ('pads','nets','floors_nm')))
    outputs,composition=pc.derive_chain(RUN,source.name,source_before)
    a.ok('full rawfloorplacementplanningadapter bytechain rederived',composition==a.read(RUN/'placement-policy.json') and all(pc.read_bytes(RUN/name)==raw for name,raw in outputs.items()))
    trees={name:g._parse_dsn(pc.read_bytes(RUN/name).decode()) for name in ('floor-guided.dsn','placement-guided.dsn','planning-guided.dsn','task.dsn')}
    expected=copy.deepcopy(trees['floor-guided.dsn']);st=sx.one(expected,'structure');keepouts=sx.children(st,'keepout');st[:]=[x for x in st if x not in keepouts]
    a.ok('exacteight attributed removals andnothingelse',len(keepouts)==8 and expected==trees['placement-guided.dsn'] and composition['removal']['removed_count']==8 and Counter((x['source_zone_uuid'],x['layer']) for x in composition['removal']['removed'])==Counter((z['uuid'],layer) for z in areas for layer in ('F.Cu','B.Cu')))
    diffs=a.ast_diff(trees['placement-guided.dsn'],trees['planning-guided.dsn']);a.ok('onlythree originalclearance atoms300to320um',len(diffs)==3 and all(x=='300' and y=='320' for _,x,y in diffs))
    adapted=copy.deepcopy(trees['planning-guided.dsn']);st=sx.one(adapted,'structure');planes=sx.children(st,'plane');st[:]=[x for x in st if x not in planes]
    a.ok('bothadapter removesonlythree DSNplanes nativezonesretained',len(planes)==3 and native['obstacles']==[] and adapted==trees['task.dsn'])
    contract=a.read(RUN/'floor-policy.json');a.ok('separateoriginal floorguidance unchanged',contract['policy']=='board-floors-v1' and contract['transformation']['derived_nm']=={'width_nm':300000,'clearance_nm':300000,'via_diameter_nm':1500000,'via_drill_nm':300000})
    f.audit_transport(RUN,data,task,candidate);a.CHECKS.append('actual SESimportsavedrefill sourceandcandidatebytes rederived')
    normalized=geometry(board);a.ok('every finaltrackandvia exactlySEStransported',ses_geometry(RUN)==normalized)
    a.ok('actual783segments21vias',len(normalized[0])==783 and len(normalized[1])==21)
    drc=p.parse_report(RUN/'final-drc.json',candidate.name);source_drc=p.parse_report(RUN/'source-drc.json',candidate.name);census=Counter((x['type'],x['severity']) for x in drc['findings']);source_census=Counter((x['type'],x['severity']) for x in source_drc['findings'])
    expected_census={('lib_footprint_mismatch','warning'):81,('connection_width','warning'):9,('silk_over_copper','warning'):4,('silk_edge_clearance','warning'):1,('nonmirrored_text_on_back_layer','warning'):1}
    a.ok('raw nativeaccepted but96warningsnotclean',drc==data['native'] and p.native_accepted(drc) and all(drc[k]==0 for k in ('opens','blocking','exclusions')) and drc['warnings']==96 and census==expected_census)
    a.ok('original ignoredchecks unchanged sourcefailuresretained',drc['ignored_checks']==source_drc['ignored_checks'] and len(drc['ignored_checks'])==7 and data['source_drc']==source_drc and source_census[('clearance','error')]==24 and source_census[('connection_width','warning')]==6)
    a.ok('freshfinalreport exactemitted input',a.sha(RUN/'final-drc.json')==data['native_report_sha256'] and a.sha(RUN/'final-drc-input'/candidate.name)==CANDIDATE)
    metric=a.read(RUN/'metrics.json');length=sum(math.dist(a0,a1)/1000000 for _,_,_,a0,a1 in normalized[0])
    a.ok('native metricstrace independentexactgeometry',metric==data['metrics'] and metric['vias']==21 and metric['pads']==327 and metric['footprints']==114 and metric['zones']==6 and math.isclose(metric['track_length_mm'],length,abs_tol=1e-9))
    a.ok('actualeightstages unique andcleanup', [s['name'] for s in data['steps']]==['source-drc','floor-export','engine','import','refill-drc','floor-final','final-drc','metrics'] and all(s['cleanup_complete'] is True for s in data['steps']))
    expected_settings=p.engine_profile_settings('completion-only',data['engine_budget']['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=True,scoring_variant='via_default');expected_settings.update(outer_task_wall_budget_seconds=120.0,outer_task_cpu_budget_seconds=120.0)
    a.ok('exactproduction allocation andfixedsearchsettings',data['engine_budget']==expected_settings and data['engine_budget']['assigned_job_timeout_seconds']==60 and data['planning_parameters']==pc.parameters())
    a.ok('fullwallCPU ceilingandcomponentarithmetic',data['budget_seconds']==data['cpu_budget_seconds']==120 and data['wall_seconds']<=120 and data['total_cpu_seconds']<=120 and math.isclose(data['total_cpu_seconds'],sum(data[k] for k in ('parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','control_child_cpu_seconds')),abs_tol=1e-8) and math.isclose(data['child_cpu_seconds'],sum(s['cpu_seconds'] for s in data['steps']),abs_tol=1e-8) and math.isclose(data['monitor_cpu_seconds'],sum(s['monitor_cpu_seconds'] for s in data['steps']),abs_tol=1e-8) and sum(s['wall_seconds'] for s in data['steps'])<=data['wall_seconds'])
    frozen=a.read(RUN/'placement-source-freeze.json')
    for rel,digest in frozen['files_sha256'].items():
        blob=subprocess.run(['git','show',HEAD+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=5).stdout;retained=RUN/'placement-toolchain.lock.json' if rel=='toolchain.lock.json' else RUN/'code'/Path(rel).name
        a.ok('exactcommitted/copied/current code '+rel,hashlib.sha256(blob).hexdigest()==digest==a.sha(ROOT/rel)==a.sha(retained))
    for name,digest in data['tools']['files'].items():a.ok('exacttoolpin '+Path(name).name,a.sha(name)==digest)
    verdict=p.check_result(RUN/'result.json');a.ok('fullproduction schema3 checkerexactrootreadback',verdict==a.read(root_readback) and verdict['current'] is True and verdict['input_policy']=='placement-clearance-v1' and verdict['applied'] is False)
    old_review=ROOT/'.runs/review-placement-search-three-arm-001';old_manifest=a.read(old_review/'manifest.json');a.ok('previousdiagnostic independentaudit pin',a.sha(old_review/'audit.json')==old_manifest['files']['audit.json']['sha256']=='f58724ea0f282928f850f4c4b1c5e86a8981f2e9c9b7810c76ee1ad86b3271b0')
    prior=a.read(old_review/'audit.json');old_record=a.read(OLD/'result.json');recorded_arm={k[len('arm-1/'):]:v for k,v in prior['run_inventory'].items() if k.startswith('arm-1/')}
    a.ok('previousaccepted diagnosticarm fulltreeunchanged',old_before==recorded_arm and old_record['routing_accepted'] is True and old_record['source_hashes']==source_before)
    old_board=sx.read(Path(old_record['candidate']));a.ok('same exactnet layer width endpoint via topologyasold diagnostic',normalized==geometry(old_board))
    a.ok('sameoriginal immutablegeometry asolddiagnostic',p.immutable(old_board)==p.immutable(board))
    a.ok('same96warningtypecounts no comparisonclaim',Counter((x['type'],x['severity']) for x in old_record['native']['findings'])==census and old_record['native']['opens']==0 and old_record['native']['blocking']==0)
    a.ok('all source/run/previousarm androotreadback unchanged',before==a.inventory(RUN) and source_before==a.inventory(source.parent) and old_before==a.inventory(OLD) and readback_hash==a.sha(root_readback))
    result={'schema':1,'audit_passed':True,'check_count':len(a.CHECKS),'checks':a.CHECKS,'native_engine_network_executed':False,'head':HEAD,'receipt_sha256':a.sha(RUN/'result.json'),'candidate_sha256':CANDIDATE,'report_sha256':data['native_report_sha256'],'source_hashes':source_before,'run_inventory':before,'check_result':verdict,'native':{'opens':drc['opens'],'blocking':drc['blocking'],'warnings':drc['warnings'],'exclusions':drc['exclusions'],'ignored_checks':drc['ignored_checks']},'finding_census':[{'type':k[0],'severity':k[1],'count':v} for k,v in sorted(census.items())],'metrics':metric,'wall_seconds':data['wall_seconds'],'total_cpu_seconds':data['total_cpu_seconds'],'transforms':{'placement_areas':4,'removed_false_keepouts':8,'clearance_atoms_changed':3,'clearance_um_before':300,'clearance_um_after':320,'adapter_planes_removed':3,'original_zones_retained':6},'same_topology_prior_diagnostic':{'result_sha256':a.sha(OLD/'result.json'),'candidate_sha256':old_record['candidate_sha256'],'segments':783,'vias':21,'exact_net_layer_endpoint_width_drill_geometry_equal':True,'comparison_claim':False},'scope':'Exposed one-board productionqualification replay. No new matchedcomparison/Cnovelty/generalization, no metric gainvsinvalidbaseline, no physical/electrical or GUIqualification. Original24clearanceerrors and93warnings remain source evidence; candidate has96warnings including3more connection_width. Storedtimings precedefinalwrite, frozenfinalguard checks cap.'}
    with (HERE/'multichannel-audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','source_hashes','run_inventory','check_result','native')},indent=2))
if __name__=='__main__':main()
