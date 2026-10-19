"""Real owned rectangular edge-clearance controls using shared native validation.

These are diagnostic controls, not benchmark families or complete-schematic
qualification. All original smoke evidence remains untouched.
"""
import argparse,copy,json,shutil,sys,time,uuid
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,floor_route as f,config as c


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--valid',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--fractional-edge',action='store_true',help='New owned sub-grid rectangle plus actual Native export/transport controls')
    parser.add_argument('--native-version',choices=['10.0.7'],help='Explicit pinned diagnostic toolchain; default retains the selected production version')
    args=parser.parse_args();valid=args.valid.resolve();out=args.output.resolve()
    if ROOT/'.runs' not in out.parents:raise p.Rejected('controls require fresh local .runs output')
    start=time.monotonic();cpu=time.process_time()+f.child_cpu();out.mkdir()
    native_toolchain=None
    if args.native_version is not None:
        selection=c.native_selection(f.read_json(ROOT/'toolchain.lock.json'),args.native_version)
        roles=selection['tools']
        native_toolchain=p.ExperimentalNativeToolchain(
            cli=Path(roles['kicad_cli']['path']),python=Path(roles['kicad_python']['path']),pcbnew=Path(roles['pcbnew']['path']),
            expected_version=selection['version'],cli_sha256=roles['kicad_cli']['sha256'],
            python_sha256=roles['kicad_python']['sha256'],pcbnew_sha256=roles['pcbnew']['sha256'])
    before=p.tree_hash(valid.parent);original=sx.read(valid)
    edges=[n for n in original if isinstance(n,list) and sx.one(n,'layer')==['layer','"Edge.Cuts"']]
    points={tuple(sx.one(n,tag)[1:]) for n in edges for tag in ('start','end')}
    if len(edges)!=4 or {n[0] for n in edges}!={'gr_line'} or points!={('5','5'),('45','5'),('45','35'),('5','35')}:
        raise p.Rejected('exact owned smoke outline required')
    source=out/'source';source.mkdir();board=source/valid.name
    fixture=copy.deepcopy(original);fixture[:]=[n for n in fixture if n not in edges]
    bounds=['5.00025','5.0005','45.00025','35.0005'] if args.fractional_edge else ['5','5','45','35']
    fixture.append(['gr_rect',['start',*bounds[:2]],['end',*bounds[2:]],['stroke',['width','0.05'],['type','default']],['fill','none'],['layer','"Edge.Cuts"'],['uuid',str(uuid.uuid5(uuid.NAMESPACE_URL,'kicad-autorouter-owned-edge-control'))]])
    sx.write(board,fixture)
    project=json.loads(valid.with_suffix('.kicad_pro').read_text())
    project.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{})['min_copper_edge_clearance']=0.3
    project['net_settings']={'classes':[{'name':'Default','clearance':0.2,'track_width':0.2,'via_diameter':0.6,'via_drill':0.3}]}
    p.save_json(board.with_suffix('.kicad_pro'),project);source_hashes=p.tree_hash(source)
    tools=p.tool_manifest();protocol=dict(schema=1,tools=tools,controller_sha256=p.sha(Path(__file__)),base=before,source=source_hashes,
        cases=['positive','edge_violation','rule_tamper'],expected_native_gaps_mm={'positive':0.35,'edge_violation':0.25,'rule_tamper':0.25},
        original_edge_minimum_mm=0.3,scope='Owned new rectangle fixture; no schematic supplied. Source and previous native smoke immutable; no routing benchmark or complete-project claim.')
    protocol['fractional_edge']=args.fractional_edge;protocol['rectangle_bounds_mm']=bounds
    protocol['native_selection']=native_toolchain.record() if native_toolchain is not None else c.current_native_selection()
    p.save_json(out/'protocol.json',protocol);rows=[]
    transport=None
    if args.fractional_edge:
        from autorouter import native_edge as edge,adapter
        job=p.Job(out/'transport',60,native_toolchain=native_toolchain);shutil.copytree(source,job.out/'snapshot')
        captured=job.out/'snapshot'/board.name
        job.native('export','export',captured,job.out/'native.dsn')
        job.native('obstacles','obstacles',captured,job.out/'obstacles.json')
        adapted,adapter_record=adapter.adapt_bytes((job.out/'native.dsn').read_bytes(),'both',f.read_json(job.out/'obstacles.json'))
        (job.out/'edge-adapter-input.dsn').write_bytes(adapted)
        corrected,record=edge.correct(adapted,p.native_edge_context(captured))
        (job.out/'task.dsn').write_bytes(corrected);p.save_json(job.out/'native-edge-correction.json',record)
        if not record.get('inward_boundary',{}).get('output_within_original_boundary'):raise p.Rejected('fractional Native export did not exercise source-contained branch')
        data=dict(adapter='both',input_policy='native',source=str(board),source_hashes=source_hashes,tools=tools,
            steps=job.steps,native_edge_correction=record,adapter_transformations=adapter_record,accepted=False)
        if p.check_native_edge_transport(job.out,data)!=record:raise p.Rejected('actual fractional transport replay differs')
        for step in job.steps:f.process_check(job.out,data,step['name'],step['argv'])
        transport=dict(passed=True,data=data,native_dsn_sha256=p.sha(job.out/'native.dsn'),corrected_dsn_sha256=p.sha(job.out/'task.dsn'),
            source_still_exact=p.tree_hash(source)==source_hashes,scope='Actual owned fractional Native export+obstacle workers and existing shared edge transport replay; no routing engine or acceptance claim.')
        p.save_json(job.out/'result.json',transport)
    for name in protocol['cases']:
        job=p.Job(out/name,60,native_toolchain=native_toolchain);target=job.out/'candidate';shutil.copytree(source,target);candidate=target/board.name
        tree=copy.deepcopy(fixture);x=str(Decimal(bounds[2])-(Decimal('0.65') if name=='positive' else Decimal('0.55'))) if args.fractional_edge else ('44.35' if name=='positive' else '44.45')
        def identity(suffix):return ['uuid',str(uuid.uuid5(uuid.NAMESPACE_URL,'kicad-autorouter-edge-'+name+'-'+suffix))]
        tree.append(['via',['at',x,'30'],['size','0.6'],['drill','0.3'],['layers','"F.Cu"','"B.Cu"'],['net','"GND"'],identity('via')])
        for layer in ('F.Cu','B.Cu'):
            tree.append(['segment',['start','40','30'],['end',x,'30'],['width','0.2'],['layer','"'+layer+'"'],['net','"GND"'],identity(layer)])
        sx.write(candidate,tree)
        row=dict(case=name,expected_accepted=name=='positive',source_hashes=source_hashes,accepted=False)
        if name=='rule_tamper':
            changed=copy.deepcopy(project);changed['board']['design_settings']['rules']['min_copper_edge_clearance']=0
            p.save_json(candidate.with_suffix('.kicad_pro'),changed)
            row['relaxed_rule_diagnostic_native']=job.drc('relaxed-rule-diagnostic',candidate)
        try:
            digest,native=p.validate_candidate(job,fixture,candidate,source_hashes,[])
            row.update(candidate_sha256=digest,native=native,accepted=p.native_accepted(native),native_rejection_reasons=p.native_rejection_reasons(native))
        except Exception as exc:
            row.update(reason=type(exc).__name__+': '+str(exc))
        row['steps']=job.steps;row['passed']=row['accepted']==row['expected_accepted']
        if name=='positive':row['passed']=row['passed'] and row.get('native',{}).get('blocking')==0
        elif name=='edge_violation':row['passed']=row['passed'] and row.get('native',{}).get('blocking')==1 and any(x['type']=='copper_edge_clearance' for x in row['native']['findings'])
        else:row['passed']=row['passed'] and row.get('relaxed_rule_diagnostic_native',{}).get('blocking')==0 and 'changed' in row.get('reason','')
        if p.tree_hash(source)!=source_hashes or p.tree_hash(valid.parent)!=before or p.tool_manifest()!=tools:
            raise p.Rejected('control source or runtime changed')
        p.save_json(job.out/'control.json',row);rows.append(row)
        print(name,row['passed'],row.get('reason',row.get('native',{}).get('blocking')),flush=True)
    report=dict(schema=1,accepted=False,all_passed=all(x['passed'] for x in rows),controls=rows,fractional_edge=args.fractional_edge,transport=transport,
        wall_seconds=time.monotonic()-start,full_cpu_seconds=time.process_time()+f.child_cpu()-cpu,protocol_sha256=p.sha(out/'protocol.json'),tools=tools,
        scope='Actual native positive/edge-negative/rule-tamper controls, not routing quality or schematic/physical qualification.')
    p.save_json(out/'result.json',report);return 0 if report['all_passed'] else 2


if __name__=='__main__':raise SystemExit(main())
