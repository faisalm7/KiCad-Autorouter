"""Whole diagnostic flow with fake native/Git stages, real tiny controlled files."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys
from unittest import mock
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
SCRIPT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else BASE/'snapshot-001/driver.py'
OUT=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else BASE/'reproduction-001'
spec=importlib.util.spec_from_file_location('review_lipo',SCRIPT);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def case(name):
    base=OUT/name;base.mkdir(parents=True);(base/'.runs').mkdir();source=base/'source';source.mkdir()
    for path in (d.SOURCE,d.SOURCE.with_suffix('.kicad_pro')):shutil.copyfile(path,source/path.name)
    board=source/d.SOURCE.name;receipt=base/'acquisition.json';receipt.write_text('{"mocked_scope":true}')
    helper=base/'helper.py';helper.write_text('# tiny frozen helper\n')
    hashes=d.inventory(source);total=sum(p.stat().st_size for p in source.iterdir());out=base/'.runs/out'
    tools={'git_head':'synthetic-controlled-commit','implementation_sha256':{},'files':{}}
    mutation={};calls=[]
    def snapshot(out,tools,remaining):
        (out/'code').mkdir();shutil.copy2(helper,out/'code/helper.py');return {'helper.py':digest(helper)}
    def tool_manifest():
        if name=='late_source' and (out/'summary.json').exists() and not mutation:
            mutation.update(path=str(board),before=digest(board));board.write_bytes(board.read_bytes()+b'\n; late source change\n');mutation['after']=digest(board)
        return copy.deepcopy(tools)
    def run(argv,*,cwd,log,**kwargs):
        log=Path(log);log.write_text('synthetic native observation; no process executed\n');calls.append(argv)
        if log.stem=='observe':
            notes=d.source_notes(d.sx.read(board),d.read(board.with_suffix('.kicad_pro')))
            (out/'native.dsn').write_text('(pcb synthetic)')
            observation={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','mode':'export','source':str(out/'observe-input'/board.name),
                'board_sha256':hashes[board.name],'project_sha256':hashes[board.with_suffix('.kicad_pro').name],'dsn_sha256':digest(out/'native.dsn'),
                'input_hashes_before':hashes,'input_hashes_after':hashes,'limits':d.f.LIMITS,'board_saved':False,'routing_accepted':False,
                'pads':notes['source_pads_identity'],'routes':[{'uuid':uid} for uid in notes['source_route_ids']],
                'nets':[{'name':name} for name in notes['source_nonempty_nets']],
                'floors_nm':{'min_track_width':100000,'min_clearance':100000,'min_via_diameter':400000,'min_through_hole_diameter':200000,'min_via_annular_width':100000}}
            d.p.save_json(out/'observation.json',observation)
        elif log.stem=='original-drc':
            native={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':board.name,'violations':[],'unconnected_items':[],
                'schematic_parity':[],'ignored_checks':[],'included_severities':['error','warning','exclusion']}
            d.p.save_json(out/'original-drc.json',native)
            if name=='rebased_observation':
                path=out/'observation.json';raw=d.read(path);mutation.update(path=str(path),before=digest(path));raw['floors_nm']['min_clearance']=999999
                d.p.save_json(path,raw);mutation['after']=digest(path)
        else:raise AssertionError('unexpected stage')
        return {'status':'success','exit_code':0,'argv':argv,'cwd':str(cwd),'log':str(log),'cleanup_complete':True,'cpu_seconds':0.0,'monitor_cpu_seconds':0.0}
    original_drc_binding=d.drc_binding
    def drc_hook(*args):
        value=original_drc_binding(*args)
        if name=='capture_drc_binding' and not mutation:
            path=out/'original-drc.json';raw=d.read(path);mutation.update(path=str(path),before=digest(path))
            raw['date']='controlled change after first DRC binding';d.p.save_json(path,raw);mutation['after']=digest(path)
        return value
    original_read=d.read
    def read_hook(path):
        value=original_read(path)
        if name=='capture_observation' and Path(path)==out/'observation.json' and not mutation:
            changed=copy.deepcopy(value);changed['floors_nm']['min_clearance']=999999
            mutation.update(path=str(path),before=digest(Path(path)));d.p.save_json(Path(path),changed);mutation['after']=digest(Path(path))
        return value
    with mock.patch.object(d,'drc_binding',side_effect=drc_hook),mock.patch.object(d,'read',side_effect=read_hook),mock.patch.object(d,'ROOT',base),mock.patch.object(d,'SOURCE',board),mock.patch.object(d,'RECEIPT',receipt),mock.patch.object(d,'RECEIPT_SHA',digest(receipt)),\
         mock.patch.object(d,'source_binding',return_value=(hashes,total)),mock.patch.object(d,'snapshot',side_effect=snapshot),\
         mock.patch.object(d.p,'tool_manifest',side_effect=tool_manifest),mock.patch.object(d.p,'check_storage',return_value=0),mock.patch.object(d,'run',side_effect=run):
        result=d.experiment(out,run_native=True)
    saved=d.read(out/'summary.json');observed=d.read(out/'observation.json')
    return {'case':name,'observations_complete':saved['observations_complete'],'status':saved['status'],'error':saved.get('error'),
        'reported_drc_sha256':saved.get('native_binding',{}).get('report_sha256'),'actual_drc_sha256':digest(out/'original-drc.json') if (out/'original-drc.json').exists() else None,
        'reported_observation_sha256':saved.get('observation_sha256'),'actual_observation_sha256':digest(out/'observation.json'),
        'reported_floor':saved.get('native_effective_floors_nm',{}).get('min_clearance'),'actual_floor':observed['floors_nm']['min_clearance'],
        'reported_original_unchanged':saved.get('original_inputs_unchanged'),'actual_source_unchanged':d.inventory(source)==hashes,
        'mutation':mutation,'mock_native_stages':len(calls),'actual_native_processes':0,
        'expected_complete':name=='unchanged','expectation_satisfied':saved['observations_complete']==(name=='unchanged')}
OUT.mkdir(exist_ok=False)
rows=[case(name) for name in ('unchanged','rebased_observation','capture_observation','capture_drc_binding','late_source')]
summary={'script_sha256':digest(SCRIPT),'scope':'Pure whole-flow reproduction with copied original PCB/project bytes only; source/commit/tool/native operations are mocked. No native/Git/engine/network processes.','rows':rows,'all_expected':all(r['expectation_satisfied'] for r in rows)}
(OUT/'review.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
