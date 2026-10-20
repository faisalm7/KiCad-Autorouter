"""DRAFT ONLY: labelled Native/CLI-only Devobordo049 development follow-up; no arm dispatch.

One unchanged exposed licensed source, all six arms420/450/600/export120 preregistered.
Reuse public freezer primitives, never its GUI-qualified freeze() entrypoint.
Only one bounded metadata/tools query runs when the lead executes this helper.
Keep its complete external exit/cost and all later arm failures. No GUI/Native
routing/DRC/download, CAD publication or original042 result rewriting here.
"""
from pathlib import Path
import copy, hashlib, json, math, os, resource, shutil, sys, time
START = time.monotonic()
def cpu():
    return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
PUBLIC = ROOT/'scripts/freeze_current_comparison.py'
PUBLIC_SHA = '7b46075113d271e87206462bfb614d1fd33cec483fca6f9b593ec87f271b2a64'
assert hashlib.sha256(PUBLIC.read_bytes()).hexdigest() == PUBLIC_SHA
from scripts import freeze_current_comparison as shared
assert Path(shared.__file__).resolve() == PUBLIC
pv, h, f, pref = shared.pv, shared.h, shared.f, shared.pref
require = shared.require
HEAD = '6e2357f975554478c2ba9fa35f18fdc3c1d194f9'
# Runtime source is fixed; require the lead's actual administration checkpoint at invocation.
MANIFEST = '70a388a6844d015350073401cb5f33bb1d552d1dc6195ece3aceee27baba5bd4'
SOURCES_SHA = '40254aaf8790681522b2b69a5edae3cbbdc6a2a5b24283d42e76d16c1017ab72'
NATIVE_FROZEN_SHA = '867a9ec09482546d0cd003bd472c5890edaf806b56040883a23350bf7a106225'
FULL_SHA = '092a71b050cd150e8cfa50317ca6ac4c9c53432fe725790ae78b96928e9f5b73'
STATIC_SHA = 'de6c0d1f75cf81d1aad0581add8b2ccbfab9247dbad9d7816abdd836c9b44f95'
DOCTOR_SHA = '6bb0764bd099eb0cec427aa1bd143fbc1793d5fd6b106f607123a8601802f9c2'
DOCTOR_PROCESS_SHA = '19b0db9f762fb4d2af1f8d21bcc4ccc2536a948b45d51691573cb522443d83e2'
NATIVE_PINS = {'improve-pour-only': {'protocol_sha256': '4d7de78189904093f45266d0008a3944fb5eec80e9945b7859c51e249faf2bb0', 'execution_sha256': '1427a8a53ea1eebadc55a273f1c2aa199c065e39c9f1655d56737c5ad8468307', 'child_sha256': 'ed294b982a69952d66d8433828094444901533437ad50df016fcb2e2746a88b5', 'route_sha256': 'cdbfa95620210f5a014bd6f9e95524c99a03d13046ca0db3d9ef498f8395dfcf', 'export_sha256': '0b0caa784637b532ceeff460962b3011a78f4284208c2c66d57df9a9207d416e'}, 'improve-fractional': {'protocol_sha256': '1cd61dd4113d6018eb11d132f57bef9fd6c1fd06e3bcf3af5a53cae41bdcbbd5', 'execution_sha256': '910ad2be66cecb5e5645ad155c31a4206557b16bcbd4c48a85724492738d2b7e', 'child_sha256': '05410af590cafba71cf9a44ae132d5ccda9e6d6a2c54c4b198a1a82de4ca4c7c', 'route_sha256': '7aa9664ea7ddda97784409ce495af6cb0f6cab5863137228931eeeec1fff6978', 'export_sha256': '5e96f869897e245f701e4b0a7f805fd17c9bfe9cb2839bbb8c955e5e3e9f01dc'}, 'improve-floor2Cu': {'protocol_sha256': 'c17cb9704524c5091efaad2dd23db3a49c8c0dbe5db62d8cd8c292aa6e5a9cf2', 'execution_sha256': '761e5370494f8d49bdad7a4ef9825e373ab1b76b0d7bbc7418c3a999b5dd6d54', 'child_sha256': 'c498792790319d45620d0f80ec8c6164e087c6a4ca259caea717f06984cb3370', 'route_sha256': 'ffd5171454a4fa90d8597de4c4bf543aacc2d5f696495faea8f2f072b911c770', 'export_sha256': 'b369e07d91b5f6f45fc3ecab6d94f6e3f359e6e8898cfb270679dcb903c43fd2'}, 'ordinary-alias2Cu': {'protocol_sha256': 'b5acf0e79ef7e5a68a78191d6ac2ed7f685e122d4524937fa30ed1e44363e78c', 'execution_sha256': 'd9778094228ddb3206b785bfed917a6b5b62fa02e390d0460cdd900d551561fd', 'child_sha256': '8e8f4ddce852251413cc7fc457c7983322fe9b1d00760673542ca61059b397f4', 'route_sha256': '4b5ea8affdeb2148e1c4c072bc42e8c5debbeddb870d17862df076d6ef4fca23', 'export_sha256': '7c039bd9f49bedc8e9031d5b8f78faab51293e8b0d58659d75d3f90f2f9c2851'}, 'ordinary-whole4Cu': {'protocol_sha256': 'a808231fa2dcdcb06e12745db5631aa50c6fc940aef23acbde1f8d891364cc1a', 'execution_sha256': '4a6edbbed17dffc4b334d20b1ca59a6c4923e292f0ac168129bf78ff9db7ac8d', 'child_sha256': '32f35f367a4b0f7a6f38846af04812b2e892110c7bcdd15a8e9b32dcb19d703a', 'route_sha256': '9b4440fab96eb6626c2b06bb7ba49ae91cbc58f59a6868eddc2985b07075604b', 'export_sha256': '2cbf4c93f034d50c4c0a0269a0757c77cea550fa03b0c34208f979394410cae9'}, 'ordinary-hierarchy2Cu': {'protocol_sha256': '523c3a6269ea09601cb3a0bceaf8e0c7d1463621a28491303c8304abbcb11aa1', 'execution_sha256': '9dacc9ca3077b67e14a5e6b05d58a68e89b473dc7baf0bff93a5becc7675d22b', 'child_sha256': 'f4a3b61a84788b22e6425a6907edbad5544bb45a227852aaa4374d5562a51b51', 'route_sha256': '5e16825ee2e178b592145d49972eab8d6bd04041564cd98d16a6255e80b8445f', 'export_sha256': '3e35bf73e1225fc742ce5bab9220115dc538c6a792d5fa96bed112ced64f5714'}}
runtime = ROOT/'.runs/runtime-directory-049/runtime'
output = ROOT/'.runs/runtime049-devobordo-development-followup-001'
sources_path = ROOT/'.runs/runtime045-devobordo-development-source-001.json'
native_root = ROOT/'.runs/runtime049-native-qualification-001'
native_frozen_path = native_root/'frozen.json'
full_path = ROOT/'.runs/full-integration-198/execution.json'
static_path = ROOT/'.runs/runtime045-devobordo-static-002/result.json'
doctor_path = native_root/'doctor.json'
doctor_process = doctor_path.with_name('doctor-process.json')

