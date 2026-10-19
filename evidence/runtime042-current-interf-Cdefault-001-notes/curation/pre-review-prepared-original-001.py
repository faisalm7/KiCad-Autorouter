"""Prepare-only twelve-arm retention port; no Native/readers/tests/GUI/Git.

One <=16MiB/2000-new-file packet per frozen family/arm. Aggregate is written
only after all twelve actual completed enclosures, external costs and packets.
"""
from pathlib import Path
import ast,datetime,hashlib,json,math,os,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
base=ROOT/'.runs/runtime042-two-family-current-comparison-001'
runtime=ROOT/'.runs/runtime-directory-042/runtime'
HEAD='82aaa3b750007ef2ffaafd367ffcb718aa93865e'
MANIFEST='1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
ADMIN='4247b7db234f7379df7d3d41d36522ee9271ccee'
FROZEN='dd6b19f842fcf2e0111c1370b904c82552e0d567025ecf26f445b0b760229f60'
POPULATION='bbfb65e347fa73d84ce3c392eff3ef7d916e96bb29986418c5a74ede948ce524'
families=['interf','sonde'];arms=['Cdefault','B0','B1','B2single_tuned','B2_portfolio','Cthermal']
assert p.sha(base/'frozen-children.json')==FROZEN and p.sha(base/'population.json')==POPULATION
frozen=f.read_json(base/'frozen-children.json');population=f.read_json(base/'population.json')
assert frozen['administration_head']==population['administration_head']==ADMIN
assert frozen['population_sha256']==POPULATION and population['source_head']==HEAD
assert population['runtime_manifest_sha256']==MANIFEST and p.sha(runtime/'runtime-distribution.json')==MANIFEST
assert population['planned_family_order']==families and population['planned_arm_order']==arms
assert population['limits']==dict(routing_seconds=420,method_wall_cpu_cap_seconds=450,delivery_wall_cpu_cap_seconds=600,export_validation_seconds=120)
assert set(frozen['protocols'])==set(families) and all(set(frozen['protocols'][family])==set(arms) for family in families)
aggregate=ROOT/'evidence/runtime042-current-two-family-comparison-001.json';assert not os.path.lexists(aggregate)
refs={};files=[];material=[];total=0;dependencies=[]
for name,pin in [('runtime042-native-milestone-001','7faf3fa21c08073ede6bbb1825b15633c25997a7440b6da37dc2e0edac140d4b'),
                 ('gui-runtime042-081-functional-summary-001','b658e4d480defb9132365c2299cc89f3af9ba3244c44d712828ecd6bc4ba0315')]:
    path=ROOT/'evidence'/(name+'.json');assert p.sha(path)==pin
    data=f.read_json(path);assert data['source_head']==HEAD and data['runtime_manifest_sha256']==MANIFEST
    indexes=[data['files_index']] if 'files_index' in data else []
    for item in data.get('packets',{}).values():
        linked=Path(item['path']);assert linked.parent==ROOT/'evidence' and p.sha(linked)==item['sha256']
        linked_data=f.read_json(linked);assert linked_data['files_index']==item['files_index']
        assert linked_data['source_head']==HEAD and linked_data['runtime_manifest_sha256']==MANIFEST
        indexes.append(item['files_index'])
    assert indexes
    for index in indexes:
        assert p.sha(ROOT/index['path'])==index['sha256'];idx=f.read_json(ROOT/index['path'])
        for row in idx.get('files',[]):refs.setdefault(row['sha256'],row['path'])
        for row in idx.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
    dependencies.append(dict(path=str(path.relative_to(ROOT)),sha256=pin,files_indexes=indexes))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions=[node for node in ast.parse(helper.read_bytes()).body if isinstance(node,ast.FunctionDef) and node.name in ('retain','tree','cost')]
assert [node.name for node in functions]==['retain','tree','cost']
exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'),globals())
real_retain=retain
def retain(path,name):queue.append((Path(path),Path(name)))

