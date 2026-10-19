"""DRAFT ONLY: labelled native-only IR043 support follow-up; no arm dispatch.

One unchanged exposed source, all six arms420/450/600/export120 preregistered.
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
HEAD = '6ec7ad2344ed060d5e0971965ef05bd9de68925d'
ADMIN_HEAD = '27acfe8f04ef87013fbb27a633e557a83e900b65'
MANIFEST = '6fdfe60bcbe6aecc2c950a6917b22d8e591f5ae3078eca5a52ae051a1aac5aa3'
SOURCES_SHA = 'b2644892c7fc718aef2791fa12d9a6fddee2a7e30c64fcb3cde993fdbfa13688'
MILESTONE_SHA = 'ea2831238c65bc1e752cd464042c8cf2f79e3e513e6d096f625c6eabe07d07e2'
INVALID_SHA = '0822f60c8e0a5caffe56d93e4c606f418cfd50cf8c719701e44de8bbcfea777b'
PRIOR_SHA = 'a9aaf1edeedb224e046cbf3fb69c2e3b73e60993fe0caaaa8e5b945c737b2f60'
runtime = ROOT/'.runs/runtime-directory-043/runtime'
output = ROOT/'.runs/runtime043-ir-support-followup-001'
sources_path = ROOT/'.runs/runtime042-unrelated-development-sources-001.json'
milestone_path = ROOT/'evidence/runtime043-native-milestone-001.json'
invalid_path = ROOT/'evidence/runtime043-native-invalid-001.json'
prior_path = ROOT/'evidence/runtime042-unrelated-development-comparison-001.json'
doctor_path = ROOT/'.runs/runtime043-native-qualification-001/doctor.json'
doctor_process = doctor_path.with_name('doctor-process.json')

def freeze():
    require(sys.platform == 'darwin', 'same-Mac selected7 follow-up only')
    require(Path(__file__).resolve() == ROOT/'.runs/freeze-runtime043-ir-followup-001.py', 'exact reviewed local wrapper required')
    self_pin = pv.file_digest(Path(__file__))[0]
    require(pv._directory(runtime) == runtime and pv._directory(runtime/'.runs').stat().st_uid == os.getuid(), 'existing owned043 runtime required')
    require(output.parent == ROOT/'.runs' and not os.path.lexists(output), 'fresh exclusive follow-up namespace required')
    manifest_raw, manifest = shared.pinned_json(runtime/pv.MANIFEST, MANIFEST)
    implementation = {name: pin for name,pin in pv._file_map(manifest.get('immutable_files_sha256')).items() if name.startswith('autorouter/')}
    identity = pv._runtime_identity(runtime, implementation)
    require(identity['git_head'] == HEAD and identity.get('native_version') == '10.0.7'
        and manifest['root'] == str(runtime) and manifest['local_engine'] is not None, 'exact current043 root/source/selected7 required')
    original_sources, source_spec = shared.pinned_json(sources_path, SOURCES_SHA)
    require(source_spec.get('schema') == 1 and source_spec.get('split') == 'development-exposed'
        and set(source_spec.get('families', {})) == {'ds18b20','ir-obstacle'}, 'exact prior exposed source manifest required')
    spec = dict(schema=1,split='development-exposed',families={'ir-obstacle':copy.deepcopy(source_spec['families']['ir-obstacle'])})
    families = shared.sources(spec, runtime)  # Hash/rights checks ONLY for IR, never parse source CAD.
    milestone_raw, milestone = shared.pinned_json(milestone_path, MILESTONE_SHA)
    invalid_raw, invalid = shared.pinned_json(invalid_path, INVALID_SHA)
    prior_raw, prior = shared.pinned_json(prior_path, PRIOR_SHA)
    require(milestone['kind'] == 'runtime043-eight-ordinary-Native-regressions-facts-only-v1'
        and milestone['source_head'] == HEAD and milestone['runtime_manifest_sha256'] == MANIFEST
        and milestone['immutable_files_sha256'] == manifest['immutable_files_sha256']
        and milestone['RuntimeCore_sha256'] == implementation and milestone['full190']['passed'] is True
        and milestone['accepted'] is False and milestone['actual_GUI'] is False, 'completed current043 Native prerequisite required; no GUI transfer')
    require({row['case'] for row in milestone['Native_deliveries']} == {'alias2Cu','whole4Cu','partial2Cu','hierarchy-whole2Cu','floor-2Cu','floor-4Cu','sonde-whole','fractional-owned'}
        and len(milestone['Native_deliveries']) == 8, 'all eight actual043 prerequisite cases required')
    for row in milestone['Native_deliveries']:
        require(row['source_unchanged'] is True and row['Native_counts'][0:2] == [0,0] and row['Native_counts'][3] == 0
            and row['own_final']['route']['candidate_sha256'] == row['own_final']['export']['candidate_sha256']
            and all(row['own_final'][name]['own_final']['full_schematic_flag'] is True for name in ('route','export')),
            'stored043 source/fullSCH/own-final prerequisite refused')
    require(invalid['kind'] == 'runtime043-actual-short-and-protected-width-invalid-facts-v1'
        and invalid['source_head'] == HEAD and invalid['runtime_manifest_sha256'] == MANIFEST
        and invalid['control_passed'] is True and invalid['source_unchanged'] is True and invalid['accepted'] is False,
        'actual043 invalid-control prerequisite required')
    negatives = {row['label']:row for row in invalid['cases']}
    require(set(negatives) == {'partial-short','partial-protected-width'} and len(invalid['cases']) == 2
        and all(row['control_observed'] is True and row['accepted'] is False and row['routing_accepted'] is False for row in negatives.values())
        and negatives['partial-short']['Native_counts'][1] > 0
        and negatives['partial-protected-width']['Native_counts'] == [0,0,0,0]
        and negatives['partial-protected-width']['no_additional_native_after_invariant_refusal'] is True,
        'observed short and Native-clean protected-mutation refusals required')
    doctor_pin = pv.file_digest(doctor_path)[0]; process_pin = pv.file_digest(doctor_process)[0]
    doctor = shared.pinned_json(doctor_path, doctor_pin)[1]; process = shared.pinned_json(doctor_process, process_pin)[1]
    require(doctor['ready'] is True and process['status'] == 'success' and process['exit_code'] == 0
        and process['cleanup_complete'] is True and process['log_truncated'] is False
        and process['cwd'] == str(runtime) and process['log'] == str(doctor_path), 'retained043 doctor/cleanup prerequisite refused')
    require(prior['source_head'] == '82aaa3b750007ef2ffaafd367ffcb718aa93865e' and prior['confirmatory'] is False, 'original042 failed cohort identity changed')
    tracked = shared.administration(ADMIN_HEAD)
    require(tracked['scripts/freeze_current_comparison.py'] == PUBLIC_SHA and tracked['scripts/enclose_current_comparison.py'] == shared.ENCLOSURE_SHA, 'reviewed public helpers changed')
    require(shutil.disk_usage(ROOT).free >= 4*1024**3, 'at least4GiB startup headroom; not a six-arm aggregate quota')
    outputs = {arm:str(runtime/'.runs'/(('native7-comparison-' if arm.startswith('B') else 'native7-method-')+output.name+'-ir-obstacle-'+arm)) for arm in shared.POPULATION}
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
        and tools['git_head'] == HEAD and tools['kicad'] == '10.0.7' and tools['comparison_route_policy'] == 'selected-native7-fixed-comparison-v2', 'actual043 query/source/defaults differ')
    require(type(tools.get('files')) is dict and 1 <= len(tools['files']) <= 8, 'bounded actual tool pins required')
    def fresh():
        require(h.owned_destination(owner) == output and shared.administration(ADMIN_HEAD) == tracked, 'administration/namespace changed')
        require(pv.file_digest(Path(__file__))[0] == self_pin and pv.file_digest(PUBLIC)[0] == PUBLIC_SHA, 'reviewed freezer bytes changed')
        for path,digest in ((sources_path,SOURCES_SHA),(milestone_path,MILESTONE_SHA),(invalid_path,INVALID_SHA),(prior_path,PRIOR_SHA),(doctor_path,doctor_pin),(doctor_process,process_pin)):
            shared.pinned_json(path,digest)
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
    qualification = dict(schema=1,kind='runtime043-labelled-native-only-IR-followup-prerequisites-v1',source_head=HEAD,runtime=str(runtime),runtime_manifest_sha256=MANIFEST,
        Native_milestone=dict(path=str(milestone_path),sha256=MILESTONE_SHA),Native_invalid=dict(path=str(invalid_path),sha256=INVALID_SHA),doctor=dict(path=str(doctor_path),sha256=doctor_pin,process_sha256=process_pin),
        actual_GUI_qualified=False,full_GUI_claim=False,scope='Actual043 Native regressions/invalid/doctor only. This does not satisfy or alter the public freezer GUI-qualified gate.')
    shared.save_new(output/'native-only-prerequisites.json',qualification)
    defaults = pref.validate(dict(query['defaults'],seconds=420))
    population = dict(schema=1,kind='frozen-runtime043-labelled-IR-native-support-followup-v1',population=list(shared.POPULATION),planned_family_order=['ir-obstacle'],planned_arm_order=list(shared.ARM_ORDER),
        runtime=str(runtime),runtime_manifest_sha256=MANIFEST,source_head=HEAD,administration_head=ADMIN_HEAD,families=families,outputs={'ir-obstacle':outputs},limits=dict(shared.LIMITS),default_settings=defaults,
        tracked_administration_files_sha256=tracked,freezer_sha256=self_pin,public_helper_sha256=PUBLIC_SHA,enclosure_sha256=shared.ENCLOSURE_SHA,qualification=qualification,
        prior_cohort=dict(path=str(prior_path),sha256=PRIOR_SHA,first_attempt=False,original_results_unchanged=True),
        hypothesis='Exact pinned7 fractional-rectangle version/proof correction permits faithful transport under unchanged source/rules/0.5um/1nm/inward-only guards; routing and delivery may still fail.',
        disposition='Integrate support only from actual qualified Native/source/protection/fullSCH/delivery evidence. Preserve valid negatives and unsupported/harness/cap failures separately. Revise only a demonstrated general defect after the frozen batch, otherwise defer; no board/constraint/policy tuning during it.',
        caveats='One already exposed IR source. CLI/native-only labelled follow-up, not an unattended repair of042, newGUI/untouched/independent-family or superiority result. B1default unchanged; B0 retains common fidelity safeguards. API/CLI delivery workloads differ: no generic speed claim. All CAD/DSN/SES/plots/rawfindings remain local pending embedded title closure; metadata-only public reporting. SameMac/account/externaldependencies; no newOS/standalone/Windows/human/physical/release claim.',Native_routing_or_DRC_executed=False,actual_GUI=False,project_complete=False)
    population_pin = shared.save_new(output/'population.json',population)
    paths = [sources_path,milestone_path,invalid_path,prior_path,doctor_path,doctor_process,runtime/pv.MANIFEST,Path(__file__),output/'sources.json',output/'native-only-prerequisites.json',output/'population.json',output/'tools-defaults.json',output/'tools-defaults-process.json',child,*[ROOT/name for name in tracked]]
    prerequisites = {str(path):pv.file_digest(path,4*1024**2)[0] for path in paths}
    require(0 < len(prerequisites) <= 32, 'unchanged single-method prerequisite ceiling exceeded')
    children = {}; admin = {name:tracked[name] for name in shared.ADMIN_FILES[:3]}; entry = families['ir-obstacle']
    for arm in shared.ARM_ORDER:
        folder = output/'ir-obstacle'/arm; folder.mkdir(parents=True)
        common = dict(schema=1,runtime=str(runtime),runtime_manifest_sha256=MANIFEST,source_head=HEAD,tools=copy.deepcopy(tools),source=entry['source'],source_hashes=copy.deepcopy(entry['source_hashes']),source_rights=copy.deepcopy(entry['source_rights']),
            output=outputs[arm],administration_root=str(ROOT),whole_wall_full_cpu_seconds=600,pass_key='controls_passed',controller_args=['--runtime',str(runtime)],enclosure_sha256=shared.ENCLOSURE_SHA,
            population_protocol_path=str(output/'population.json'),population_protocol_sha256=population_pin,scope='Labelled post-correction exposed IR043/'+arm+':420allocation/450method/600completewall+fullCPU/export120; no original042 rewrite, GUI/untouched/firstattempt/superiority claim.')
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
    record = dict(schema=1,kind='runtime043-labelled-native-only-IR-six-arm-freeze-v1',population_path=str(output/'population.json'),population_sha256=population_pin,protocols={'ir-obstacle':children},administration_head=ADMIN_HEAD,
        policy_or_board_changes_after_first_arm=False,project_complete=False,actual_GUI=False,Native_routing_or_DRC_executed=False,sampled_setup_wall_seconds=time.monotonic()-START,sampled_setup_full_CPU_seconds=cpu()-CPU0,
        setup_acceptance_cap_seconds=120,external_complete_exit_required=True,scope='Prepared protocols only. Lead dispatches sequentially after noGUIjob/Nativeworker busy; record all complete external exits/costs, including failures, against600wall+CPU perarm. Sixarms maximum3600wall/3600CPU, setup/full190/diagnostics/GUI/admin costs additional; no aggregate disk quota or future outcome implied.')
    final_pin = shared.save_new(output/'frozen-children.json',record); fresh(); copied_child()
    require(pv.file_digest(output/'frozen-children.json',4*1024**2)[0] == final_pin, 'final freeze changed')
    return record

if __name__ == '__main__':
    try:
        require(len(sys.argv) == 1, 'fixed reviewed IR043 wrapper accepts no path/budget overrides')
        print(json.dumps(freeze()))
    except (ValueError,OSError,shared.p.Rejected) as exc:
        print('IR043 native-only freeze refused: '+str(exc),file=sys.stderr); raise SystemExit(2)
