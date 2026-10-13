"""Pure continuation seams using the draft's existing fixture; no native/Git."""
import hashlib, importlib.util, json, subprocess, sys
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
HERE = Path(__file__).absolute().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('resume_controls_existing', ROOT / '.runs/portfolio-resume-draft-001/test_resume.py')
fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
m, p = fixture.m, fixture.p

class RetainedTemporaryDirectory:
    def __init__(self, directory):
        self.name = str(directory); directory.mkdir()
    def cleanup(self):
        pass  # Preserve synthetic controls and all failures as local evidence.

def forbidden(*args, **kwargs):
    raise AssertionError('subprocess forbidden in pure reviewer control')

def run_case(name, mode):
    case = fixture.ResumeControls('test_resume_only_unattempted_variants_and_preserve_prior_contract')
    with patch.object(fixture.legacy.tempfile, 'TemporaryDirectory', side_effect=lambda: RetainedTemporaryDirectory(HERE / name)):
        case.setUp()
    try:
        before = m.pc.inventory(case.old, with_directories=True)
        saved = p.save_json; publication = []
        def write(path, value):
            if path.name != 'portfolio-summary.json':
                return saved(path, value)
            publication.append({'status': value.get('status'), 'eligible': value.get('comparison_eligible'), 'cpu': value.get('total_cpu_seconds')})
            if mode == 'corrective-fails' and value.get('status') == 'invalidated':
                raise OSError('injected corrective publication failure')
            saved(path, value)
            if value.get('comparison_eligible') is True:
                if mode == 'corrective-fails':
                    raise p.Rejected('injected failure after positive publication')
                if mode == 'publication-cost':
                    case.cpu += 4.0; case.wall += 3.0
        result = None; failure = None
        with patch.object(p, 'save_json', side_effect=write):
            try: result = case.resumed()
            except BaseException as exc: failure = type(exc).__name__ + ': ' + str(exc)
        final_path = case.out / 'portfolio-summary.json'
        disk = json.loads(final_path.read_text()) if final_path.is_file() else None
        return {'mode':mode, 'failure':failure, 'calls':case.calls, 'retained_unchanged':m.pc.inventory(case.old, with_directories=True)==before,
                'returned_status':None if result is None else result['status'],
                'returned_eligible':None if result is None else result['comparison_eligible'],
                'disk_status':None if disk is None else disk['status'],
                'disk_eligible':None if disk is None else disk['comparison_eligible'],
                'disk_selected':None if disk is None else disk['selected']['id'] if disk.get('selected') else None,
                'stored_cpu_seconds':None if disk is None else disk.get('total_cpu_seconds'),
                'full_synthetic_cpu_seconds':32.0+case.cpu,
                'stored_wall_seconds':None if disk is None else disk.get('wall_seconds'),
                'full_synthetic_wall_seconds':30.0+case.wall, 'publication':publication}
    finally: case.doCleanups()

if __name__ == '__main__':
    with patch.object(subprocess, 'run', side_effect=forbidden), patch.object(subprocess, 'Popen', side_effect=forbidden):
        results = {name:run_case(name, mode) for name, mode in [('positive','normal'), ('corrective-fails','corrective-fails'), ('publication-cost','publication-cost')]}
    results['source_sha256'] = hashlib.sha256((ROOT / '.runs/portfolio-resume-draft-001/experiment_portfolio.py').read_bytes()).hexdigest()
    (HERE / 'controls.json').write_text(json.dumps(results, indent=2, sort_keys=True)+'\n')
    print(json.dumps(results, indent=2, sort_keys=True))
