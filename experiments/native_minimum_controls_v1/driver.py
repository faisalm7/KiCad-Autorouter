"""UNAPPLIED owned Native size controls; never routing/format/production admission.

After lead review/pins/checkpoint, promote to experiments/native_minimum_controls_v1/driver.py.
Explicit --run-native, fresh absolute .runs output; no engine/export/import or SCH claim.
Five candidates share one exact authored source/project and one 180-second wall/full-CPU budget.
This checks saved/final Native size enforcement, not DSN via-ID/SES decoding or PAW feasibility.
"""
from pathlib import Path
import argparse,copy,fcntl,hashlib,json,signal,sys,time,uuid
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,board_floor as g,sexpr as sx,handoff as h,placement_clearance as io,local_settings
from experiments.placement_handoff_native_v1.driver import copy_bytes
SECONDS=180;LIMIT=20*1024**2
CASES=(('positive','.2','.4','.3',()),('track_under','.1998','.4','.3',('track_width',)),
       ('via_under','.2','.3998','.3',('via_diameter','annular_width')),
       ('hole_under','.2','.4','.2998',('drill_out_of_range',)),
       ('annulus_under','.2','.4','.3002',('annular_width',)))
def ident(label):return str(uuid.uuid5(uuid.NAMESPACE_URL,'kicad-autorouter-owned-minimum-control-v1/'+label))
def owned_source():
    # Entirely authored fixture; no downloaded/reference route, preset or library input.
    tree=['kicad_pcb',['version','20260206'],['generator','"pcbnew"'],['general',['thickness','1.6']],['paper','"A4"'],
        ['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal'],['1','"F.Mask"','user'],['3','"B.Mask"','user'],
         ['5','"F.SilkS"','user'],['7','"B.SilkS"','user'],['13','"F.Paste"','user'],['15','"B.Paste"','user'],
         ['25','"Edge.Cuts"','user'],['35','"F.Fab"','user'],['33','"B.Fab"','user']],['setup',['pad_to_mask_clearance','0']],
        ['gr_rect',['start','0','0'],['end','40','20'],['stroke',['width','.05'],['type','default']],['fill','no'],['layer','"Edge.Cuts"'],['uuid',ident('edge')]]]
    for ref,x,side in (('J1','10','F'),('J2','30','B')):
        tree.append(['footprint','"owned_minimum_terminal"',['layer','"'+side+'.Cu"'],['uuid',ident(ref)],['at',x,'10'],
            ['property','"Reference"','"'+ref+'"',['at','0','0'],['layer','"'+side+'.SilkS"'],['hide','yes'],['uuid',ident(ref+'-reference')],['effects',['font',['size','1.27','1.27']]]],
            ['property','"Value"','"owned_minimum_terminal"',['at','0','0'],['layer','"'+side+'.Fab"'],['hide','yes'],['uuid',ident(ref+'-value')],['effects',['font',['size','1.27','1.27']]]],
            ['attr','smd'],['pad','"1"','smd','rect',['at','0','0'],['size','2','2'],['layers','"'+side+'.Cu"','"'+side+'.Paste"','"'+side+'.Mask"'],['net','"SIGNAL"'],['uuid',ident(ref+'-pad')]]])
    rules=dict(min_track_width=.2,min_clearance=0,min_via_diameter=.4,min_through_hole_diameter=.3,min_via_annular_width=.05,
        min_hole_clearance=.25,min_hole_to_hole=.25,min_copper_edge_clearance=.3,min_connection=0,min_resolved_spokes=2,
        allow_blind_buried_vias=False,allow_microvias=False)
    severities={key:'error' for key in ('track_width','via_diameter','drill_out_of_range','annular_width','clearance','hole_clearance','hole_near_hole','copper_edge_clearance','shorting_items','unconnected_items')}
    project={'meta':{'filename':'owned-minimum.kicad_pro','version':1},'board':{'design_settings':{'rules':rules,'rule_severities':severities,'drc_exclusions':[]}},
        'net_settings':{'classes':[dict(name='Default',track_width=.25,clearance=.2,via_diameter=.8,via_drill=.4)],'netclass_patterns':[],'netclass_assignments':None}}
    return {'owned-minimum.kicad_pcb':(sx.dump(tree)+'\n').encode(),'owned-minimum.kicad_pro':(json.dumps(project,indent=2,sort_keys=True)+'\n').encode()}