def complete_cost(path):
    """Shared -p parser, or the exact six-token macOS time -l header."""
    raw=io.read_bytes(path,64*1024).decode('utf8')
    try:result=cost(path)
    except AssertionError:
        matches=[re.fullmatch(r'\s*([0-9]+(?:\.[0-9]+)?)\s+real\s+([0-9]+(?:\.[0-9]+)?)\s+user\s+([0-9]+(?:\.[0-9]+)?)\s+sys\s*',line) for line in raw.splitlines()]
        found=[match for match in matches if match is not None];assert len(found)==1
        wall,user,system=map(float,found[0].groups())
        result=dict(wall_seconds=wall,CPU_seconds=round(user+system,2),user_seconds=user,system_seconds=system)
    assert all(math.isfinite(result[key]) and result[key]>=0 for key in ('wall_seconds','CPU_seconds'))
    return dict(**result,time_log_sha256=p.sha(path),source=str(path.relative_to(ROOT)),scope='Complete external parent exit; nested samples not additional.')

keys=('opens','blocking','warnings','exclusions')
def counts(native):
    if native is None:return None
    assert type(native) is dict and all(type(native[key]) is int and native[key]>=0 for key in keys)
    return [native[key] for key in keys]

def delivered_proof(receipt,*,export,source_hashes,allowed):
    """Stored proof binding only, not a new Native or central-reader execution."""
    assert receipt.is_file() and receipt.resolve()==receipt and any(root in receipt.parents for root in allowed)
    data=f.read_json(receipt);assert data['source_hashes']==source_hashes
    assert data['tools']['source_provenance']['git_head']==HEAD and data['tools']['source_provenance']['manifest_sha256']==MANIFEST
    assert data['schematic_parity']=='checked by final native DRC'
    assert data['export_accepted' if export else 'accepted'] is True
    assert data['original_geometry_and_routing_unchanged' if export else 'invariants_unchanged'] is True
    native=counts(data['native']);assert native[0]==native[1]==native[3]==0
    candidate=Path(data['candidate']);assert any(root in candidate.parents for root in allowed)
    assert p.sha(candidate)==data['candidate_sha256']
    directory=receipt.parent/'validation' if export else receipt.parent
    report=directory/'final-drc.json';assert p.sha(report)==data['native_report_sha256']
    raw=f.read_json(report);assert raw['kicad_version']=='10.0.7'
    selected=[step for step in data['steps'] if step['cwd']==str(directory) and '--output' in step['argv']
        and step['argv'][step['argv'].index('--output')+1]==str(report)]
    assert len(selected)==1 and '--schematic-parity' in selected[0]['argv'] and selected[0]['exit_code'] in (0,5)
    assert all(step['cleanup_complete'] is True and step['log_truncated'] is False for step in data['steps'])
    return dict(receipt=str(receipt),receipt_sha256=p.sha(receipt),candidate_sha256=data['candidate_sha256'],
        native_report_sha256=data['native_report_sha256'],Native_counts=native,ignored_checks=data['native']['ignored_checks'],
        whole_project_drc_clean=data['whole_project_drc_clean'],protected_count=(None if export else len(data.get('protected_route_import',{}).get('matches',[]))))

# All12 terminal outer receipts and complete costs must exist before any output.
completed=[]
for family in families:
    source=Path(population['families'][family]['source']);hashes=population['families'][family]['source_hashes']
    assert p.tree_hash(source.parent)==hashes
    for arm in arms:
        pin=frozen['protocols'][family][arm];protocol=Path(pin['path'])
        assert protocol==base/family/arm/'protocol.json' and p.sha(protocol)==pin['sha256']
        plan=f.read_json(protocol);out=Path(plan['output']);outer_path=protocol.parent/'enclosure/result.json'
        assert plan['source_head']==HEAD and plan['runtime_manifest_sha256']==MANIFEST and plan['source']==str(source)
        assert plan['source_hashes']==hashes and plan['population_protocol_sha256']==POPULATION
        assert ROOT in Path(plan['controller']).parents and p.sha(Path(plan['controller']))==plan['controller_sha256']
        assert out==Path(population['outputs'][family][arm]) and out.parent==runtime/'.runs'
        assert outer_path.is_file(), 'All twelve complete outer results required'
        outer=f.read_json(outer_path);child=out/'result.json';data=f.read_json(child) if child.is_file() else {}
        assert outer['protocol_sha256']==pin['sha256'] and outer['child_sha256']==(p.sha(child) if child.is_file() else None)
        for filename in ('process.json','command.log'):assert (outer_path.parent/filename).is_file()
        assert (protocol.parent/'outer.log').is_file()
        timing=complete_cost(protocol.parent/'outer-time.log')
        assert type(outer['passed']) is bool
        notes=ROOT/'evidence'/('runtime042-current-'+family+'-'+arm+'-001-notes')
        packet=ROOT/'evidence'/('runtime042-current-'+family+'-'+arm+'-001.json')
        assert not os.path.lexists(notes) and not os.path.lexists(packet)
        completed.append((family,arm,protocol,plan,out,outer,data,timing,notes,packet))