def freeze(ADMIN_HEAD):
    require(sys.platform == 'darwin', 'same-Mac selected7 follow-up only')
    require(Path(__file__).resolve() == ROOT/'.runs/freeze-runtime049-devobordo-followup-001.py', 'exact reviewed local wrapper required')
    self_pin = pv.file_digest(Path(__file__))[0]
    require(pv._directory(runtime) == runtime and pv._directory(runtime/'.runs').stat().st_uid == os.getuid(), 'existing owned049 runtime required')
    require(output.parent == ROOT/'.runs' and not os.path.lexists(output), 'fresh exclusive follow-up namespace required')
    manifest_raw, manifest = shared.pinned_json(runtime/pv.MANIFEST, MANIFEST)
    implementation = {name: pin for name,pin in pv._file_map(manifest.get('immutable_files_sha256')).items() if name.startswith('autorouter/')}
    identity = pv._runtime_identity(runtime, implementation)
    require(identity['git_head'] == HEAD and identity.get('native_version') == '10.0.7'
        and manifest['root'] == str(runtime) and manifest['local_engine'] is not None, 'exact current049 root/source/selected7 required')
    original_sources, source_spec = shared.pinned_json(sources_path, SOURCES_SHA)
    require(source_spec.get('schema') == 1 and source_spec.get('split') == 'development-exposed'
        and set(source_spec.get('families', {})) == {'devobordo'}, 'exact exposed Devobordo source manifest required')
    spec = copy.deepcopy(source_spec)
    families = shared.sources(spec, runtime)  # Hash/rights checks only; never parse or execute source CAD/hooks.
    _, frozen = shared.pinned_json(native_frozen_path, NATIVE_FROZEN_SHA)
    _, full = shared.pinned_json(full_path, FULL_SHA)
    _, static = shared.pinned_json(static_path, STATIC_SHA)
    require(full['passed'] is True and full['sources_unchanged'] is True, 'actual full198 prerequisite required')
    require(static['source_manifest_sha256'] == SOURCES_SHA and static['source_unchanged'] is True
        and static['Native_validation_performed'] is False and static['actual_GUI'] is False
        and static['preview']['static_preflight_passed'] is True
        and static['preview']['source'] == families['devobordo']['source']
        and static['preview']['source_sha256'] == families['devobordo']['source_hashes']['devboard.kicad_pcb'],
        'historical045 static source identity required; never Native admission')
    require(frozen['source_head'] == HEAD and frozen['runtime_manifest_sha256'] == MANIFEST
        and len(frozen['protocols']) == 6 and {row['case'] for row in frozen['protocols']} == set(NATIVE_PINS),
        'all six completed049 Native/CLI prerequisites required; frozen executed=False is historical preparation only')
    native_pins = {}; native_rows = []
    for row in frozen['protocols']:
        label = row['case']; expected = NATIVE_PINS[label]
        protocol = native_root/label/'protocol.json'; execution = protocol.with_name('execution.json')
        _, protocol_data = shared.pinned_json(protocol, expected['protocol_sha256'])
        _, result = shared.pinned_json(execution, expected['execution_sha256'])
        child_path = Path(protocol_data['output'])/'result.json'
        require(row['protocol'] == str(protocol) and row['protocol_sha256'] == expected['protocol_sha256']
            and protocol_data['runtime'] == str(runtime) and protocol_data['source_head'] == HEAD
            and protocol_data['runtime_manifest_sha256'] == MANIFEST and result['protocol_sha256'] == expected['protocol_sha256']
            and result['child_receipt'] == str(child_path) and result['child_sha256'] == expected['child_sha256'],
            'completed049 protocol/child custody differs')
        _, child_result = shared.pinned_json(child_path, expected['child_sha256'])
        process = result['process']; workspace = pv._directory(Path(child_result['workspace']))
        require(workspace.parent == Path(protocol_data['output']) and result['controls_passed'] is True
            and result['workflow_delivered'] is True and child_result['workflow_delivered'] is True
            and child_result['status'] == 'completed' and child_result['actual_GUI'] is False
            and child_result['source_hashes'] == protocol_data['source_hashes']
            and child_result['tools']['source_provenance'] == identity
            and process['status'] == 'success' and process['exit_code'] == 0 and process['cleanup_complete'] is True
            and process['log_truncated'] is False
            and max(result['complete_wall_seconds'],result['complete_full_CPU_seconds']) <= 240,
            'completed049 workflow/process/budget prerequisite refused')
        route = workspace/'route/result.json'; export = workspace/'export/export.json'
        _, routed = shared.pinned_json(route, expected['route_sha256'])
        _, exported = shared.pinned_json(export, expected['export_sha256'])
        require(routed['accepted'] is True and routed['status'] == 'routing_accepted'
            and exported['export_accepted'] is True and exported['status'] == 'export_validated'
            and routed['schematic_parity'] == exported['schematic_parity'] == 'checked by final native DRC'
            and routed['source_hashes'] == exported['source_hashes'] == protocol_data['source_hashes']
            and routed['candidate_sha256'] == exported['candidate_sha256']
            and all(record['native']['opens'] == record['native']['blocking'] == record['native']['exclusions'] == 0
                    for record in (routed,exported)), 'actual049 original/fullSCH/own-final prerequisite refused')
        cli=[path for path in protocol_data['tools']['files'] if path.endswith('/Contents/MacOS/kicad-cli')]
        require(len(cli)==1, 'exact selected Native CLI prerequisite required')
        for folder,record in ((workspace/'route',routed),(workspace/'export/validation',exported)):
            report = folder/'final-drc.json'; journal = folder/'final-drc-process.json'
            _, own = shared.pinned_json(journal, pv.file_digest(journal)[0])
            report_data=f.read_json(report)
            argv=[*(f.SANDBOX if folder==workspace/'export/validation' else []),cli[0],'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--schematic-parity','--exit-code-violations','--output',str(report),str(folder/'final-drc-input'/Path(protocol_data['source']).name)]
            f.process_check(folder,record,'final-drc',argv,allowed=(5 if any(report_data[key] for key in ('violations','unconnected_items','schematic_parity')) else 0,))
            require(pv.file_digest(Path(record['candidate']))[0] == record['candidate_sha256']
                and pv.file_digest(report)[0] == record['native_report_sha256']
                and '--schematic-parity' in own['argv'] and own['argv'][-1] == str(folder/'final-drc-input'/Path(protocol_data['source']).name)
                and own['cwd'] == str(folder) and own['cleanup_complete'] is True and own['log_truncated'] is False
                and own['status'] in ('success','nonzero_exit') and own['exit_code'] in (0,5),
                'actual049 own candidate/report/Native fullSCH journal differs')
            native_pins[str(report)] = pv.file_digest(report)[0]; native_pins[str(journal)] = pv.file_digest(journal)[0]
        for path,key in ((protocol,'protocol_sha256'),(execution,'execution_sha256'),(child_path,'child_sha256'),(route,'route_sha256'),(export,'export_sha256')):
            native_pins[str(path)] = expected[key]
        native_rows.append(dict(case=label,execution=str(execution),execution_sha256=expected['execution_sha256'],
            Native_counts=result['Native_counts'],protected_count=result['protected_count'],actual_GUI=False))
    doctor_pin, process_pin = DOCTOR_SHA, DOCTOR_PROCESS_SHA
    doctor = shared.pinned_json(doctor_path,doctor_pin)[1]; process = shared.pinned_json(doctor_process,process_pin)[1]
    require(doctor['ready'] is True and process['status'] == 'success' and process['exit_code'] == 0
        and process['cleanup_complete'] is True and process['log_truncated'] is False
        and process['cwd'] == str(runtime) and process['log'] == str(doctor_path), 'retained049 doctor/cleanup prerequisite refused')
    tracked = shared.administration(ADMIN_HEAD)
    require(tracked['scripts/freeze_current_comparison.py'] == PUBLIC_SHA and tracked['scripts/enclose_current_comparison.py'] == shared.ENCLOSURE_SHA, 'reviewed public helpers changed')
    require(shutil.disk_usage(ROOT).free >= 4*1024**3, 'at least4GiB startup headroom; not a six-arm aggregate quota')
    outputs = {arm:str(runtime/'.runs'/(('native7-comparison-' if arm.startswith('B') else 'native7-method-')+output.name+'-devobordo-'+arm)) for arm in shared.POPULATION}
    portfolio = Path(outputs['B2_portfolio']+'-portfolio')
    extras = [portfolio,*[Path(str(portfolio)+'-'+f'{i:02d}-'+variant) for i,variant in enumerate(shared.VARIANTS,1)]]
    roots = [Path(value) for value in outputs.values()]+extras
    require(len(set(roots)) == 10 and not any(os.path.lexists(pv.canonical(path)) for path in roots), 'all six method/four portfolio roots must be fresh before freeze')
    child = runtime/'.runs/qualify-current-method-001.py'; payload = pv.read_bytes(ROOT/'scripts/qualify_current_method.py')
    def copied_child():
        require(child.stat().st_uid == os.getuid() and child.stat().st_nlink == 1 and pv.read_bytes(child) == payload, 'copied child changed/unowned/linked')
    if os.path.lexists(child): copied_child()
    output.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, output)
    query, query_pins = shared.query_runtime(runtime, output); tools = query['tools']
    require(query['runtime'] == str(runtime) and query['interpreter'] == str(runtime/'.venv/bin/python') and query['prefix'] == str(runtime/'.venv')
        and query['defaults'] == dict(pref.DEFAULTS) and tools['source_provenance'] == identity and tools['implementation_sha256'] == implementation
        and tools['git_head'] == HEAD and tools['kicad'] == '10.0.7' and tools['comparison_route_policy'] == 'selected-native7-fixed-comparison-v2', 'actual049 query/source/defaults differ')
    require(type(tools.get('files')) is dict and 1 <= len(tools['files']) <= 8, 'bounded actual tool pins required')
    def fresh():
        require(h.owned_destination(owner) == output and shared.administration(ADMIN_HEAD) == tracked, 'administration/namespace changed')
        require(pv.file_digest(Path(__file__))[0] == self_pin and pv.file_digest(PUBLIC)[0] == PUBLIC_SHA, 'reviewed freezer bytes changed')
        for path,digest in ((sources_path,SOURCES_SHA),(native_frozen_path,NATIVE_FROZEN_SHA),(full_path,FULL_SHA),(static_path,STATIC_SHA),(doctor_path,doctor_pin),(doctor_process,process_pin)):
            shared.pinned_json(path,digest)
        for path,digest in native_pins.items(): require(pv.file_digest(Path(path),4*1024**2)[0] == digest, 'completed049 prerequisite material changed')
        require(pv.read_bytes(runtime/pv.MANIFEST,pv.MAX_MANIFEST_BYTES) == manifest_raw and pv._runtime_identity(runtime,implementation) == identity
            and shared.sources(spec,runtime) == families, 'runtime/source/native prerequisite changed')
        for path,digest in query_pins.items(): require(pv.file_digest(Path(path),512*1024)[0] == digest, 'actual query proof changed')
        for path,digest in tools['files'].items(): require(pv.file_digest(pv.canonical(Path(path)),pv.MAX_ENGINE_BYTES)[0] == digest, 'queried tool bytes changed')
        require(not any(os.path.lexists(path) for path in roots), 'an arm appeared before all six protocols were frozen')
        require(max(time.monotonic()-START,cpu()-CPU0) < 118, '120s setup acceptance cap/publication reserve exhausted; external exit still required')
    fresh()
    if not os.path.lexists(child):
        with child.open('xb') as stream: stream.write(payload)
    copied_child()
    shared.save_new(output/'sources.json',spec)
    qualification = dict(schema=1,kind='runtime049-labelled-native-CLI-Devobordo-prerequisites-v1',source_head=HEAD,runtime=str(runtime),runtime_manifest_sha256=MANIFEST,
        Native_frozen=dict(path=str(native_frozen_path),sha256=NATIVE_FROZEN_SHA),full198=dict(path=str(full_path),sha256=FULL_SHA),
        Native_workflows=native_rows,Native_material_sha256=native_pins,doctor=dict(path=str(doctor_path),sha256=doctor_pin,process_sha256=process_pin),
        historical_static045=dict(path=str(static_path),sha256=STATIC_SHA,Native_validation_performed=False),
        actual_GUI_qualified=False,full_GUI_claim=False,scope='Actual049 six completed Native/CLI workflows and doctor/full198 only. Historical045 static source eligibility is not Native validation. This does not satisfy or alter the public freezer042 GUI-qualified gate; no optionalImprove comparison arm.')
    shared.save_new(output/'native-only-prerequisites.json',qualification)
    defaults = pref.validate(dict(query['defaults'],seconds=420))
    population = dict(schema=1,kind='frozen-runtime049-labelled-Devobordo-native-CLI-development-followup-v1',population=list(shared.POPULATION),planned_family_order=['devobordo'],planned_arm_order=list(shared.ARM_ORDER),
        runtime=str(runtime),runtime_manifest_sha256=MANIFEST,source_head=HEAD,administration_head=ADMIN_HEAD,families=families,outputs={'devobordo':outputs},limits=dict(shared.LIMITS),default_settings=defaults,
        tracked_administration_files_sha256=tracked,freezer_sha256=self_pin,public_helper_sha256=PUBLIC_SHA,enclosure_sha256=shared.ENCLOSURE_SHA,qualification=qualification,
        prior_static=dict(path=str(static_path),sha256=STATIC_SHA,development_exposed=True,Native_validation_performed=False,original_results_unchanged=True),
        hypothesis='Measure current ordinary default and optional thermal recovery against unchanged B0/B1/tuned/restart baselines on one already exposed Devobordo source. Static eligibility is only a lead; Native routing, original-design validity and complete delivery may fail.',
        disposition='Integrate support only from actual qualified Native/source/protection/fullSCH/delivery evidence. Preserve valid negatives and unsupported/harness/cap failures separately. Revise only a demonstrated general defect after the frozen batch, otherwise defer; no board/constraint/policy tuning during it.',
        caveats='One already exposed Devobordo source; historical source-only diagnostic and original existing routing are disclosed. Native/CLI-only labelled development follow-up, not newGUI/untouched/independent-family or superiority result. B1default unchanged; B0 retains common fidelity safeguards. API/CLI delivery workloads differ: no generic speed claim. All source/candidate CAD/DSN/SES/plots/rawfindings remain LOCAL; creator MIT grant is recorded but optional model/asset/title rights closure and CAD redistribution are not authorized by the source manifest. No model/download/source-script execution; metadata-only reporting subject to publication audit. SameMac/account/externaldependencies; no newOS/standalone/Windows/human/physical/release claim.',Native_routing_or_DRC_executed=False,actual_GUI=False,project_complete=False)
    population_pin = shared.save_new(output/'population.json',population)
    paths = [sources_path,native_frozen_path,full_path,static_path,doctor_path,doctor_process,runtime/pv.MANIFEST,Path(__file__),output/'sources.json',output/'native-only-prerequisites.json',output/'population.json',output/'tools-defaults.json',output/'tools-defaults-process.json',child,*[ROOT/name for name in tracked]]
    prerequisites = {str(path):pv.file_digest(path,4*1024**2)[0] for path in paths}
    require(0 < len(prerequisites) <= 32, 'unchanged single-method prerequisite ceiling exceeded')
    children = {}; admin = {name:tracked[name] for name in shared.ADMIN_FILES[:3]}; entry = families['devobordo']
    for arm in shared.ARM_ORDER:
        folder = output/'devobordo'/arm; folder.mkdir(parents=True)
        common = dict(schema=1,runtime=str(runtime),runtime_manifest_sha256=MANIFEST,source_head=HEAD,tools=copy.deepcopy(tools),source=entry['source'],source_hashes=copy.deepcopy(entry['source_hashes']),source_rights=copy.deepcopy(entry['source_rights']),
            output=outputs[arm],administration_root=str(ROOT),whole_wall_full_cpu_seconds=600,pass_key='controls_passed',controller_args=['--runtime',str(runtime)],enclosure_sha256=shared.ENCLOSURE_SHA,
            population_protocol_path=str(output/'population.json'),population_protocol_sha256=population_pin,scope='Labelled exposed Devobordo049 Native-CLI development/'+arm+':420allocation/450method/600completewall+fullCPU/export120; no prior result rewrite, GUI/untouched/independent-family/superiority claim.')
        if arm == 'B2_portfolio':
            plan = dict(common,kind='installed-native7-comparison-portfolio-functional-v1',**shared.LIMITS,variants=list(shared.VARIANTS),allocation='balanced',trial_readback_reserve_seconds=30,root_finalization_reserve_seconds=15,
                installed_trial_accounting_policy='installed-route-readback-reserve-v1',comparison_api_policy='installed-native7-scored-portfolio-api-v2',administration_head=ADMIN_HEAD,administration_files_sha256=admin,
                family=entry['source_rights']['family'],controller=str(ROOT/shared.ADMIN_FILES[0]),controller_sha256=admin[shared.ADMIN_FILES[0]],portfolio_output=str(portfolio),material_roots=[str(path) for path in extras])
        else:
            plan = dict(common,kind='installed-native7-current-method-v1',arm=arm,population=list(shared.POPULATION),outputs=outputs,controller=str(child),controller_sha256=tracked['scripts/qualify_current_method.py'],qualifier_sha256=tracked['scripts/qualify_installed_workflow.py'],
                source_inventory_sha256=hashlib.sha256((f.canonical(entry['source_hashes'])+'\n').encode()).hexdigest(),source_rights_sha256=hashlib.sha256(f.canonical(entry['source_rights']).encode()).hexdigest(),prerequisite_sha256=prerequisites,default_settings=copy.deepcopy(defaults),limits=dict(shared.LIMITS))
        path = folder/'protocol.json'; children[arm] = dict(path=str(path),sha256=shared.save_new(path,plan))
    fresh(); copied_child()
    for item in children.values(): require(pv.file_digest(Path(item['path']),4*1024**2)[0] == item['sha256'], 'derived protocol changed')
    for path,digest in prerequisites.items(): require(pv.file_digest(Path(path),4*1024**2)[0] == digest, 'frozen prerequisite changed')
    record = dict(schema=1,kind='runtime049-labelled-native-CLI-Devobordo-six-arm-freeze-v1',population_path=str(output/'population.json'),population_sha256=population_pin,protocols={'devobordo':children},administration_head=ADMIN_HEAD,
        policy_or_board_changes_after_first_arm=False,project_complete=False,actual_GUI=False,Native_routing_or_DRC_executed=False,sampled_setup_wall_seconds=time.monotonic()-START,sampled_setup_full_CPU_seconds=cpu()-CPU0,
        setup_acceptance_cap_seconds=120,external_complete_exit_required=True,scope='Prepared protocols only. Lead dispatches sequentially after noGUIjob/Nativeworker busy; record all complete external exits/costs, including failures, against600wall+CPU perarm. Sixarms maximum3600wall/3600CPU, setup/full198/current049 qualification/diagnostics/GUI/admin costs additional; no aggregate disk quota or future outcome implied.')
    final_pin = shared.save_new(output/'frozen-children.json',record); fresh(); copied_child()
    require(pv.file_digest(output/'frozen-children.json',4*1024**2)[0] == final_pin, 'final freeze changed')
    return record

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--administration-head',required=True,help='Exact committed current administration HEAD; runtime source/build is separately fixed.')
    args=parser.parse_args()
    try:
        print(json.dumps(freeze(args.administration_head)))
    except (ValueError,OSError,shared.p.Rejected) as exc:
        print('Devobordo049 Native-CLI development freeze refused: '+str(exc),file=sys.stderr); raise SystemExit(2)