def candidate_tree(original,width,diameter,drill):
    tree=copy.deepcopy(original)
    for label,start,end,layer,w in (('track-F',['10','10'],['20','10'],'F.Cu',width),('track-B',['20','10'],['30','10'],'B.Cu','.2')):
        tree.append(['segment',['start',*start],['end',*end],['width',w],['layer','"'+layer+'"'],['net','"SIGNAL"'],['uuid',ident(label)]])
    tree.append(['via',['at','20','10'],['size',diameter],['drill',drill],['layers','"F.Cu"','"B.Cu"'],['net','"SIGNAL"'],['uuid',ident('via')]])
    return tree

def experiment(output,*,run_native=False):
    if run_native is not True:raise p.Rejected('explicit --run-native required')
    started=time.monotonic();cpu0=h.cpu_seconds();remaining=lambda:min(SECONDS-(time.monotonic()-started),SECONDS-(h.cpu_seconds()-cpu0))
    out=h.real_path(output,existing=False)
    if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('fresh absolute direct .runs output required')
    out.mkdir();owner={};h.capture_destination(owner,out);rows=[];completed={};source=None;files=None;tools=None;code=None
    record=dict(schema=1,kind='owned-native-minimum-size-controls',accepted=False,production_support_qualified=False,controls_passed=False,status='incomplete',
        budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,output_cap_bytes=LIMIT,routing_executed=False,new_engine_executed=False,
        schematic_parity='unavailable: authored fixture has no schematic',cases=rows,
        limit_semantics='whole wall/fullCPU post-stage acceptance cap; no totalCPU OS preemption')
    def size():return sum(len(raw) for raw in io.inventory(out,contents=True,max_bytes=LIMIT,max_files=2500,max_entries=5000).values())
    def read_case(row):
        directory=Path(row['directory']);candidate=Path(row['candidate']);refill=directory/'refill'/candidate.name
        saved=f.check_drc_stage(directory,row,'refill-drc',refill,refill,True,row['candidate_before_hashes'])
        final=f.check_drc_stage(directory,row,'final-drc',candidate,directory/'final-drc-input'/candidate.name,False,{**record['source_hashes'],candidate.name:row['candidate_sha256']})
        if (f.canonical(saved)!=f.canonical(row['saved_native']) or f.canonical(final)!=f.canonical(row['native'])
                or p.sha(candidate)!=row['candidate_sha256'] or p.sha(directory/'refill-drc.json')!=row['saved_report_sha256']
                or p.sha(directory/'final-drc.json')!=row['final_report_sha256']):raise p.Rejected('owned control candidate/report binding changed')
        if p.immutable(sx.read(candidate))!=p.immutable(original) or p.routes(sx.read(candidate))!=row['authored_routes']:
            raise p.Rejected('owned control immutable source or exact probe routing changed')
        p.verify_candidate_files(candidate,record['source_hashes'],row['candidate_sha256'])
        p.check_legacy_zone_evidence(directory,original,candidate,implementation=tools['implementation_sha256'])
        local_settings.check_normal_policy(directory,row,max_bytes=LIMIT,max_files=2500)
    def stable():
        h.owned_destination(owner)
        if remaining()<=0 or size()>LIMIT:raise p.Rejected('owned controls whole wall/fullCPU/output cap')
        if tools is not None and p.tool_manifest()!=tools:raise p.Rejected('owned control tools/source/HEAD changed')
        if code is not None:
            if p.tree_hash(out/'code')!=record['code_sha256'] or any(p.sha(ROOT/name)!=pin for name,pin in record['code_sha256'].items()):raise p.Rejected('owned control captured/live source changed')
        if source is not None and p.tree_hash(source.parent)!=record['source_hashes']:raise p.Rejected('owned original fixture changed')
        for row in rows:
            if row.get('passed'):
                read_case(row)
                if io.evidence_inventory(Path(row['directory']))!=completed[row['case']]:raise p.Rejected('completed control evidence changed')
    def account():
        record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=h.cpu_seconds()-cpu0,output_bytes=size())
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS and record['output_bytes']<=LIMIT
        if record['status']!='completed' or not record['within_budget']:record['controls_passed']=False
    try:
        files=owned_source();copy_bytes(files,out/'original');source=out/'original/owned-minimum.kicad_pcb';record['source_hashes']=p.tree_hash(source.parent);original=p.preflight(source)
        project=json.loads(files['owned-minimum.kicad_pro']);cls=project['net_settings']['classes'][0];rules=project['board']['design_settings']['rules']
        raw={key:g.millimetres(cls[field]) for key,field in g.DIMENSIONS.items()};floors={key:g.millimetres(rules[key],zero=True) for key in g.FLOORS}
        targets=g.derive(raw,floors,target_policy=g.MINIMUM_POLICY)
        if targets!={'width_nm':200000,'clearance_nm':200000,'via_diameter_nm':400000,'via_drill_nm':300000}:raise p.Rejected('owned source hard-minimum recipe differs')
        record.update(original_preferred_nm=raw,original_hard_floors_nm=floors,source_derived_targets_nm=targets,fixture_source='wholly authored literals; no reference board/preset/routes')
        tools=p.tool_manifest();extra=(str(Path(__file__).relative_to(ROOT)),'experiments/placement_handoff_native_v1/driver.py')
        code={name:io.read_bytes(ROOT/name) for name in (*tools['implementation_sha256'],*extra)};copy_bytes(code,out/'code')
        record.update(tools=tools,code_sha256={name:hashlib.sha256(raw).hexdigest() for name,raw in code.items()});stable()
        for case,width,diameter,drill,expected in CASES:
            stable();job=f.FloorJob(out/case,remaining(),remaining,protect_local_settings=True)
            copy_bytes({Path(name).name:code[name] for name in tools['implementation_sha256']},job.out/'code')
            candidate=job.out/'candidate'/source.name;copy_bytes(files,candidate.parent);probe=candidate_tree(original,width,diameter,drill);sx.write(candidate,probe)
            row=dict(case=case,directory=str(job.out),candidate=str(candidate),passed=False,expected_error_types=list(expected),probe_uuid=ident('track-F' if case=='track_under' else 'via'),
                dimensions_mm=dict(first_track=width,other_track='.2',via_diameter=diameter,via_drill=drill),source_hashes=record['source_hashes'],tools=tools,steps=job.steps,
                candidate_before_hashes={**record['source_hashes'],candidate.name:p.sha(candidate)},authored_routes=copy.deepcopy(p.routes(probe)),schematic_parity=record['schematic_parity'])
            rows.append(row)
            try:
                digest,native=p.validate_candidate(job,original,candidate,record['source_hashes'],[])
                refill=job.out/'refill'/candidate.name;saved=f.check_drc_stage(job.out,row,'refill-drc',refill,refill,True,row['candidate_before_hashes'])
                final=f.check_drc_stage(job.out,row,'final-drc',candidate,job.out/'final-drc-input'/candidate.name,False,{**record['source_hashes'],candidate.name:digest})
                if f.canonical(final)!=f.canonical(native):raise p.Rejected('owned final Native summaries differ')
                row.update(candidate_sha256=digest,native=final,saved_native=saved,saved_report_sha256=p.sha(job.out/'refill-drc.json'),final_report_sha256=p.sha(job.out/'final-drc.json'))
                detected=[]
                for report in (saved,final):
                    hits={r['type'] for r in report['findings'] if r['severity']=='error' and any(i['uuid']==row['probe_uuid'] for i in r['items'])}
                    detected.append(sorted(hits))
                    if report['opens']!=0 or report['exclusions']!=0:raise p.Rejected('owned fixture unexpectedly open/excluded')
                    if case=='positive':
                        if not p.native_accepted(report):raise p.Rejected('owned minimum positive rejected by actual Native')
                    elif p.native_accepted(report) or not set(expected)<=hits:raise p.Rejected('required actual size violation/UUID not detected')
                row.update(detected_error_types=detected,passed=True);read_case(row)
            except (Exception,KeyboardInterrupt) as exc:
                row.update(passed=False,error=type(exc).__name__+': '+str(exc));raise
            finally:p.save_json(job.out/'control.json',row)
            completed[case]=io.evidence_inventory(job.out);stable()
        record.update(status='completed',controls_passed=len(rows)==len(CASES) and all(r['passed'] for r in rows),completed_evidence=completed)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc),controls_passed=False)
    finally:f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    return record

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',required=True);args=parser.parse_args()
    if not args.run_native:parser.error('explicit --run-native required')
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in handlers:signal.signal(sig,interrupted)
        with (ROOT/'.runs/experiment.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.output,run_native=True)
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)
    print(json.dumps({key:result.get(key) for key in ('status','controls_passed','error','wall_seconds','total_cpu_seconds')}));return 0 if result['controls_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
