"""One fresh0174Cu six-stage CLI workflow; source-only before lead qualification.

Reuses016's Request/Workflow/CliJob sequence and unchanged shipped validators.
The owned matching source,10 protected items,4Cu,3zones and90s settings are fixed.
No actual GUI, new family, physical approval or routing improvement is claimed.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,importlib.util,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,gui,handoff as h,review_export as ex,local_settings as ls,schematic_field_evidence as fields,schematic_class_evidence as classes
SHARED_PIN='c412dc76a66bea20b52a071ce6b0de255047d817f5c432a3dbc7d287dc81e12e'
KIND='installed-runtime017-production-four-cu-v1'
SETTINGS=dict(schema=1,seconds=90,scope='whole_board_unlocked_routing',layers='source_all',adapter='both',guidance='native',profile='standard',scoring_preference=None)

def require(value,reason):
    if not value:raise p.Rejected(reason)

def execute(protocol,pin):
    plan=f.read_json(protocol)
    require(p.sha(protocol)==pin and plan.get('status')=='frozen' and plan.get('kind')=='runtime017-four-cu-production-protocol-v1'
        and plan['settings']==SETTINGS,'exact frozen017 protocol/settings required')
    require(c.ROOT==ROOT==Path(plan['runtime']) and Path(sys.prefix).resolve()==ROOT/'.venv'
        and p.sha(Path(__file__))==plan['child_sha256'],'exact installed017 runtime/child required')
    shared_path=Path(plan['shared_pair_helper']);require(p.sha(shared_path)==plan['shared_pair_helper_sha256']==SHARED_PIN,'frozen shared pair helper changed')
    spec=importlib.util.spec_from_file_location('frozen_pair_helpers017',shared_path);shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
    require(p.sha(shared_path)==SHARED_PIN,'shared helper changed during import')
    tools=p.tool_manifest();require(tools==plan['runtime_tools'] and shared.coordinator_python_context()==plan['runtime_python'],'actual installed017 tools/Python differ')
    require(sys.version_info[:2]==(3,11),'actual Python3.11 required')
    helper=Path(plan['signal_bridge_controller']);require(p.sha(helper)==plan['signal_bridge_sha256'],'frozen queued bridge required')
    spec=importlib.util.spec_from_file_location('frozen_queued_bridge017',helper);bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    out=ROOT/'.runs/production-delivery-001';out.mkdir();owner={};h.capture_destination(owner,out)
    source=out/'source';source.mkdir()
    for name,text in plan['fixture_files'].items():
        require(Path(name).name==name and type(text)is str,'flat exact owned source required')
        with (source/name).open('xb')as stream:stream.write(text.encode())
    name=plan['board_name'];require(type(name)is str and Path(name).name==name and name.endswith('.kicad_pcb'),'exact owned PCB required')
    board=source/name;hashes=p.tree_hash(source);require(hashes==plan['fixture_sha256'],'owned matching4file packet changed')
    original=p.sx.read(board);protected_source=p.routes(original)
    layers=[p.sx.unquote(row[1])for row in p.sx.one(original,'layers')[1:]if isinstance(row,list)and len(row)>2 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',p.sx.unquote(row[1]))]
    require(layers==['F.Cu','In1.Cu','In2.Cu','B.Cu'] and len(p.sx.children(original,'zone'))==3
        and len(protected_source)==10 and all(p.locked(row)for row in protected_source),'exact protected10/4Cu/3zone source differs')
    jobs=out/'jobs';jobs.mkdir();flow=gui.Request(str(board),str(jobs),json.dumps(plan['settings']),True).prepare();job=gui.CliJob()
    record=dict(schema=1,kind=KIND,accepted=False,passed=False,status='failed',actual_GUI=False,human_review=False,
        source_head=plan['source_head'],tools=tools,python_context=shared.coordinator_python_context(),workspace=str(flow.workspace),protocol_sha256=pin,processes=[],
        accounting_point='Inner pre-final-publication sample; reaped outer and external260s whole wall/fullCPU remain mandatory.',
        qualification='One fresh017 installed4Cu CLI workflow through unchanged GUI model; same exposed owned matching family, no016rerun/newfamily/quality gain/actualGUI/human approval claim.')
    def remaining():return min(238-(time.monotonic()-START),238-(cpu()-CPU0))
    def stable():
        live();h.owned_destination(owner)
        require(p.sha(protocol)==pin and p.sha(Path(__file__))==plan['child_sha256'] and p.sha(shared_path)==SHARED_PIN
            and p.sha(helper)==plan['signal_bridge_sha256'] and p.tool_manifest()==tools
            and shared.coordinator_python_context()==plan['runtime_python'] and p.tree_hash(source)==hashes,'runtime/Python/protocol/source changed')
        flow.fresh();live()
    def qualify():
        route,export=flow.records['route'],flow.records['export']
        require(flow.records['verify_export'].get('current')is True and route['source']==str(board) and route['source_hashes']==hashes,
            'real final export/current source lineage required')
        require(route.get('native_edge_admission_policy')=='known-named-whole-native-edge-v1','actual captured-producer receipt marker differs')
        require(route.get('schematic_parity')==export.get('schematic_parity')=='checked by final native DRC','complete schematic final proof required')
        require(type(route.get('schematic_class_task'))is dict and type(route.get('schematic_class_final'))is dict
            and type(export.get('schematic_class_final'))is dict,'required task/final class proof missing')
        protected=p.protected_for_record(route,original);require(protected==protected_source,'protected copper prediction differs')
        proof=[]
        for stage,data,folder in [('route',route,flow.workspace/'route'),('export',export,flow.workspace/'export/validation')]:
            native=data['native'];candidate=Path(data['candidate']);tree=p.sx.read(candidate)
            require(p.native_accepted(native) and [native[key]for key in('opens','blocking','warnings','exclusions')]==[0,0,6,0]
                and native['ignored_checks']==plan['expected_ignored_checks']
                and sorted(f.canonical(row)for row in native['findings']if row['severity']=='warning')==plan['expected_warning_rows'],
                'own original fullNative findings/ignored checks differ')
            require(data['metrics']['version']=='10.0.0' and data['metrics']['copper_layers']==4 and data['metrics']['zones']==3
                and p.immutable(tree)==p.immutable(original) and all(row in p.routes(tree)for row in protected),'candidate original4Cu/zone/protected design differs')
            mapping=f.read_json(folder/'final-netclasses.json');audit=p.audit_candidate_netclasses(candidate,protected,mapping)
            audit['native_map_file_sha256']=p.sha(folder/'final-netclasses.json')
            require(audit==f.read_json(folder/'final-netclass-audit.json')and audit['route_dimensions']['checked']['protected']==10,'own class/dimension proof differs')
            proof.append(dict(stage=stage,candidate_sha256=data['candidate_sha256'],native=native,metrics=data['metrics'],class_audit=audit,
                schematic_class_final=data['schematic_class_final'],final_native_sha256=p.sha(folder/'final-drc.json'),map_sha256=p.sha(folder/'final-netclasses.json'),
                sample_wall_seconds=data['wall_seconds'],sample_full_cpu_seconds=data['total_cpu_seconds']))
        edge_path=flow.workspace/'route/native-edge-correction.json';edge=f.read_json(edge_path)
        require(edge==route.get('native_edge_correction')and edge.get('applied')is False
            and edge.get('reason')=='named class clearance exceeds exact inherited edge scope','originalCRITICAL.5>edge.3 named skip must remain')
        return dict(source_sha256=hashes,protected_routes=10,own_candidate_native=proof,schematic_class_task=route['schematic_class_task'],
            native=export['native'],metrics=export['metrics'],native_edge_correction=edge,native_edge_correction_sha256=p.sha(edge_path),
            route_sha256=p.sha(flow.workspace/'route/result.json'),export_sha256=p.sha(flow.workspace/'export/export.json'),
            checked_export=flow.records['verify_export'],whole_project_drc_clean=export['whole_project_drc_clean'])
    def late_prls():
        for folder,data in [(flow.workspace/'route',flow.records.get('route')),(flow.workspace/'export/validation',flow.records.get('export'))]:
            if data is None:continue
            if fields.has_fields(data.get('native',{}).get('findings',[])):fields.check_local_settings(folder,'final-drc',f.read_json(folder/'final-drc-binding.json'))
            for stage in (('task','final')if folder==flow.workspace/'route'else('final',)):classes.check_local_settings(folder,stage)
            for step in data.get('steps',[]):
                argv=step.get('argv',[]);bare=argv[len(f.SANDBOX):]if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
                if bare[:3]==[str(c.CLI),'pcb','drc']:
                    directory=Path(step['cwd']);name=step['name'];binding=f.read_json(directory/(name+'-binding.json'))
                    ls.check_event(directory,binding,f.process_check(directory,data,name,argv,allowed=(0,5)))
        preview=flow.records.get('review',{}).get('preview',{});folder=flow.workspace/'review/plot-work'
        for step in preview.get('steps',[]):
            name=step['name'];ls.check_event(folder,f.read_json(folder/(name+'-input-binding.json')),f.process_check(folder,preview,name,step['argv']))
    with bridge.cancellation_bridge(job)as(queued,live):
        try:
            for stage in ('preview','route','review','choice','export','verify_export'):
                require(remaining()>=30,'whole delivery reserve unavailable')
                log=out/(stage+'.command.log');choice='accept'if stage=='choice'else None
                process=job.run(flow.command(stage,choice=choice),log,timeout=min(flow.timeout(stage),remaining()-2))
                p.save_json(out/(stage+'.process.json'),process);record['processes'].append(process)
                job.adopt(flow,stage,process,log,choice=choice);stable()
            qualified=qualify();record.update(**qualified,passed=True,status='completed')
        except(Exception,KeyboardInterrupt)as exc:
            record.update(passed=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',error=type(exc).__name__+': '+str(exc))
        material=f.evidence_inventory(out)
        def fresh():
            stable();require(f.evidence_inventory(out)==material,'completed delivery material changed');late_prls();live()
        def final():
            fresh()
            if record['passed']:
                require(ex.check_export(flow.workspace/'export/export.json')['current']is True,'final shared export/route proof refused')
                require(qualify()==qualified,'current own candidate/class/native observations changed')
            fresh();require(remaining()>0,'whole child deadline exhausted during final proof')
        def account():
            record.update(inner_sample_wall_seconds=time.monotonic()-START,inner_sample_full_cpu_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(passed=False,status='budget_exceeded')
            if queued[0]or job.cancel_requested:record.update(passed=False,status='cancelled')
            if record['status']!='completed':record['passed']=False
        try:
            f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final)
            if record['passed']:fresh();live();require(remaining()>0,'whole child final publication deadline exhausted')
        except BaseException as exc:
            def failed():raise exc
            f.publish(out,record,failed,account,remaining,owned=lambda:h.owned_destination(owner))
        print(json.dumps({key:record.get(key)for key in('passed','status','inner_sample_wall_seconds','inner_sample_full_cpu_seconds','error')}))
        return 0 if record['passed']and record['status']=='completed'else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args()
    raise SystemExit(execute(args.protocol,args.protocol_sha256))