assert len(completed)==12
rows=[];packets=[]
for family,arm,protocol,plan,out,outer,data,timing,notes,packet in completed:
    files=[];material=[];total=0;queue=[];omissions=[]
    tree(protocol.parent,Path('enclosure-and-external-costs'))
    if out.is_dir():tree(out,Path('method'))
    allowed=[out]
    for index,value in enumerate(plan.get('material_roots',[])):
        path=Path(value);assert path.parent==runtime/'.runs';allowed.append(path)
        if path.is_dir():tree(path,Path('portfolio-material')/str(index))
    source=Path(plan['source']);tree(source.parent,Path('original-source'))
    retain(Path(plan['controller']),Path('controller')/Path(plan['controller']).name)
    for name in ('population.json','frozen-children.json'):retain(base/name,Path('population')/name)
    if not rows:
        freezer=ROOT/'.runs/freeze-runtime042-two-family-current-comparison-001.py'
        enclosure=ROOT/'.runs/enclose-native7-independent-control-004.py'
        assert p.sha(freezer)==population['freezer_sha256'] and p.sha(enclosure)==population['enclosure_sha256']
        retain(freezer,'preparation/freeze-runtime042-two-family-current-comparison-001.py')
        retain(enclosure,'controller/enclose-native7-independent-control-004.py')
        for name,pin in population['tracked_administration_files_sha256'].items():
            path=ROOT/name;assert p.sha(path)==pin;retain(path,Path('administration')/name)
        for name in ('runtime042-two-family-current-comparison-freeze-001.log','runtime042-two-family-current-comparison-freeze-001-time.log'):
            retain(ROOT/'.runs'/name,Path('preparation')/name)
        context=base/'host-context-001.json'
        if context.is_file():retain(context,'preparation/host-context-001.json')
        capacity=ROOT/'.runs/runtime042-comparison-capacity-review-001.json'
        if capacity.is_file():retain(capacity,'preparation/runtime042-comparison-capacity-review-001.json')
        retain(Path(__file__),Path('curation')/Path(__file__).name)
        retain(ROOT/'.runs/curate-runtime033-current-comparison-001.py','curation/template033.py')
        retain(helper,'curation/shared-retention030.py')
    summary=None
    if arm=='B2_portfolio':
        path=Path(plan['portfolio_output'])/'portfolio-summary.json'
        if path.is_file():summary=f.read_json(path)
    full_cap_ok=timing['wall_seconds']<=600 and timing['CPU_seconds']<=600
    method_wall=data.get('method_wall_seconds');method_cpu=data.get('method_full_cpu_seconds',data.get('method_full_CPU_seconds'))
    method_cap_ok=all(type(value) in (int,float) and math.isfinite(value) and 0<=value<=450 for value in (method_wall,method_cpu))
    qualified=bool(outer['passed'] and data.get('status')=='completed' and data.get('controls_passed') is True and full_cap_ok and method_cap_ok)
    if summary is not None and summary['status'] in {'budget_exceeded','invalidated','cancelled'}:qualified=False
    if arm!='B2_portfolio':qualified=qualified and data.get('attempt_qualified') is True
    delivered=bool(qualified and data.get('workflow_delivered') is True)
    validated_negative=bool(qualified and data.get('outcome') in ('validated_completed_negative','validated_no_valid_candidate') and not delivered)
    native=data.get('route_native',data.get('native'))
    row=dict(family=family,arm=arm,outer_passed=outer['passed'],outer_status=outer.get('status'),outer_process=outer.get('process'),
        child_receipt_present=bool(data),controller_status=data.get('status'),
        outcome=data.get('outcome'),controller_reported_attempt_qualified=data.get('attempt_qualified'),
        controller_reported_workflow_delivered=data.get('workflow_delivered'),controls_passed=data.get('controls_passed'),
        attempt_qualified=qualified,validated_completed_negative=validated_negative,workflow_delivered=delivered,
        complete_external_cap_ok=full_cap_ok,method_cap_ok=method_cap_ok,complete_cost=timing,protocol_sha256=p.sha(protocol),child_sha256=outer['child_sha256'],
        reason=data.get('reason') or data.get('error') or outer.get('reason') or outer.get('error'),
        evidence_classification=('validated_delivery' if delivered else 'validated_completed_negative' if validated_negative else 'unqualified_or_not_delivered_method'),
        Native_counts=counts(native),route_metrics=data.get('route_metrics'),
        delivered_metrics=data.get('metrics') if delivered else None,source_hashes=plan['source_hashes'],
        selected_route_receipt=data.get('selected_route_receipt'),export_receipt=data.get('export_receipt'),
        method_sample=dict(wall_seconds=data.get('method_wall_seconds'),full_CPU_seconds=data.get('method_full_cpu_seconds',data.get('method_full_CPU_seconds'))),
        whole_controller_sample=dict(wall_seconds=data.get('sampled_wall_seconds'),full_CPU_seconds=data.get('sampled_full_cpu_seconds',data.get('sampled_full_CPU_seconds'))),
        interpretation='Only completed/cap-clean explicit qualified outcomes are negatives or deliveries. All other cases remain method/harness/cap/cancel failures, not routing-infeasibility proof.')
    if delivered:
        route_path=Path(data['selected_route_receipt']);export_path=Path(data['export_receipt'])
        assert p.sha(route_path)==data['selected_route_sha256'] and p.sha(export_path)==data['export_sha256']
        own_route=delivered_proof(route_path,export=False,source_hashes=plan['source_hashes'],allowed=allowed)
        own_export=delivered_proof(export_path,export=True,source_hashes=plan['source_hashes'],allowed=allowed)
        assert own_route['candidate_sha256']==own_export['candidate_sha256']
        row['delivered_own_proof']=dict(route=own_route,export=own_export)
        if native is None:row['Native_counts']=own_route['Native_counts']
    if arm=='B0':
        row['stock_DSN_observation']={key:data.get(key) for key in ('stock_native_dsn_sha256','stock_task_dsn_sha256','stock_dsn_identical')}
    if summary is not None:
        row['portfolio']=dict(status=summary['status'],selected=summary.get('selected'),all_variants_attempted=summary.get('all_variants_attempted'),
            trials=[dict(variant=trial.get('id'),eligible=trial.get('eligible'),validated_rejection=trial.get('validated_rejection'),
                Native_counts=counts(trial.get('native')),status=trial.get('status'),reason=trial.get('reason'),
                receipt=trial.get('receipt'),receipt_sha256=trial.get('receipt_sha256')) for trial in summary.get('trials',[])],
            scope='Raw trial observations retained even if the portfolio method/cap failed; never infer qualified all-negative from trial counts.')
    known=set(refs);planned_bytes=0;planned_files=0;filtered=[];expected={}
    for path,destination in queue:
        raw=io.read_bytes(path,4*1024**2);digest=hashlib.sha256(raw).hexdigest()
        if path.suffix.lower() in {'.zip','.png','.jpg','.jpeg','.gif','.webp','.bmp','.pyc'} or b'\0' in raw:
            omissions.append(dict(original=str(path.relative_to(ROOT)),bytes=len(raw),sha256=digest,reason='Binary/asset/pixels/cache local-only; exact source/snapshot digest retained.'));continue
        raw.decode('utf8')
        if digest not in known:known.add(digest);planned_bytes+=len(raw);planned_files+=1
        filtered.append((path,destination));expected[str(path)]=(len(raw),digest)
    assert planned_bytes<16*1024**2-8192 and planned_files<1999,(family,arm,planned_bytes,planned_files)
    for path,destination in filtered:
        assert (path.stat().st_size,p.sha(path))==expected[str(path)]
        real_retain(path,destination)
    notes.mkdir(parents=True,exist_ok=True)
    index_path=notes/'files.json';p.save_json(index_path,dict(schema=1,files=files,material=material,omitted_binary_payloads=omissions))
    record=dict(schema=1,kind='frozen-current042-single-arm-actual-evidence-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        accepted=False,project_complete=False,actual_GUI=False,human_review=False,source_head=HEAD,runtime_manifest_sha256=MANIFEST,
        administration_head=ADMIN,population_sha256=POPULATION,row=row,source_rights=population['families'][family]['source_rights'],
        limits=population['limits'],stock_caveat=population['stock_caveat'],dependencies=dependencies,
        scope='One of12 prospectively frozen exposed development arms. Same420allocation/450method/600whole/export120. API baseline versus actual default/recoveryCLI distinction retained; no broad/family-independent/holdout/cleanup/speed/electrical claim.',
        backup_scope='Essential licensed text proof and exact binary/source mappings; full raw remains Mac-only outside010, no restoration or package claim.',
        retention=dict(helper_sha256=p.sha(helper),max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,new_files=len(files),new_bytes=total,material_rows=len(material)),
        files_index=dict(path=str(index_path.relative_to(ROOT)),sha256=p.sha(index_path)))
    p.save_json(packet,record)
    for item in material:
        raw=io.read_bytes(ROOT/item['retained'],4*1024**2);assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
    rows.append(row);packets.append(dict(path=str(packet.relative_to(ROOT)),sha256=p.sha(packet),files=len(files),bytes=total,material=len(material)))
