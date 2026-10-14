"""Bounded original-project observations using shared native/process validators.

No engine, routing, source mutation, production admission or physical approval.
The Devobordo observations already exist; do not rerun them to resume work.
"""
from pathlib import Path
import argparse,copy,fcntl,hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,sexpr as sx,floor_route as f,placement_clearance as io,handoff as h
from autorouter.runner import run
from experiments.placement_handoff_native_v1.driver import copy_bytes
LIMIT=20*1024**2;SECONDS=90
CASES={
    'cp2102-uart':('v8','CP2102.kicad_pcb','eecf7bb08afbd1494f3136a5124f4b6b6ea6c63e','.runs/licensed-acquisition-011-run-001/receipt.json'),
    'paw3395':('v2','paw3395.kicad_pcb','b71e346fc04ef18c26e0e8638ce0333395d41a14','.runs/licensed-acquisition-005-run-001/receipt.json'),
    'audio-player-my1690x':('portable-demo','Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pcb','49d66d63eb43105b7dbe437cc9299c637c69c61d',None),
    'navigation-switch':('portable-demo','Hardware/SparkFun_Qwiic_Navigation.kicad_pcb','b64c0dac2134d69963bf28120305bd79aad3c8ac',None),
    'uv-dosimeter':('portable-demo','hardware/AOL_PD_2.kicad_pcb','63153ac5ca9879299f57e3fb68df606bf78d96f8',None),
    'cellscan':('portable-demo','hardware/CellScan_Schematic.kicad_pcb','628c8a7d80f9de07c24d86102dfca9e353c038ce',None),
    'analog-filter':('portable-demo','kicad/analog_filter_module.kicad_pcb','6a34b221758fe32f33eca20d735e88028346753a',None),
    'interf_u':('managed-interf','interf_u.kicad_pcb','69cafb907ebc09e7722a2a464b1d466fc2e3608d',None),
    'arcdice':('arcdice-source','hardware/ArcDice.kicad_pcb','5908d99db1ef98b5996b380c75e5aee8bb8caaa6',None),
    'push-button-led':('v7','PushButtonLed.kicad_pcb','29c46b7c03d2afd9fe3a58fe2070309b12f94b42','.runs/licensed-acquisition-010-run-001/receipt.json'),
    'als311-clock':('v6','hardware/hardware.kicad_pcb','494ab6baf40746d313fe11379425900ebe97c319','.runs/licensed-acquisition-009-run-001/receipt.json'),
    'ardujoy-c64':('v4','Ardujoy_HW/Ardujoy_HW.kicad_pcb','1b63471d9726fb6a38f8544ca73ebf10c7f19820','.runs/licensed-acquisition-007-run-001/receipt.json'),
    'nus-usb-led':('v5','src/usb_led.kicad_pcb','ad3fbd582e3915b585c453ea202f591720a1f427','.runs/licensed-acquisition-008-run-001/receipt.json'),
}
REFILLED_ORIGINALS=frozenset({'cp2102-uart','paw3395','als311-clock','push-button-led','arcdice','interf_u','analog-filter','cellscan','uv-dosimeter','navigation-switch','audio-player-my1690x'})

def capture_interf_source():
    """Read the already acquired fixed complete project; never stage or fetch."""
    from data import fetch
    from scripts.experiment_quality import selected_source
    manifest=fetch.load_manifest()
    if manifest['commit']!=CASES['interf_u'][2]:raise p.Rejected('fixed interf source revision differs')
    board,_=selected_source('interf_u')
    rows=[row for row in manifest['files'] if row['project_id']=='kicad-interf-u']
    before=io.inventory(board.parent,max_bytes=LIMIT,max_files=64,max_entries=128)
    files={}
    for row in rows:
        source=fetch.safe_destination(row['destination'])
        relative=str(source.relative_to(board.parent))
        if relative in files:raise p.Rejected('duplicate interf source path')
        raw=io.read_bytes(source);fetch.verify_bytes(raw,row);files[relative]=raw
    expected={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}
    if (len(files)!=25 or sum(map(len,files.values()))!=1490971 or before!=expected
            or io.inventory(board.parent,max_bytes=LIMIT,max_files=64,max_entries=128)!=before
            or selected_source('interf_u')[0]!=board):
        raise p.Rejected('fixed complete interf source changed during capture')
    return files

