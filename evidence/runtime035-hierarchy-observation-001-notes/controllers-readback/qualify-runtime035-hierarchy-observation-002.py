"""Prepared non-admitting Native hierarchy observation; never ordinary admission.

Execute only its exact runtime035 copy with a separately frozen protocol/hash,
through enclose-native7-independent-control-004.py. No route engine or writer.
Existing ordinary/class/hierarchy guards are not changed or bypassed for a
product result. Raw instance/pad/class evidence may justify revise or defer;
even complete observability never establishes support or routing acceptance.
"""
import time, resource
START = time.monotonic()
def cpu():
    return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, shutil, signal, sys
HERE = Path(__file__).resolve()
PROJECT = HERE.parents[1] if HERE.parents[1].name != 'runtime' else HERE.parents[1].parents[2]
RUNTIME = PROJECT / '.runs/runtime-directory-035/runtime'
sys.path.insert(0, str(RUNTIME)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, floor_route as f, handoff as h, placement_clearance as io
from autorouter import local_settings as local, sexpr as sx, schematic_fields as fields, board_floor as g
HEAD = '7edc7229ea905e6734bf6cec8ff926a92e6a8613'
MANIFEST = '8f0c455d7db2beb64e23283081fe788cfc26ee4d49cd95c8fd152b8e45ccb677'
NAME = 'qualify-runtime035-hierarchy-observation-002.py'
KIND = 'runtime035-hierarchy-observability-resume-v2'
SOURCE = PROJECT / '.data/boards/kicad-multichannel/multichannel_mixer.kicad_pcb'
FIXED = {
    'evidence/corpus-population015-class-guard-cohort-001/population.json': 'ef08d9b0653a5cc5572b03d41bccbeee048c025ac58bf268b019ad3012321d96',
    'evidence/corpus-population015-class-guard-cohort-001/inputs.json': '8d9a84b6932a4d97705ba1d437aa92b27b1e8e6555f0a3db4c4e6c4f1f7544ac',
    'experiments/licensed_acquisition_v7/existing-data-inventory.json': '8047cc66c6cc6bcc1320d1509ea268dbd35e11901cc5f07ea01627e30ef4c7b8',
    'experiments/licensed_acquisition_v1/fetch.py': '1f8bd087dbf7d7c63b51724c8bc7b752e3482d84e6feb9543a0fec9572dfc0dd',
    'data/sources.json': 'a2a8e9e22ff3e109de94733aa8f5e99ca5fd476ef9ec20be837c54100036eac1',
    '.runs/enclose-native7-independent-control-004.py': '9a77bdc832988f45d3bd920dfeeed09288700569db8da7788d043308deb478e4',
}
def require(ok, message):
    if not ok: raise p.Rejected(message)
def text(node, key):
    rows = sx.children(node, key)
    return fields.atom(rows[0][1]) if len(rows)==1 and len(rows[0])==2 and type(rows[0][1]) is str else None
def properties(node):
    rows = sx.children(node, 'property'); result = {}
    for row in rows:
        require(len(row)>=3 and type(row[1]) is str and type(row[2]) is str, 'malformed literal property')
        key=fields.atom(row[1]); require(key not in result, 'duplicate literal property')
        result[key]=fields.atom(row[2])
    return result

def source_contract():
    """Exact existing acquisition inventory and rights; no acquisition/network."""
    for name, pin in FIXED.items(): require(p.sha(PROJECT/name)==pin, 'changed prerequisite source: '+name)
    sys.path.append(str(PROJECT))
    from experiments.licensed_acquisition_v1 import fetch
    require(Path(fetch.__file__).resolve()==PROJECT/'experiments/licensed_acquisition_v1/fetch.py', 'wrong shared inventory helper')
    cohort=f.read_json(PROJECT/'evidence/corpus-population015-class-guard-cohort-001/population.json')
    inputs=f.read_json(PROJECT/'evidence/corpus-population015-class-guard-cohort-001/inputs.json')
    require(inputs['preexisting_inventory_sha256']==FIXED['experiments/licensed_acquisition_v7/existing-data-inventory.json'], 'cohort acquisition binding differs')
    require(cohort['canonical_boards']==25 and cohort['statically_unsupported']==18 and cohort['statically_eligible']==7, 'cohort denominator changed')
    row=next(row for row in cohort['boards'] if row['board']==str(SOURCE.relative_to(PROJECT)))
    require(row['sha256']=='44b7c119a0d05c98e9f294659879184038a5f6c30073c04d9536990429ca413e'
        and row['statically_eligible'] is False and row['unsupported_reason'].startswith('unsupported: schematic class intent not qualified: schematic hierarchy'), 'wrong fixed development source')
    full=f.read_json(PROJECT/'experiments/licensed_acquisition_v7/existing-data-inventory.json'); prefix='boards/kicad-multichannel/'
    files={name[len(prefix):]:item for name,item in full['files'].items() if name.startswith(prefix)}
    directories=[name[len(prefix):] for name in full['directories'] if name.startswith(prefix)]
    expected=dict(schema=1,files=dict(sorted(files.items())),directories=sorted(directories),file_count=len(files),bytes=sum(item['bytes'] for item in files.values()))
    require(len(files)==17 and set(name for name in files if name.endswith('.kicad_sch'))=={'multichannel_mixer.kicad_sch','channel_strip.kicad_sch'}, 'exact acquired project required')
    fetch.inventory(SOURCE.parent, expected)
    sources=f.read_json(PROJECT/'data/sources.json')
    project=next(row for row in sources['projects'] if row['project_id']=='kicad-multichannel')
    require(project['license']=='CC-BY-SA-4.0' and project['split']=='development'
        and project['family_independence']=='unverified_pending_deduplication', 'source rights/split differ')
    licenses={row['destination'][len(prefix):]:row for row in sources['files'] if row.get('project_id')=='kicad-multichannel'}
    require(set(licenses)==set(files), 'acquired rights/file population differs')
    for name,item in files.items():
        require(licenses[name]['sha256']==item['sha256'] and licenses[name]['bytes']==item['bytes']
            and licenses[name]['mode']=='100644' and licenses[name]['license'] in {'CC-BY-SA-4.0','upstream license notice'}, 'source license/hash/mode differs')
    require(next(row for row in project['boards'] if row['board']==prefix+SOURCE.name)['rules_binding']=='native_same_basename', 'do not adopt the unrelated unrouted board project')
    return expected, project

def closure(directory):
    """Extract literal instance edges; do not flatten or grant class support."""
    captured=io.inventory(directory); instances=[]; parsed={}
    def visit(name, path, stack):
        require(len(stack)<8 and len(instances)<64 and name not in stack, 'bounded acyclic sheet closure required')
        require(name in captured and Path(name).suffix=='.kicad_sch', 'missing captured sheet')
        tree=sx.parse(io.read_bytes(directory/name,8*1024**2).decode('utf8'))
        require(tree[0]=='kicad_sch', 'unknown source schematic root'); parsed[name]=p.sha(directory/name)
        instances.append(dict(file=name,instance_path=path,root_uuid=text(tree,'uuid'),class_flag_count=len([node for node in walk(tree) if node and node[0]=='netclass_flag'])))
        for sheet in sx.children(tree,'sheet'):
            props=properties(sheet); value=props.get('Sheetfile'); label=props.get('Sheetname'); uid=text(sheet,'uuid')
            require(type(value) is str and type(label) is str and label and uid is not None, 'literal sheet file/name/UUID required')
            rel=PurePosixPath(value)
            require(not rel.is_absolute() and str(rel)==value and '..' not in rel.parts and '\\' not in value
                and not any(ord(ch)<32 for ch in value), 'escaping or expanded sheet path unsupported')
            target=str(PurePosixPath(name).parent/rel)
            visit(target,path+label+'/',stack+(name,))
    visit('multichannel_mixer.kicad_sch','/',())
    require(set(parsed)=={name for name in captured if name.endswith('.kicad_sch')}, 'unaccounted captured schematic')
    require(len(instances)==5 and {row['instance_path'] for row in instances}=={'/','/CH1/','/CH2/','/CH3/','/CH4/'}, 'fixed repeated four-channel hierarchy differs')
    return dict(files=parsed,instances=instances,qualified_for_support=False)
def walk(tree):
    yield tree
    for child in tree[1:]:
        if type(child) is list: yield from walk(child)

# Small experiment-only observer. Reuse native.netclasses and verified pad/FP
# primitives. Missing GetPath/AsString is recorded, never substituted or guessed.
WORKER = r'''from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
runtime=Path(sys.argv[6]);sys.path.insert(0,str(runtime))
import pcbnew,_pcbnew
from autorouter import config as c,placement_clearance as io
from autorouter.native import netclasses
board_path,output=map(Path,sys.argv[1:3]);version,python,extension=sys.argv[3:6]
assert c.ROOT==runtime
assert pcbnew.GetBuildVersion()==version==c.NATIVE_VERSION=='10.0.7'
assert Path(sys.executable).resolve()==Path(python).resolve()==c.PYTHON.resolve()
assert Path(_pcbnew.__file__).resolve()==Path(extension).resolve()==c.PCBNEW.resolve()
before=io.inventory(board_path.parent);board=pcbnew.LoadBoard(str(board_path));assert board
mapping=netclasses(board,str(board_path),(before[board_path.name],before[board_path.with_suffix('.kicad_pro').name]))
footprints=[];pads=[]
for fp in board.GetFootprints():
 if len(footprints)>=512:raise ValueError('footprint observation ceiling')
 path=None;error=None
 try:path=str(fp.GetPath().AsString())
 except Exception as exc:error=(type(exc).__name__+': '+str(exc))[:1024]
 footprints.append(dict(uuid=str(fp.m_Uuid.AsString()),reference=str(fp.GetReference()),path=path,path_method_error=error))
for pad in board.GetPads():
 if len(pads)>=10000:raise ValueError('pad observation ceiling')
 fp=pad.GetParentFootprint()
 pads.append(dict(uuid=str(pad.m_Uuid.AsString()),footprint_uuid=str(fp.m_Uuid.AsString()),reference=str(fp.GetReference()),number=str(pad.GetNumber()),netcode=int(pad.GetNetCode()),net=str(pad.GetNetname()),copper=any(pad.IsOnLayer(layer) for layer in (pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu))))
assert io.inventory(board_path.parent)==before
record=dict(schema=1,native_version=pcbnew.GetBuildVersion(),source=str(board_path),input_hashes_before=before,input_hashes_after=before,board_saved=False,native_classes=mapping,footprints=footprints,pads=pads,accepted=False,routing_accepted=False,support_admitted=False)
raw=json.dumps(record,sort_keys=True,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<=8*1024**2
with output.open('x') as stream:stream.write(raw)
'''

def extract(netlist, native, source):
    """Bounded raw observations and literal joins; not a hierarchy verifier."""
    tree=sx.parse(io.read_bytes(netlist,8*1024**2).decode('utf8'))
    require(tree[0]=='export' and text(tree,'version')=='E', 'unknown Native netlist schema')
    design=sx.one(tree,'design');require(design is not None and text(design,'source')==str(source.with_suffix('.kicad_sch')) and text(design,'tool')=='Eeschema 10.0.7','Native netlist source/tool differs')
    sheets=[dict(number=text(row,'number'),name=text(row,'name'),tstamps=text(row,'tstamps')) for row in sx.children(design,'sheet')]
    components=[];nets=[];unknown=[]
    section=sx.one(tree,'components');require(section is not None and len(section)<=513,'bounded Native components required')
    for row in sx.children(section,'comp'):
        path=sx.one(row,'sheetpath',[])
        components.append(dict(reference=text(row,'ref'),tstamps=text(row,'tstamps'),sheetpath_names=text(path,'names'),sheetpath_tstamps=text(path,'tstamps')))
    section=sx.one(tree,'nets');require(section is not None and len(section)<=1025,'bounded Native nets required')
    for row in sx.children(section,'net'):
        nets.append(dict(code=text(row,'code'),name=text(row,'name'),class_identity=text(row,'class'),terminals=[[text(node,'ref'),text(node,'pin')] for node in sx.children(row,'node')]))
    board=sx.read(source);_,resolve=g.source_net_identity(board);literal=[]
    for fp in sx.children(board,'footprint'):
        props=properties(fp)
        for pad in sx.children(fp,'pad'):
            node=sx.one(pad,'net')
            literal.append(dict(uuid=text(pad,'uuid'),footprint_uuid=text(fp,'uuid'),reference=props.get('Reference'),path=text(fp,'path'),number=fields.atom(pad[1]),net=resolve(node) if node is not None else None))
    observed={row['uuid']:row for row in native['pads']};footprints={row['uuid']:row for row in native['footprints']}
    if len(observed)!=len(native['pads']) or len(observed)!=len(literal):unknown.append('Source/Native pad UUID population missing, duplicate or different')
    for row in literal:
        found=observed.get(row['uuid']);fp=footprints.get(row['footprint_uuid'])
        if found is None or fp is None or any(found.get(key)!=row[key] for key in ('footprint_uuid','reference','number','net')):unknown.append('Source/Native literal pad identity differs: '+str(row['uuid']))
        if fp is not None and (fp['path'] is None or fp['path']!=row['path']):unknown.append('Native footprint path missing/different; no fallback: '+str(row['footprint_uuid']))
    names={row['name'] for row in sheets}
    if not {'/CH1/','/CH2/','/CH3/','/CH4/'}<=names:unknown.append('Native design does not expose all four distinct channel instance names')
    if any(not row['tstamps'] or not row['sheetpath_tstamps'] for row in components):unknown.append('Native component UUID/instance stamps missing')
    if len({row['reference'] for row in components})!=len(components):unknown.append('Native expanded component references are not unique')
    pcb={};sch={};classes={row['name']:row for row in native['native_classes']['nets']}
    for row in native['pads']:
        if row['copper'] and row['netcode']>0:pcb.setdefault(row['net'],[]).append([row['reference'],row['number']])
    for row in nets:
        sch[row['name']]=row['terminals'];actual=classes.get(row['name'])
        if row['class_identity'] is None or actual is None or row['class_identity']!=actual.get('class'):unknown.append('Missing/different literal SCH/PCB class: '+str(row['name']))
        if actual is not None and set(actual.get('parameter_parents',{}))!={'width_nm','clearance_nm','via_diameter_nm','via_drill_nm'}:unknown.append('Incomplete actual scalar parent identities: '+str(row['name']))
    if {name:sorted(rows) for name,rows in pcb.items()}!={name:sorted(rows) for name,rows in sch.items()}:unknown.append('Complete SCH terminal partition differs from Native copper-pad partition')
    return dict(sheets=sheets,components=components,schematic_nets=nets,source_literal_pads=literal,
        Native_copper_terminal_partitions=pcb,unknowns=sorted(set(unknown)),support_admitted=False,
        UUID_path_join_qualified=False,scope='Raw exact observations/literal comparison only. A versioned hierarchy instance/source binding proof remains necessary even when lists match.')

def completed_export001(plan):
    row=plan['completed_export001'];root=RUNTIME/'.runs/native7-comparison-control-runtime035-hierarchy-001'
    require(row['root']==str(root) and p.sha(root/'result.json')==row['result_sha256'],'retained failed001 changed')
    data=f.read_json(root/'result.json')
    require(data['status']=='failed' and data['control_passed'] is False and data['accepted'] is False
        and data['error']=='Rejected: Native observation changed copied original project'
        and data['source_hashes']==plan['source_hashes'] and data['tools']==plan['tools'],'wrong prior observation')
    copied=root/'observation/candidate'/SOURCE.name
    require(io.inventory(copied.parent)==row['after_hashes'],'retained export inputs changed')
    require(all(row['after_hashes'].get(n)==v for n,v in plan['source_hashes'].items())
        and set(row['after_hashes'])-set(plan['source_hashes'])=={SOURCE.with_suffix('.kicad_prl').name},
        'prior export changed an original file or unexpected companion')
    netlist=root/'observation/hierarchy.net';require(p.sha(netlist)==row['netlist_sha256'],'prior Native netlist changed')
    argv=[*f.SANDBOX,str(c.CLI),'sch','export','netlist','--format','kicadsexpr','--output',str(netlist),str(copied.with_suffix('.kicad_sch'))]
    process=f.process_check(root/'observation',data,'hierarchy-netlist',argv)
    require(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
        and process['log_truncated'] is False and len(data['steps'])==1,'prior export did not actually complete')
    require(p.sha(root/'observation/hierarchy-netlist-process.json')==row['process_sha256'],'prior process changed')
    return netlist,copied

def execute(protocol, pin):
    protocol=h.real_path(protocol);require(p.sha(protocol)==pin,'frozen protocol hash required');plan=f.read_json(protocol)
    require(plan['kind']==KIND and plan['schema']==1 and plan['runtime']==str(RUNTIME) and HERE==RUNTIME/'.runs'/NAME
        and p.sha(HERE)==plan['controller_sha256'] and plan['whole_wall_full_cpu_seconds']==180
        and plan['pass_key']=='control_passed' and plan['controller_args']==[], 'exact copied diagnostic contract required')
    require(Path(sys.executable).absolute()==RUNTIME/'.venv/bin/python' and Path(sys.prefix).resolve()==RUNTIME/'.venv' and c.ROOT==RUNTIME,'exact035 runtime interpreter required')
    expected,rights=source_contract();require(expected==plan['source_inventory'] and rights==plan['source_rights']
        and plan['source']==str(SOURCE) and plan['source_hashes']=={name:item['sha256'] for name,item in expected['files'].items()},'fixed full source/rights required')
    tools=p.tool_manifest();require(tools==plan['tools'] and tools['git_head']==HEAD==plan['source_head'] and tools['kicad']=='10.0.7'
        and p.sha(RUNTIME/'runtime-distribution.json')==MANIFEST==plan['runtime_manifest_sha256'],'runtime/source/tools changed')
    require(hashlib.sha256(WORKER.encode()).hexdigest()==plan['observation_worker_sha256'],'sealed observation worker differs')
    prior_netlist,prior_board=completed_export001(plan)
    prereq={Path(name):value for name,value in plan['prerequisite_files'].items()}
    for path,value in prereq.items():require(p.sha(path)==value,'qualification prerequisite changed')
    out=Path(plan['output']);require(out==RUNTIME/'.runs/native7-comparison-control-runtime035-hierarchy-002' and not out.exists(),'fresh exact output required')
    out.mkdir(mode=0o700);owner={};h.capture_destination(owner,out);(out/'protocol.json').write_bytes(io.read_bytes(protocol))
    report=dict(schema=1,kind=KIND,status='failed',control_passed=False,accepted=False,routing_accepted=False,comparison_eligible=False,support_admitted=False,production_admitted=False,
        actual_GUI=False,human_review=False,source=str(SOURCE),source_hashes=plan['source_hashes'],source_rights=rights,tools=tools,source_head=HEAD,runtime_manifest_sha256=MANIFEST,protocol_sha256=pin,
        completed_export001=plan['completed_export001'],source_zone_refill_performed=False,
        prior_export_scope='Reused raw completed Native export from failed001. Every original17 file remains exact; added local preferences retained. Original missing post-export binding is not fabricated or promoted to acceptance. No export rerun.',
        disposition='defer',whole_wall_full_cpu_budget_seconds=180,scope=plan['scope'],GUI_qualification_required_for_this_diagnostic=False,GUI_support_not_qualified_by_this_diagnostic=True)
    def remaining():return min(178-(time.monotonic()-START),178-(cpu()-CPU0))
    def stable():
        completed_export001(plan)
        require(h.owned_destination(owner)==out and p.sha(protocol)==pin and p.sha(out/'protocol.json')==pin and p.sha(HERE)==plan['controller_sha256']
            and p.sha(RUNTIME/'runtime-distribution.json')==MANIFEST and p.tool_manifest()==tools,'diagnostic authority changed')
        for path,value in prereq.items():require(p.sha(path)==value,'frozen prerequisite changed')
        for path,value in FIXED.items():require(p.sha(PROJECT/path)==value,'source/provenance record changed')
        require(io.inventory(SOURCE.parent)==plan['source_hashes'] and remaining()>0,'source changed or whole wall/fullCPU budget exhausted')
    class DiagnosticJob(p.Job):
        def step(self,name,argv,allowed=(0,)):
            require(remaining()>15,'Native diagnostic publication reserve exhausted')
            self.deadline=time.monotonic()+min(30,remaining()-15)
            return super().step(name,[*f.SANDBOX,*argv],allowed)
    job=None;bindings=[];drc=None
    try:
        stable();job=DiagnosticJob(out/'observation',min(120,remaining()-15),protect_local_settings=True)
        copied=job.out/'candidate'/SOURCE.name;shutil.copytree(SOURCE.parent,copied.parent)
        require(io.inventory(copied.parent)==plan['source_hashes'],'owned observation copy differs')
        structure=closure(copied.parent);require(structure==plan['source_closure'],'frozen source closure differs')
        worker=job.out/'observe-pcb.py';worker.write_text(WORKER);require(p.sha(worker)==plan['observation_worker_sha256'],'worker copy differs')
        for name,argv,output in (
            ('pcb-observation',[str(c.PYTHON),'-B',str(worker),str(copied),str(job.out/'native-pcb.json'),'10.0.7',str(c.PYTHON),str(c.PCBNEW),str(RUNTIME)],job.out/'native-pcb.json')):
            stable();before=io.inventory(copied.parent);state={'complete':False}
            with local.preserve(copied.with_suffix('.kicad_prl'),job.out,job._local_settings_owner,cleanup_complete=lambda:state['complete']) as protection:
                try:process=job.step(name,argv)
                finally:state['complete']=bool(job.steps and job.steps[-1]['name']==name and job.steps[-1]['cleanup_complete'] is True)
            require(io.inventory(copied.parent)==before,'Native observation changed copied original project')
            require(f.process_check(job.out,{'steps':job.steps},name,[*f.SANDBOX,*argv])==process,'actual observation process differs')
            binding=dict(schema=1,input=str(copied),before=before,after=before,worker_sha256=plan['observation_worker_sha256'] if name=='pcb-observation' else None,argv=process['argv'],output=str(output),output_sha256=p.sha(output),protection=protection)
            p.save_json(job.out/(name+'-input-binding.json'),binding);bindings.append(binding)
        native=f.read_json(job.out/'native-pcb.json');require(native['native_version']=='10.0.7' and native['source']==str(copied)
            and native['input_hashes_before']==native['input_hashes_after']==plan['source_hashes'] and native['board_saved'] is False,'actual PCB observation input identity differs')
        observed=extract(prior_netlist,native,prior_board);p.save_json(job.out/'extracted-observations.json',observed)
        drc=job.drc('source-full-drc',copied,schematic_parity=True)
        require(f.check_drc_stage(job.out,{'steps':job.steps},'source-full-drc',copied,job.out/'source-full-drc-input'/SOURCE.name,False,plan['source_hashes'],schematic_parity=True)==drc,'full schematic DRC input/report/process binding differs')
        require(io.inventory(copied.parent)==plan['source_hashes'],'diagnostic modified candidate originals')
        report.update(status='completed',control_passed=True,source_closure=structure,native=drc,native_report_sha256=p.sha(job.out/'source-full-drc.json'),
            observations=observed,disposition='revise' if not observed['unknowns'] else 'defer',
            disposition_reason='Raw requested observations are available; a reviewed versioned hierarchy binder is still required, no integration/admission.' if not observed['unknowns'] else 'Unverified/mismatched observability remains explicit; do not weaken the product guard.',
            Native_findings_meaning='Actual source findings including exit5/opens are diagnostic; neither routing failure nor clean/routing acceptance.')
    except (Exception,KeyboardInterrupt) as exc:
        report.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc),control_passed=False,disposition='defer')
    report['steps']=job.steps if job is not None else []
    material=f.evidence_inventory(out);report['evidence_sha256']=material
    def final_check():
        stable();require(f.evidence_inventory(out)==material,'diagnostic evidence changed')
        if report['control_passed']:
            require(p.sha(job.out/'observe-pcb.py')==plan['observation_worker_sha256'],'observation worker changed')
            for binding in bindings:require(p.sha(binding['output'])==binding['output_sha256'] and io.inventory(Path(binding['input']).parent)==binding['before'],'observation input/output changed')
            require(f.check_drc_stage(job.out,report,'source-full-drc',job.out/'candidate'/SOURCE.name,job.out/'source-full-drc-input'/SOURCE.name,False,plan['source_hashes'],schematic_parity=True)==drc,'final Native DRC readback differs')
            stable();require(f.evidence_inventory(out)==material,'diagnostic evidence changed after readback')
            local.check_final_events([(job.out,report)],c.CLI)
            for binding in bindings:local.check_preserved(Path(binding['input']).with_suffix('.kicad_prl'),binding['before'],binding['protection'])
    def account():
        report.update(complete_wall_seconds=time.monotonic()-START,complete_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True)
        if remaining()<=0:report.update(status='budget_exceeded',control_passed=False,disposition='defer')
        if report['status']!='completed':report['control_passed']=False
        for key in ('accepted','routing_accepted','comparison_eligible','support_admitted','production_admitted'):report[key]=False
    f.publish(out,report,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_check)
    print(json.dumps({key:report.get(key) for key in ('status','control_passed','disposition','error','complete_wall_seconds','complete_full_CPU_seconds')}))
    return 0 if report['control_passed'] and report['status']=='completed' else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args()
    def interrupted(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    raise SystemExit(execute(args.protocol,args.protocol_sha256))
