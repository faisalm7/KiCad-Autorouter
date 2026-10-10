"""Independent pure policy review. Reads retained native evidence; launches no worker."""
from pathlib import Path
import copy
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from autorouter import pipeline as p, strategy

OUT = Path(__file__).resolve().parent
checks = []


def check(name, value):
    checks.append({'name': name, 'passed': bool(value)})


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


files = ['autorouter/pipeline.py', 'autorouter/strategy.py', 'autorouter/handoff.py',
         'scripts/experiment_quality.py', 'scripts/experiment_portfolio.py',
         'scripts/experiment_paired.py', 'scripts/native_padstack_controls.py',
         'scripts/native_controls.py', 'scripts/native_thermal_bridge_control.py',
         'scripts/experiment_krt.py', 'tests/test_padstack_policy.py']
before = {name: digest(ROOT/name) for name in files}
reports = []
for run in ('padstack-native-controls-001', 'padstack-native-controls-002'):
    folder = ROOT/'.runs'/run
    summary = json.loads((folder/'summary.json').read_text())
    for case in summary['cases']:
        raw = folder/(case['case']+'-drc.json')
        raw_hash = digest(raw)
        native = p.parse_report(raw, 'multichannel_mixer.kicad_pcb')
        snapshot = copy.deepcopy(native)
        accepted = p.native_accepted(native)
        reasons = p.native_rejection_reasons(native)
        tag = run+'/'+case['case']
        check(tag+'/raw_hash', raw_hash == case['report_sha256'])
        check(tag+'/summary_unchanged', native == case['native'])
        expected = case['case'] in ('positive', 'smd_hole')
        check(tag+'/expected_policy', accepted is expected)
        check(tag+'/strategy_policy', strategy._valid(native) is expected)
        check(tag+'/no_mutation', native == snapshot and digest(raw) == raw_hash)
        reports.append({'run': run, 'case': case['case'], 'raw_sha256': raw_hash,
                        'accepted_by_current_policy': accepted, 'reasons': reasons,
                        'native_counts': {k: native[k] for k in ('opens','blocking','warnings','exclusions')},
                        'findings': [(f['type'], f['severity']) for f in native['findings']]})

clean = {'opens':0, 'blocking':0, 'warnings':0, 'exclusions':0,
         'ignored_checks':[], 'findings':[]}
for kind in sorted(p.CRITICAL_FINDINGS):
    for severity in ('warning', 'error', 'exclusion'):
        native = dict(clean, findings=[{'type':kind,'severity':severity,'items':[]}])
        snapshot = copy.deepcopy(native)
        check('critical/'+kind+'/'+severity,
              p.native_accepted(native) is False and native == snapshot)
for kind in ('padstack', 'padstack_invalid', 'unrecognized_namespace'):
    check('disabled/'+kind, not p.native_accepted(dict(clean, ignored_checks=[{'key':kind}])))
for key in ('opens', 'blocking', 'warnings', 'exclusions'):
    for bad in (None, False, -1, '0', [], {}, float('nan')):
        check('malformed_count/'+key+'/'+repr(bad), not p.native_accepted(dict(clean, **{key:bad})))
for field, bad_values in {
    'findings': (None, {}, [None], [{}], [{'type':'padstack','severity':[],'items':[]}],
                 [{'type':'padstack','severity':'warning','items':[None]}]),
    'ignored_checks': (None, {}, [None], [{}], [{'key':[]}]),
}.items():
    for i, bad in enumerate(bad_values):
        check('malformed/'+field+'/'+str(i), not p.native_accepted(dict(clean, **{field:bad})))
for severity in ('error', 'exclusion'):
    check('ordinary_finding/'+severity, not p.native_accepted(dict(clean,
        findings=[{'type':'track_dangling','severity':severity,'items':[]}])) )
check('ordinary_excluded_finding', not p.native_accepted(dict(clean,
    findings=[{'type':'track_dangling','severity':'warning','items':[],'excluded':True}])))
check('ordinary_warning_still_allowed', p.native_accepted(dict(clean, warnings=1,
    findings=[{'type':'lib_footprint_mismatch','severity':'warning','items':[]}])))

# Enumerate exact severity-setting exceptions using only a controlled review fixture.
fixture = OUT/'scratch'
fixture.mkdir(exist_ok=False)
board = fixture/'board.kicad_pcb'
board.write_text('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)))\n')
project = board.with_suffix('.kicad_pro')
for key in sorted(p.CRITICAL_CHECKS | {'padstack_invalid','unrecognized_namespace'}):
    for severity in ('error','warning','ignore'):
        project.write_text(json.dumps({'board':{'design_settings':{'rule_severities':{key:severity}}}}))
        source = project.read_bytes()
        try:
            p.preflight(board)
            allowed = True
        except p.Rejected:
            allowed = False
        expected = (key in p.CRITICAL_CHECKS and severity == 'error') or (key,severity)==('padstack','warning')
        check('preflight/'+key+'/'+severity, allowed == expected and project.read_bytes() == source)

check('reviewed_code_unchanged', before == {name:digest(ROOT/name) for name in files})
result = {'kind':'independent read-only policy review plus controlled pure fixtures',
          'native_executed':False, 'engines_executed':False,
          'source_sha256':before, 'script_sha256':digest(Path(__file__)),
          'checks':checks, 'passed':all(c['passed'] for c in checks),
          'retained_native_reports':reports,
          'limits':['This is not fresh native validation.',
                    'Historical smd_hole negative remains invalid; no findings were emitted.',
                    'A policy helper is not an authenticating report parser; production callers derive it from parse_report.',
                    'Passing this review does not qualify thermal topology, new pad geometries, or general routing superiority.']}
(OUT/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[c['name'] for c in checks if not c['passed']]}))
sys.exit(0 if result['passed'] else 1)
