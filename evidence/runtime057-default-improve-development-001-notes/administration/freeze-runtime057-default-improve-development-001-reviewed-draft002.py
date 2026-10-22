"""DRAFT: identity-port the frozen056 twelve-arm study to fresh installed057.

Preparation/query only; never launch Native, an engine, a comparison or a GUI.
The public factory's literal050 installation branch is not reused or relabelled.
Current057 original-root cohort admission is kept separate from exact root-only
artifact derivation and the completed two actual fresh-root CLI slices. The
unchanged arm controllers/enclosure/reporter retain all outcome authority.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,copy,hashlib,json,os,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,handoff as h,preferences as pref,floor_route as f
from scripts import freeze_current_comparison as factory
HEAD='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
MANIFEST='b1d7066dff94e331f967afa89a4c0b3e2cfa10067324c3216996b31476898c51'
ORIGINAL_MANIFEST='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e'
RUNTIME=ROOT/'.runs/runtime057 fresh install 001'
ORIGINAL_RUNTIME=ROOT/'.runs/runtime-directory-057/runtime'
BASE=ROOT/'.runs/runtime057-default-improve-development-001'
TEMPLATE=ROOT/'.runs/runtime056-default-improve-development-001'
TEMPLATE_POPULATION_SHA='483d39a12f35705dcc72848ce9fa9a18b66a5d05a7574dee8b18d0e00a035cea'
TEMPLATE_CHILDREN_SHA='c8980b9bab253b054b7bc6543b87c00120adaf2d13cf80f4390ed3af6842e625'
SOURCES_SHA='b2644892c7fc718aef2791fa12d9a6fddee2a7e30c64fcb3cde993fdbfa13688'
NATIVE=ROOT/'evidence/runtime057-native-milestone-001.json'
NATIVE_SHA='37620250ac71559915a80873be8d9cfc36c4d65853fd337fa5537e0eac904eb9'
INSTALL=ROOT/'evidence/runtime057-install-existing-001.json'
INSTALL_SHA='9d87a27e8a6329698b80e2e6f905361f40cb2391b70f9a54d7cf0f2917e6d006'
PREP=ROOT/'.runs/runtime057-install-existing-qualification-001/preparation.json'
PREP_SHA='64a555603f104f670e53459d05c72f2a86385ff79223adeef6bb7340f32f1d9b'
LIMITS=dict(routing_seconds=420,method_wall_cpu_cap_seconds=450,delivery_wall_cpu_cap_seconds=600,export_validation_seconds=120)
REPORTER_SHA='0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'

def remaining():
    value=min(90-(time.monotonic()-START),90-(cpu()-CPU0))
    if value<=0:raise p.Rejected('preparation90s wall/fullCPU exhausted')
    return value

def main():
    freezer_pin=p.sha(Path(__file__))
    ap=argparse.ArgumentParser();ap.add_argument('--expected-administration-head',required=True);a=ap.parse_args()
    assert sys.platform=='darwin' and not os.path.lexists(BASE) and shutil.disk_usage(ROOT).free>=4*1024**3
    tracked=factory.administration(a.expected_administration_head)
    assert p.sha(ROOT/'scripts/enclose_current_comparison.py')==factory.ENCLOSURE_SHA
    assert p.sha(ROOT/'scripts/report_current_comparison.py')==REPORTER_SHA
    _,oldpop=factory.pinned_json(TEMPLATE/'population.json',TEMPLATE_POPULATION_SHA)
    _,oldchildren=factory.pinned_json(TEMPLATE/'frozen-children.json',TEMPLATE_CHILDREN_SHA)
    source_raw,spec=factory.pinned_json(TEMPLATE/'sources.json',SOURCES_SHA)
    names,order,kind,method_kind,child_name=factory.contract('improve-v2')
    assert oldpop['kind']==kind and oldpop['population']==list(names) and oldpop['limits']==LIMITS==factory.LIMITS
    assert tracked==oldpop['tracked_administration_files_sha256']
    assert oldpop['planned_family_order']==['ds18b20','ir-obstacle'] and oldpop['planned_arm_order']==list(order)
    assert oldchildren['population_sha256']==TEMPLATE_POPULATION_SHA and set(oldchildren['protocols'])=={'ds18b20','ir-obstacle'}
    families=factory.sources(spec,RUNTIME);assert families==oldpop['families']
    original_raw,original=factory.pinned_json(ORIGINAL_RUNTIME/pv.MANIFEST,ORIGINAL_MANIFEST)
    manifest_raw,manifest=factory.pinned_json(RUNTIME/pv.MANIFEST,MANIFEST)
    assert original['root']==str(ORIGINAL_RUNTIME) and manifest['root']==str(RUNTIME)
    assert {k:v for k,v in manifest.items() if k!='root'}=={k:v for k,v in original.items() if k!='root'}
    implementation={n:pin for n,pin in pv._file_map(manifest['immutable_files_sha256']).items() if n.startswith('autorouter/')}
    identity=pv._runtime_identity(RUNTIME,implementation);original_identity=pv._runtime_identity(ORIGINAL_RUNTIME,implementation)
    assert identity['git_head']==original_identity['git_head']==HEAD and identity['manifest_sha256']==MANIFEST and identity['native_version']=='10.0.7'
    _,native=factory.pinned_json(NATIVE,NATIVE_SHA)
    admitted,dependencies=factory.qualification_scope(native,ORIGINAL_RUNTIME,ORIGINAL_MANIFEST,original_identity,original,'improve-v2')
    cohort_dependencies=dict(dependencies)
    assert admitted['Native_cohort_only'] is True and admitted['actual_GUI_qualified'] is False and admitted['full_GUI_claim'] is False
    install_raw,installed=factory.pinned_json(INSTALL,INSTALL_SHA);_,prepared=factory.pinned_json(PREP,PREP_SHA)
    assert installed['kind']=='runtime057-fresh-root-two-Native-CLI-private-environment-slices-v1'
    assert installed['source_head']==HEAD and installed['runtime']==str(RUNTIME) and installed['runtime_manifest_sha256']==MANIFEST
    assert installed['original_runtime_manifest_sha256']==ORIGINAL_MANIFEST and installed['immutable_map_build_lock_version_unchanged'] is True
    assert installed['immutable_files']==len(manifest['immutable_files_sha256']) and installed['workflow_CLI'] is installed['workflow_delivered'] is True
    assert installed['accepted'] is installed['actual_GUI'] is installed['human_review'] is installed['installation_record_is_authoritative'] is False
    assert prepared['source_head']==HEAD and prepared['runtime']==str(RUNTIME) and prepared['runtime_manifest_sha256']==MANIFEST
    assert prepared['immutable_maps_build_source_engine_unchanged'] is True and prepared['doctor_ready'] is True and prepared['python_version']=='3.11.9'
    assert {r['case'] for r in installed['rows']}=={'ordinary-alias2Cu','via-high-partial2Cu'} and len(installed['rows'])==2
    # Bind already-retained own-final witnesses, never call Native/central readers.
    proof_pins={}
    for row in installed['rows']:
        assert row['workflow_delivered'] is True and row['actual_GUI'] is False and row['Native_counts']==[0,0,0,0] and all(type(n) is int for n in row['Native_counts']) and row['protected_count']==4
        assert row['scoring_preference']==('via_high' if row['case']=='via-high-partial2Cu' else None)
        for label,proof in row['own_final'].items():
            assert label in {'route','export'} and proof['Native_counts']==[0,0,0,0] and proof['protected_count']==4 and proof['full_schematic_flag'] is True and proof['Native_application_policy']['accepted'] is True
            receipt=Path(proof['receipt']);assert receipt.is_relative_to(RUNTIME/'.runs') and p.sha(receipt)==proof['receipt_sha256']
            data=f.read_json(receipt);assert data['candidate_sha256']==proof['candidate_sha256']==row['candidate_sha256']
            folder=receipt.parent if label=='route' else receipt.parent/'validation'
            for filename,key in [('final-drc.json','native_report_sha256'),('final-drc-process.json','process_sha256'),('final-drc-binding.json','binding_sha256')]:
                path=folder/filename;assert p.sha(path)==proof[key];proof_pins[str(path)]=proof[key]
            proof_pins[str(receipt)]=proof['receipt_sha256']
    assert all(set(row['own_final'])=={'route','export'} for row in installed['rows'])
    index=ROOT/installed['files_index']['path'];assert p.sha(index)==installed['files_index']['sha256'];dependencies[str(index)]=p.sha(index)
    dependencies.update({str(NATIVE):NATIVE_SHA,str(INSTALL):INSTALL_SHA,str(PREP):PREP_SHA,str(ORIGINAL_RUNTIME/pv.MANIFEST):ORIGINAL_MANIFEST})
    for name,pin in proof_pins.items():assert p.sha(Path(name))==pin
    child=RUNTIME/'.runs'/child_name;payload=pv.read_bytes(ROOT/'scripts/qualify_current_method.py')
    assert pv._directory(RUNTIME/'.runs').stat().st_uid==os.getuid()
    if os.path.lexists(child):assert child.stat().st_uid==os.getuid() and pv.read_bytes(child)==payload
    outputs={slug:{arm:str(RUNTIME/'.runs'/(('native7-comparison-' if arm.startswith('B') else 'native7-method-')+BASE.name+'-'+slug+'-'+arm)) for arm in names} for slug in families}
    extras={slug:[Path(outputs[slug]['B2_portfolio']+'-portfolio'),*[Path(outputs[slug]['B2_portfolio']+'-portfolio-'+f'{i:02d}-'+v) for i,v in enumerate(factory.VARIANTS,1)]] for slug in families}
    roots=[Path(v) for row in outputs.values() for v in row.values()]+[path for row in extras.values() for path in row]
    assert len(roots)==len(set(roots))==20 and not any(os.path.lexists(path) for path in roots)
    templates={}
    for slug in families:
        assert set(oldchildren['protocols'][slug])==set(names)
        for arm in order:
            record=oldchildren['protocols'][slug][arm];_,plan=factory.pinned_json(Path(record['path']),record['sha256']);templates[slug,arm]=plan
            assert plan['source']==families[slug]['source'] and plan['source_hashes']==families[slug]['source_hashes'] and plan['source_rights']==families[slug]['source_rights']
            assert plan['whole_wall_full_cpu_seconds']==600 and plan['controller_args']==['--runtime',oldpop['runtime']]
            if arm=='B2_portfolio':
                assert [plan[k] for k in LIMITS]==list(LIMITS.values()) and plan['variants']==list(factory.VARIANTS) and plan['allocation']=='balanced'
                assert plan['trial_readback_reserve_seconds']==30 and plan['root_finalization_reserve_seconds']==15
            else:assert plan['limits']==LIMITS and plan['default_settings']==oldpop['default_settings'] and plan['improve_settings']==oldpop['improve_settings']
    BASE.mkdir(mode=0o700);owner={};h.capture_destination(owner,BASE)
    query,query_pins=factory.query_runtime(RUNTIME,BASE);tools=query['tools'];remaining()
    assert query['runtime']==str(RUNTIME) and query['interpreter']==str(RUNTIME/'.venv/bin/python') and query['prefix']==str(RUNTIME/'.venv') and query['defaults']==dict(pref.DEFAULTS)
    assert tools['source_provenance']==identity and tools['implementation_sha256']==implementation and tools['git_head']==HEAD and tools['kicad']=='10.0.7'
    expected_tools={str(RUNTIME/Path(n).relative_to(ORIGINAL_RUNTIME)) if Path(n).is_relative_to(ORIGINAL_RUNTIME) else n:pin for n,pin in admitted['tools_files_sha256'].items()}
    assert tools['files']==expected_tools==prepared['tools']['files'] and tools==prepared['tools']
    if not os.path.lexists(child):
        with child.open('xb') as stream:stream.write(payload)
    assert child.stat().st_uid==os.getuid() and pv.read_bytes(child)==payload
    with (BASE/'sources.json').open('xb') as stream:stream.write(source_raw)
    with (BASE/'qualification.json').open('xb') as stream:stream.write(install_raw)
    qualification=dict(admitted,path=str(INSTALL),sha256=INSTALL_SHA,runtime=str(RUNTIME),runtime_manifest_sha256=MANIFEST,source_head=HEAD,tools_files_sha256=tools['files'],original_cohort=dict(path=str(NATIVE),sha256=NATIVE_SHA,runtime=str(ORIGINAL_RUNTIME),runtime_manifest_sha256=ORIGINAL_MANIFEST),root_only_artifact_derivation=True,fresh_root_two_CLI_slices=True,actual_GUI_qualified=False,full_GUI_claim=False,scope='Exact unchanged artifact derived only at root plus actual two fresh-root CLI slices. Original057 cohort/IR lineage retained separately; no GUI or thermal qualification transferred.')
    assert p.sha(Path(__file__))==freezer_pin, "identity-port freezer changed"
    population=copy.deepcopy(oldpop)
    population.update(runtime=str(RUNTIME),runtime_manifest_sha256=MANIFEST,source_head=HEAD,administration_head=a.expected_administration_head,outputs=outputs,tracked_administration_files_sha256=tracked,qualification=qualification,freezer_sha256=tracked['scripts/freeze_current_comparison.py'],enclosure_sha256=factory.ENCLOSURE_SHA,identity_port_freezer_sha256=freezer_pin,reporter_sha256=REPORTER_SHA,identity_port_template=dict(population_sha256=TEMPLATE_POPULATION_SHA,frozen_children_sha256=TEMPLATE_CHILDREN_SHA),Native_executed=False,actual_GUI=False)
    pop_pin=factory.save_new(BASE/'population.json',population)
    prereqs={str(path):p.sha(path) for path in [TEMPLATE/'sources.json',TEMPLATE/'population.json',TEMPLATE/'frozen-children.json',RUNTIME/pv.MANIFEST,BASE/'sources.json',BASE/'qualification.json',BASE/'population.json',child,Path(__file__),ROOT/'scripts/report_current_comparison.py',*[ROOT/name for name in tracked]]}
    prereqs[str(Path(__file__))]=freezer_pin
    prereqs.update(query_pins);prereqs.update(dependencies);assert 0<len(prereqs)<=32
    def fresh():
        remaining();assert p.sha(Path(__file__))==freezer_pin, "identity-port freezer changed"
        assert h.owned_destination(owner)==BASE and factory.administration(a.expected_administration_head)==tracked
        assert pv._runtime_identity(RUNTIME,implementation)==identity and pv._runtime_identity(ORIGINAL_RUNTIME,implementation)==original_identity
        assert pv.read_bytes(RUNTIME/pv.MANIFEST)==manifest_raw and pv.read_bytes(ORIGINAL_RUNTIME/pv.MANIFEST)==original_raw
        assert factory.sources(spec,RUNTIME)==families and p.sha(INSTALL)==INSTALL_SHA and p.sha(PREP)==PREP_SHA
        assert factory.qualification_scope(native,ORIGINAL_RUNTIME,ORIGINAL_MANIFEST,original_identity,original,'improve-v2')==(admitted,cohort_dependencies)
        for name,pin in {**prereqs,**proof_pins}.items():assert p.sha(Path(name))==pin
        for name,pin in tools['files'].items():assert pv.file_digest(Path(name),pv.MAX_ENGINE_BYTES)[0]==pin
        assert child.stat().st_uid==os.getuid() and pv.read_bytes(child)==payload and not any(os.path.lexists(path) for path in roots)
    children={slug:{} for slug in families};commands=[];fresh()
    for slug in families:
        for arm in order:
            plan=copy.deepcopy(templates[slug,arm]);folder=BASE/slug/arm;folder.mkdir(parents=True)
            plan.update(runtime=str(RUNTIME),runtime_manifest_sha256=MANIFEST,source_head=HEAD,tools=copy.deepcopy(tools),output=outputs[slug][arm],controller_args=['--runtime',str(RUNTIME)],enclosure_sha256=factory.ENCLOSURE_SHA,population_protocol_path=str(BASE/'population.json'),population_protocol_sha256=pop_pin)
            if arm=='B2_portfolio':
                plan.update(administration_head=a.expected_administration_head,administration_files_sha256={name:tracked[name] for name in factory.ADMIN_FILES[:3]},controller_sha256=tracked[factory.ADMIN_FILES[0]],portfolio_output=str(extras[slug][0]),material_roots=[str(path) for path in extras[slug]])
            else:plan.update(outputs=outputs[slug],controller=str(child),controller_sha256=p.sha(child),qualifier_sha256=tracked['scripts/qualify_installed_workflow.py'],prerequisite_sha256=prereqs)
            path=folder/'protocol.json';pin=factory.save_new(path,plan);children[slug][arm]=dict(path=str(path),sha256=pin)
            commands.append(dict(family=slug,arm=arm,argv=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/enclose_current_comparison.py'),'--protocol',str(path),'--protocol-sha256',pin],stdout=str(folder/'outer.log'),stderr_complete_time=str(folder/'outer-time.log'),metering_prefix=['/usr/bin/time','-lp']))
    frozen=dict(schema=1,population_path=str(BASE/'population.json'),population_sha256=pop_pin,protocols=children,administration_head=a.expected_administration_head,policy_or_board_changes_after_first_arm=False,project_complete=False,sampled_setup_wall_seconds=time.monotonic()-START,sampled_setup_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,manual_sequential_commands=commands,batch_operational_ceiling_proposal=dict(wall_seconds=1800,full_CPU_seconds=1800,implemented=False,not_an_arm_acceptance_change=True,unstarted_arms_must_remain_visible=True),scope='Fresh installed057 exact twelve-arm qualification rerun of exposed056 policy; no new research/tuning/family/superiority/GUI/holdout claim.')
    final_pin=factory.save_new(BASE/'frozen-children.json',frozen);fresh()
    assert p.sha(BASE/'frozen-children.json')==final_pin
    for rows in children.values():
        for record in rows.values():assert p.sha(Path(record['path']))==record['sha256']
    print(json.dumps(dict(prepared=True,executed=False,Native=False,engine=False,population=str(BASE/'population.json'),population_sha256=pop_pin,frozen_children_sha256=final_pin,protocols=12,source_head=HEAD,runtime_manifest_sha256=MANIFEST,freezer_sha256=freezer_pin)))
if __name__=='__main__':main()
