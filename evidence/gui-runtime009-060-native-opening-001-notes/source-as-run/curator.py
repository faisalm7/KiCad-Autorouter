"""Curate saved GUI060 using GUI059's shared-reader pattern; no Native rerun.

Only this controller and selected public evidence/notes are written. Stale
opened export material remains untouched. SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
from decimal import Decimal
import datetime,hashlib,json,sys,time
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'.runs/runtime-directory-009/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,review_export as ex,placement_clearance as io,sexpr as sx,config as c,floor_route as f
base=runtime/'.runs/gui-session060'
workspace=base/'jobs/autorouter-gui-9b9f23662c8f49f2b0f4103d75063e7e'
PUBLIC=ROOT/'evidence/gui-runtime009-060-native-opening-001.json'
NOTES=ROOT/'evidence/gui-runtime009-060-native-opening-001-notes'
LAYERS=['F.Cu','B.Cu']

def read(path):return f.read_json(Path(path))
def pin(path):
    path=Path(path);return dict(path=str(path.relative_to(ROOT)),sha256=p.sha(path),bytes=path.stat().st_size)
def require(condition,reason):
    if not condition:raise p.Rejected(reason)
def timing(path):
    values={k:Decimal(v)for k,v in(line.split()for line in path.read_text().splitlines())}
    require(set(values)=={'real','user','sys'},'external timing schema differs')
    return dict(wall_seconds=float(values['real']),full_CPU_seconds=float(values['user']+values['sys']),log=pin(path))
def cli_stage(path):
    value=read(path);log=path.with_name(path.name[:-len('.process.json')]+'.log');raw=io.read_bytes(log,512*1024)
    require(type(value.get('exit_code'))is int and value.get('cancel_requested')is False and
        value.get('log_truncated')is False and value.get('log_bytes')==len(raw) and
        value.get('cleanup_scope')=='CLI existing workers; UI does not certify descendant cleanup' and
        type(value.get('wall_seconds'))in(int,float)and value['wall_seconds']>=0,'actual CliJob process/log schema differs')
    return dict(process=pin(path),log=pin(log),argv=value['argv'],exit_code=value['exit_code'],wall_seconds=value['wall_seconds'],
        cancel_requested=False,log_truncated=False,cleanup_scope=value['cleanup_scope'])
def geometry(source,candidate,protected):
    tree=sx.read(candidate)
    require(p.immutable(source)==p.immutable(tree)and sx.one(tree,'layers')==sx.one(source,'layers'),
        'original invariant AST/physical-display layer table differs')
    require(len(protected)==1 and all(p.locked(row)and row in p.routes(tree)for row in protected),'one exact protected route required')
    source_pads=[(sx.one(fp,'uuid'),sx.children(fp,'pad'))for fp in sx.children(source,'footprint')]
    candidate_pads=[(sx.one(fp,'uuid'),sx.children(fp,'pad'))for fp in sx.children(tree,'footprint')]
    require(source_pads==candidate_pads and len(source_pads)==8 and sum(len(rows)for _,rows in source_pads)==6,
        'complete eight-footprint/six-pad geometry differs')
    return dict(full_source_invariant_AST_exact=True,complete_layer_table_exact=True,source_pad_census_exact=True,
        footprints=8,pads=6,physical_copper_layers=LAYERS,protected_route_count=len(protected))
def retained_native(folder,data,*,exported):
    stages={}
    for name in ['refill-drc','final-drc']:
        binding=read(folder/(name+'-binding.json'));step=next(row for row in data['steps']if row['name']==name)
        stages[name]=f.check_drc_stage(folder,data,name,Path(binding['source']),Path(binding['input']),binding['saved'],binding['before'],
            schematic_parity=name=='final-drc',sandboxed=exported)
    native=stages['final-drc'];proof=read(folder/'final-drc-fields-proof.json');fields=proof['qualification'];census=proof['board_only_field_census']
    require(native==data['native']and p.native_accepted(native)and
        [native[k]for k in ['opens','blocking','warnings','exclusions']]==[0,0,8,0]and len(native['ignored_checks'])==2,
        'own final original-rule Native findings differ')
    require(fields['qualified']is True and fields['component_count']==6 and fields['compared_field_count']==18 and len(fields['warning_uuids'])==6 and
        census['policy']=='source-bound-padless-field-census-v2'and census['complete_footprint_count']==8 and census['compared_footprint_count']==6 and
        census['duplicate_artwork_reference_groups']==[dict(folded_reference='g***',uuids=['484f77d7-9568-5f0e-b158-10562d44e148','c5ce1923-2b0b-541a-be1b-0213cc622101'])],
        'own complete duplicate-artwork/ordinary field proof differs')
    return dict(refill=stages['refill-drc'],final_native=native,field_proof=pin(folder/'final-drc-fields-proof.json'))

def main():
    require(c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv','installed009 reader context required')
    require(not PUBLIC.exists()and not NOTES.exists(),'fresh curation destinations required')
    setup=read(runtime.parent/'setup.json');launch=read(base/'launch.json');pre=read(base/'preopen-001.json')
    observations=read(base/'observations-001.json');snapshot=Path(pre['snapshot']);initial=dict(pre['snapshot_hashes'])
    tools=p.tool_manifest();original=Path(launch['source']);source=sx.read(original)
    require(tools['git_head']==setup['source_head']==launch['source_git_head']==observations['source_head']==
        'da2db9606027d9e430ff1e6f83b0e64f55d698c9','source-as-built identity differs')
    require(p.tree_hash(original.parent)==launch['source_sha256']==setup['duplicate_artwork_source_hashes'],'owned source changed')
    require(tools==launch['launcher']['tools']and p.sha(runtime/'runtime-distribution.json')==setup['manifest_sha256']and
        p.sha(runtime/'autorouter/gui.py')==launch['gui_sha256'],'installed source/tool/GUI pins differ')
    route_path=workspace/'route/result.json';export_path=workspace/'export/export.json';gr=read(route_path);ge=read(export_path);exportpin=p.sha(export_path)
    require(p.tree_hash(snapshot)==initial and len(initial)==87 and p.sha(snapshot/'export.json')==exportpin,'87-file pre-open snapshot changed')
    require(pre['source_unchanged']is True and pre['route']['current']is True and pre['export']['current']is True and pre['human_review']is False,
        'saved fresh pre-open reader proof incomplete')
    require(gr['accepted']is True and ge['export_accepted']is True and ge['status']=='export_validated'and
        gr['tools']==ge['tools']==tools,'accepted original runtime proof differs')
    p.check_resource_accounting(ge,child_key='child_step_cpu_seconds')
    with p.validation_readback_session():
        route_check=p.check_result(route_path);binding,original_report=ex.bind(ge['inputs']['choice'])
        require(route_check['current']is True and binding==ge['inputs']and original_report==gr,'route/review/choice lineage differs')
        try:ex.check_export(export_path)
        except p.Rejected as exc:stale=str(exc)
        else:raise p.Rejected('opened export unexpectedly current')
        require(stale=='export inputs/runtime/evidence changed','unexpected current export refusal')
        route_native=retained_native(workspace/'route',gr,exported=False)
        export_native=retained_native(workspace/'export/validation',ge,exported=True)
    after=p.tree_hash(workspace/'export');changes=dict(added=sorted(set(after)-set(initial)),removed=sorted(set(initial)-set(after)),
        changed=sorted(k for k in set(initial)&set(after)if initial[k]!=after[k]))
    require(any(changes.values()),'natural post-open material change absent')
    for name,digest in initial.items():
        if not name.startswith('validation/candidate/'):require(after.get(name)==digest,'noncandidate evidence changed: '+name)
    for suffix in ['.kicad_pcb','.kicad_sch']:
        name='validation/candidate/'+original.with_suffix(suffix).name
        require(after.get(name)==initial[name],'opened board/schematic changed')
    protected=p.protected_for_record(gr,source);candidate=Path(gr['candidate']);frozen=snapshot/'validation/candidate'/original.name
    require(p.sha(candidate)==gr['candidate_sha256']==ge['candidate_sha256']==p.sha(frozen)==pre['export']['candidate_sha256'],
        'own candidate lineage differs')
    shape=geometry(source,candidate,protected)
    require(shape==geometry(source,frozen,protected)and p.routes(sx.read(candidate))==p.routes(sx.read(frozen)),'pre-open candidate geometry differs')
    require(gr['metrics']==ge['metrics']and ge['metrics']['copper_layers']==2 and ge['metrics']['pads']==6 and
        ge['metrics']['footprints']==8 and ge['metrics']['zones']==1 and
        gr['schematic_parity']==ge['schematic_parity']=='checked by final native DRC','fullSCH/physical census differs')
    normalized={}
    for suffix in ['.kicad_pro','.kicad_prl']:
        name='validation/candidate/'+original.with_suffix(suffix).name;old=read(snapshot/name);new=read(workspace/'export'/name)
        normalized[suffix]=dict(preopen_sha256=initial[name],postopen_sha256=after[name],changed=initial[name]!=after[name],
            added_top_level_json_keys=sorted(set(new)-set(old)),changed_top_level_json_keys=sorted(k for k in set(old)&set(new)if old[k]!=new[k]),
            effective_equivalence_claimed=False)
    preview=read(workspace/'preview.command.log');review=read(workspace/'review/review.json');choice=read(workspace/'choice/choice.json')
    require(preview['existing_route_items']==preview['protected_route_items']==1 and preview['rerouted_route_items']==0 and
        preview['copper_layers']==LAYERS and preview['effective_preferences']==gr['routing_preferences']['effective'],
        'actual preview/preferences differ')
    require(review['preview']['layers']==LAYERS and choice['choice']=='accept'and choice['human_pcb_approval_observed']is False and
        choice['applied']is False and ge['native_validation_performed']is True and ge['human_pcb_approval_observed']is False,
        'review/test-intent/export flags differ')
    for name,digest in review['preview']['files'].items():require(p.sha(workspace/'review'/name)==digest,'preview changed: '+name)
    saved=base/'inspection/gui060-protected90-retry.json'
    require(saved.stat().st_size==194 and read(saved)==read(workspace/'settings.json')and
        read(saved)['seconds']==90,'actual saved 194-byte preference values differ')
    stages=[cli_stage(path)for path in sorted(workspace.glob('*.command.process.json'))];checks=[]
    for path in sorted(workspace.glob('inspect-export-*.command.log')):
        value=read(path);process=cli_stage(path.with_suffix('.process.json'))
        require(process['argv'][-2:]==['review-export-check',str(export_path)]and process['exit_code']==(0 if value['current']else 2),
            'actual Open checked export reader/status differs')
        checks.append(dict(receipt=pin(path),process=process,current=value['current'],reason=value.get('reason')))
    require(len(stages)==8 and len(checks)==2 and sum(x['current']is True for x in checks)==1 and
        sum(x['current']is False for x in checks)==1,'actual eight CLI journals/current-stale pair differs')
    for row in stages:
        if row['exit_code']!=0:require('inspect-export-'in Path(row['process']['path']).name and row['exit_code']==2,'unexpected GUI command failure')
    verify=read(workspace/'verify_export.command.log')
    require(verify['current']is True and verify['candidate_sha256']==ge['candidate_sha256'],'saved fresh export verification differs')
    copies={'source-as-run/curator.py':Path(__file__),'source-as-run/prepare-gui-runtime009-060.py':ROOT/'.runs/prepare-gui-runtime009-060.py',
        'source-as-run/gui060-preopen-001.py':ROOT/'.runs/gui060-preopen-001.py','LICENSE':ROOT/'LICENSE',
        'records/launch.json':base/'launch.json','records/preopen-001.json':base/'preopen-001.json','records/observations-001.json':base/'observations-001.json',
        'records/runtime-distribution.json':runtime/'runtime-distribution.json','records/settings.json':workspace/'settings.json',
        'records/saved-gui060-protected90-retry.json':saved,'records/route-result.json':route_path,'records/review.json':workspace/'review/review.json',
        'records/choice.json':workspace/'choice/choice.json','timing/preopen-time.log':ROOT/'.runs/gui060-preopen-001-time.log',
        'timing/preparation-time.log':ROOT/'.runs/gui-runtime009-060-preparation-time.log',
        'timing/preopen-command.log':ROOT/'.runs/gui060-preopen-001-command.log','timing/preparation-command.log':ROOT/'.runs/gui-runtime009-060-preparation-command.log'}
    for name in initial:copies['preopen-export/'+name]=snapshot/name
    for destination,folder in [('original-source',original.parent),('route-final-project',candidate.parent)]:
        for name in io.inventory(folder,contents=True,max_bytes=16*1024**2,max_files=40,max_entries=80):copies[destination+'/'+name]=folder/name
    omitted=[]
    for path in sorted((workspace/'route').iterdir()):
        if path.is_file()and path.suffix in {'.json','.log','.net','.dsn','.ses','.kicad_pcb'}:
            if path.stat().st_size<=256*1024:copies['route-stage-records/'+path.name]=path
            else:omitted.append(pin(path))
    for path in (workspace/'route/refill').glob('*.kicad_pcb'):copies['route-stage-records/native-saved-refill.kicad_pcb']=path
    for path in workspace.glob('*.command.*'):
        if path.is_file():copies['GUI-command-records/'+path.name]=path
    record=dict(schema=1,kind='actual-runtime009-GUI060-duplicate-artwork-route-export-opening-and-stale-refusal',accepted=False,qualification_passed=True,
        qualification_scope='Owned two-copper duplicate-artwork Finish gaps GUI route/review/fresh Native export/opening before natural staleness; actual inline generic refusal retained.',
        actual_GUI=True,human_review=False,physical_electrical_validation=False,GUI_DRC_performed=False,live_apply=False,
        GUI_route_export_open_passed=True,natural_stale_reader_passed=True,visual_generic_stale_refusal_observed=True,
        source_head=tools['git_head'],tools=tools,runtime_manifest=pin(runtime/'runtime-distribution.json'),source_hashes=launch['source_sha256'],source_unchanged=True,
        route_receipt=pin(route_path),route_current_readback=route_check,export_receipt=pin(export_path),preopen_export_accepted=True,export_current=False,current_export_refusal=stale,
        candidate_sha256=gr['candidate_sha256'],native=ge['native'],metrics=ge['metrics'],geometry=shape,route_own_native=route_native,
        preopen_export_retained_shared_stages=export_native,
        preopen_export_proof_scope='Historical87-file pre-open proof plus current retained shared refill/final DRC readers with original absolute input/process/report/field bindings. Opened candidate PRO/PRL are stale; no current export acceptance or class-equivalence claim.',
        preopen=pin(base/'preopen-001.json'),preopen_snapshot_hashes=initial,post_open_changes=changes,post_open_project_normalization=normalized,
        project_settings_effective_equivalence_claimed=False,whole_project_DRC_clean=False,
        observations=observations,observations_provenance='Retained lead direct CUA observations; curator performed no GUI operation.',
        inspection_readers=checks,CLI_stages=stages,preview_file_count=len(review['preview']['files']),
        settings_roundtrip=dict(saved_file=pin(saved),settings_values_equal_actual_job=True,settings_bytes_equal_actual_job=False,
            serialization_note='Saved and job JSON have different key order; all parsed preferences match.',display_changed_75_then_Load_restored_90='lead actual CUA observation',
            first_picker_attempt='Failed navigation retained in observations; chooser retained inspection PRO, so this is not demonstrated JSON serialization failure.',
            feedback_limitation='Prior refusal text persisted until next Preview.'),
        stage_compute={name:{k:value.get(k)for k in ['wall_seconds','total_cpu_seconds','budget_seconds','cpu_budget_seconds']}for name,value in
            [('route',gr),('rendered_review',review),('test_intent',choice),('fresh_export',ge)]},
        preopen_external_cost=timing(ROOT/'.runs/gui060-preopen-001-time.log'),preparation_external_cost=timing(ROOT/'.runs/gui-runtime009-060-preparation-time.log'),
        interactive_whole_wall_seconds=None,interactive_full_CPU_seconds=None,
        source_as_built_scope='Immutable runtime009 da2; later root GUI correction is not qualified by009. Frozen implementation/source/manifest pins are retained in launch and preopen code.',
        related_evidence=[pin(ROOT/'evidence/runtime009-duplicate-artwork-integration-001.json'),pin(ROOT/'evidence/duplicate-artwork-field-native-001.json')],
        limitations=['Owned exposed fixture on existing Mac/apps/cache/fixed path; no routing gain, new circuit family or generalized support claim.',
            'Eight warnings: six ordinary Datasheet warnings plus two artwork missing-courtyard warnings; two original ignored checks remain, zero exclusions. Whole-project cleanliness is false.',
            'Full interactive/UI-idle wall and full CPU are unknown; CLI stage/Native receipt/preparation/preopen samples are separate and must not be added as a whole-interactive benchmark.',
            'Software-test accept intent is not human PCB approval. No new cancel/reject-intent/live apply/undo/unsaved-buffer/GUI DRC or physical/electrical qualification.',
            'Opened export project normalization is retained by hashes only. No repair, archive inspection, current effective class equivalence or accepted current export is claimed.',
            'Generic inline refusal and prior settings-refusal text persisted in actual009 UX. Specific stale reason exists in command log; later GUI correction requires separate qualification.',
            'Selected owned originals/finals and entire preopen snapshot are copied. Large route alias-geometry JSON is hash-pinned/local; current route shared reader validated it. No binaries/caches/incidental Finder or browser content.',
            'No Native/JVM/test/GUI rerun, source/runtime/docs/HEAD edit or commit during curation. No new external spending or paid services used.'],
        curation_first_attempt=dict(status='controller assumption refused before public writes',reason='Saved and job JSON key order differs; corrected controller compares parsed preference values, retaining both actual byte hashes.',
            external_wall_seconds=2.20,external_full_CPU_seconds=2.06,raw_output_retained_in_notes='curation-first-attempt.log',Native_executed=False),
        omitted_large_local_raw_files=omitted,curation_source=pin(Path(__file__)),notes_directory=str(NOTES.relative_to(ROOT)),
        retained_files={name:dict(original=str(path.relative_to(ROOT)),sha256=p.sha(path),bytes=path.stat().st_size)for name,path in copies.items()},
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    require(p.tree_hash(snapshot)==initial and p.sha(export_path)==exportpin and p.tree_hash(original.parent)==launch['source_sha256']and
        p.tree_hash(workspace/'export')==after and p.tool_manifest()==tools,'late original/runtime/proof drift')
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0]=='autorouter'and getattr(module,'__file__',None):require(Path(module.__file__).resolve().is_relative_to(runtime),'reader import escaped009')
    NOTES.mkdir()
    for name,path in copies.items():
        target=NOTES/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb')as handle:handle.write(io.read_bytes(path,2*1024**2))
        require(p.sha(target)==p.sha(path),'copied record differs')
    p.save_json(PUBLIC,record)
    print(json.dumps(dict(GUI_route_export_open_passed=True,natural_stale_reader_passed=True,source_unchanged=True,export_current=False,
        preopen_files=len(initial),public_sha256=p.sha(PUBLIC),curation_wall_seconds=time.monotonic()-START)))

if __name__=='__main__':main()
