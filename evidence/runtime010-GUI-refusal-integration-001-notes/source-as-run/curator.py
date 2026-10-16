"""Read-only shared-reader curation of two completed runtime010 CLI workflows.

Writes only its selected public evidence/notes; no Native/JVM/test/GUI execution.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
from decimal import Decimal
import copy,datetime,hashlib,json,subprocess,sys,time
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'.runs/runtime-directory-010';RUNTIME=CASE/'runtime'
PUBLIC=ROOT/'evidence/runtime010-GUI-refusal-integration-001.json'
NOTES=ROOT/'evidence/runtime010-GUI-refusal-integration-001-notes'
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
    require(c.ROOT==RUNTIME and Path(sys.prefix).resolve()==RUNTIME/'.venv','installed010 reader context required')
    require(not PUBLIC.exists() and not NOTES.exists(),'fresh public destinations required')
    setup=read(CASE/'setup.json');manifest=read(RUNTIME/'runtime-distribution.json');tools=p.tool_manifest()
    head='5d85f5f146658aabe015ec468c07a9339e85e146'
    require(tools['git_head']==setup['source_head']==manifest['build_source']['git_head']==head,'source HEAD differs')
    require(len(tools['implementation_sha256'])==42 and p.sha(RUNTIME/'runtime-distribution.json')==setup['manifest_sha256'],'runtime module census/manifest differs')
    for name,digest in tools['implementation_sha256'].items():
        require(p.sha(RUNTIME/name)==manifest['immutable_files_sha256'][name]==digest,'runtime module changed: '+name)
        frozen=subprocess.run(['git','show',head+':'+name],cwd=ROOT,capture_output=True,timeout=10,check=True)
        require(hashlib.sha256(frozen.stdout).hexdigest()==digest,'source-as-built Git object differs: '+name)
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
    specs=[('route4Cu','qualification-route','enclosure-route',6,10,4,'runtime-directory010-workflow-route'),
        ('improve2Cu','qualification-improve-2cu','enclosure-improve-2cu',6,1,2,'runtime010-improve-2cu')]
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
    prior_path=ROOT/'evidence/runtime009-duplicate-artwork-integration-001.json';prior=read(prior_path)
    full143_path=ROOT/'evidence/gui-export-refusal-full143-001.json';full143=read(full143_path)
    GUI061_path=ROOT/'evidence/gui-runtime010-061-native-opening-001.json';GUI061=read(GUI061_path)
    old_pins=prior['tools']['implementation_sha256'];new_pins=tools['implementation_sha256']
    require(set(old_pins)==set(new_pins),'runtime009/010 implementation census differs')
    changed={name:dict(runtime009_sha256=old_pins[name],runtime010_sha256=new_pins[name])for name in new_pins if old_pins[name]!=new_pins[name]}
    require(set(changed)=={'autorouter/gui.py'}and prior['source_head']=='da2db9606027d9e430ff1e6f83b0e64f55d698c9',
        'expected actual GUI-only implementation difference from009 absent')
    require(full143['passed']is True and full143['source_head']==head and full143['runtime_code_sha256']==new_pins and
        GUI061['qualification_passed']is True and GUI061['source_head']==head and GUI061['tools']==tools,
        'linked source/full143/actualGUI061 pin differs')
    for name in ['prepare-runtime-directory-010.py','run-runtime-directory010-workflow.py','run-runtime010-improve-2cu.py']:
        copies['source-as-run/'+name]=ROOT/'.runs'/name
    for name in ['scripts/qualify_runtime_workflow.py','experiments/stronger_incumbent_v1/global_width_fixture.py',
        'experiments/four_copper_pour_support_v1/fixture.py']:
        copies['source-as-run/'+name.replace('/','--')]=ROOT/name
    setup_cost=timing('prepare-runtime-directory-010');copies['records/runtime-preparation-time.log']=ROOT/setup_cost['log']['path']
    copies['related/full143.json']=full143_path;copies['related/GUI061.json']=GUI061_path
    negative_history={number:dict(status=item['status'],controls_passed=item['controls_passed'],interpretation=item['interpretation'],
        external_cost=item['external_cost'],retained_in=pin(prior_path))for number,item in prior['negative_attempts'].items()}
    result=dict(schema=1,kind='runtime010-two-owned-CLI-route-export-regressions-after-GUI-refusal-correction',source_head=head,artifact_id='runtime010',
        accepted=False,CLI_qualification_passed=True,actual_GUI=False,actual_GUI061_evidence_separately_linked=True,
        human_PCB_review=False,physical_electrical_validation=False,whole_project_DRC_clean=False,
        runtime=str(RUNTIME),runtime_manifest=pin(RUNTIME/'runtime-distribution.json'),tools=tools,
        runtime_manifest_frozen_Git_42_implementation_pins_match=True,immutable_artifact_file_count=len(manifest['immutable_files_sha256']),
        actual_runtime009_to010_implementation_differences=changed,unchanged_implementation_files=41,
        positives=positives,runtime_setup_external_cost=setup_cost,
        runtime_setup_internal_sample={key:setup[key]for key in ['wall_seconds','full_CPU_seconds']},
        historical_runtime009_negative_attempts=negative_history,new_runtime010_negative_reruns=[],
        original_requirement_scope='Each accepted route and fresh export has its own original-rule Native refill/connectivity/fullSCH/field/invariant proof bound to its actual candidate. Selected complete owned original/final packets and all raw Native findings are public.',
        scope='Two exposed owned CLI-driven production regression workflows after a GUI-only refusal-diagnostic correction. Separate actual GUI061 covers the duplicate-artwork Finish gaps path; no third duplicate-artwork CLI rerun is claimed.',
        costs_limits='External complete wall/full CPU logs are retained for both workflows and setup. Nested child/receipt samples must not be added. Authoring/review and whole interactive GUI costs remain unknown, not zero. No new external spending or paid services used.',
        negative_scope='No new010 Description, short, fill, cancel or other invalid Native control rerun. Prior009 failed001 and actual final Description rejection002 remain linked historical evidence with their own costs and limitations.',
        limitations=['CLI Request/Workflow/CliJob execution is not actual GUI observation. GUI061 is separately linked with its historical pre-open export proof and natural stale refusal.',
            'Each route/export pair retains six Datasheet warnings, two original ignored checks and zero exclusions. Native routing scope acceptance is not whole-project cleanliness or electrical/human approval.',
            'Existing Mac, pinned production10.0.0/tools/cache and fixed path. No routing gain, new independent circuit family, Windows/relocation/standalone, four-copper Improve, NetTie or class/hierarchy support expansion.',
            'Mutable local consistency evidence is not hostile-writer or power-loss authentication. Resource polling may overshoot; no OS aggregate quota.',
            'Only selected small raw files/owned CAD are copied. Large alias-geometry JSON remains local and hash-pinned; all four complete current shared readers validated it locally. No cache, complete code-tree, binary, third-party CAD or incidental Finder/browser content copied.',
            'Frozen source is5d85; later current HEAD documentation/evidence changes are not used as runtime source identity.',
            'No Native/JVM/GUI/full tests or backup execution during curation; no product/runtime/docs/HEAD edits or commit.'],
        related_evidence=[pin(GUI061_path),pin(full143_path),pin(prior_path)],
        omitted_large_local_raw_files=omitted,notes_directory=str(NOTES.relative_to(ROOT)),curation_source=pin(Path(__file__)),
        retained_files={name:dict(original=str(path.relative_to(ROOT)),sha256=p.sha(path),bytes=path.stat().st_size)for name,path in copies.items()},
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    require(p.tool_manifest()==tools and all(p.tree_hash(path)==hashes for path,hashes in source_witnesses.items()),'late runtime/source drift')
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0]=='autorouter'and getattr(module,'__file__',None):require(Path(module.__file__).resolve().is_relative_to(RUNTIME),'reader import escaped010')
    NOTES.mkdir()
    for name,path in copies.items():
        target=NOTES/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb')as handle:handle.write(io.read_bytes(path,2*1024**2))
        require(p.sha(target)==p.sha(path),'copied owned record differs')
    p.save_json(PUBLIC,result)
    print(json.dumps(dict(CLI_qualification_passed=True,current_positive_readers=4,new_negative_attempts=0,
        actual_GUI=False,sha256=p.sha(PUBLIC),curation_wall_seconds=time.monotonic()-START)))

if __name__=='__main__':main()
