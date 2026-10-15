"""Prospective lead-only fresh DS18B20 temperature interface four-arm matrix; not a comparison reader."""
import time, resource
START = time.monotonic()
def cpu():
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
CPU0 = cpu()

from pathlib import Path
import datetime, json, re, shutil, subprocess, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import floor_route as f, pipeline as p, placement_clearance as pc
from autorouter.runner import run
from scripts import experiment_quality as q, experiment_portfolio as portfolio

OUT = ROOT / '.runs/ds18b20-native-paired240-001'
PROTOCOL = ROOT / '.runs/ds18b20-native-paired240-001-protocol.json'
READER = ROOT / '.runs/read-ds18b20-native-paired240-001.py'
DEPENDENCY = 'experiments/native_paired_v1/readback.py'
CAPTURED_DEPENDENCY = OUT / 'reader-dependencies/native_paired_v1/readback.py'
OBSERVATIONS = 'experiments/native_paired_v1/observations.py'
CAPTURED_OBSERVATIONS = OUT / 'reader-dependencies/native_paired_v1/observations.py'
ARMS = ['B0', 'B1', 'B2_portfolio', 'C_feedback']
CAP = 540.0
spec = f.read_json(PROTOCOL)
dependencies = spec.get('reader_dependencies_sha256')
if (spec.get('status') != 'frozen' or spec.get('schema') != 1
        or spec.get('kind') != 'prospective-exposed-DS18B20-normal-four-arm-delivered240'
        or not re.fullmatch(r'[0-9a-f]{40}', str(spec.get('git_head')))
        or spec.get('project') != 'ds18b20' or spec.get('system') != 'native-all'
        or spec.get('output') != str(OUT / 'run') or spec.get('arm_order') != ARMS
        or spec.get('external_reserve_seconds') != 0
        or spec.get('reader_source') != str(READER)
        or spec.get('reader_wall_full_cpu_cap_seconds') != 45
        or spec.get('reader_startup_allowance_seconds') != 1
        or spec.get('outer_publication_allowance_seconds') != 2
        or spec.get('batch_wall_cap_seconds') != CAP
        or spec.get('batch_full_cpu_cap_seconds') != CAP
        or spec.get('delivered_wall_full_cpu_budget_per_arm_seconds') != 240
        or spec.get('wall_budget_per_arm_seconds') != 120
        or spec.get('full_cpu_budget_per_arm_seconds') != 120
        or spec.get('batch_output_cap_bytes') != 256 * 1024**2
        or spec.get('batch_group_rss_cap_bytes') != 2 * 1024**3
        or spec.get('max_log_bytes') != 256 * 1024
        or spec.get('wrapper_sha256') != p.sha(Path(__file__))
        or spec.get('reader_sha256') != p.sha(READER)
        or type(dependencies) is not dict or set(dependencies) != {DEPENDENCY,OBSERVATIONS}
        or re.fullmatch(r'[0-9a-f]{64}', str(dependencies[DEPENDENCY])) is None
        or (ROOT / DEPENDENCY).is_symlink() or READER.is_symlink()
        or dependencies[DEPENDENCY] != p.sha(ROOT / DEPENDENCY)
        or dependencies[OBSERVATIONS] != p.sha(ROOT / OBSERVATIONS) or (ROOT / OBSERVATIONS).is_symlink()
        or re.fullmatch(r'[0-9a-f]{64}',str(dependencies[OBSERVATIONS])) is None
        or type(spec.get('prior_exposed_exploration')) is not dict
        or spec['prior_exposed_exploration'].get('status') != 'recorded_separately'):
    raise p.Rejected('populate and freeze the exact prospective protocol before launch')