def route_records(tree):
    result={}
    for row in p.routes(tree):
        identity=sx.one(row,'uuid')
        if identity is None or len(identity)!=2 or identity[1] in result:raise p.Rejected('missing or duplicated route UUID')
        result[identity[1]]=row
    return result

def completed_evidence(out):
    """Bound the finished native inputs, outputs and directories through publication.

    Publication files are already guarded by the shared publisher. Every
    completed candidate/context/process/log/report remains in this witness.
    """
    files,directories=io.inventory(out,max_bytes=LIMIT,max_files=2048,max_entries=4096,with_directories=True)
    files={name:digest for name,digest in files.items() if name not in {'result.json','result.json.partial'}
           and not name.startswith(('invalidated-result-','interrupted-result-'))}
    return {'files':files,'directories':list(directories)}

def experiment(project,output,*,run_native=False,protect_local_settings=False):
    if type(protect_local_settings) is not bool:raise p.Rejected('explicit local-settings guard flag required')
    if run_native is not True or project not in CASES:raise p.Rejected('explicit fixed source and --run-native required')
    started=time.monotonic();cpu0=time.process_time()+f.child_cpu();out=Path(output).absolute()
    if not out.is_relative_to(ROOT/'.runs') or '..' in out.parts or any(x.is_symlink() for x in (out,*out.parents)):raise p.Rejected('fresh canonical checkout output required')
    out.mkdir();owner={};h.capture_destination(owner,out);version,relative,commit,acquisition=CASES[project]
    def remaining():return min(SECONDS-(time.monotonic()-started),SECONDS-(time.process_time()+f.child_cpu()-cpu0))
    def size():return sum(len(x) for x in io.inventory(out,contents=True,max_bytes=LIMIT,max_files=2048,max_entries=4096).values())
    class BoundJob(f.FloorJob):
        def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
            if remaining()<=0:raise p.Rejected('whole original diagnostic budget exhausted')
            actual=[str(a) for a in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
            def execute():return run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=min(30,remaining()),env=self.env,max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
            step=protection=None
            try:
                if protect_local_settings and [str(x) for x in argv[:3]]==[str(c.CLI),'pcb','drc']:
                    from experiments.original_project_native_v1.local_settings import preserve
                    cleanup={'complete':False}
                    with preserve(Path(argv[-1]).with_suffix('.kicad_prl'),out,owner,cleanup_complete=lambda:cleanup['complete']) as protection:
                        step=execute();cleanup['complete']=step.get('cleanup_complete') is True
                else:step=execute()
            except (Exception,KeyboardInterrupt) as exc:
                if protection is not None:protection['guard_error']=type(exc).__name__+': '+str(exc)
                raise
            finally:
                # Retain the real process and protection outcome even when
                # restoration refuses or child cleanup was not confirmed.
                if step is not None:
                    if protection is not None:step['local_settings_protection']=protection
                    step['name']=name;self.steps.append(step);p.save_json(self.out/(name+'-process.json'),step)
            if step['status'] not in ('success','nonzero_exit') or step['exit_code'] not in allowed or step.get('cleanup_complete') is not True:raise p.Rejected('native stage failed: '+name)
            if remaining()<=0 or size()>LIMIT:raise p.Rejected('whole original diagnostic cap exceeded')
            return step
    record={'schema':1,'kind':'original_hardware_native_diagnostic','project':project,'accepted':False,'physical_electrical_validation':False,'status':'incomplete','budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_cap_bytes':LIMIT,'source_commit':commit,'routing_executed':False,'helper_sha256':p.sha(Path(__file__)),'protect_local_settings':protect_local_settings}
    before=files=job=completed=bound_native=None
    try:
        from importlib import import_module
        if version=='managed-interf':capture=capture_interf_source
        elif version=='portable-demo':
            from scripts.fetch_led_demo import capture_native_source,fixed_profile
            if fixed_profile(project)['commit']!=commit:raise p.Rejected('fixed original demo revision differs')
            capture=lambda:capture_native_source(project,root=ROOT)[1]
        else:capture=import_module('experiments.arcdice_native_class_v1.source' if version=='arcdice-source' else 'experiments.licensed_acquisition_'+version+'.native_snapshot').capture
        files=capture();copy_bytes(files,out/'original');before=p.tree_hash(out/'original');board=out/'original'/relative
        record.update(original_hashes=before,tools=p.tool_manifest())
        if project=='arcdice':
            record.update(source_origin='frozen public source lead; no managed acquisition or new download',
                source_metadata_sha256={name:p.sha(ROOT/'.runs/arcdice-native-class-scope-001'/name) for name in ('SOURCE_BINDINGS.json','inspection-001.json')},
                custom_asset_closure_qualified=False)
        elif version=='managed-interf':
            record.update(source_origin='already acquired fixed licensed KiCad demo; no new download',
                source_manifest_sha256=p.sha(ROOT/'data/sources.json'),source_file_count=len(files),source_bytes=sum(map(len,files.values())))
        elif version=='portable-demo':
            record.update(source_origin='verified fixed public demo originals and separate notice packet; no original diagnostic download',
                source_file_count=len(files),source_bytes=sum(map(len,files.values())),
                source_profile_id=project,custom_asset_closure_qualified=False)
        else:record['acquisition_receipt_sha256']=p.sha(ROOT/acquisition)
        code={n:io.read_bytes(ROOT/n) for n in record['tools']['implementation_sha256']}
        for relative in ('experiments/original_project_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py'):
            code[relative]=io.read_bytes(ROOT/relative)
        if protect_local_settings:
            relative='experiments/original_project_native_v1/local_settings.py';code[relative]=io.read_bytes(ROOT/relative)
        if project=='arcdice':
            for name in ('source.py','worker.py','PROTOCOL.json'):
                relative='experiments/arcdice_native_class_v1/'+name;code[relative]=io.read_bytes(ROOT/relative)
        if version=='managed-interf':
            for relative in ('data/fetch.py','data/sources.json','scripts/experiment_quality.py'):
                code[relative]=io.read_bytes(ROOT/relative)
        if version in ('v2','v8'):
            directory='experiments/licensed_acquisition_'+version+'/'
            for relative in (directory+'native_snapshot.py',directory+'protocol.json',
                    directory+'existing-data-inventory.json','experiments/licensed_acquisition_v1/fetch.py'):
                code[relative]=io.read_bytes(ROOT/relative)
        if version=='portable-demo':
            for relative in ('scripts/fetch_led_demo.py','experiments/licensed_acquisition_v1/fetch.py'):
                code[relative]=io.read_bytes(ROOT/relative)
        record['additional_implementation_sha256']={name:p.sha(ROOT/name) for name in code if not name.startswith('autorouter/')}
        for name,raw in code.items():
            committed=subprocess.run(['git','show',record['tools']['git_head']+':'+name],cwd=ROOT,capture_output=True,check=True,timeout=min(3,remaining())).stdout
            if raw!=committed:raise p.Rejected('commit exact native implementation before observations')
        copy_bytes(code,out/'code')
        # Observation of an original unsupported board does not admit it to
        # production routing. Keep its literal preflight refusal in evidence,
        # then inspect native behavior without changing any source constraint.
        try:
            record['static_supported']=p.preflight(board) is not None
        except p.Rejected as exc:
            record.update(static_supported=False,static_unsupported_reason=str(exc))
        job=BoundJob(out/'job',SECONDS,remaining)
        if project in REFILLED_ORIGINALS:
            # Narrow new original diagnostic: no solver/export or repeated
            # source baseline. Exact original-shell candidate, fresh saved fill
            # and complete finalSCH check. Native serialization differences
            # remain evidence; this branch never grants production support.
            import shutil
            if project=='arcdice':
                # One same-load export/parent observation, using the existing
                # context's before/after Source and native-state binding.
                class_source=job.out/'class-source';shutil.copytree(board.parent,class_source)
                context=job.out/'class-context.json';observation=job.out/'class-observation.json';dsn=job.out/'original.dsn'
                job.step('class-context',[c.PYTHON,ROOT/'experiments/arcdice_native_class_v1/worker.py',class_source/board.name,context,dsn,observation])
                observed=f.read_json(observation);native_context=f.read_json(context)
                if (observed['input_hashes_before']!=p.tree_hash(board.parent) or observed['input_hashes_after']!=observed['input_hashes_before']
                        or native_context['input_hashes_before']!=observed['input_hashes_before'] or observed['floor_context_sha256']!=p.sha(context)
                        or observed['dsn_sha256']!=p.sha(dsn) or observed['observation_before_export']!=observed['observation_after_export']):
                    raise p.Rejected('class observation/export Source binding differs')
                record.update(class_context_sha256=p.sha(context),class_observation_sha256=p.sha(observation),
                    original_dsn_sha256=p.sha(dsn),class_observation=observed['observation_before_export'],
                    class_transport_qualified=False,production_support_qualified=False)
            original=sx.read(board);saved=out/'saved';shutil.copytree(board.parent,saved);savedboard=saved/board.name;saved_before=p.tree_hash(saved)
            refill=job.drc('original-refill',savedboard,save=True)
            if f.check_drc_stage(job.out,{'steps':job.steps},'original-refill',savedboard,savedboard,True,saved_before)!=refill:raise p.Rejected('saved original native binding differs')
            emitted=sx.read(savedboard);record['native_saved_nonfill_ast_equal']=p.immutable(emitted)==p.immutable(original)
            record['native_saved_route_records_equal']=route_records(emitted)==route_records(original)
            candidate=out/'candidate'/board.name;shutil.copytree(board.parent,candidate.parent);sx.write(candidate,p.transplant_fill(original,emitted));candidate_before=p.tree_hash(candidate.parent)
            if p.immutable(sx.read(candidate))!=p.immutable(original) or route_records(sx.read(candidate))!=route_records(original):raise p.Rejected('original-shell constraints/protected routes changed')
            p.verify_candidate_files(candidate,p.tree_hash(board.parent),p.sha(candidate))
            final=job.drc('original-final',candidate,schematic_parity=True)
            if f.check_drc_stage(job.out,{'steps':job.steps},'original-final',candidate,job.out/'original-final-input'/board.name,False,candidate_before,schematic_parity=True)!=final:raise p.Rejected('final original native binding differs')
            p.verify_candidate_files(candidate,p.tree_hash(board.parent),p.sha(candidate));record.update(status='observed',original_native=refill,parity_native=final,
                final_candidate=str(candidate),final_candidate_sha256=p.sha(candidate),final_native_report_sha256=p.sha(job.out/'original-final.json'),
                original_shell_nonfill_ast_equal=True,all_original_route_records_exact=True,
                native_routing_scope_accepted=p.native_accepted(final),schematic_parity_findings=len(f.read_json(job.out/'original-final.json')['schematic_parity']),
                production_support_qualified=False,serialization_equivalence_qualified=False)
            return record
        record['original_native']=job.drc('original-drc',board)
        record['parity_native']=job.drc('parity-drc',board,schematic_parity=True)
        job.native('original-export','export',board,job.out/'original.dsn',job.out/'original-netclasses.json')
        job.native('original-metrics','metrics',board,job.out/'original-metrics.json');record['metrics']=f.read_json(job.out/'original-metrics.json')
        job.native('original-roundtrip','roundtrip',board,job.out/'roundtrip.kicad_pcb')
        original=sx.read(board);saved=sx.read(job.out/'roundtrip.kicad_pcb');record['native_saved_nonfill_ast_equal']=p.immutable(original)==p.immutable(saved)
        shell=p.transplant_routes(original,saved,protected=copy.deepcopy(p.routes(original)),policy='exact_non_uuid_lock_position_v2')
        record['original_shell_nonfill_ast_equal']=p.immutable(shell)==p.immutable(original)
        record['all_original_route_records_exact']=route_records(shell)==route_records(original)
        if not record['original_shell_nonfill_ast_equal'] or not record['all_original_route_records_exact']:raise p.Rejected('roundtrip original-shell preservation failed')
        record.update(status='observed',native_routing_scope_accepted=p.native_accepted(record['original_native']),schematic_parity_findings=len(f.read_json(job.out/'parity-drc.json')['schematic_parity']))
    except (Exception,KeyboardInterrupt) as exc:record.update(status='failed',error=type(exc).__name__+': '+str(exc))
    finally:
        if job is not None:record['steps']=job.steps
        if record.get('status')=='observed':
            def bound_native():
                if project in REFILLED_ORIGINALS:
                    if (p.sha(candidate)!=record['final_candidate_sha256'] or p.sha(job.out/'original-final.json')!=record['final_native_report_sha256']
                            or p.immutable(sx.read(candidate))!=p.immutable(sx.read(board))
                            or route_records(sx.read(candidate))!=route_records(sx.read(board))):
                        raise p.Rejected('completed original candidate/report binding changed')
                    p.verify_candidate_files(candidate,p.tree_hash(board.parent),record['final_candidate_sha256'])
                    for name,native_board,saved_flag,input_hashes,key in (
                            ('original-refill',savedboard,True,saved_before,'original_native'),
                            ('original-final',candidate,False,candidate_before,'parity_native')):
                        native_input=native_board if saved_flag else job.out/(name+'-input')/native_board.name
                        if f.check_drc_stage(job.out,{'steps':job.steps},name,native_board,native_input,saved_flag,input_hashes,schematic_parity=not saved_flag)!=record[key]:
                            raise p.Rejected('completed original native stage binding changed')
                    if project=='arcdice' and any(p.sha(path)!=record[key] for path,key in (
                            (context,'class_context_sha256'),(observation,'class_observation_sha256'),(dsn,'original_dsn_sha256'))):
                        raise p.Rejected('completed class observation/export changed')
                else:
                    for name,key,parity in (('original-drc','original_native',False),('parity-drc','parity_native',True)):
                        if f.check_drc_stage(job.out,{'steps':job.steps},name,board,job.out/(name+'-input')/board.name,False,p.tree_hash(board.parent),schematic_parity=parity)!=record[key]:
                            raise p.Rejected('completed original native stage changed')
            try:
                bound_native();completed=completed_evidence(out)
                record['completed_evidence_sha256']=hashlib.sha256(f.canonical(completed).encode()).hexdigest()
            except (Exception,KeyboardInterrupt) as exc:
                record.update(status='failed',native_routing_scope_accepted=False,error=type(exc).__name__+': '+str(exc))
        def stable():
            h.owned_destination(owner)
            if bound_native is not None:bound_native()
            if completed is not None and completed_evidence(out)!=completed:raise p.Rejected('completed native evidence changed')
            if p.sha(Path(__file__))!=record['helper_sha256']:raise p.Rejected('original diagnostic helper changed')
            if before is not None:
                if p.tree_hash(out/'original')!=before or capture()!=files:raise p.Rejected('original/acquired source changed')
            if record.get('tools') is not None and p.tool_manifest()!=record['tools']:raise p.Rejected('original diagnostic tool/code/HEAD changed')
            if any(p.sha(ROOT/name)!=digest for name,digest in record.get('additional_implementation_sha256',{}).items()):raise p.Rejected('additional original diagnostic implementation changed')
        def account():
            if before is not None:record.update(original_preserved=p.tree_hash(out/'original')==before,acquired_source_still_exact=capture()==files)
            record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu0,output_bytes=size())
            record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS and record['output_bytes']<=LIMIT
            if not record['within_budget'] or record.get('original_preserved') is not True or record.get('acquired_source_still_exact') is not True:record['status']='failed'
            if record['status']!='observed':record['native_routing_scope_accepted']=False
        f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner))
        try:
            stable();published=f.read_json(out/'result.json');account();stable()
            if published.get('status')=='observed' and (record['status']!='observed' or remaining()<=0):raise p.Rejected('final original diagnostic budget/source invalidated observation')
        except (Exception,KeyboardInterrupt) as exc:
            record.update(status='failed',native_routing_scope_accepted=False,error=type(exc).__name__+': '+str(exc))
            f.publish(out,record,lambda:(_ for _ in ()).throw(p.Rejected(record['error'])),account,remaining,owned=lambda:h.owned_destination(owner))
    return record

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=list(CASES),required=True);parser.add_argument('--output',required=True);parser.add_argument('--run-native',action='store_true');parser.add_argument('--protect-local-settings',action='store_true',help='Experimental Mac immutable PRL in owned native input copies; no field waiver');args=parser.parse_args()
    with (ROOT/'.runs/experiment.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.project,args.output,run_native=args.run_native,protect_local_settings=args.protect_local_settings)
    print(json.dumps({k:result.get(k) for k in ('status','error','native_routing_scope_accepted','schematic_parity_findings','metrics','wall_seconds','total_cpu_seconds','within_budget')}));return 0 if result['status']=='observed' else 2
if __name__=='__main__':raise SystemExit(main())
