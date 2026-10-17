"""Source-only draft: same six installed CLI stages for each frozen pair arm.

Copy these exact bytes into each frozen runtime's .runs before freezing the
shared pair protocol. Do not execute this authoring copy or a draft protocol.
No actual GUI or human acceptance is claimed. No routing policy is changed.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,importlib.util,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,gui,handoff as h,review_export as ex,local_settings as ls,schematic_field_evidence as fields,adapter,provenance as pv

STAGES=('preview','route','review','choice','export','verify_export')
SETTINGS=dict(schema=1,seconds=90,scope='whole_board_unlocked_routing',layers='source_all',adapter='both',guidance='native',profile='standard',scoring_preference=None)

def require(value,reason):
    if not value:raise p.Rejected(reason)

def active_python():
    path=pv.canonical(Path(sys.executable).absolute());digest,size=pv.file_digest(path,128*1024**2)
    return dict(path=str(path),resolved_path=str(path.resolve(strict=True)),sha256=digest,bytes=size,
        version=list(sys.version_info[:3]),implementation=sys.implementation.name)

def execute(protocol,pin,arm_name):
    plan=f.read_json(protocol);arm=plan['arms'][arm_name]
    require(p.sha(protocol)==pin and plan.get('status')=='frozen' and plan.get('kind')=='adapter-fidelity-installed-pair-v1'
        and list(plan['arms'])==['016','017'] and plan['settings']==SETTINGS,'both arms/common settings must be frozen before either run')
    require(c.ROOT==ROOT==Path(arm['runtime']) and Path(sys.prefix).resolve()==ROOT/'.venv'
        and p.sha(Path(__file__))==plan['child_sha256'],'exact installed runtime and frozen child required')
    require(sys.version_info[:2]==(3,11) and active_python()==arm['python_context'],'actual regular installed Python3.11 bytes/path/version differ')
    tools=p.tool_manifest();require(tools==arm['runtime_tools'],'installed arm tools/source differ')
    require(arm['required_receipt_policy']==({}if arm_name=='016'else{'native_edge_admission_policy':'known-named-whole-native-edge-v1'}),
        'exact observed receipt policy must be frozen; no harness opt-in authorizes routing')
    helper=Path(plan['signal_bridge_controller']);require(p.sha(helper)==plan['signal_bridge_sha256'],'frozen queued bridge required')
    spec=importlib.util.spec_from_file_location('frozen_signal_bridge',helper);bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    out=ROOT/'.runs'/arm['child_output_name'];out.mkdir();owner={};h.capture_destination(owner,out)
    source=out/'source';source.mkdir()
    for name,text in plan['fixture_files'].items():
        require(Path(name).name==name and type(text)is str,'flat owned source packet required')
        with (source/name).open('xb') as stream:stream.write(text.encode())
    name=plan['board_name'];require(type(name)is str and Path(name).name==name and name.endswith('.kicad_pcb'),'exact source board name required')
    board=source/name;hashes=p.tree_hash(source);require(hashes==plan['fixture_sha256'],'source packet changed')
    original=p.sx.read(board);protected_source=[route for route in p.routes(original) if p.locked(route)]
    layers=[p.sx.unquote(row[1]) for row in p.sx.one(original,'layers')[1:] if isinstance(row,list) and len(row)>2 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',p.sx.unquote(row[1]))]
    require(layers==plan['expected_copper_layers']==['F.Cu','B.Cu'] and not p.sx.children(original,'zone')
        and len(p.routes(original))==len(protected_source)==plan['expected_protected']==1,'owned2Cu/nozone/exact protected source differs')
    jobs=out/'jobs';jobs.mkdir();flow=gui.Request(str(board),str(jobs),json.dumps(plan['settings']),True).prepare();job=gui.CliJob()
    record=dict(schema=1,kind='installed-named-edge-pair-arm-v1',accepted=False,passed=False,status='failed',arm=arm_name,
        actual_GUI=False,human_review=False,tools=tools,python_context=active_python(),workspace=str(flow.workspace),protocol_sha256=pin,processes=[],
        accounting_point='Inner pre-final-publication sample; outer reaped-process wall/full parent+waited-child CPU and external260s gates are mandatory.',
        qualification='One exposed owned literal300 family; adapter fidelity and installed delivery qualification, not C-over-B2/new-family/quality-superiority evidence.')
    def remaining():return min(238-(time.monotonic()-START),238-(cpu()-CPU0))
    def stable():
        live();h.owned_destination(owner)
        require(p.sha(protocol)==pin and p.sha(Path(__file__))==plan['child_sha256'] and p.sha(helper)==plan['signal_bridge_sha256']
            and p.tool_manifest()==tools and active_python()==arm['python_context'] and p.tree_hash(source)==hashes,'runtime/protocol/source/Python changed')
        flow.fresh();live()
    def observations():
        rows={}
        for stage,path in [('route',flow.workspace/'route/result.json'),('export',flow.workspace/'export/export.json')]:
            if path.is_file():
                data=gui.read_record(path)
                rows[stage]=dict(receipt=str(path),sha256=p.sha(path),status=data.get('status'),accepted=data.get('accepted'),
                    export_accepted=data.get('export_accepted'),candidate=data.get('candidate'),candidate_sha256=data.get('candidate_sha256'),
                    native=data.get('native'),metrics=data.get('metrics'),reason=data.get('reason'),native_edge_correction=data.get('native_edge_correction'),
                    whole_project_drc_clean=data.get('whole_project_drc_clean'))
        return rows
    def qualify():
        route=flow.records['route'];export=flow.records['export']
        require(flow.records['verify_export'].get('current')is True,'shared final export/current route lineage must complete first')
        for key,value in arm['required_receipt_policy'].items():require(route.get(key)==value,'actual route receipt policy observation differs')
        require(route['source']==str(board) and route['source_hashes']==hashes and route.get('schematic_parity')=='checked by final native DRC'
            and export.get('schematic_parity')=='checked by final native DRC','complete own source/schematic lineage differs')
        protected=p.protected_for_record(route,original);require(protected==protected_source,'protected KEEP prediction differs')
        proof=[]
        expected_warnings=sorted(f.canonical(row) for row in plan['source_native']['findings'] if row['severity']=='warning')
        for stage,data,folder in [('route',route,flow.workspace/'route'),('export',export,flow.workspace/'export/validation')]:
            native=data['native'];candidate=Path(data['candidate']);tree=p.sx.read(candidate)
            require(p.native_accepted(native) and native['opens']==native['blocking']==native['exclusions']==0
                and native['ignored_checks']==plan['source_native']['ignored_checks']
                and sorted(f.canonical(row) for row in native['findings'] if row['severity']=='warning')==expected_warnings,
                'original full Native findings/ignored policy differ')
            require(data['metrics']['version']=='10.0.0' and p.immutable(tree)==p.immutable(original)
                and all(row in p.routes(tree) for row in protected) and not p.sx.children(tree,'zone'),'original design/protected copper changed')
            audit=f.read_json(folder/'final-netclass-audit.json');mapping=f.read_json(folder/'final-netclasses.json')
            actual=p.audit_candidate_netclasses(candidate,protected,mapping);actual['native_map_file_sha256']=p.sha(folder/'final-netclasses.json')
            require(audit==actual and audit['route_dimensions']['checked']['protected']==1,'own fresh class map/dimensions differ')
            proof.append(dict(stage=stage,candidate_sha256=data['candidate_sha256'],native=native,metrics=data['metrics'],class_audit=audit,
                final_native_sha256=p.sha(folder/'final-drc.json'),map_sha256=p.sha(folder/'final-netclasses.json'),
                sample_wall_seconds=data['wall_seconds'],sample_full_cpu_seconds=data['total_cpu_seconds']))
        edge_path=flow.workspace/'route/native-edge-correction.json';edge=f.read_json(edge_path)
        require(type(edge)is dict and edge==route.get('native_edge_correction'),'bound observed edge record differs from validated route')
        for key,value in arm['transport_equals'].items():require(edge.get(key)==value,'arm edge observation differs: '+key)
        if arm_name=='017':
            require(edge.get('named_class_scope',{}).get('source_classes')==plan['expected_named_source_classes'],'known named scope differs')
        raw=adapter._parse_dsn((flow.workspace/'route/native.dsn').read_text())
        rule=p.sx.one(p.sx.one(raw,'structure'),'rule');clearances=p.sx.children(rule,'clearance')
        require(len(clearances)==2 and len(clearances[0])==2,'unknown raw global clearance schema')
        return dict(source_sha256=hashes,protected_routes=1,own_candidate_native=proof,edge_transport=edge,edge_transport_sha256=p.sha(edge_path),
            native_dsn_sha256=p.sha(flow.workspace/'route/native.dsn'),raw_declared_global_clearance_um=clearances[0][1],
            raw_declared_clearance_caveat='Declared global value only. Prior004 full-manager edge observations are separately bound; this is not a fresh manager experiment.',
            route_sha256=p.sha(flow.workspace/'route/result.json'),export_sha256=p.sha(flow.workspace/'export/export.json'),
            checked_export=flow.records['verify_export'],whole_project_drc_clean=export['whole_project_drc_clean'])
    def late_prls():
        # Existing PRL-only readers after byte/tool checks; no new verifier or Native work.
        for folder,data in [(flow.workspace/'route',flow.records.get('route')), (flow.workspace/'export/validation',flow.records.get('export'))]:
            if data is None:continue
            if fields.has_fields(data.get('native',{}).get('findings',[])):
                fields.check_local_settings(folder,'final-drc',f.read_json(folder/'final-drc-binding.json'))
            for step in data.get('steps',[]):
                argv=step.get('argv',[]);bare=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
                if bare[:3]==[str(c.CLI),'pcb','drc']:
                    root=Path(step['cwd']);name=step['name'];binding=f.read_json(root/(name+'-binding.json'))
                    ls.check_event(root,binding,f.process_check(root,data,name,argv,allowed=(0,5)))
        preview=flow.records.get('review',{}).get('preview',{});root=flow.workspace/'review/plot-work'
        for step in preview.get('steps',[]):
            name=step['name'];binding=f.read_json(root/(name+'-input-binding.json'))
            ls.check_event(root,binding,f.process_check(root,preview,name,step['argv']))
    with bridge.cancellation_bridge(job)as(queued,live):
        try:
            for stage in STAGES:
                require(remaining()>=30,'whole delivery reserve unavailable')
                log=out/(stage+'.command.log');choice='accept' if stage=='choice' else None
                process=job.run(flow.command(stage,choice=choice),log,timeout=min(flow.timeout(stage),remaining()-2))
                p.save_json(out/(stage+'.process.json'),process);record['processes'].append(process)
                job.adopt(flow,stage,process,log,choice=choice);stable()
            record.update(**qualify(),passed=True,status='completed')
        except(Exception,KeyboardInterrupt)as exc:
            record.update(passed=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',error=type(exc).__name__+': '+str(exc))
        record['observations']=observations();material=f.evidence_inventory(out)
        def fresh():
            stable();require(f.evidence_inventory(out)==material,'completed arm evidence changed');late_prls();live()
        def final():
            fresh()
            if record['passed']:
                require(ex.check_export(flow.workspace/'export/export.json')['current']is True,'central final own export proof refused')
                require(qualify()=={key:record[key] for key in qualify_keys},'completed candidate observations changed')
            fresh();require(remaining()>0,'whole child deadline exhausted during final replay')
        qualify_keys=tuple(key for key in record if key in ('source_sha256','protected_routes','own_candidate_native','edge_transport','edge_transport_sha256','native_dsn_sha256','raw_declared_global_clearance_um','raw_declared_clearance_caveat','route_sha256','export_sha256','checked_export','whole_project_drc_clean'))
        def account():
            record.update(inner_sample_wall_seconds=time.monotonic()-START,inner_sample_full_cpu_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(passed=False,status='budget_exceeded')
            if queued[0]or job.cancel_requested:record.update(passed=False,status='cancelled')
            if record['status']!='completed':record['passed']=False
        try:
            f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final)
            if record['passed']:live()
        except BaseException as exc:
            def failed():raise exc
            f.publish(out,record,failed,account,remaining,owned=lambda:h.owned_destination(owner))
        print(json.dumps({key:record.get(key)for key in('passed','status','inner_sample_wall_seconds','inner_sample_full_cpu_seconds','error')}))
        return 0 if record['passed']and record['status']=='completed'else 2

if __name__=='__main__':
    if sys.argv[1:]==['--python-metadata']:
        require(sys.version_info[:2]==(3,11),'installed Python3.11 metadata required')
        print(json.dumps(active_python(),sort_keys=True));raise SystemExit(0)
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);parser.add_argument('--arm',choices=('016','017'),required=True);args=parser.parse_args()
    raise SystemExit(execute(args.protocol,args.protocol_sha256,args.arm))