common=spec['common_prerequisites']
def prerequisites():
    if common.get('source_gate_costs_complete') is not True or common.get('reader_startup_allowance_seconds')!=1:
        raise p.Rejected('complete actual source/control-gate costs required before launch')
    wall=cpu=1.;seen=set()
    for item in common['stages']:
        name=item['path'];path=ROOT/name
        if name in seen or not name.startswith('.runs/') or '..' in Path(name).parts or path.is_symlink() or p.sha(path)!=item['sha256']:
            raise p.Rejected('prerequisite receipt pin/path differs')
        seen.add(name);record=f.read_json(path)
        if record.get('passed') is not True or record.get('publication_allowance_seconds')!=2 or not (record.get('source_current') is True or record.get('protocol_and_source_current') is True):
            raise p.Rejected('prerequisite process did not qualify')
        for key in ('wall_seconds','full_cpu_seconds'):
            value=record[key]
            if not q.finite_nonnegative(value) or value!=item[key]:raise p.Rejected('prerequisite cost differs')
        if {k:v for k,v in record['tools'].items() if k!='git_head'}!={k:v for k,v in spec['tools'].items() if k!='git_head'}:
            raise p.Rejected('retained prerequisite actual tool/core bytes differ; historical HEAD remains literal')
        wall+=record['wall_seconds']+2;cpu+=record['full_cpu_seconds']+2
    required={'.runs/ds18b20-fetch-execution-001/execution.json','.runs/ds18b20-original-native-execution-001/execution.json','.runs/ds18b20-original-native-readback-execution-001/execution.json'}
    if required!=seen or wall!=common['wall_seconds'] or cpu!=common['full_cpu_seconds'] or max(wall,cpu)+180>240:
        raise p.Rejected('prerequisite240 reserve or complete cost differs')
    gate=spec['qualified_source_gate'];path=ROOT/gate['path'];review=f.read_json(path);native=f.read_json(ROOT/gate['original_receipt'])
    if gate.get('original_native_readback_passed') is not True or p.sha(path)!=gate['sha256'] or review.get('passed') is not True or review['checks']['consistent'] is not True:
        raise p.Rejected('qualified retained original Native readback required')
    if (native['project']!='ds18b20' or native['status']!='observed' or native['accepted'] is not False or native['production_support_qualified'] is not False or native['serialization_equivalence_qualified'] is not False
            or native['protect_local_settings'] is not True or native['original_hashes']!=spec['complete_native_packet_sha256'] or native['source_file_count']!=6 or native['source_bytes']!=124777
            or review['checks']['receipt_sha256']!=p.sha(ROOT/gate['original_receipt']) or native['final_native_report_sha256']!=spec['original_native_report']['sha256']
            or not p.native_accepted(native['parity_native']) or (native['parity_native']['warnings'],len(native['parity_native']['ignored_checks']))!=(11,7)):
        raise p.Rejected('original source/native/PRL/11warning/7ignored metadata differs')
    for name,pin in native['additional_implementation_sha256'].items():
        if p.sha(ROOT/name)!=pin:raise p.Rejected('original source/helper implementation changed: '+name)
    for name,pin in common['pins'].items():
        if p.sha(ROOT/name)!=pin:raise p.Rejected('source/control qualification material changed')
    return wall,cpu
prerequisites()
protocol_pin = p.sha(PROTOCOL)
board, family = q.selected_source('ds18b20')
if (spec.get('source') != str(board) or spec.get('family') != family
        or spec.get('original_source_sha256') != p.tree_hash(board.parent)
        or type(spec.get('freeze')) is not dict
        or spec['freeze'].get('tools') != spec.get('tools')
        or spec['freeze'].get('source_hashes') != spec['original_source_sha256']
        or spec['tools'].get('git_head') != spec['git_head']):
    raise p.Rejected('prospective source/tool freeze differs')

def clean():
    result = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=normal'],
        cwd=ROOT, capture_output=True, timeout=10, check=True)
    return result.stdout == b''

def stable():
    # Tool callbacks precede the final byte witnesses.
    if p.tool_manifest() != spec['tools']:
        raise p.Rejected('current tools or checkpoint differ')
    prerequisites()
    if (any(path.is_symlink() for path in (ROOT / DEPENDENCY, CAPTURED_DEPENDENCY, READER, OUT / 'reader.py'))
            or p.sha(ROOT / DEPENDENCY) != dependencies[DEPENDENCY]
            or p.sha(CAPTURED_DEPENDENCY) != dependencies[DEPENDENCY]
            or p.sha(ROOT / OBSERVATIONS) != dependencies[OBSERVATIONS] or p.sha(CAPTURED_OBSERVATIONS) != dependencies[OBSERVATIONS]
            or CAPTURED_OBSERVATIONS.is_symlink()
            or p.sha(OUT / 'reader.py') != spec['reader_sha256']):
        raise p.Rejected('frozen reader or shared-reader dependency changed')
    if (p.sha(PROTOCOL) != protocol_pin or p.sha(Path(__file__)) != spec['wrapper_sha256']
            or p.sha(READER) != spec['reader_sha256']
            or p.sha(OUT / 'prospective-protocol.json') != protocol_pin
            or p.sha(OUT / 'wrapper.py') != spec['wrapper_sha256']
            or p.tree_hash(board.parent) != spec['original_source_sha256']):
        raise p.Rejected('prospective protocol/launcher/reader/source changed')
    for name,pin in spec['complete_source_files_sha256'].items():
        if p.sha(ROOT/name)!=pin:raise p.Rejected('complete DS18B20 source packet changed')
    for name, digest in spec['freeze']['files_sha256'].items():
        if p.sha(ROOT / name) != digest:
            raise p.Rejected('frozen implementation changed: ' + name)

