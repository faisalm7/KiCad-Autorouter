"""Explicit, bounded pinned-JAR area/contact import observation; never route a board."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).absolute().parent
ROOT = next(p for p in HERE.parents if (p / 'autorouter/runner.py').is_file())
sys.path.insert(0, str(ROOT))
from autorouter import runner

SECONDS = 60.0
LIMIT = 10 * 1024**2
HELPERS = ('driver.py', 'AreaContactProbe.java', 'derive.py', 'checks.py', 'test_driver.py', 'test_derive.py', 'PROTOCOL.json', 'README.md')
SANDBOX = ['/usr/bin/sandbox-exec', '-p', '(version 1)(allow default)(deny network*)']
import derive
from checks import validate as validate_observation
IDS = derive.IDS


def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return (json.dumps(value, sort_keys=True, allow_nan=False, separators=(',', ':')) + '\n').encode()
def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def real(path):
    path = Path(path).absolute()
    if '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('canonical non-symlink path required')
    return path


def content(path, cap=LIMIT, *, digest=False):
    path = real(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > cap: raise ValueError('regular bounded file required')
        total = 0; chunks = []; hashed = hashlib.sha256()
        while total <= cap:
            block = stream.read(min(65536, cap + 1 - total))
            if not block: break
            total += len(block); hashed.update(block)
            if not digest: chunks.append(block)
        after = os.fstat(stream.fileno())
    keys = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    if total > cap or total != before.st_size or keys(before) != keys(after): raise ValueError('file changed or exceeded cap')
    return {'bytes': total, 'sha256': hashed.hexdigest()} if digest else b''.join(chunks)


def inventory(directory):
    pending = [real(directory)]; files = {}; total = entries = 0
    while pending:
        folder = real(pending.pop())
        with os.scandir(folder) as stream:
            for item in stream:
                entries += 1
                if entries > 2048 or item.is_symlink(): raise ValueError('output entry/symlink bound')
                path = Path(item.path)
                if item.is_dir(follow_symlinks=False): pending.append(path); continue
                if not item.is_file(follow_symlinks=False) or len(files) >= 1024: raise ValueError('output file bound')
                row = content(path, LIMIT - total, digest=True); total += row['bytes']
                files[str(path.relative_to(directory))] = row
    return files


def fixtures_and_expected():
    return derive.prepare(ROOT, lambda path: content(path,1024**2))


def cpu():
    values = [resource.getrusage(k) for k in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)]
    return sum(x.ru_utime + x.ru_stime for x in values)


def head_witness():
    # Explicit ROOT-only normal local checkout; no managed worktree indirection.
    raw = content(ROOT / '.git/HEAD', 4096); text = raw.decode().strip()
    if not re.fullmatch(r'ref: refs/heads/rebuild/local-[A-Za-z0-9_-]+', text): raise ValueError('designated ordinary local rebuild branch required')
    path = ROOT / '.git' / text[5:]; ref = content(path, 4096); head = ref.decode().strip()
    if not re.fullmatch('[0-9a-f]{40}', head): raise ValueError('loose local branch identity required')
    return {'head': head, 'HEAD_sha256': sha(raw), 'ref': text[5:], 'ref_sha256': sha(ref)}


def source_paths():
    return ([HERE / n for n in HELPERS] + [ROOT / ('autorouter/' + n) for n in ('runner.py','__init__.py','adapter.py','sexpr.py')]
            + [ROOT / 'toolchain.lock.json', ROOT / derive.BASIS / 'summary.json']
            + [ROOT / derive.BASIS / case / name for case in IDS for name in derive.FILES])


def runtime(protocol):
    git = head_witness()  # Metadata first; complete tool/source samples follow this owned read.
    tools = {name: content(Path(row['path']) if Path(row['path']).is_absolute() else ROOT / row['path'], row['bytes'], digest=True) for name, row in protocol['tools'].items()}
    sources = {str(p.relative_to(ROOT)): content(p, 1024**2, digest=True) for p in source_paths()}
    return {'tools': tools, 'sources': sources, 'git': git}


def write(path, value):
    raw = canonical(value); partial = path.with_suffix(path.suffix + '.partial')
    with partial.open('wb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(partial, path); return raw


def publish(out, record, stable, account, remaining):
    path = out / 'summary.json'
    def invalidate():
        for current in (path, path.with_suffix('.json.partial')):
            if current.exists(): current.rename(out / ('invalidated-' + uuid.uuid4().hex + '-' + current.name))
    try:
        stable(); account(); wanted = canonical(record); write(path, record)
        stable()  # Includes final bounded output scan before material and canonical checks.
        if content(path) != wanted or canonical(record) != wanted: raise ValueError('summary changed during final publication')
        remaining()
    except (Exception, KeyboardInterrupt) as exc:
        invalidate(); first = record.get('error')
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'invalidated', observations_complete=False,
                      expected_observations_match=False, routing_accepted=False, custom_pad_support_qualified=False,
                      error=first or (type(exc).__name__ + ': ' + str(exc)), final_validation_error=type(exc).__name__ + ': ' + str(exc))
        account()
        try: write(path, record)
        except (Exception, KeyboardInterrupt): invalidate()
    return record


def experiment(out, *, started=None, cpu_started=None):
    if HERE.relative_to(ROOT).as_posix() != 'experiments/custom_pad_area_probe_v1': raise ValueError('reviewed committed helper location required')
    started = time.monotonic() if started is None else started
    cpu_started = cpu() if cpu_started is None else cpu_started
    out = real(out)
    if out.parent != ROOT / '.runs' or out.exists(): raise ValueError('fresh direct project .runs output required')
    protocol = decode(content(HERE / 'PROTOCOL.json')); record = {'schema': 2, 'scope': 'owned_area_contact_import_only',
        'status': 'preparing', 'observations_complete': False, 'routing_accepted': False, 'custom_pad_support_qualified': False,
        'native_executed': False, 'routing_executed': False, 'import_process_requested': False, 'import_process_executed': False, 'steps': [],
        'budget_seconds': SECONDS, 'cpu_budget_seconds': SECONDS, 'max_output_bytes': LIMIT,
        'accounting_point': 'Stored sample precedes final publication checks; final wall/full-CPU caps include those checks.',
        'cpu_budget_enforcement': 'Observed total SELF plus waited CHILDREN; post-stage/final acceptance cap, no hard CPU preemption.'}
    def remaining():
        left = min(SECONDS - (time.monotonic() - started), SECONDS - (cpu() - cpu_started))
        if left <= 0: raise TimeoutError('shared wall/full-CPU cap exceeded')
        return left
    def account(): record.update(wall_seconds=time.monotonic() - started, total_cpu_seconds=cpu() - cpu_started)
    out.mkdir(); frozen = {}; before = None
    def capture(names):
        for name in names:
            row = content(out / name, digest=True)
            if name in frozen and frozen[name] != row: raise ValueError('completed evidence changed')
            frozen[name] = row
    def stable():
        observed = inventory(out)
        if any(observed.get(name) != row for name, row in frozen.items()): raise ValueError('completed evidence stale')
        if before is not None and runtime(protocol) != before: raise ValueError('runtime/source/tool/HEAD changed')
        observed = inventory(out)
        if any(observed.get(name) != row for name, row in frozen.items()): raise ValueError('completed evidence stale after runtime scan')
        remaining()
    try:
        if protocol['schema'] != 2 or protocol['case_ids'] != list(IDS) or protocol['expected'] != fixtures_and_expected()[1] or protocol['limits'] != {'wall_seconds': 60, 'full_cpu_seconds': 60, 'output_bytes': LIMIT, 'java_heap': '256m'}:
            raise ValueError('fixed six-scene prospective protocol differs')
        if set(protocol['tools']) != {'jar', 'java', 'javac', 'sandbox', 'python'} or Path(sys.executable).resolve() != Path(protocol['tools']['python']['path']):
            raise ValueError('fixed tool set/invoking Python differs')
        if protocol['input_sha256'] != {k: sha(v) for k, v in fixtures_and_expected()[0].items()}:
            raise ValueError('prospective input/coordinate pins differ')
        before = runtime(protocol)
        if {n:v for n,v in before['sources'].items() if n.startswith(derive.BASIS+'/')} != protocol['native_source_pins']:
            raise ValueError('fixed native basis bytes changed')
        for name, pin in protocol['tools'].items():
            if before['tools'][name] != {k: pin[k] for k in ('bytes', 'sha256')}: raise ValueError('tool pin differs: ' + name)
        for relative, pin in before['sources'].items():
            raw = content(ROOT / relative, 1024**2)
            proc = subprocess.run(['git', 'show', before['git']['head'] + ':' + relative], cwd=ROOT, capture_output=True, timeout=min(3, remaining()), check=True)
            if proc.stdout != raw or sha(raw) != pin['sha256']: raise ValueError('commit exact helper/runtime sources first')
            target = out / 'code' / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
            capture([str(target.relative_to(out))])
        stable(); write(out / 'runtime.json', before); capture(['runtime.json']); record['runtime'] = before
        for folder in ('inputs', 'classes', 'home', 'tmp'): (out / folder).mkdir()
        inputs, expected = fixtures_and_expected()
        write(out / 'expectations.json', expected); capture(['expectations.json'])
        for name, raw in inputs.items(): (out / 'inputs' / name).write_bytes(raw); capture(['inputs/' + name])
        env = {'HOME': str(out / 'home'), 'TMPDIR': str(out / 'tmp'), 'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C'}
        jar = ROOT / protocol['tools']['jar']['path']; java = protocol['tools']['java']['path']; javac = protocol['tools']['javac']['path']
        source = out / 'code' / str(HERE.relative_to(ROOT)) / 'AreaContactProbe.java'
        commands = [('compile', [*SANDBOX, javac, '-J-Xmx256m', '-J-Duser.home=' + env['HOME'], '-proc:none', '-classpath', str(jar), '-d', str(out / 'classes'), str(source)]),
                    ('import', [*SANDBOX, java, '-Xmx256m', '-Djava.awt.headless=true', '-Duser.home=' + env['HOME'], '-Djava.io.tmpdir=' + env['TMPDIR'], '-cp', str(out / 'classes') + os.pathsep + str(jar), 'AreaContactProbe', str(out / 'inputs'), str(out / 'observations.json')])]
        for name, argv in commands:
            stable()
            if name == 'import': record['import_process_requested'] = True
            step = runner.run(argv, cwd=out, log=out / (name + '.log'), timeout=min(30, remaining()), max_log_bytes=262144,
                              env=env, max_workdir_bytes=LIMIT, max_group_rss_bytes=1024**3)
            record['steps'].append({'name': name, **step}); write(out / (name + '-process.json'), step)
            if name == 'import': record['import_process_executed'] = type(step.get('pid')) is int
            names = [name + '.log', name + '-process.json']
            if name == 'compile': names += ['classes/' + p for p in inventory(out / 'classes')]
            elif (out / 'observations.json').exists(): names.append('observations.json')
            capture(names)  # Freeze complete raw stage evidence BEFORE any derived observation parsing.
            if step['status'] != 'success' or step['exit_code'] != 0 or step.get('cleanup_complete') is not True:
                if step['status'] == 'cancelled': raise KeyboardInterrupt('owned import worker cancelled')
                raise ValueError(name + ' process unsuccessful; retained raw artifacts')
            stable()
        rows = validate_observation(decode(content(out / 'observations.json', 262144)), expected)
        record.update(status='completed', observations_complete=True, expected_observations_match=all(x['expected_observation_matches'] for x in rows),
                      case_comparison=rows, observations_sha256=frozen['observations.json']['sha256'])
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed', error=type(exc).__name__ + ': ' + str(exc))
    record['frozen_evidence'] = frozen
    return publish(out, record, stable, account, remaining)


@contextmanager
def cancellation():
    previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    def cancel(signum, frame): raise KeyboardInterrupt('cancelled signal ' + str(signum))
    try:
        for s in previous: signal.signal(s, cancel)
        yield
    finally:
        for s, old in previous.items(): signal.signal(s, old)


def main(argv=None):
    started = time.monotonic(); cpu_started = cpu()
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run-import', action='store_true'); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.run_import: parser.error('--run-import is required; no implicit execution')
    with cancellation(), real(ROOT / '.runs/quality-experiment.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); result = experiment(args.output, started=started, cpu_started=cpu_started)
    print(json.dumps({k: result.get(k) for k in ('status', 'observations_complete', 'expected_observations_match', 'wall_seconds', 'total_cpu_seconds')}))
    return 0 if result['observations_complete'] else 1


if __name__ == '__main__': raise SystemExit(main())
