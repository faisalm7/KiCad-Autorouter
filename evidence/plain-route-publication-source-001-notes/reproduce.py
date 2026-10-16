"""Bounded mocked-worker publication counterexample; never Native routing proof.

Run from the checkout with:
  .venv/bin/python -B .runs/direct-plain-publication-001/reproduce.py --label before-fix
Each label is write-once. Reuses the regression fixture and owned self-signals.
"""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests.test_preference_publication import PreferencePublicationTests
from autorouter import pipeline as p


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True, choices=('before-fix', 'after-fix'))
    label = parser.parse_args().label
    directory = Path(__file__).resolve().parent
    report_path = directory / (label + '-report.json')
    if report_path.exists():
        raise RuntimeError('refusing to replace an existing reproduction report')
    sources = [ROOT / name for name in ('autorouter/pipeline.py', 'autorouter/floor_route.py',
                                       'tests/test_preference_publication.py')]
    pins = {str(path.relative_to(ROOT)): digest(path) for path in sources}
    source = sources[0].read_text()
    start = source.find("    if _preferences is not None or native_toolchain is not None or engine_profile=='tuned-free-angle'")
    end = source.find('\n\n_readback_session=', start) if start >= 0 else -1
    rows = []
    fixture = PreferencePublicationTests(methodName='runTest')
    fixture.setUp()
    try:
        for mutation in (None, 'SIGINT', 'SIGTERM', 'interrupt_after_positive_write',
                         'canonical_after_positive_write', 'canonical_after_checker'):
            handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
            error = None
            returned = None
            try:
                returned, _ = fixture.exercise_route(mutation=mutation, direct=True)
            except KeyboardInterrupt as exc:
                error = {'type': 'KeyboardInterrupt', 'message': str(exc)}
            except Exception as exc:
                error = {'type': type(exc).__name__, 'message': str(exc)}
            work = fixture.root / str(fixture.count)
            out = work / 'run'
            canonical = out / 'result.json'
            raw = canonical.read_bytes() if canonical.is_file() else None
            record = json.loads(raw) if raw is not None else None
            name = mutation or 'unchanged'
            saved = directory / (label + '-FAKE-POSITIVE-' + name + '-result.json')
            if saved.exists():
                raise RuntimeError('refusing to replace an existing canonical counterexample')
            if raw is not None:
                saved.write_bytes(raw)
            rows.append({
                'mutation': mutation,
                'invocation': 'p.route(source / smoke.kicad_pcb, out), no preferences or class flag',
                'caught_exception': error,
                'returned_accepted': None if returned is None else returned.get('accepted'),
                'canonical_accepted': None if record is None else record.get('accepted'),
                'canonical_status': None if record is None else record.get('status'),
                'canonical_file': saved.name if raw is not None else None,
                'canonical_sha256': hashlib.sha256(raw).hexdigest() if raw is not None else None,
                'checker_reached': fixture.last_publication_state['checked'],
                'mutation_triggered': fixture.last_publication_state['triggered'],
                'invalidated_files': sorted(path.name for path in out.glob('invalidated-result-*')),
                'signal_handlers_restored': all(signal.getsignal(sig) == handler for sig, handler in handlers.items()),
                'source_unchanged': p.tree_hash(work / 'project') == p.tree_hash(ROOT / 'fixtures/smoke'),
            })
    finally:
        fixture.doCleanups()
    after = {str(path.relative_to(ROOT)): digest(path) for path in sources}
    report = {
        'schema': 1,
        'kind': 'plain direct route publication safety counterexample with explicitly mocked workers',
        'native_executed': False,
        'routing_quality_claim': False,
        'class_proof_claim': False,
        'label': label,
        'source_sha256': pins,
        'source_unchanged_during_reproduction': pins == after,
        'legacy_publication_excerpt': source[start:end] if start >= 0 and end > start else None,
        'controls': rows,
        'acceptance_requirement': 'Every positive reaches the central checker; interruption or late receipt mutation leaves no accepted canonical result.',
        'claims_limit': 'FakeWorkerJob emits synthetic worker outputs. This exercises real publication and signal handlers only, and establishes no native routing correctness.',
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'report': str(report_path.relative_to(ROOT)), 'controls': [
        {key: row[key] for key in ('mutation', 'caught_exception', 'canonical_accepted',
                                  'checker_reached', 'mutation_triggered', 'signal_handlers_restored')}
        for row in rows], 'source_unchanged': pins == after}, indent=2))
    if pins != after:
        raise RuntimeError('runtime source changed during reproduction')


if __name__ == '__main__':
    main()
