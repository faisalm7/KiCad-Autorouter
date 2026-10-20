#!/usr/bin/env python3
"""Freeze 1–4 explicitly exposed local families before any comparison arm runs.

Mac/selected7 only. All six arms use 420 routing / 450 method / 600 complete
wall+CPU seconds and 120 export seconds. This performs one bounded tools query, never Native routing, a
board preflight, source scripts, downloads or publication. Explicit rights are
caller declarations, not legal clearance or independent/untouched pedigree.
Keep administration HEAD and all inputs fixed while running each protocol with
scripts/enclose_current_comparison.py. Record complete external costs/failures;
setup costs are additional. Four GiB startup headroom is not a future job quota.
A failure retains its partial new namespace; never delete/reuse it automatically.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import re
import resource
import shutil
import sys
import time

START = time.monotonic()
def cpu():
    return sum(row.ru_utime + row.ru_stime for row in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import provenance as pv, handoff as h, placement_clearance as io
from autorouter import floor_route as f, preferences as pref, pipeline as p
from autorouter.gui import child_environment
from autorouter.runner import run

POPULATION = ('B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cdefault', 'Cthermal')
ARM_ORDER = ('Cdefault', 'B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cthermal')
VARIANTS = ('via_default', 'via_low', 'via_high')
LIMITS = dict(routing_seconds=420, method_wall_cpu_cap_seconds=450,
              delivery_wall_cpu_cap_seconds=600, export_validation_seconds=120)
ADMIN_FILES = ('scripts/qualify_comparison_portfolio.py', 'scripts/experiment_portfolio.py',
    'scripts/experiment_quality.py', 'scripts/qualify_installed_workflow.py',
    'scripts/qualify_current_method.py', 'scripts/freeze_current_comparison.py',
    'scripts/enclose_current_comparison.py')
ENCLOSURE_SHA = 'a441b05adc76deb55e75b809c0d6ec39f3d6a6ee7d700cf545c8f893d5e0dc34'
QUALIFICATION_KIND = 'runtime042-install-existing-actual-Native-and-single-GUI-vertical-slice-v1'
IMPROVE_POPULATION = ('B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cdefault', 'Cimprove')
IMPROVE_ARM_ORDER = ('Cdefault', 'B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cimprove')
IMPROVE_POPULATION_KIND = 'frozen-current-improve-six-arm-exposed-development-v2'
IMPROVE_METHOD_KIND = 'installed-native7-current-method-v2'
IMPROVE_QUALIFICATION_KIND = 'runtime050-install-existing-actual-Native-CLI-prepared-GUI-only-v1'
MAX_PROJECT_FILES = 2000
# The unchanged arm controllers use the shared 32 MiB source census.
MAX_PROJECT_BYTES = 32 * 1024**2


def require(ok, message):
    if not ok: raise ValueError(message)


def contract(version):
    if version == 'legacy-v1':
        return POPULATION, ARM_ORDER, 'frozen-current-six-arm-exposed-development-v1', 'installed-native7-current-method-v1', 'qualify-current-method-001.py'
    require(version == 'improve-v2', 'unknown comparison population version')
    return IMPROVE_POPULATION, IMPROVE_ARM_ORDER, IMPROVE_POPULATION_KIND, IMPROVE_METHOD_KIND, 'qualify-current-method-002.py'


def qualification_scope(qualified, runtime, manifest_pin, identity, manifest, version):
    """Keep the old GUI gate separate from the explicit050 CLI-only gate."""
    native = qualified.get('Native')
    require(type(qualified.get('schema')) is int and qualified['schema'] == 1
        and type(native) is dict and qualified.get('runtime') == str(runtime)
        and qualified.get('runtime_manifest_sha256') == manifest_pin and qualified.get('source_head') == identity['git_head']
        and qualified.get('immutable_map_build_lock_version_unchanged') is True
        and type(qualified.get('immutable_files')) is int and qualified['immutable_files'] == len(manifest['immutable_files_sha256'])
        and qualified.get('accepted') is False and native.get('doctor_ready') is True
        and native.get('six_stage_delivery') is True and native.get('counts') == [0,0,0,0]
        and all(type(v) is int for v in native['counts'])
        and identity.get('native_version') == '10.0.7' and manifest['local_engine'] is not None,
        'exact qualified root/source/manifest/map required')
    if version == 'legacy-v1':
        require(qualified.get('kind') == QUALIFICATION_KIND and qualified.get('actual_newroot_GUI_vertical_slice') is True
            and type(qualified.get('full188')) is dict and qualified['full188'].get('passed') is True
            and native.get('protected4') is True, 'exact042 GUI qualification required; no historical GUI transfer')
        return dict(kind=QUALIFICATION_KIND, full_GUI_claim=False), {}
    require(version == 'improve-v2' and qualified.get('kind') == IMPROVE_QUALIFICATION_KIND
        and qualified.get('workflow_CLI') is True and qualified.get('workflow_delivered') is True
        and qualified.get('production_admitted') is False and qualified.get('actual_GUI') is False
        and qualified.get('full_GUI_claim') is False and qualified.get('installation_record_is_authoritative') is False
        and type(native.get('protected_routes')) is int and native['protected_routes'] == 4
        and type(qualified.get('GUI087')) is dict and qualified['GUI087'].get('actual_GUI') is False
        and qualified['GUI087'].get('state') == 'PREPARED_ONLY_NOT_EXECUTED',
        'exact050 installed CLI/prepared-only GUI qualification required')
    dependency = ROOT/'evidence/runtime050-native-milestone-002.json'
    rows = qualified.get('dependencies')
    require(type(rows) is list and len(rows) == 1 and type(rows[0]) is dict
        and rows[0].get('path') == str(dependency.relative_to(ROOT)), 'exact050 Native prerequisite required')
    _, proof = pinned_json(dependency, rows[0].get('sha256'))
    expected = {'ordinary-whole4Cu','improve-floor2Cu','ordinary-hierarchy2Cu','ordinary-npth2Cu',
                'improve-pour-only','ordinary-alias2Cu','improve-fractional'}
    require(type(proof.get('schema')) is int and proof['schema'] == 1
        and proof.get('kind') == 'runtime050-seven-completed-native-workflows-v1'
        and proof.get('source_head') == identity['git_head']
        and proof.get('runtime_manifest_sha256') == qualified.get('original_runtime_manifest_sha256')
        and proof.get('Native_cohort_passed') is True and proof.get('full199',{}).get('passed') is True
        and proof.get('invalid_controls',{}).get('passed') is True and type(proof.get('cases')) is list
        and len(proof['cases']) == 7 and {row.get('case') for row in proof['cases']} == expected,
        'completed050 full199/Native/invalid prerequisite differs')
    return dict(kind=IMPROVE_QUALIFICATION_KIND, actual_GUI_qualified=False, full_GUI_claim=False,
        scope='Installed Native CLI prerequisite; GUI087 prepared only, no current graphical qualification.'), {str(dependency): rows[0]['sha256']}


def pinned_json(path, digest):
    require(type(digest) is str and pv._DIGEST.fullmatch(digest), 'exact lowercase SHA256 required')
    path = pv.canonical(Path(path)); raw = pv.read_bytes(path, 4 * 1024**2)
    require(hashlib.sha256(raw).hexdigest() == digest, 'pinned JSON changed: ' + str(path))
    def nonfinite(_): raise ValueError('nonfinite JSON refused')
    value = json.loads(raw, object_pairs_hook=pv._strict_object, parse_constant=nonfinite)
    require(type(value) is dict, 'JSON object required')
    return raw, value


def administration(head):
    require(type(head) is str and pv._HEAD.fullmatch(head), 'exact administration HEAD required')
    require(pv.git_head(ROOT) == head, 'administration HEAD changed')
    options = ('-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '--literal-pathspecs')
    names = sorted(ADMIN_FILES)
    require(not pv._git(ROOT, *options, 'status', '--porcelain=v1', '--untracked-files=all', '--', *names),
            'commit exact administration files before freezing')
    rows = pv._git(ROOT, *options, 'ls-tree', '-r', '-l', '-z', head, '--', *names).split(b'\0')
    blobs = {}
    for row in filter(None, rows):
        metadata, name = row.split(b'\t', 1); mode, kind, oid, size = metadata.split()
        require(mode in (b'100644', b'100755') and kind == b'blob' and size.isdigit(), 'ordinary committed administration required')
        blobs[name.decode()] = (oid.decode(), int(size))
    require(set(blobs) == set(names), 'incomplete administration population')
    pins = {}
    for name, (oid, size) in blobs.items():
        raw = pv.read_bytes(ROOT / name)
        require(size == len(raw) and pv._git(ROOT, *options, 'cat-file', 'blob', oid, limit=pv.MAX_FILE_BYTES) == raw,
                'administration differs from committed HEAD: ' + name)
        pins[name] = hashlib.sha256(raw).hexdigest()
    require(pv.git_head(ROOT) == head, 'administration HEAD changed during checks')
    return pins


def sources(spec, runtime):
    require(set(spec) == {'schema', 'split', 'families'} and type(spec['schema']) is int and spec['schema'] == 1
        and spec['split'] == 'development-exposed' and type(spec['families']) is dict
        and 1 <= len(spec['families']) <= 4, 'exact exposed-development source schema required')
    seen = set(); boards = set(); families = set()
    for slug, row in spec['families'].items():
        require(type(slug) is str and re.fullmatch('[a-z][a-z0-9-]{0,31}', slug), 'canonical family slug required')
        require(type(row) is dict and set(row) == {'source', 'source_hashes', 'source_rights', 'publication'}
            and row['publication'] == 'hashes_only' and type(row['source']) is str, 'exact local hashes-only family entry required')
        board = pv.canonical(Path(row['source'])); pv._directory(board.parent)
        require(board.suffix == '.kicad_pcb' and runtime not in board.parents and board.parent.stat().st_uid == os.getuid(),
                'complete owned external PCB project required')
        hashes = row['source_hashes']; rights = row['source_rights']
        require(type(hashes) is dict and 1 <= len(hashes) <= MAX_PROJECT_FILES, 'bounded source population required')
        for name, digest in hashes.items():
            require(type(name) is str and len(name) <= 1024 and '\\' not in name and str(Path(name)) == name
                and not Path(name).is_absolute() and not any(part in ('', '.', '..') for part in name.split('/'))
                and type(digest) is str and pv._DIGEST.fullmatch(digest), 'canonical source path/hash required')
        require(all(board.with_suffix(suffix).name in hashes for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch')),
                'paired complete PCB/PRO/SCH required')
        require(io.inventory(board.parent, max_bytes=MAX_PROJECT_BYTES, max_files=MAX_PROJECT_FILES, max_entries=4000) == hashes,
                'source inventory changed or incomplete')
        require(all((board.parent / name).stat().st_uid == os.getuid() and (board.parent / name).stat().st_nlink == 1
                    for name in hashes), 'owned single-link source files required')
        require(type(rights) is dict and set(rights) == {'family', 'license', 'provenance'}
            and all(type(rights[key]) is str and 1 <= len(rights[key]) <= (256 if key == 'family' else 8192) for key in rights),
                'bounded explicit rights declarations required; not automated clearance')
        require(str(board) not in seen and hashes[board.name] not in boards and rights['family'] not in families,
                'duplicate board or family population')
        seen.add(str(board)); boards.add(hashes[board.name]); families.add(rights['family'])
    return copy.deepcopy(dict(sorted(spec['families'].items())))


def save_new(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    require(len(raw) <= 4 * 1024**2, 'frozen metadata file ceiling')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def query_runtime(runtime, output):
    python = runtime / '.venv/bin/python'; pv.file_digest(python, pv.MAX_ENGINE_BYTES)
    require(os.access(python, os.X_OK), 'copied runtime interpreter required')
    code = ('import json,sys;sys.path.insert(0,' + repr(str(runtime)) + ');'
        'from autorouter import pipeline as p,preferences as pref;'
        'print(json.dumps(dict(runtime=str(p.c.ROOT),interpreter=sys.executable,prefix=sys.prefix,'
        'tools=p.tool_manifest(),defaults=dict(pref.DEFAULTS)),sort_keys=True))')
    process = run([*f.SANDBOX, str(python), '-B', '-c', code], cwd=output, env=child_environment(),
        log=output/'tools-defaults.json', timeout=30, max_log_bytes=512*1024,
        max_group_rss_bytes=1024**3, max_workdir_bytes=16*1024**2)
    process_pin = save_new(output/'tools-defaults-process.json', process)
    require(process['status'] == 'success' and process['exit_code'] == 0 and process['cleanup_complete'] is True
        and process['log_truncated'] is False and process['log'] == str(output/'tools-defaults.json'), 'runtime query failed/incomplete')
    raw = pv.read_bytes(output/'tools-defaults.json', 512*1024)
    require(type(process['log_bytes']) is int and len(raw) == process['log_bytes'], 'runtime query log size differs')
    log_pin = hashlib.sha256(raw).hexdigest()
    return pinned_json(output/'tools-defaults.json', log_pin)[1], {
        str(output/'tools-defaults.json'): log_pin, str(output/'tools-defaults-process.json'): process_pin}


def freeze(*, runtime, expected_manifest_sha256, sources_path, sources_sha256, qualification,
           qualification_sha256, expected_administration_head, output, enclosure, enclosure_sha256,
           population_version='legacy-v1'):
    population_names, arm_order, population_kind, method_kind, child_name = contract(population_version)
    require(sys.platform == 'darwin', 'this freezer qualifies Mac/selected7 only')
    runtime = pv._directory(Path(runtime)); output = pv.canonical(Path(output)); enclosure = pv.canonical(Path(enclosure))
    require(Path(__file__).resolve() == ROOT/'scripts/freeze_current_comparison.py', 'exact public freezer required')
    require(output.parent == ROOT/'.runs' and output.parent.stat().st_uid == os.getuid()
        and re.fullmatch('[a-z][a-z0-9-]{0,63}', output.name) and not os.path.lexists(output)
        and runtime != output and runtime not in output.parents and output not in runtime.parents, 'fresh canonical administration namespace required')
    require(enclosure == ROOT/'scripts/enclose_current_comparison.py' and enclosure_sha256 == ENCLOSURE_SHA
        and pv.file_digest(enclosure)[0] == enclosure_sha256, 'exact public reviewed enclosure required')
    require(pv._directory(runtime/'.runs').stat().st_uid == os.getuid(), 'owned runtime work directory required')
    raw_sources, spec = pinned_json(sources_path, sources_sha256)
    raw_qualification, qualified = pinned_json(qualification, qualification_sha256)
    manifest_raw, manifest = pinned_json(runtime/pv.MANIFEST, expected_manifest_sha256)
    implementation = {name: pin for name, pin in pv._file_map(manifest.get('immutable_files_sha256')).items() if name.startswith('autorouter/')}
    identity = pv._runtime_identity(runtime, implementation); source_head = identity['git_head']
    qualification_record, qualification_dependencies = qualification_scope(
        qualified, runtime, expected_manifest_sha256, identity, manifest, population_version)
    families = sources(spec, runtime); tracked = administration(expected_administration_head)
    require(shutil.disk_usage(ROOT).free >= 4*1024**3, 'at least4GiB startup headroom required; future jobs have no aggregate quota')
    outputs = {slug: {arm: str(runtime/'.runs'/(
        ('native7-comparison-' if arm.startswith('B') else 'native7-method-') + output.name + '-' + slug + '-' + arm))
        for arm in population_names} for slug in families}
    roots = [Path(value) for row in outputs.values() for value in row.values()]
    extras = {slug: [Path(outputs[slug]['B2_portfolio']+'-portfolio'), *[Path(outputs[slug]['B2_portfolio']+'-portfolio-'+f'{i:02d}-'+v)
        for i,v in enumerate(VARIANTS,1)]] for slug in families}
    roots += [path for row in extras.values() for path in row]
    require(len(set(roots)) == len(roots) and not any(os.path.lexists(pv.canonical(path)) for path in roots), 'fresh distinct population and portfolio roots required')
    child = runtime/'.runs'/child_name; payload = pv.read_bytes(ROOT/'scripts/qualify_current_method.py')
    if os.path.lexists(child):
        require(child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload, 'existing copied controller differs, is unowned or linked')
    output.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, output)
    query, query_pins = query_runtime(runtime, output); tools = query['tools']
    require(query['runtime'] == str(runtime) and query['interpreter'] == str(runtime/'.venv/bin/python')
        and query['prefix'] == str(runtime/'.venv') and query['defaults'] == dict(pref.DEFAULTS)
        and tools['source_provenance'] == identity and tools['implementation_sha256'] == implementation
        and tools['git_head'] == source_head and tools['kicad'] == '10.0.7'
        and tools['comparison_route_policy'] == 'selected-native7-fixed-comparison-v2', 'actual runtime query/defaults differ')
    require(type(tools.get('files')) is dict and 1 <= len(tools['files']) <= 8, 'bounded actual tool pins required')
    def fresh():
        require(h.owned_destination(owner) == output and administration(expected_administration_head) == tracked, 'administration changed')
        require(pinned_json(sources_path, sources_sha256)[0] == raw_sources and pinned_json(qualification, qualification_sha256)[0] == raw_qualification
            and pv.read_bytes(runtime/pv.MANIFEST, pv.MAX_MANIFEST_BYTES) == manifest_raw
            and pv._runtime_identity(runtime, implementation) == identity and sources(spec, runtime) == families, 'source/qualification/runtime changed')
        require(pv._directory(runtime/'.runs').stat().st_uid == os.getuid(), 'runtime work directory ownership changed')
        for path, pin in query_pins.items(): require(pv.file_digest(Path(path),512*1024)[0] == pin, 'runtime query proof changed')
        for name, pin in tools['files'].items(): require(pv.file_digest(pv.canonical(Path(name)), pv.MAX_ENGINE_BYTES)[0] == pin, 'queried tool bytes changed')
        for name, pin in qualification_dependencies.items(): pinned_json(Path(name), pin)
        require(not any(os.path.lexists(path) for path in roots), 'Native outputs appeared before population frozen')
    fresh()
    if not os.path.lexists(child):
        with child.open('xb') as stream: stream.write(payload)
    require(child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload, 'copied controller changed or unowned')
    inputs = {'sources.json': raw_sources, 'qualification.json': raw_qualification}
    for name, raw in inputs.items():
        with (output/name).open('xb') as stream: stream.write(raw)
    defaults = pref.validate(dict(query['defaults'], seconds=420))
    improve_settings = pref.validate(dict(defaults, profile='tuned'))
    population = dict(schema=1, kind=population_kind, population=list(population_names),
        planned_family_order=list(families), planned_arm_order=list(arm_order), runtime=str(runtime),
        runtime_manifest_sha256=expected_manifest_sha256, source_head=source_head, administration_head=expected_administration_head,
        families=families, outputs=outputs, limits=LIMITS, default_settings=defaults, tracked_administration_files_sha256=tracked,
        qualification=dict(path=str(qualification),sha256=qualification_sha256,**qualification_record),
        freezer_sha256=tracked['scripts/freeze_current_comparison.py'], enclosure_sha256=enclosure_sha256,
        policy='B1 corrected standard remains default. Fixed one tuned attempt plus ordered via_default/via_low/via_high balanced portfolio;30inside each trial and15root reserve, no extra budget or board tuning.',
        caveats='All exposed families/failures/warnings retained; rights are declarations, not legal clearance/holdout/independent pedigree. B0 shares fidelity safeguards, not untouched vanilla. API baselines versus actual default/recoverCLI startup differ. Recover420 is whole-method allocation. Every actual outer wall/fullCPU cost includes all startup/conversion/selection/Native/delivery/readback; setup separate. All raw local, publication hashes_only; no publication function or aggregate future-job quota.',
        Native_executed=False,actual_GUI=False,project_complete=False)
    if population_version == 'improve-v2':
        population.update(improve_settings=copy.deepcopy(improve_settings),
            policy='B1 corrected standard remains default. Cimprove uses the shipped single tuned Improve preset;420 includes incumbent/trials and25 finalization reserve. Baselines and portfolio policy unchanged.',
            caveats=population['caveats'].replace('Recover420 is whole-method allocation.',
                'Improve420 is whole-method allocation including its incumbent and25-second return reserve; no extra incumbent budget. CLI-installed qualification has no current GUI outcome.'))
    population_pin = save_new(output/'population.json', population)
    prerequisite_paths = [Path(sources_path), Path(qualification), runtime/pv.MANIFEST, output/'sources.json', output/'qualification.json',
        output/'population.json', output/'tools-defaults.json', output/'tools-defaults-process.json', child, *[ROOT/name for name in tracked]]
    prerequisites = {str(path): pv.file_digest(path,4*1024**2)[0] for path in prerequisite_paths}
    prerequisites.update(qualification_dependencies)
    require(0 < len(prerequisites) <= 32, 'current prerequisite ceiling exceeded')
    children = {}; admin = {name: tracked[name] for name in ADMIN_FILES[:3]}
    for slug, entry in families.items():
        children[slug] = {}
        for arm in arm_order:
            folder = output/slug/arm; folder.mkdir(parents=True)
            common = dict(schema=1,runtime=str(runtime),runtime_manifest_sha256=expected_manifest_sha256,source_head=source_head,
                tools=copy.deepcopy(tools),source=entry['source'],source_hashes=copy.deepcopy(entry['source_hashes']),source_rights=copy.deepcopy(entry['source_rights']),
                output=outputs[slug][arm],administration_root=str(ROOT),whole_wall_full_cpu_seconds=600,pass_key='controls_passed',
                controller_args=['--runtime',str(runtime)],enclosure_sha256=enclosure_sha256,
                population_protocol_path=str(output/'population.json'),population_protocol_sha256=population_pin,
                scope='Predeclared exposed '+slug+'/'+arm+':420allocation/450method/600completewall+fullCPU/export120; every failure/warning/cost retained, no superiority/GUI/human/electrical claim.')
            if arm == 'B2_portfolio':
                plan = dict(common,kind='installed-native7-comparison-portfolio-functional-v1',**LIMITS,variants=list(VARIANTS),allocation='balanced',
                    trial_readback_reserve_seconds=30,root_finalization_reserve_seconds=15,installed_trial_accounting_policy='installed-route-readback-reserve-v1',
                    comparison_api_policy='installed-native7-scored-portfolio-api-v2',administration_head=expected_administration_head,administration_files_sha256=admin,
                    family=entry['source_rights']['family'],controller=str(ROOT/ADMIN_FILES[0]),controller_sha256=admin[ADMIN_FILES[0]],
                    portfolio_output=str(extras[slug][0]),material_roots=[str(path) for path in extras[slug]])
            else:
                plan = dict(common,kind=method_kind,arm=arm,population=list(population_names),outputs=outputs[slug],
                    controller=str(child),controller_sha256=tracked['scripts/qualify_current_method.py'],qualifier_sha256=tracked['scripts/qualify_installed_workflow.py'],
                    source_inventory_sha256=hashlib.sha256((f.canonical(entry['source_hashes'])+'\n').encode()).hexdigest(),
                    source_rights_sha256=hashlib.sha256(f.canonical(entry['source_rights']).encode()).hexdigest(),
                    prerequisite_sha256=prerequisites,default_settings=copy.deepcopy(defaults),limits=dict(LIMITS))
                if population_version == 'improve-v2': plan['improve_settings'] = copy.deepcopy(improve_settings)
            path = folder/'protocol.json'; children[slug][arm] = dict(path=str(path),sha256=save_new(path,plan))
    fresh(); require(child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload, 'copied controller changed or unowned at final freeze')
    for rows in children.values():
        for item in rows.values(): require(pv.file_digest(Path(item['path']),4*1024**2)[0] == item['sha256'], 'derived protocol changed')
    for path,pin in prerequisites.items(): require(pv.file_digest(Path(path),4*1024**2)[0] == pin, 'frozen prerequisite changed')
    record = dict(schema=1,population_path=str(output/'population.json'),population_sha256=population_pin,protocols=children,
        administration_head=expected_administration_head,policy_or_board_changes_after_first_arm=False,project_complete=False,
        sampled_setup_wall_seconds=time.monotonic()-START,sampled_setup_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True)
    final_pin = save_new(output/'frozen-children.json',record)
    fresh()
    require(pv.file_digest(output/'frozen-children.json',4*1024**2)[0] == final_pin
        and child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload, 'final freeze or copied controller changed')
    return record


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--population-version', choices=('legacy-v1','improve-v2'), default='legacy-v1')
    for name in ('runtime','sources','qualification','output','enclosure'): parser.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-manifest-sha256','sources-sha256','qualification-sha256','expected-administration-head','enclosure-sha256'):
        parser.add_argument('--'+name,required=True)
    args=vars(parser.parse_args(argv)); args['sources_path']=args.pop('sources')
    try: print(json.dumps(freeze(**args))); return 0
    except (ValueError,OSError,p.Rejected) as exc: print('Comparison freeze refused: '+str(exc),file=sys.stderr); return 2


if __name__=='__main__': raise SystemExit(main())
