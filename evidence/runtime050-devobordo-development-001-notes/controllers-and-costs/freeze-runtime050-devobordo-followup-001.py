"""DRAFT ONLY: labelled Native/CLI-only Devobordo050 development follow-up; no arm dispatch.

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
HEAD = 'aa0072c6b3d8090de2603e5ecb42a95968fb873b'
# Runtime source is fixed; require the lead's actual administration checkpoint at invocation.
MANIFEST = 'c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
SOURCES_SHA = '40254aaf8790681522b2b69a5edae3cbbdc6a2a5b24283d42e76d16c1017ab72'
NATIVE_FROZEN_SHA = 'c87576e2ca460c8bdb652ab72b8ebebbe9742336707a0563d6672c04d731e13e'
FULL_SHA = '47d02dd7c591b0e3efe7f7f01664d64558383a6a9f7223e3c2a91927d4c21268'
STATIC_SHA = 'de6c0d1f75cf81d1aad0581add8b2ccbfab9247dbad9d7816abdd836c9b44f95'
DOCTOR_SHA = '6747144141bac8dff333f2e6c2baa45c8406528f3f2a520f3175ae8590b2e6d1'
DOCTOR_PROCESS_SHA = '90a43958f8e188fab1450f988add963e70aa5a6d9a6fdff0d0b8b6fb735bdf7a'
NATIVE_CASES = {'ordinary-npth2Cu','improve-pour-only','improve-fractional',
                'improve-floor2Cu','ordinary-alias2Cu','ordinary-whole4Cu','ordinary-hierarchy2Cu'}
runtime = ROOT/'.runs/runtime-directory-050/runtime'
output = ROOT/'.runs/runtime050-devobordo-development-followup-001'
sources_path = ROOT/'.runs/runtime045-devobordo-development-source-001.json'
native_root = ROOT/'.runs/runtime050-native-qualification-001'
native_frozen_path = native_root/'frozen.json'
full_path = ROOT/'.runs/full-integration-199/execution.json'
static_path = ROOT/'.runs/runtime045-devobordo-static-002/result.json'
doctor_path = native_root/'doctor.json'
doctor_process = doctor_path.with_name('doctor-process.json')

def freeze(ADMIN_HEAD):
    require(sys.platform == 'darwin', 'same-Mac selected7 follow-up only')
    require(Path(__file__).resolve() == ROOT/'.runs/freeze-runtime050-devobordo-followup-001.py', 'exact reviewed local wrapper required')
    self_pin = pv.file_digest(Path(__file__))[0]
    tracked = shared.administration(ADMIN_HEAD)
    require(pv._directory(runtime) == runtime and pv._directory(runtime/'.runs').stat().st_uid == os.getuid(), 'existing owned050 runtime required')
    require(output.parent == ROOT/'.runs' and not os.path.lexists(output), 'fresh exclusive follow-up namespace required')
    manifest_raw, manifest = shared.pinned_json(runtime/pv.MANIFEST, MANIFEST)
    implementation = {name: pin for name,pin in pv._file_map(manifest.get('immutable_files_sha256')).items() if name.startswith('autorouter/')}
    identity = pv._runtime_identity(runtime, implementation)
    require(identity['git_head'] == HEAD and identity.get('native_version') == '10.0.7'
        and manifest['root'] == str(runtime) and manifest['local_engine'] is not None, 'exact current050 root/source/selected7 required')
    original_sources, source_spec = shared.pinned_json(sources_path, SOURCES_SHA)
    require(source_spec.get('schema') == 1 and source_spec.get('split') == 'development-exposed'
        and set(source_spec.get('families', {})) == {'devobordo'}, 'exact exposed Devobordo source manifest required')
    spec = copy.deepcopy(source_spec)
    families = shared.sources(spec, runtime)  # Hash/rights checks only; never parse or execute source CAD/hooks.
    _, frozen = shared.pinned_json(native_frozen_path, NATIVE_FROZEN_SHA)
    _, full = shared.pinned_json(full_path, FULL_SHA)
    full_plan_path = full_path.with_name('protocol.json'); full_plan_pin = pv.file_digest(full_plan_path)[0]
    _, full_plan = shared.pinned_json(full_plan_path, full_plan_pin)
    require(full_plan['tools']['git_head'] == HEAD
        and all(full_plan['source_sha256'].get(name) == pin for name,pin in implementation.items())
        and full['process']['status'] == 'success' and full['process']['exit_code'] == 0
        and full['process']['cleanup_complete'] is True and full['process']['log_truncated'] is False,
        'full199 source/process identity differs')
    _, static = shared.pinned_json(static_path, STATIC_SHA)
    require(full['passed'] is True and full['sources_unchanged'] is True, 'actual full199 prerequisite required')
    require(static['source_manifest_sha256'] == SOURCES_SHA and static['source_unchanged'] is True
        and static['Native_validation_performed'] is False and static['actual_GUI'] is False
        and static['preview']['static_preflight_passed'] is True
        and static['preview']['source'] == families['devobordo']['source']
        and static['preview']['source_sha256'] == families['devobordo']['source_hashes']['devboard.kicad_pcb'],
        'historical045 static source identity required; never Native admission')
    require(frozen['source_head'] == HEAD and frozen['runtime_manifest_sha256'] == MANIFEST
        and type(frozen['protocols']) is list and len(frozen['protocols']) == 7 and {row['case'] for row in frozen['protocols']} == NATIVE_CASES,
        'all seven completed050 Native/CLI prerequisites required; frozen executed=False is historical preparation only')
    native_pins = {}; native_rows = []; native_material = {}; native_sources = {}; packets = []; pairs = []; native_cli = None; native_tools = None
    from autorouter import local_settings as local
    for row in frozen['protocols']:
        label = row['case']; expected = {'protocol_sha256':row['protocol_sha256']}
        protocol = native_root/label/'protocol.json'; execution = protocol.with_name('execution.json')
        expected['execution_sha256'] = pv.file_digest(execution,4*1024**2)[0]
        _, protocol_data = shared.pinned_json(protocol, expected['protocol_sha256'])
        _, result = shared.pinned_json(execution, expected['execution_sha256'])
        require(protocol_data['schema'] == 1 and protocol_data['kind'] == 'runtime050-six-stage-route-or-improve-CLI'
            and protocol_data['case'] == label and protocol_data['method'] == row['method']
            and protocol_data['output'] == str(runtime/'.runs'/(label+'-001')), 'exact fresh050 case/output required')
        child_path = Path(protocol_data['output'])/'result.json'
        expected['child_sha256'] = pv.file_digest(child_path,4*1024**2)[0]
        require(row['protocol'] == str(protocol) and row['protocol_sha256'] == expected['protocol_sha256']
            and protocol_data['runtime'] == str(runtime) and protocol_data['source_head'] == HEAD
            and protocol_data['runtime_manifest_sha256'] == MANIFEST and result['protocol_sha256'] == expected['protocol_sha256']
            and result['child_receipt'] == str(child_path) and result['child_sha256'] == expected['child_sha256'],
            'completed050 protocol/child custody differs')
        _, child_result = shared.pinned_json(child_path, expected['child_sha256'])
        process = result['process']; workspace = pv._directory(Path(child_result['workspace']))
        require(workspace.parent == Path(protocol_data['output']) and result['controls_passed'] is True
            and result['workflow_delivered'] is True and child_result['workflow_delivered'] is True
            and child_result['status'] == 'completed' and child_result['actual_GUI'] is False
            and child_result['source_hashes'] == protocol_data['source_hashes']
            and child_result['tools']['source_provenance'] == identity
            and process['status'] == 'success' and process['exit_code'] == 0 and process['cleanup_complete'] is True
            and process['log_truncated'] is False
            and all(type(value) in (int,float) and math.isfinite(value) and 0 <= value <= 240
                for value in (result['complete_wall_seconds'],result['complete_full_CPU_seconds'])),
            'completed050 workflow/process/budget prerequisite refused')
        if native_tools is None: native_tools = protocol_data['tools']
        require(protocol_data['tools'] == native_tools, 'Native prerequisite tool populations differ')
        source = pv.canonical(Path(protocol_data['source'])); hashes = protocol_data['source_hashes']
        require(shared.io.inventory(source.parent) == hashes, 'Native prerequisite original source changed')
        native_sources[str(source.parent)] = hashes
        require(child_result['source'] == str(source) and child_result['settings'] == protocol_data['settings']
            and [item['stage'] for item in child_result['processes']] == ['preview','route','review','choice','export','verify_export'],
            'six current stages/source/settings required')
        for item in child_result['processes']:
            process_row = item['process']; log = Path(protocol_data['output'])/(item['stage']+'.log')
            require(process_row['exit_code'] == 0 and process_row['cancel_requested'] is False
                and process_row['log_truncated'] is False and pv.file_digest(log)[0] == item['log_sha256'], 'Native workflow stage failed or changed')
        route = workspace/'route/result.json'; export = workspace/'export/export.json'
        expected['route_sha256'] = pv.file_digest(route,4*1024**2)[0]; expected['export_sha256'] = pv.file_digest(export,4*1024**2)[0]
        _, routed = shared.pinned_json(route, expected['route_sha256'])
        _, exported = shared.pinned_json(export, expected['export_sha256'])
        require(routed['accepted'] is True and routed['status'] == 'routing_accepted'
            and exported['export_accepted'] is True and exported['status'] == 'export_validated'
            and routed['schematic_parity'] == exported['schematic_parity'] == 'checked by final native DRC'
            and routed['source_hashes'] == exported['source_hashes'] == protocol_data['source_hashes']
            and routed['candidate_sha256'] == exported['candidate_sha256']
            and all(record['native']['opens'] == record['native']['blocking'] == record['native']['exclusions'] == 0
                    for record in (routed,exported)), 'actual050 original/fullSCH/own-final prerequisite refused')
        require(routed['tools'] == exported['tools'] == child_result['tools'] == protocol_data['tools']
            and routed['candidate_sha256'] == child_result['candidate_sha256']
            and routed['invariants_unchanged'] is True and exported['original_geometry_and_routing_unchanged'] is True
            and exported['inputs']['source'] == str(source) and exported['inputs']['receipt'] == str(route)
            and exported['inputs']['receipt_sha256'] == expected['route_sha256'], 'Native original/export lineage differs')
        settings = protocol_data['settings']; original = shared.p.sx.read(source)
        protected = shared.p.protected_for_record(routed,original)
        require(len(protected) == protocol_data['expected_protected_count']
            and routed['scope'] == settings['scope'] and routed['adapter'] == settings['adapter']
            and routed['engine_profile'] == settings['profile']
            and routed['budget_seconds'] == routed['cpu_budget_seconds'] == protocol_data['budgets']['route']
            and exported['budget_seconds'] == exported['cpu_budget_seconds'] == protocol_data['budgets']['export'], 'Native task/protection/budget binding differs')
        actual_counts = [routed['native'][key] for key in ('opens','blocking','warnings','exclusions')]
        require(actual_counts == [exported['native'][key] for key in ('opens','blocking','warnings','exclusions')] == result['Native_counts']
            and all(type(n) is int and n >= 0 for n in actual_counts)
            and result['protected_count'] == protocol_data['expected_protected_count'], 'Native/protection counts differ')
        if protocol_data['expected_counts'] is None:
            require(protocol_data['warning_policy'] == 'retain_all_native_findings' and actual_counts[3] == protocol_data['expected_exclusions'], 'Native warning/exclusion policy differs')
        else: require(actual_counts == protocol_data['expected_counts'], 'Native control findings differ')
        cli=[path for path in protocol_data['tools']['files'] if path.endswith('/Contents/MacOS/kicad-cli')]
        require(len(cli)==1 and (native_cli is None or native_cli == Path(cli[0])), 'exact selected Native CLI prerequisite required')
        native_cli = Path(cli[0])
        for folder,record in ((workspace/'route',routed),(workspace/'export/validation',exported)):
            report = folder/'final-drc.json'; journal = folder/'final-drc-process.json'
            _, own = shared.pinned_json(journal, pv.file_digest(journal)[0])
            report_data=f.read_json(report)
            binding_path=folder/'final-drc-binding.json'; binding=f.read_json(binding_path)
            candidate=folder/'candidate'/source.name; final_hashes=dict(hashes);final_hashes[source.name]=record['candidate_sha256']
            require(record['candidate'] == str(candidate) and binding['source'] == str(candidate)
                and binding['input'] == str(folder/'final-drc-input'/source.name) and binding['saved'] is False
                and binding['before'] == final_hashes and shared.io.inventory(folder/'final-drc-input') == binding['after']
                and all(binding['after'].get(name) == pin for name,pin in final_hashes.items())
                and not (set(binding['after'])-set(final_hashes)-{source.with_suffix('.kicad_prl').name}), 'Native original/fullSCH final input changed')
            shared.p.verify_candidate_files(candidate,hashes,record['candidate_sha256'])
            candidate_tree = shared.p.sx.read(candidate)
            require(shared.p.immutable(candidate_tree) == shared.p.immutable(original)
                and all(item in shared.p.routes(candidate_tree) for item in protected), 'Native original/protected geometry changed')
            findings=report_data['violations']+report_data['unconnected_items']+report_data['schematic_parity']
            raw_counts=[len(report_data['unconnected_items']),sum(item['severity']=='error' for item in report_data['violations']+report_data['schematic_parity']),
                sum(item['severity']=='warning' for item in findings),sum(item['severity']=='exclusion' or item.get('excluded',False) for item in findings)]
            require(report_data['kicad_version']=='10.0.7' and report_data['source']==source.name
                and set(report_data['included_severities'])=={'error','warning','exclusion'}
                and raw_counts==actual_counts and record['native']['findings']==findings
                and record['native']['ignored_checks']==report_data['ignored_checks'], 'own raw Native report scope/findings differ')
            packets.append((folder,record))
            argv=[*(f.SANDBOX if folder==workspace/'export/validation' else []),cli[0],'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--schematic-parity','--exit-code-violations','--output',str(report),str(folder/'final-drc-input'/Path(protocol_data['source']).name)]
            f.process_check(folder,record,'final-drc',argv,allowed=(5 if any(report_data[key] for key in ('violations','unconnected_items','schematic_parity')) else 0,))
            require(pv.file_digest(Path(record['candidate']))[0] == record['candidate_sha256']
                and pv.file_digest(report)[0] == record['native_report_sha256']
                and '--schematic-parity' in own['argv'] and own['argv'][-1] == str(folder/'final-drc-input'/Path(protocol_data['source']).name)
                and own['cwd'] == str(folder) and own['cleanup_complete'] is True and own['log_truncated'] is False
                and own['status'] in ('success','nonzero_exit') and own['exit_code'] in (0,5),
                'actual050 own candidate/report/Native fullSCH journal differs')
            native_pins[str(report)] = pv.file_digest(report)[0]; native_pins[str(journal)] = pv.file_digest(journal)[0]
            native_pins[str(binding_path)] = pv.file_digest(binding_path)[0]
        for path,key in ((protocol,'protocol_sha256'),(execution,'execution_sha256'),(child_path,'child_sha256'),(route,'route_sha256'),(export,'export_sha256')):
            native_pins[str(path)] = expected[key]
        review_path=workspace/'review/review.json';review=f.read_json(review_path);plot=workspace/'review/plot-work'
        require(review['receipt_sha256']==expected['route_sha256'] and review['candidate_sha256']==routed['candidate_sha256'], 'Native review lineage differs')
        for step in review['preview']['steps']:
            process_row=f.process_check(plot,review['preview'],step['name'],step['argv'])
            pairs.append((plot,f.read_json(plot/(step['name']+'-input-binding.json')),process_row))
        native_material[protocol_data['output']]=shared.io.inventory(Path(protocol_data['output']),max_bytes=256*1024**2,max_files=8000,max_entries=16000)
        native_rows.append(dict(case=label,execution=str(execution),completed_receipts_sha256=expected,
            Native_counts=result['Native_counts'],protected_count=result['protected_count'],actual_GUI=False))
    doctor_pin, process_pin = DOCTOR_SHA, DOCTOR_PROCESS_SHA
    doctor = shared.pinned_json(doctor_path,doctor_pin)[1]; process = shared.pinned_json(doctor_process,process_pin)[1]
    require(doctor['ready'] is True and process['status'] == 'success' and process['exit_code'] == 0
        and process['cleanup_complete'] is True and process['log_truncated'] is False
        and process['cwd'] == str(runtime) and process['log'] == str(doctor_path)
        and doctor['workspace'] == str(runtime) and doctor['checks']['runtime_provenance'] == {'verified':True,'identity':identity}, 'retained050 doctor/cleanup prerequisite refused')
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
        and query['defaults'] == dict(pref.DEFAULTS) and tools == native_tools and tools['source_provenance'] == identity and tools['implementation_sha256'] == implementation
        and tools['git_head'] == HEAD and tools['kicad'] == '10.0.7' and tools['comparison_route_policy'] == 'selected-native7-fixed-comparison-v2', 'actual050 query/source/defaults differ')
    require(type(tools.get('files')) is dict and 1 <= len(tools['files']) <= 8, 'bounded actual tool pins required')
    def fresh():
        require(h.owned_destination(owner) == output and shared.administration(ADMIN_HEAD) == tracked, 'administration/namespace changed')
        require(pv.file_digest(Path(__file__))[0] == self_pin and pv.file_digest(PUBLIC)[0] == PUBLIC_SHA, 'reviewed freezer bytes changed')
        for path,digest in ((sources_path,SOURCES_SHA),(native_frozen_path,NATIVE_FROZEN_SHA),(full_path,FULL_SHA),(full_plan_path,full_plan_pin),(static_path,STATIC_SHA),(doctor_path,doctor_pin),(doctor_process,process_pin)):
            shared.pinned_json(path,digest)
        for name,hashes in native_sources.items(): require(shared.io.inventory(Path(name)) == hashes, 'Native prerequisite source changed')
        for name,hashes in native_material.items(): require(shared.io.inventory(Path(name),max_bytes=256*1024**2,max_files=8000,max_entries=16000) == hashes, 'Native prerequisite material changed')
        for path,digest in native_pins.items(): require(pv.file_digest(Path(path),4*1024**2)[0] == digest, 'completed050 prerequisite material changed')
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
    qualification = dict(schema=1,kind='runtime050-labelled-native-CLI-Devobordo-prerequisites-v1',source_head=HEAD,runtime=str(runtime),runtime_manifest_sha256=MANIFEST,
        Native_frozen=dict(path=str(native_frozen_path),sha256=NATIVE_FROZEN_SHA),full199=dict(path=str(full_path),sha256=FULL_SHA),
        Native_workflows=native_rows,Native_material_sha256=native_pins,Native_material_roots=native_material,Native_source_roots=native_sources,doctor=dict(path=str(doctor_path),sha256=doctor_pin,process_sha256=process_pin),
        historical_static045=dict(path=str(static_path),sha256=STATIC_SHA,Native_validation_performed=False),
        actual_GUI_qualified=False,full_GUI_claim=False,scope='Actual050 seven completed Native/CLI workflows and doctor/full199 only. Historical045 static source eligibility is not Native validation. This does not satisfy or alter the public freezer042 GUI-qualified gate; no optionalImprove comparison arm.')
    shared.save_new(output/'native-only-prerequisites.json',qualification)
    defaults = pref.validate(dict(query['defaults'],seconds=420))
    population = dict(schema=1,kind='frozen-runtime050-labelled-Devobordo-native-CLI-development-followup-v1',population=list(shared.POPULATION),planned_family_order=['devobordo'],planned_arm_order=list(shared.ARM_ORDER),
        runtime=str(runtime),runtime_manifest_sha256=MANIFEST,source_head=HEAD,administration_head=ADMIN_HEAD,families=families,outputs={'devobordo':outputs},limits=dict(shared.LIMITS),default_settings=defaults,
        tracked_administration_files_sha256=tracked,freezer_sha256=self_pin,public_helper_sha256=PUBLIC_SHA,enclosure_sha256=shared.ENCLOSURE_SHA,qualification=qualification,
        prior_static=dict(path=str(static_path),sha256=STATIC_SHA,development_exposed=True,Native_validation_performed=False,original_results_unchanged=True),
        hypothesis='Measure current ordinary default and optional thermal recovery against unchanged B0/B1/tuned/restart baselines on one already exposed Devobordo source. Static eligibility is only a lead; Native routing, original-design validity and complete delivery may fail.',
        disposition='Integrate support only from actual qualified Native/source/protection/fullSCH/delivery evidence. Preserve valid negatives and unsupported/harness/cap failures separately. Revise only a demonstrated general defect after the frozen batch, otherwise defer; no board/constraint/policy tuning during it.',
        caveats='One already exposed Devobordo source; historical source-only diagnostic and original existing routing are disclosed. Native/CLI-only labelled development follow-up, not newGUI/untouched/independent-family or superiority result. B1default unchanged; B0 retains common fidelity safeguards. API/CLI delivery workloads differ: no generic speed claim. All source/candidate CAD/DSN/SES/plots/rawfindings remain LOCAL; creator MIT grant is recorded but optional model/asset/title rights closure and CAD redistribution are not authorized by the source manifest. No model/download/source-script execution; metadata-only reporting subject to publication audit. SameMac/account/externaldependencies; no newOS/standalone/Windows/human/physical/release claim.',Native_routing_or_DRC_executed=False,actual_GUI=False,project_complete=False)
    population_pin = shared.save_new(output/'population.json',population)
    paths = [sources_path,native_frozen_path,full_path,full_plan_path,static_path,doctor_path,doctor_process,runtime/pv.MANIFEST,Path(__file__),output/'sources.json',output/'native-only-prerequisites.json',output/'population.json',output/'tools-defaults.json',output/'tools-defaults-process.json',child,*[ROOT/name for name in tracked]]
    prerequisites = {str(path):pv.file_digest(path,4*1024**2)[0] for path in paths}
    require(0 < len(prerequisites) <= 32, 'unchanged single-method prerequisite ceiling exceeded')
    children = {}; admin = {name:tracked[name] for name in shared.ADMIN_FILES[:3]}; entry = families['devobordo']
    for arm in shared.ARM_ORDER:
        folder = output/'devobordo'/arm; folder.mkdir(parents=True)
        common = dict(schema=1,runtime=str(runtime),runtime_manifest_sha256=MANIFEST,source_head=HEAD,tools=copy.deepcopy(tools),source=entry['source'],source_hashes=copy.deepcopy(entry['source_hashes']),source_rights=copy.deepcopy(entry['source_rights']),
            output=outputs[arm],administration_root=str(ROOT),whole_wall_full_cpu_seconds=600,pass_key='controls_passed',controller_args=['--runtime',str(runtime)],enclosure_sha256=shared.ENCLOSURE_SHA,
            population_protocol_path=str(output/'population.json'),population_protocol_sha256=population_pin,scope='Labelled exposed Devobordo050 Native-CLI development/'+arm+':420allocation/450method/600completewall+fullCPU/export120; no prior result rewrite, GUI/untouched/independent-family/superiority claim.')
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
    record = dict(schema=1,kind='runtime050-labelled-native-CLI-Devobordo-six-arm-freeze-v1',population_path=str(output/'population.json'),population_sha256=population_pin,protocols={'devobordo':children},administration_head=ADMIN_HEAD,
        policy_or_board_changes_after_first_arm=False,project_complete=False,actual_GUI=False,Native_routing_or_DRC_executed=False,sampled_setup_wall_seconds=time.monotonic()-START,sampled_setup_full_CPU_seconds=cpu()-CPU0,
        setup_acceptance_cap_seconds=120,external_complete_exit_required=True,scope='Prepared protocols only. Lead dispatches sequentially after noGUIjob/Nativeworker busy; record all complete external exits/costs, including failures, against600wall+CPU perarm. Sixarms maximum3600wall/3600CPU, setup/full199/current050 qualification/diagnostics/GUI/admin costs additional; no aggregate disk quota or future outcome implied.')
    final_pin = shared.save_new(output/'frozen-children.json',record); fresh(); copied_child()
    require(pv.file_digest(output/'frozen-children.json',4*1024**2)[0] == final_pin, 'final freeze changed')
    local.check_final_events(packets,native_cli,pairs=pairs)  # All callbacks/material reads precede the last PRL fence.
    require(max(time.monotonic()-START,cpu()-CPU0) < 120, '120s setup acceptance cap exceeded after metadata fence')
    return record

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--administration-head',required=True,help='Exact committed current administration HEAD; runtime source/build is separately fixed.')
    args=parser.parse_args()
    try:
        print(json.dumps(freeze(args.administration_head)))
    except (ValueError,OSError,shared.p.Rejected) as exc:
        print('Devobordo050 Native-CLI development freeze refused: '+str(exc),file=sys.stderr); raise SystemExit(2)
