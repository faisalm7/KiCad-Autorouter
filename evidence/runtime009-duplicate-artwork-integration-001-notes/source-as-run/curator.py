"""Read-only shared-reader curation of three completed runtime009 CLI workflows.

Writes only its selected public evidence/notes; no Native/JVM/test/GUI execution.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
from decimal import Decimal
import copy,datetime,hashlib,json,subprocess,sys,time
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'.runs/runtime-directory-009';RUNTIME=CASE/'runtime'
PUBLIC=ROOT/'evidence/runtime009-duplicate-artwork-integration-001.json'
NOTES=ROOT/'evidence/runtime009-duplicate-artwork-integration-001-notes'
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,review_export as ex,sexpr as sx,placement_clearance as io,local_settings as ls

def read(path):return f.read_json(path)
def require(value,reason):
    if not value:raise p.Rejected(reason)
def pin(path):return dict(path=str(path.relative_to(ROOT)),sha256=p.sha(path),bytes=path.stat().st_size)
def timing(name):
    path=ROOT/'.runs'/(name+'-time.log');rows={k:Decimal(v)for k,v in (line.split()for line in path.read_text().splitlines())}
    require(set(rows)=={'real','user','sys'},'unexpected complete external timing schema')
    return dict(wall_seconds=float(rows['real']),full_CPU_seconds=float(rows['user']+rows['sys']),
        user_seconds=float(rows['user']),system_seconds=float(rows['sys']),log=pin(path))

def main():
    require(c.ROOT==RUNTIME and Path(sys.prefix).resolve()==RUNTIME/'.venv','installed009 reader context required')
    require(not PUBLIC.exists() and not NOTES.exists(),'fresh public destinations required')
    setup=read(CASE/'setup.json');manifest=read(RUNTIME/'runtime-distribution.json');tools=p.tool_manifest()
    head='da2db9606027d9e430ff1e6f83b0e64f55d698c9'
    require(tools['git_head']==setup['source_head']==manifest['build_source']['git_head']==head,'source HEAD differs')
    require(len(tools['implementation_sha256'])==42 and p.sha(RUNTIME/'runtime-distribution.json')==setup['manifest_sha256'],'runtime module census/manifest differs')
    root_drift={}
    for name,digest in tools['implementation_sha256'].items():
        require(p.sha(RUNTIME/name)==manifest['immutable_files_sha256'][name]==digest,'runtime module changed: '+name)
        frozen=subprocess.run(['git','show',head+':'+name],cwd=ROOT,capture_output=True,timeout=10,check=True)
        require(hashlib.sha256(frozen.stdout).hexdigest()==digest,'source-as-built Git object differs: '+name)
        current=p.sha(ROOT/name)
        if current!=digest:root_drift[name]=dict(runtime_sha256=digest,current_root_sha256=current)
    for name,digest in manifest['immutable_files_sha256'].items():require(p.sha(RUNTIME/name)==digest,'immutable artifact changed: '+name)
    copies={'source-as-run/curator.py':Path(__file__),'records/setup.json':CASE/'setup.json',
        'records/runtime-distribution.json':RUNTIME/'runtime-distribution.json','LICENSE':ROOT/'LICENSE'}
    omitted=[]
    def packet(path,destination):
        files=io.inventory(path,contents=True,max_bytes=16*1024**2,max_files=40,max_entries=80)
        for name in files:copies[destination+'/'+name]=path/name
        return {name:p.sha(path/name)for name in files}
    def stages(path,destination):
        for item in sorted(path.iterdir()):
            if item.is_file() and item.suffix in {'.json','.log','.net','.dsn','.ses'}:
                if item.stat().st_size<=256*1024:copies[destination+'/'+item.name]=item
                else:omitted.append(pin(item))
        for name in ['pre-refill.kicad_pcb','imported.kicad_pcb']:
            if (path/name).is_file():copies[destination+'/'+name]=path/name
        refill=path/'refill'
        if refill.is_dir():
            for item in refill.glob('*.kicad_pcb'):copies[destination+'/native-saved-refill.kicad_pcb']=item
    specs=[('route4Cu','qualification-route','enclosure-route',6,10,4,'runtime009-route-wrapper'),
        ('improve2Cu','qualification-improve-2cu','enclosure-improve-2cu',6,1,2,'runtime009-improve-2cu-wrapper'),
        ('duplicate_artwork2Cu','qualification-route-duplicate-artwork','enclosure-route-duplicate-artwork',8,1,2,'runtime009-duplicate-artwork-wrapper')]
    positives={};source_witnesses={};route_records={}
    with p.validation_readback_session():
        for label,name,enclosure_name,warnings,protected_count,copper,time_name in specs:
            path=RUNTIME/'.runs'/name;workflow=read(path/'result.json');workspace=Path(workflow['workspace'])
            route=read(workspace/'route/result.json');export=read(workspace/'export/export.json')
            enclosure=read(RUNTIME/'.runs'/enclosure_name/'execution.json')
            require(workflow['workflow_delivered'] is True and workflow['actual_GUI'] is False and workflow['tools']==tools,
                'completed installed CLI workflow/context differs: '+label)
            require(workflow['driver_sha256']==p.sha(ROOT/'scripts/qualify_runtime_workflow.py'),
                'actual production workflow controller differs: '+label)
            require(enclosure['workflow_delivered'] is True and enclosure['child_sha256']==p.sha(path/'result.json') and
                enclosure['process']['status']=='success' and enclosure['process']['exit_code']==0 and
                enclosure['process']['cleanup_complete'] is True,'workflow enclosure differs: '+label)
            current=p.check_result(workspace/'route/result.json');current_export=ex.check_export(workspace/'export/export.json')
            require(current['current'] is True and current_export['current'] is True,'current final proof refused: '+label)
            source=Path(workflow['source']);original=sx.read(source);protected=p.protected_for_record(route,original)
            require(p.tree_hash(source.parent)==workflow['source_hashes']==route['source_hashes']==export['source_hashes'] and
                len(protected)==protected_count,'original source/protection census differs: '+label)
            source_witnesses[source.parent]=workflow['source_hashes'];route_records[label]=(workflow,route,export)
            require(route['candidate_sha256']==export['candidate_sha256'],'own route/export candidate hashes differ: '+label)
            for phase,data,folder in [('route',route,workspace/'route'),('export',export,workspace/'export/validation')]:
                candidate=Path(data['candidate']);tree=sx.read(candidate);raw=read(folder/'final-drc.json')
                require(data['tools']==tools and p.sha(candidate)==data['candidate_sha256'] and
                    p.sha(folder/'final-drc.json')==data['native_report_sha256'] and
                    raw['violations']+raw['unconnected_items']+raw['schematic_parity']==data['native']['findings'],
                    'final raw report/candidate binding differs: '+label+'/'+phase)
                require(p.immutable(original)==p.immutable(tree) and all(row in p.routes(tree)for row in protected),
                    'original invariants/protected copper differ: '+label+'/'+phase)
                require([data['native'][key]for key in ['opens','blocking','warnings','exclusions']]==[0,0,warnings,0] and
                    len(data['native']['ignored_checks'])==2 and p.native_accepted(data['native']) and
                    data['schematic_parity']=='checked by final native DRC' and data['whole_project_drc_clean'] is False,
                    'actual final Native scope differs: '+label+'/'+phase)
                require(data['metrics']['copper_layers']==copper,'physical copper census differs: '+label)
                proof=read(folder/'final-drc-fields-proof.json')
                require(proof['qualification']['qualified'] is True and proof['qualification']['component_count']==6 and
                    proof['qualification']['compared_field_count']==18,'complete ordinary field proof differs: '+label)
                if label=='duplicate_artwork2Cu':
                    census=proof['board_only_field_census']
                    require(census['policy']=='source-bound-padless-field-census-v2' and census['complete_footprint_count']==8 and
                        census['compared_footprint_count']==6 and census['duplicate_artwork_reference_groups']==[
                            {'folded_reference':'g***','uuids':sorted(setup['duplicate_artwork_UUIDs'])}],
                        'actual duplicate-artwork proof differs')
                packet(candidate.parent,'positives/'+label+'/'+phase+'/final-project')
                stages(folder,'positives/'+label+'/'+phase+'/stage-records')
            for row in workflow['processes']:
                process=row['process'];log=path/(row['stage']+'.log')
                require(process['exit_code']==0 and process['log_truncated'] is False and p.sha(log)==row['log_sha256'],
                    'saved production CLI stage/log differs: '+label)
            packet(source.parent,'positives/'+label+'/original-source')
            for file in path.iterdir():
                if file.is_file() and file.suffix in {'.json','.log'}:copies['positives/'+label+'/CLI/'+file.name]=file
            copies['positives/'+label+'/enclosure.json']=RUNTIME/'.runs'/enclosure_name/'execution.json'
            copies['positives/'+label+'/route/result.json']=workspace/'route/result.json'
            copies['positives/'+label+'/export/export.json']=workspace/'export/export.json'
            copies['positives/'+label+'/review.json']=workspace/'review/review.json'
            copies['positives/'+label+'/choice.json']=workspace/'choice/choice.json'
            copies['positives/'+label+'/external-time.log']=ROOT/timing(time_name)['log']['path']
            positives[label]=dict(workflow_delivered=True,actual_GUI=False,source=str(source),source_hashes=workflow['source_hashes'],
                settings=workflow['settings'],whole_workflow_budget_seconds=workflow['whole_budget_seconds'],
                protected_route_count=protected_count,original_invariant_AST_exact=True,
                route=dict(candidate_sha256=route['candidate_sha256'],native=route['native'],metrics=route['metrics'],current_readback=current),
                export=dict(candidate_sha256=export['candidate_sha256'],native=export['native'],metrics=export['metrics'],current_readback=current_export),
                external_cost=timing(time_name),internal_workflow_sample={key:workflow[key]for key in
                    ['sampled_wall_seconds','sampled_full_cpu_seconds','publication_allowance_seconds']},
                route_compute={key:route.get(key)for key in ['wall_seconds','total_cpu_seconds','budget_seconds','cpu_budget_seconds']},
                export_compute={key:export.get(key)for key in ['wall_seconds','total_cpu_seconds','budget_seconds','cpu_budget_seconds']},
                raw_route_receipt=pin(workspace/'route/result.json'),raw_export_receipt=pin(workspace/'export/export.json'))
    negatives={}
    for number in ['001','002']:
        path=ROOT/('.runs/runtime009-duplicate-artwork-field-negative-'+number);record=read(path/'result.json');route=read(path/'route/result.json')
        require(record['tools']==route['tools']==tools and record['route']==route and route['accepted'] is False and
            record['process']['exit_code']==2 and record['process']['cleanup_complete'] is True,'negative record/process differs')
        source=Path(route['source']);require(p.tree_hash(source.parent)==record['source_hashes'],'negative owned source changed')
        original=Path(route_records['duplicate_artwork2Cu'][0]['source']) if number=='001' else Path(route_records['duplicate_artwork2Cu'][1]['candidate'])
        require(p.tree_hash(original.parent)==record['original_source_hashes'],'negative starting packet changed')
        source_tree=sx.read(source);restored=copy.deepcopy(source_tree);before_tree=sx.read(original)
        def fp(tree):return next(row for row in sx.children(tree,'footprint')if sx.unquote(sx.one(row,'uuid')[1])==record['ordinary_footprint_uuid'])
        def desc(tree):return next(row for row in sx.children(fp(tree),'property')if sx.unquote(row[1])=='Description')
        require(sx.unquote(desc(restored)[2])=='OWNED_INVALID_ORDINARY_DESCRIPTION','intended hidden field absent')
        desc(restored)[2]=desc(before_tree)[2]
        require(restored==before_tree and all(record['source_hashes'][n]==v for n,v in record['original_source_hashes'].items()if n!=source.name),
            'negative changed more than the one ordinary Description')
        p.check_resource_accounting(route)
        for name in ['source-drc','refill-drc','final-drc']:
            if not (path/'route'/(name+'-binding.json')).exists():continue
            binding=read(path/'route'/(name+'-binding.json'));step=next(row for row in route['steps']if row['name']==name)
            replay=f.check_drc_stage(path/'route',route,name,Path(binding['source']),Path(binding['input']),binding['saved'],binding['before'],
                schematic_parity='--schematic-parity'in step['argv'],sandboxed=step['argv'][:len(f.SANDBOX)]==f.SANDBOX)
            if name!='refill-drc':require(replay==route['native'if name=='final-drc'else'source_drc'],'negative retained DRC stage differs')
        ls.check_normal_policy(path/'route',route,max_bytes=128*1024**2,max_files=2048)
        if number=='001':
            require(record['status']=='failed' and record['controls_passed'] is False and record['error']=="KeyError: 'field_parity'" and
                route['status']=='rejected' and 'insufficient remaining budget'in route['reason'] and
                [row['name']for row in route['steps']]==['source-drc','export','obstacles'] and
                not (path/'route/final-drc.json').exists(),'first harness/budget failure changed')
            meaning='Failed harness: source Native DRC/export/obstacles ran; production refused engine/finalization reserve at30seconds, then harness expected absent source field_parity and raised KeyError. No engine, final Native field rejection or delivered candidate was demonstrated.'
        else:
            require(record['status']=='completed' and record['controls_passed'] is True and record['engine_executed'] is True and
                route['status']=='drc_rejected' and route['native']['field_parity']['qualification']==
                    {'qualified':False,'reason':'unqualified field mismatch: Description'} and not p.native_accepted(route['native']) and
                [route['native'][key]for key in ['opens','blocking','warnings','exclusions']]==[0,0,8,0],
                'actual final hidden-field rejection differs')
            candidate=Path(route['candidate']);packet(candidate.parent,'negatives/'+number+'/attempted-final-project')
            require(all(row in p.routes(sx.read(candidate))for row in p.routes(source_tree)), 'negative protected source route changed')
            meaning='Actual final hidden-Description rejection, starting from routed positive with all source copper protected and90second CLI budget. Engine executed and is counted; this is not a before-engine refusal or a delivered candidate.'
        packet(source.parent,'negatives/'+number+'/owned-source');stages(path/'route','negatives/'+number+'/stage-records')
        copies['negatives/'+number+'/harness-result.json']=path/'result.json'
        copies['negatives/'+number+'/route-result.json']=path/'route/result.json';copies['negatives/'+number+'/command.log']=path/'command.log'
        name='runtime009-duplicate-artwork-field-negative-'+number+'-wrapper'
        copies['negatives/'+number+'/external-time.log']=ROOT/timing(name)['log']['path']
        negatives[number]=dict(status=record['status'],controls_passed=record['controls_passed'],interpretation=meaning,
            error=record.get('error'),source_hashes=record['source_hashes'],starting_packet_hashes=record['original_source_hashes'],
            source_field_delta_exact=True,route_status=route['status'],accepted=False,route_reason=route.get('reason'),
            final_native=route.get('native'),steps=route['steps'],external_cost=timing(name),
            internal_sample={key:record[key]for key in ['wall_seconds','full_CPU_seconds']},process=record['process'],
            no_positive_export_created=not (path/'export').exists(),retained_receipt=pin(path/'result.json'))
    require(p.sha(ROOT/'experiments/stronger_incumbent_v1/global_width_fixture.py')==setup['duplicate_base_factory_sha256'] and
        p.sha(ROOT/'experiments/duplicate_artwork_fields_v1/fixture.py')==setup['duplicate_art_factory_sha256'],'owned factory pins changed')
    for name in ['prepare-runtime-directory-009.py','run-runtime-directory009-workflow.py','run-runtime009-improve-2cu.py',
        'run-runtime009-duplicate-artwork-workflow.py','runtime009-duplicate-artwork-field-negative-001.py','runtime009-duplicate-artwork-field-negative-002.py']:
        copies['source-as-run/'+name]=ROOT/'.runs'/name
    for name in ['scripts/qualify_runtime_workflow.py','experiments/stronger_incumbent_v1/global_width_fixture.py',
        'experiments/duplicate_artwork_fields_v1/fixture.py','experiments/four_copper_pour_support_v1/fixture.py']:
        copies['source-as-run/'+name.replace('/','--')]=ROOT/name
    setup_cost=timing('runtime-directory-009-preparation');copies['records/runtime-preparation-time.log']=ROOT/setup_cost['log']['path']
    result=dict(schema=1,kind='runtime009-three-owned-CLI-route-export-integration',source_head=head,artifact_id='runtime009',
        accepted=False,CLI_qualification_passed=True,actual_GUI=False,GUI060_qualification_included=False,
        human_PCB_review=False,physical_electrical_validation=False,whole_project_DRC_clean=False,
        runtime=str(RUNTIME),runtime_manifest=pin(RUNTIME/'runtime-distribution.json'),tools=tools,
        runtime_manifest_frozen_Git_42_implementation_pins_match=True,current_root_runtime_implementation_pins_match=not root_drift,
        current_root_drift=root_drift,immutable_artifact_file_count=len(manifest['immutable_files_sha256']),
        positives=positives,negative_attempts=negatives,runtime_setup_external_cost=setup_cost,
        runtime_setup_internal_sample={key:setup[key]for key in ['wall_seconds','full_CPU_seconds']},
        original_requirement_scope='Each accepted route and fresh export has its own original-rule Native refill/connectivity/fullSCH/field/invariant proof bound to its actual candidate. Complete selected owned original/final packets and raw Native evidence are public.',
        scope='Three exposed owned CLI-driven production workflows; duplicate-artwork is a supported prerequisite integration on an owned fixture variant, not a new independent circuit family or comparative routing gain.',
        costs_limits='All attempts, including failed001 and actual engine work in002, are retained with complete external wall/full CPU. Nested receipt/child samples must not be added. Authoring/review/full interactive costs remain unknown, not zero. No new external spending or paid services used.',
        metadata_limitation='Failed001 receipt labels schematic_parity checked by final native DRC although no final stage exists. Accepted=false/status=rejected and actual stage records control; this label is not treated as completed fullSCH proof.',
        curation_first_attempt=dict(status='refused before public writes',reason='Current root autorouter/gui.py differs from frozen installed009; corrected curation binds installed artifact and discloses root drift.',
            external_wall_seconds=0.29,external_full_CPU_seconds=0.23,raw_output_retained_in_notes='curation-first-attempt.log',Native_executed=False),
        curation_second_attempt=dict(status='controller error before public writes',reason='Controller assumed qualification driver was installed in runtime/scripts; driver is retained separately in repository.',
            external_wall_seconds=0.79,external_full_CPU_seconds=0.67,raw_output_retained_in_notes='curation-second-attempt.log',Native_executed=False),
        curation_third_attempt=dict(status='controller error before public writes',reason='Controller assumed process contained log path; CLI workflow records stage-relative log paths.',
            external_wall_seconds=2.90,external_full_CPU_seconds=2.71,raw_output_retained_in_notes='curation-third-attempt.log',Native_executed=False),
        curation_fourth_attempt=dict(status='controller assumption refused before public writes',reason='Improve2Cu retains one locked SIGNAL route; controller initially expected zero protected routes.',
            external_wall_seconds=6.19,external_full_CPU_seconds=5.93,raw_output_retained_in_notes='curation-fourth-attempt.log',Native_executed=False),
        limitations=['GUI060 is ongoing separately and excluded; CLI Request/Workflow/CliJob execution is not actual GUI observation.',
            'Final warnings are6/6/8 per route/export pair, with2original ignored checks and no exclusions. Native scope acceptance is not whole-project cleanliness or electrical/human approval.',
            'Same Mac, pinned production10.0.0/tools/cache and fixed path. No Windows/relocation/standalone, four-copper Improve, NetTie or class/hierarchy support expansion.',
            'Raw source/runtime/code/Native records are mutable local consistency evidence, not hostile-writer or power-loss authentication. Resource polling may overshoot; no OS aggregate quota.',
            'Only selected small raw files/owned CAD are copied. Large alias-geometry JSON files remain local and hash-pinned; all six complete shared positive readers validated them locally. No cache, complete code-tree, binary, third-party CAD or incidental Finder/browser content copied.',
            'Current root GUI source may differ from installed009, as explicitly hashed in current_root_drift. These results qualify only the frozen runtime009 artifact, not later GUI changes.',
            'No Native/JVM/GUI/full tests or backup execution during curation; no product/runtime/docs/HEAD edits or commit.'],
        related_duplicate_prerequisite_evidence=pin(ROOT/'evidence/duplicate-artwork-field-native-001.json'),
        omitted_large_local_raw_files=omitted,notes_directory=str(NOTES.relative_to(ROOT)),curation_source=pin(Path(__file__)),
        retained_files={name:dict(original=str(path.relative_to(ROOT)),sha256=p.sha(path),bytes=path.stat().st_size)for name,path in copies.items()},
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    require(p.tool_manifest()==tools and all(p.tree_hash(path)==hashes for path,hashes in source_witnesses.items()),'late runtime/source drift')
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0]=='autorouter'and getattr(module,'__file__',None):require(Path(module.__file__).resolve().is_relative_to(RUNTIME),'reader import escaped009')
    NOTES.mkdir()
    for name,path in copies.items():
        target=NOTES/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb')as handle:handle.write(io.read_bytes(path,2*1024**2))
        require(p.sha(target)==p.sha(path),'copied owned record differs')
    p.save_json(PUBLIC,result)
    print(json.dumps(dict(CLI_qualification_passed=True,current_positive_readers=6,retained_negative_attempts=2,
        actual_GUI=False,sha256=p.sha(PUBLIC),curation_wall_seconds=time.monotonic()-START)))

if __name__=='__main__':main()
