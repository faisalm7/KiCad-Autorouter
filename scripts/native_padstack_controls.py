"""Native padstack controls; diagnostic only, no support gate changes.

Run with ordinary Python from this checkout after the lead releases the native
lane. Native DRC is bounded by one 120-second Job. No routing or source writes.
"""
from __future__ import annotations
import argparse
import copy
import fcntl
import signal
import json
from pathlib import Path
import resource
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autorouter import config as c, pipeline as p, sexpr as sx

PROJECT = ROOT / '.data/boards/kicad-multichannel/multichannel_mixer.kicad_pro'
# Complete immutable project hash, deliberately not a subset of its settings.
PROJECT_SHA = 'ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538'
FIXTURE = ROOT / 'fixtures/smoke/smoke.kicad_pcb'
CASES = ('positive', 'wrong_paste', 'pth_tiny_hole')
PAD_TYPES = {'padstack', 'padstack_invalid'}


def fixture(case):
    """Make a new owned diagnostic board, never alter either reference input."""
    if case not in (*CASES, 'smd_hole'):
        raise ValueError('unknown fixture case')
    tree = sx.read(FIXTURE)
    fp = copy.deepcopy(sx.children(tree, 'footprint')[0])
    tree[:] = [v for v in tree if not isinstance(v, list) or not v or
               v[0] not in {'footprint', 'net', 'zone', 'segment', 'arc', 'via'}]
    fp[:] = [v for v in fp if not isinstance(v, list) or not v or v[0] != 'attr']
    fp.append(['attr', 'smd'])
    pad = sx.one(fp, 'pad')
    pad[2:4] = ['smd', 'rect']
    pad[:] = [v for v in pad if not isinstance(v, list) or not v or
              v[0] not in {'net', 'drill', 'layers', 'remove_unused_layers'}]
    pad.append(['layers', '"F.Cu"', '"F.Mask"',
                '"B.Paste"' if case == 'wrong_paste' else '"F.Paste"'])
    if case == 'smd_hole':
        # Retained failed recipe from run001: KiCad discards SMD drills on load.
        pad.append(['drill', '0.8'])
    elif case == 'pth_tiny_hole':
        sx.one(fp, 'attr')[1:] = ['through_hole']
        pad[2:4] = ['thru_hole', 'circle']
        sx.one(pad, 'layers')[1:] = ['"*.Cu"', '"*.Mask"']
        # Positive one-nanometre PTH drill survives parsing and is below the
        # pinned padstack check's four-internal-unit tolerance. Other original
        # drill-rule errors remain recorded; only padstack_invalid qualifies.
        pad.append(['drill', '0.000001'])
    tree.append(fp)
    return tree, sx.unquote(sx.one(pad, 'uuid')[1])


def proposed_summary(report, name):
    """Production policy on an actual report; native severities stay untouched."""
    summary = p.parse_report(report, name)
    critical = [v for v in summary['findings']
                if v['type'] in p.CRITICAL_FINDINGS]
    return {'native': summary, 'policy_critical_count': len(critical),
            'policy_critical_findings': critical,
            'policy_accepted': p.native_accepted(summary),
            'native_rejection_reasons': p.native_rejection_reasons(summary)}


def cpu():
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + child.ru_utime + child.ru_stime