OUT.mkdir(exist_ok=False)
shutil.copyfile(PROTOCOL, OUT / 'prospective-protocol.json')
shutil.copyfile(Path(__file__), OUT / 'wrapper.py')
shutil.copyfile(READER, OUT / 'reader.py')
CAPTURED_DEPENDENCY.parent.mkdir(parents=True)
shutil.copyfile(ROOT / DEPENDENCY, CAPTURED_DEPENDENCY)
shutil.copyfile(ROOT / OBSERVATIONS, CAPTURED_OBSERVATIONS)
record = dict(schema=1, kind='DS18B20-normal-four-arm-enclosing-execution',
    git_head=spec['git_head'], tools=spec['tools'], started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    process=None, source_current=False, clean_checkpoint_before=False, clean_checkpoint_after=False,
    qualified=False, accepted=False, production_qualified=False,
    wrapper_sha256=spec['wrapper_sha256'], prospective_protocol_sha256=protocol_pin,
    reader_sha256=spec['reader_sha256'], reader_dependencies_sha256=dependencies,
    outer_publication_allowance_seconds=2, reader_required=True, common_prerequisites=common, qualified_source_gate=spec['qualified_source_gate'], delivered_wall_full_cpu_budget_per_arm_seconds=240,
    scope='One exposed DS18B20 family; each method has internal120 and declared delivered240 cap; raw paired eligibility requires the separate shared reader and enclosing per-arm charges. No comparative, population, novelty, human-review, physical or electrical claim from this launcher.')
try:
    if not clean():
        raise p.Rejected('clean committed checkpoint required before matrix')
    record['clean_checkpoint_before'] = True
    frozen = portfolio.freeze(board)
    paired_script = ROOT / 'scripts/experiment_paired.py'
    frozen['files_sha256']['scripts/experiment_paired.py'] = p.sha(paired_script)
    if f.canonical(frozen) != f.canonical(spec['freeze']):
        raise p.Rejected('complete current shared freeze differs from prospective pins')
    stable()
    argv = [*f.SANDBOX, str(ROOT / '.venv/bin/python'), '-B', str(paired_script),
        '--project', 'ds18b20', '--system', 'native-all', '--external-reserve-seconds', '0',
        '--output', str(OUT / 'run')]
    record['process'] = run(argv, cwd=OUT, log=OUT / 'command.log',
        timeout=max(.001, CAP - 2 - (time.monotonic() - START)),
        max_log_bytes=256 * 1024, max_workdir_bytes=256 * 1024**2, max_group_rss_bytes=2 * 1024**3)
except BaseException as exc:
    record['reason'] = type(exc).__name__ + ': ' + str(exc)
finally:
    try:
        record['clean_checkpoint_after'] = clean()
        stable()
        record['source_current'] = True
    except BaseException as exc:
        record['final_check_error'] = type(exc).__name__ + ': ' + str(exc)
    summary_path = OUT / 'run/paired-summary.json'
    paired_protocol = OUT / 'run/protocol.json'
    record['paired_summary_sha256'] = p.sha(summary_path) if summary_path.is_file() else None
    record['paired_protocol_sha256'] = p.sha(paired_protocol) if paired_protocol.is_file() else None
    summary = None
    try:
        if summary_path.exists(): summary = f.read_json(summary_path)
        record['paired_material'] = pc.inventory(OUT / 'run', max_bytes=256 * 1024**2,
            max_files=16000, max_entries=32000) if (OUT / 'run').is_dir() else {}
    except BaseException as exc:
        record['material_error'] = type(exc).__name__ + ': ' + str(exc)
    rows = summary.get('results', []) if type(summary) is dict else []
    record['arm_population'] = [dict(id=arm, raw_row_indices=[i for i, row in enumerate(rows)
        if type(row) is dict and row.get('id') == arm], disposition='retained' if any(
        type(row) is dict and row.get('id') == arm for row in rows) else 'unavailable_after_failure') for arm in ARMS]
    record['paired_status'] = summary.get('status') if type(summary) is dict else None
    record['log_sha256'] = p.sha(OUT / 'command.log') if (OUT / 'command.log').is_file() else None
    record['wall_seconds'] = time.monotonic() - START
    record['full_cpu_seconds'] = cpu() - CPU0
    record['whole_delivery_within_budget'] = max(record['wall_seconds'], record['full_cpu_seconds']) + 2 <= CAP
    record['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    p.save_json(OUT / 'execution.json', record)

process = record['process'] or {}
ok = (process.get('status') == 'success' and process.get('exit_code') == 0
    and process.get('cleanup_complete') is True and process.get('log_truncated') is False
    and record['source_current'] and record['clean_checkpoint_before'] and record['clean_checkpoint_after']
    and record['whole_delivery_within_budget'] and record['paired_status'] == 'completed'
    and not any(key in record for key in ('reason', 'final_check_error', 'material_error')))
print(json.dumps({key:record[key] for key in ('paired_status', 'source_current', 'wall_seconds', 'full_cpu_seconds', 'qualified')}))
raise SystemExit(0 if ok else 2)
