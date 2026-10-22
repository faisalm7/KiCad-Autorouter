"""DRAFT: freeze all18 exposed DS18/IR/EEPROM arms on fresh installed058.

Preparation/query only; no Native, Java, engine, comparison, or GUI execution.
Reuse pinned057 source/settings templates, never their outcomes or058 singleton
results. Current058 original-root cohort admission and root-only artifact copy
plus two fresh-root CLI slices are separate. Shared arm/report authority stays
unchanged; build source8f is distinct from required administration HEAD.
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
HEAD='8f5e96b88dd22cd25919bb71ce47711612994efa'
MANIFEST='19bdfe08169624f49a3b2bee1b789258f2ccaac63ad24a1e06c1d6ba371788f2'
ORIGINAL_MANIFEST='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'
RUNTIME=ROOT/'.runs/runtime058 fresh install 001'
ORIGINAL_RUNTIME=ROOT/'.runs/runtime-directory-058/runtime'
BASE=ROOT/'.runs/runtime058-installed-three-family-001'
TEMPLATE=ROOT/'.runs/runtime057-default-improve-development-001'
TEMPLATE_POPULATION_SHA='cb39bc8fd63b77c44f5ee96bb0d9bdf5f8571500f53c91cf19c24e0904bc5e4e'
TEMPLATE_CHILDREN_SHA='aeb1379bb7e34066517043c4a9dd517a5de45e1100044892ce696db7ed45b485'
SOURCES_SHA='b2644892c7fc718aef2791fa12d9a6fddee2a7e30c64fcb3cde993fdbfa13688'
EEPROM=ROOT/'.runs/runtime057-eeprom-development-001'
EEPROM_POPULATION_SHA='f9c871ea5259cc4b977b6448ceb9439dffb6e8f5626bf2b437d90afd2a8cf99b'
EEPROM_CHILDREN_SHA='99101afda90de8fe7af40e8183ffb6d903be8f2b97cf24aa0ed3347bf51e17cc'
EEPROM_SOURCES_SHA='5d00eef20403051eefbab36cd52b1f3c30266844cc051da22910caf81dbb4563'
FAMILY_ORDER=('ds18b20','ir-obstacle','eeprom')
FORECAST_BYTES=1024**3;RETAIN_FREE_BYTES=3*1024**3  # Planning allowance, not a job quota.

NATIVE=ROOT/'evidence/runtime058-native-milestone-001.json'
NATIVE_SHA='1dd9972cdf5b20392cde77f42ddb177838e8a65c2b4cd22dc8409580ad42fc29'
INSTALL=ROOT/'evidence/runtime058-install-existing-001.json'
INSTALL_SHA='0058dd996b0a57249d05e80a9b8e5703eb8cdb413510a7ff0a4d1e0db0bb02f5'
PREP=ROOT/'.runs/runtime058-install-existing-qualification-001/preparation.json'
PREP_SHA='3c33ee334f4664227918128e686c41427e41956def7a914c1d7a4ae162b4978d'
LIMITS=dict(routing_seconds=420,method_wall_cpu_cap_seconds=450,delivery_wall_cpu_cap_seconds=600,export_validation_seconds=120)
REPORTER_SHA='0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'
FACTORY_SHA='9729687563f9dd23fcee7b85d1cb4835dd57f436a23626d7f07d93a9d07033bd'

def remaining():
    value=min(90-(time.monotonic()-START),90-(cpu()-CPU0))
    if value<=0:raise p.Rejected('preparation90s wall/fullCPU exhausted')
    return value

def main():
    freezer_pin=p.sha(Path(__file__))
    ap=argparse.ArgumentParser();ap.add_argument('--expected-administration-head',required=True);a=ap.parse_args()
    assert sys.platform=='darwin' and not os.path.lexists(BASE) and shutil.disk_usage(ROOT).free>=RETAIN_FREE_BYTES+FORECAST_BYTES
    tracked=factory.administration(a.expected_administration_head)
    assert p.sha(ROOT/'scripts/enclose_current_comparison.py')==factory.ENCLOSURE_SHA
    assert p.sha(ROOT/'scripts/report_current_comparison.py')==REPORTER_SHA
    _,oldpop=factory.pinned_json(TEMPLATE/'population.json',TEMPLATE_POPULATION_SHA)
    _,oldchildren=factory.pinned_json(TEMPLATE/'frozen-children.json',TEMPLATE_CHILDREN_SHA)
    _,spec=factory.pinned_json(TEMPLATE/'sources.json',SOURCES_SHA)
    _,eepop=factory.pinned_json(EEPROM/'population.json',EEPROM_POPULATION_SHA)
    _,eechildren=factory.pinned_json(EEPROM/'frozen-children.json',EEPROM_CHILDREN_SHA)
    _,eespec=factory.pinned_json(EEPROM/'sources.json',EEPROM_SOURCES_SHA)
    assert set(eespec['families'])==set(eepop['families'])==set(eechildren['protocols'])=={'eeprom'}
    assert eechildren['population_sha256']==EEPROM_POPULATION_SHA and eepop['planned_family_order']==['eeprom']
    spec['families'].update(copy.deepcopy(eespec['families']))
    source_raw=(json.dumps(spec,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()

    names,order,kind,method_kind,child_name=factory.contract('improve-v2')
    assert oldpop['kind']==kind and oldpop['population']==list(names) and oldpop['limits']==LIMITS==factory.LIMITS
    old_tracked=oldpop['tracked_administration_files_sha256'];factory_name='scripts/freeze_current_comparison.py'
    assert set(tracked)==set(old_tracked) and tracked[factory_name]==FACTORY_SHA
    assert tracked==old_tracked==eepop['tracked_administration_files_sha256']
    assert oldpop['planned_family_order']==['ds18b20','ir-obstacle'] and oldpop['planned_arm_order']==list(order)
    assert oldchildren['population_sha256']==TEMPLATE_POPULATION_SHA and set(oldchildren['protocols'])=={'ds18b20','ir-obstacle'}
    assert all(eepop[k]==oldpop[k] for k in ('kind','population','limits','default_settings','improve_settings','planned_arm_order','policy'))
    checked=factory.sources(spec,RUNTIME);families={slug:checked[slug] for slug in FAMILY_ORDER}
    assert families=={**oldpop['families'],**eepop['families']} and len(families)==3

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
    assert installed['kind']=='runtime058-fresh-root-two-Native-CLI-private-environment-slices-v1'
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
            assert label in {'route','export'} and proof['Native_counts']==[0,0,0,0] and proof['protected_count']==(4 if label=='route' else None) and proof['full_schematic_flag'] is True and proof['Native_application_policy']['accepted'] is True
            receipt=Path(proof['receipt']);assert receipt.is_relative_to(RUNTIME/'.runs') and p.sha(receipt)==proof['receipt_sha256']
            data=f.read_json(receipt);assert data['candidate_sha256']==proof['candidate_sha256']==row['candidate_sha256']
            folder=receipt.parent if label=='route' else receipt.parent/'validation'
            audit_path=folder/'final-netclass-audit.json';audit=f.read_json(audit_path)
            assert audit['candidate_sha256']==proof['candidate_sha256'] and audit['route_dimensions']['passed'] is True
            assert type(audit['route_dimensions']['checked']['protected']) is int and audit['route_dimensions']['checked']['protected']==4
            assert audit['project_sha256']==data['source_hashes'][Path(data['source'] if label=='route' else data['inputs']['source']).with_suffix('.kicad_pro').name]
            proof_pins[str(audit_path)]=p.sha(audit_path)
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
    assert len(roots)==len(set(roots))==30 and not any(os.path.lexists(path) for path in roots)
    templates={}
    for slug in families:
        prior_children=eechildren if slug=='eeprom' else oldchildren;prior_population=eepop if slug=='eeprom' else oldpop
        assert set(prior_children['protocols'][slug])==set(names)
        for arm in order:
            record=prior_children['protocols'][slug][arm];_,plan=factory.pinned_json(Path(record['path']),record['sha256']);templates[slug,arm]=plan
            assert plan['source']==families[slug]['source'] and plan['source_hashes']==families[slug]['source_hashes'] and plan['source_rights']==families[slug]['source_rights']
            assert plan['whole_wall_full_cpu_seconds']==600 and plan['controller_args']==['--runtime',prior_population['runtime']]
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
    qualification=dict(admitted,path=str(INSTALL),sha256=INSTALL_SHA,runtime=str(RUNTIME),runtime_manifest_sha256=MANIFEST,source_head=HEAD,tools_files_sha256=tools['files'],original_cohort=dict(path=str(NATIVE),sha256=NATIVE_SHA,runtime=str(ORIGINAL_RUNTIME),runtime_manifest_sha256=ORIGINAL_MANIFEST),root_only_artifact_derivation=True,fresh_root_two_CLI_slices=True,actual_GUI_qualified=False,full_GUI_claim=False,scope='Exact unchanged artifact derived only at root plus actual two fresh-root CLI slices. Original058 cohort/IR lineage retained separately; no GUI or thermal qualification transferred.')
    assert p.sha(Path(__file__))==freezer_pin, "identity-port freezer changed"
    population=copy.deepcopy(oldpop)
    population.pop('identity_port_administration_change',None)
    population.update(runtime=str(RUNTIME),runtime_manifest_sha256=MANIFEST,source_head=HEAD,administration_head=a.expected_administration_head,families=families,planned_family_order=list(FAMILY_ORDER),outputs=outputs,tracked_administration_files_sha256=tracked,qualification=qualification,freezer_sha256=tracked['scripts/freeze_current_comparison.py'],enclosure_sha256=factory.ENCLOSURE_SHA,identity_port_freezer_sha256=freezer_pin,reporter_sha256=REPORTER_SHA,identity_port_template=dict(two_family_population_sha256=TEMPLATE_POPULATION_SHA,two_family_children_sha256=TEMPLATE_CHILDREN_SHA,eeprom_population_sha256=EEPROM_POPULATION_SHA,eeprom_children_sha256=EEPROM_CHILDREN_SHA,scope='Source/settings/protocol templates only; all18 outcomes require new058 execution, no057/058 singleton result transfer.'),disk_planning=dict(observed057_complete18arm_bytes=225531982,observed_files=8653,forecast_bytes=FORECAST_BYTES,retain_free_bytes=RETAIN_FREE_BYTES,scope='Specific old output roots only;1GiB allowance is a forecast, not a future quota. Recheck current free space before execution.'),Native_executed=False,actual_GUI=False)
    pop_pin=factory.save_new(BASE/'population.json',population)
    prereqs={str(path):p.sha(path) for path in [TEMPLATE/'sources.json',TEMPLATE/'population.json',TEMPLATE/'frozen-children.json',EEPROM/'sources.json',EEPROM/'population.json',EEPROM/'frozen-children.json',RUNTIME/pv.MANIFEST,BASE/'sources.json',BASE/'qualification.json',BASE/'population.json',child,Path(__file__),ROOT/'scripts/report_current_comparison.py',*[ROOT/name for name in tracked]]}
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
    assert len(commands)==18 and [(c['family'],c['arm']) for c in commands]==[(slug,arm) for slug in FAMILY_ORDER for arm in order]
    frozen=dict(schema=1,population_path=str(BASE/'population.json'),population_sha256=pop_pin,protocols=children,administration_head=a.expected_administration_head,policy_or_board_changes_after_first_arm=False,project_complete=False,sampled_setup_wall_seconds=time.monotonic()-START,sampled_setup_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,manual_sequential_commands=commands,scope='Fresh installed058 complete18-arm exposed-three-family rerun; all outcomes/failures/unstarted rows remain visible. No policy/source changes after first arm, new tuning/family/ancestry/holdout/broad-gain/GUI/human claim. Single worker; existing per-arm caps only, no new aggregate execution quota.')
    final_pin=factory.save_new(BASE/'frozen-children.json',frozen);fresh()
    assert p.sha(BASE/'frozen-children.json')==final_pin
    for rows in children.values():
        for record in rows.values():assert p.sha(Path(record['path']))==record['sha256']
    print(json.dumps(dict(prepared=True,executed=False,Native=False,engine=False,population=str(BASE/'population.json'),population_sha256=pop_pin,frozen_children_sha256=final_pin,protocols=18,source_head=HEAD,runtime_manifest_sha256=MANIFEST,freezer_sha256=freezer_pin)))
if __name__=='__main__':main()