def experiment(out):
    start = time.monotonic(); start_cpu = cpu()
    out = Path(out).absolute()
    if out.exists() or out.is_symlink() or not out.parent.is_dir():
        raise ValueError('output must be a new child of an existing directory')
    if not out.resolve().is_relative_to(ROOT / '.runs'):
        raise ValueError('diagnostic output must remain under this checkout .runs')
    for ancestor in (out, *out.parents):
        if ancestor.is_symlink():
            raise ValueError('symlink in output path')
    if PROJECT.is_symlink() or FIXTURE.is_symlink() or p.sha(PROJECT) != PROJECT_SHA:
        raise ValueError('original project changed or a reference is a symlink')
    project = json.loads(PROJECT.read_text())
    settings = project['board']['design_settings']
    if settings['rule_severities'].get('padstack') != 'warning' or settings.get('drc_exclusions'):
        raise ValueError('expected unmodified warning-severity project without exclusions')
    # The actual source has no custom rules file. Refuse to omit one if it appears.
    if PROJECT.with_suffix('.kicad_dru').exists():
        raise ValueError('new original rule file requires explicit control review')
    original_hashes = {'project': p.sha(PROJECT), 'fixture': p.sha(FIXTURE)}
    manifest = p.tool_manifest()
    job = p.Job(out, max(0.01, 120 - (time.monotonic() - start)))
    record = {'schema': 1, 'purpose': 'native padstack diagnostic qualification only',
              'routing_accepted': False, 'control_changes_production_support': False,
              'controls_passed': False, 'seconds_ceiling': 120,
              'script_sha256': p.sha(__file__), 'tools': manifest,
              'original_inputs': original_hashes, 'cases': []}
    shutil.copy2(__file__, out / 'control.py')
    if p.sha(out / 'control.py') != record['script_sha256']:
        raise ValueError('control changed during snapshot')
    p.save_json(out / 'summary.json', record)
    try:
        for case in CASES:
            entry = {'case': case, 'passed': False}
            record['cases'].append(entry)
            case_dir = out / case; case_dir.mkdir()
            board = case_dir / PROJECT.with_suffix('.kicad_pcb').name
            tree, pad_uuid = fixture(case)
            sx.write(board, tree)
            shutil.copy2(PROJECT, board.with_suffix('.kicad_pro'))
            before = p.tree_hash(case_dir)
            entry.update({'source_hashes': before, 'target_pad_uuid': pad_uuid,
                          'fixture_roundtrip_equal': sx.read(board) == tree})
            try:
                # DRC validates an exact isolated copy and binds its raw report.
                job.drc(case + '-drc', board)
                report = out / (case + '-drc.json')
                policy = proposed_summary(report, board.name)
                hits = [v for v in policy['native']['findings'] if v['type'] in PAD_TYPES]
                targeted = [v for v in hits if any(i.get('uuid') == pad_uuid for i in v['items'])]
                entry.update(policy)
                entry['report_sha256'] = p.sha(report)
                entry['targeted_padstack_findings'] = targeted
                if case == 'positive':
                    expected = policy['policy_accepted'] and not hits
                elif case == 'wrong_paste':
                    expected = (not policy['policy_accepted'] and
                                policy['native']['blocking'] == 0 and
                                any(v['type'] == 'padstack' and v['severity'] == 'warning'
                                    for v in targeted))
                else:
                    expected = (not policy['policy_accepted'] and
                                any(v['type'] == 'padstack_invalid' and v['severity'] == 'error'
                                    for v in targeted))
                entry['passed'] = bool(expected and not policy['native']['opens'] and
                                       not policy['native']['exclusions'] and
                                       entry['fixture_roundtrip_equal'] and
                                       p.tree_hash(case_dir) == before)
            except Exception as exc:
                entry['error'] = type(exc).__name__ + ': ' + str(exc)
            if any(step.get('status') == 'cancelled' for step in job.steps):
                raise KeyboardInterrupt
            p.save_json(out / 'summary.json', record)
        if p.tool_manifest() != manifest or p.sha(__file__) != record['script_sha256']:
            raise ValueError('tool or control code changed during native qualification')
        if p.sha(PROJECT) != original_hashes['project'] or p.sha(FIXTURE) != original_hashes['fixture']:
            raise ValueError('reference input changed')
        record['controls_passed'] = all(v['passed'] for v in record['cases'])
    except (Exception, KeyboardInterrupt) as exc:
        record['error'] = type(exc).__name__ + ': ' + str(exc)
        record['controls_passed'] = False
    def account():
        record['steps'] = job.steps
        record['wall_seconds'] = time.monotonic() - start
        record['cpu_seconds'] = cpu() - start_cpu
        if record['wall_seconds'] > 120 or record['cpu_seconds'] > 120:
            record['controls_passed'] = False
            record['budget_exceeded'] = True
    try:
        account()
        p.save_json(out / 'summary.json', record)
        if time.monotonic() - start > 120 or cpu() - start_cpu > 120:
            account()
            p.save_json(out / 'summary.json', record)
    except KeyboardInterrupt:
        record.update(controls_passed=False, error='KeyboardInterrupt during final publication')
        partial = out / 'summary.json.partial'
        if partial.exists():
            partial.rename(out / 'cancelled-summary.partial')
        account()
        p.save_json(out / 'summary.json', record)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, interrupted)
    lock_path = ROOT / '.runs/quality-experiment.lock'
    if lock_path.is_symlink():
        parser.error('experiment lock is a symlink')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = experiment(args.out)
    print(json.dumps({'controls_passed': result['controls_passed'], 'output': str(args.out)}))
    raise SystemExit(0 if result['controls_passed'] else 1)