assert [(row['family'],row['arm']) for row in rows]==[(family,arm) for family in families for arm in arms]
for family in families:
    assert p.tree_hash(Path(population['families'][family]['source']).parent)==population['families'][family]['source_hashes']
assert p.sha(base/'population.json')==POPULATION and p.sha(base/'frozen-children.json')==FROZEN
assert p.sha(runtime/'runtime-distribution.json')==MANIFEST
assert all(p.sha(ROOT/item['path'])==item['sha256'] for item in packets)
p.save_json(aggregate,dict(schema=1,kind='frozen-current042-twelve-arm-two-exposed-family-comparison-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,actual_GUI=False,human_review=False,
    source_head=HEAD,runtime_manifest_sha256=MANIFEST,administration_head=ADMIN,population_sha256=POPULATION,frozen_children_sha256=FROZEN,
    exposed_circuit_family_labels=2,independent_pedigree_count=None,exposed_development=True,confirmatory=False,
    population=population,rows=rows,packets=packets,dependencies=dependencies,
    preparation_complete_external=complete_cost(ROOT/'.runs/runtime042-two-family-current-comparison-freeze-001-time.log'),
    accounting='All12 complete external parent exits and fullCPU retained, including failures/caps/skips. Method/controller samples are nested, not extra; API/library versus installed CLI startup remains explicit. Full/install/GUI/invalid prerequisites, source/freezing/research/authoring/review/curation additional, unknown notzero. Recovery420 covers whole method; no synthetic420engine or quiet-host/speed claim.',
    interpretation='Corrected-standard/B1 default unchanged. Different exposed circuit labels share KiCad demo publisher, not independent pedigrees/untouched confirmation. Stored individual completions/failures never establish broad superiority, electrical suitability or human cleanup.',
    release_gates=['Broader independent licensed development/untouched confirmation and actual engineer cleanup','Native Windows equivalent safeguards','Current new-target restoration/receipt capacity','CleanOS/relocation/standalone/artifact and authorized human/physical review','Separate formal publication approval']))
print(json.dumps(dict(aggregate=str(aggregate),arms=len(rows),delivered=[(row['family'],row['arm']) for row in rows if row['workflow_delivered']],packets=packets)))
