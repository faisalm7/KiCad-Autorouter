"""Derived from the retained explicit1007 delivery controller; shared helpers remain authority.

This fixed corrected comparison API is non-admitting. Execute only in the new
curated runtime after source freeze/review/full integration and frozen protocol.
Two fixed owned API controls are functional proof only, never a fair benchmark.
"""
import time, resource
START = time.monotonic()
def cpu():
    return sum(x.ru_utime + x.ru_stime for x in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import argparse, hashlib, json, math, re, sys
from decimal import Decimal
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, handoff as h, review_export as ex, config as c, comparison as cmp
from autorouter import placement_clearance as pc, provenance as pv, review_view as view

KIND = 'native7-comparison-functional-delivery-v1'
CASES = {'standard_positive': ('standard', 'native7-comparison-functional-001'),
         'tuned_variant': ('tuned', 'native7-comparison-functional-tuned-001')}
LIMITS = dict(whole_wall_full_cpu_seconds=180, worker_seconds=176, child_acceptance_seconds=172,
             route_seconds=120, export_min_seconds=30, export_max_seconds=60, final_reserve_seconds=12)


def preparation(plan):
    """Use the actual complete external preparation observation, not an old sample."""
    path = h.real_path(plan['preparation_time_log']); raw = pc.read_bytes(path, 64 * 1024)
    if hashlib.sha256(raw).hexdigest() != plan['preparation_time_log_sha256']:
        raise p.Rejected('frozen preparation time log changed')
    rows = re.findall(r'^(real|user|sys) ([0-9]+(?:\.[0-9]+)?)$', raw.decode(), re.M)
    if len(rows) != 3 or {key for key, _ in rows} != {'real', 'user', 'sys'}:
        raise p.Rejected('one complete external /usr/bin/time -lp preparation observation required')
    values = {key: Decimal(value) for key, value in rows}
    for key, expected in (('preparation_wall_seconds', values['real']),
                          ('preparation_full_cpu_seconds', values['user'] + values['sys'])):
        value = plan[key]
        if type(value) not in (int, float) or not math.isfinite(value) or Decimal(str(value)) != expected:
            raise p.Rejected('preparation cost differs from actual complete log: ' + key)
    if type(plan['preparation_publication_budget_charge_seconds']) is not int or plan['preparation_publication_budget_charge_seconds'] != 4:
        raise p.Rejected('fixed four-second planning charge required; not measured runtime')
    return float(values['real']) + 4, float(values['user'] + values['sys']) + 4, path

def execute(protocol, pin):
    protocol = h.real_path(protocol); plan = f.read_json(protocol)
    self_path = h.real_path(__file__); self_pin = p.sha(self_path)
    if (p.sha(protocol) != pin or plan.get('kind') != KIND or type(plan.get('schema')) is not int or plan['schema'] != 1
            or plan.get('runtime') != str(ROOT) or plan.get('controller_sha256') != self_pin
            or c.ROOT != ROOT or c.NATIVE_VERSION != '10.0.7' or Path(sys.executable) != ROOT / '.venv/bin/python'):
        raise p.Rejected('frozen caller protocol and curated interpreter required')
    if Path(sys.prefix).resolve() != ROOT / '.venv' or sys.prefix == sys.base_prefix:
        raise p.Rejected('independent copied venv required')
    manifest = ROOT / pv.MANIFEST
    if p.sha(manifest) != plan['runtime_manifest_sha256'] or plan.get('limits') != LIMITS:
        raise p.Rejected('frozen runtime manifest or fixed control limits differ')
    case = plan['case']
    if (case not in CASES or plan.get('profile') != CASES[case][0]
            or plan.get('output') != str(ROOT / '.runs' / CASES[case][1])):
        raise p.Rejected('one fixed standard/tuned functional case required')
    if (type(plan.get('route_seconds')) is not int or plan['route_seconds'] != 120
            or type(plan.get('expected_source_opens')) is not int or plan['expected_source_opens'] != 2
            or type(plan.get('expected_protected_routes')) is not int or plan['expected_protected_routes'] != 1
            or plan.get('expected_Native_counts') != [0, 0, 0, 0]
            or any(type(value) is not int for value in plan['expected_Native_counts'])
            or plan.get('board_name') != 'owned1007-transport.kicad_pcb'):
        raise p.Rejected('fixed owned unflagged2Cu predictions differ')
    prep_wall, prep_cpu, prep_log = preparation(plan)
    tools = p.tool_manifest()
    if (tools != plan['runtime_tools'] or tools.get('git_head') != plan['source_head']
            or tools.get('kicad') != '10.0.7' or tools['source_provenance'].get('kind') != pv.KIND
            or tools['source_provenance'].get('native_version') != '10.0.7'):
        raise p.Rejected('frozen runtime/source/tool context differs')
    out = h.real_path(plan['output'], existing=False)
    if out.exists(): raise p.Rejected('fresh delivery destination required')
    p.check_storage(active_root=out)
    out.mkdir(); owner = {}; h.capture_destination(owner, out)
    constants = (c.CLI, c.PYTHON, c.PCBNEW, c.JAVA, c.JAR)
    source = out / 'source'; source.mkdir()
    files = plan['fixture_files']
    if (type(files) is not dict or not 3 <= len(files) <= 8 or set(files) != set(plan['fixture_sha256'])
            or any(type(text) is not str for text in files.values()) or sum(len(text.encode()) for text in files.values()) > 2 * 1024**2):
        raise p.Rejected('small exact frozen owned fixture packet required')
    for name, text in files.items():
        if type(name) is not str or Path(name).name != name or name in ('.','..'):
            raise p.Rejected('one flat owned packet required')
        with (source / name).open('xb') as stream: stream.write(text.encode())
    name = plan['board_name']
    if (type(name) is not str or Path(name).name != name or Path(name).suffix != '.kicad_pcb'
            or name not in plan['fixture_files'] or name not in plan['fixture_sha256']):
        raise p.Rejected('exact flat owned PCB name required')
    board = source / name; original = p.tree_hash(source)
    if original != plan['fixture_sha256']: raise p.Rejected('fresh fixture differs from frozen packet')
    authority = cmp.Context(board, out/'route', plan['profile'], plan['route_seconds'], tools, original)
    ctx = dict(comparison_context=authority)
    record = dict(schema=1, accepted=False, passed=False, status='failed',
                  production_admitted=False, actual_GUI=False, human_review=False,
                  source_head=plan['source_head'], tools=tools, protocol_sha256=pin, case=case,
                  controller_sha256=self_pin, runtime_manifest_sha256=plan['runtime_manifest_sha256'],
                  source=str(board), source_hashes=original, profile=plan['profile'], route_seconds=120,
                  limits=LIMITS, preparation_time_log=str(prep_log), preparation_time_log_sha256=plan['preparation_time_log_sha256'],
                  recorded_preparation_wall_seconds=plan['preparation_wall_seconds'],
                  recorded_preparation_full_cpu_seconds=plan['preparation_full_cpu_seconds'],
                  preparation_publication_budget_charge_seconds=4, fair_comparison=False, complete_external_exit_required=True)
    def remaining(): return min(172-prep_wall-(time.monotonic()-START),172-prep_cpu-(cpu()-CPU0))
    def stable():
        h.owned_destination(owner)
        authority.check()
        if (p.sha(protocol) != pin or p.sha(self_path) != self_pin or p.sha(manifest) != plan['runtime_manifest_sha256']
                or p.sha(prep_log) != plan['preparation_time_log_sha256'] or p.tool_manifest() != tools
                or constants != (c.CLI, c.PYTHON, c.PCBNEW, c.JAVA, c.JAR)
                or p.tree_hash(source) != original):
            raise p.Rejected('source/runtime/protocol changed')
        for name, module in tuple(sys.modules.items()):
            if name.split('.')[0] == 'autorouter' and getattr(module, '__file__', None) and not Path(module.__file__).resolve().is_relative_to(ROOT):
                raise p.Rejected('foreign helper imported: ' + name)
    try:
        if remaining() < 150: raise p.Rejected('insufficient frozen whole-slice reserve')
        route = p.route(board, out/'route', seconds=plan['route_seconds'], adapter='both', engine_profile=plan['profile'], **ctx)
        record.update(route_status=route.get('status'), route_accepted=route.get('accepted'),
                      source_native=route.get('source_drc'), route_native=route.get('native'))
        if route.get('accepted') is not True: raise p.Rejected('fresh route refused: '+str(route.get('reason', route.get('status'))))
        if route.get('source') != str(board) or route.get('source_hashes') != original:
            raise p.Rejected('route source differs from fresh owned packet')
        if route['source_drc']['opens'] != plan['expected_source_opens']: raise p.Rejected('source-open prediction differs')
        record['source_native'] = route['source_drc']
        for key, value in dict(zip(('opens','blocking','warnings','exclusions'),plan['expected_Native_counts'])).items():
            if route['native'][key] != value: raise p.Rejected('route population prediction differs: '+key)
        if route['metrics']['version'] != '10.0.7': raise p.Rejected('actual metrics version differs')
        route_current = p.check_result(out/'route/result.json', **ctx)
        protected = p.protected_for_record(route, p.sx.read(board))
        if len(protected) != 1 or not p.locked(protected[0]): raise p.Rejected('owned KEEP prediction differs')
        if remaining() < 80: raise p.Rejected('review/export delivery reserve unavailable')
        review = h.review_copy(out/'route/result.json', out/'review', render=True, **ctx)
        choice = h.review_choice(out/'review/review.json', out/'choice', 'accept', **ctx)
        export_cap = min(60, remaining()-12)
        if export_cap < 30: raise p.Rejected('fresh export minimum/reserve unavailable')
        exported = ex.export(out/'choice/choice.json', out/'export', seconds=export_cap, **ctx)
        current = ex.check_export(out/'export/export.json', **ctx)
        if route_current.get('current') is not True or current.get('current') is not True: raise p.Rejected('fresh own Route/export current proof refused')
        for label, data in (('route', route), ('export', exported)):
            if (data.get('schematic_parity') != 'checked by final native DRC'
                    or [data['native'][key] for key in ('opens','blocking','warnings','exclusions')] != [0,0,0,0]
                    or data['metrics']['version'] != '10.0.7'
                    or not all(item in p.routes(p.sx.read(Path(data['candidate']))) for item in protected)):
                raise p.Rejected(label + ' full-SCH/Native/protected prediction differs')
        for data in (route, route_current, review, review['preview'], choice, exported, current):
            if data.get('production_admitted') is not False: raise p.Rejected('comparison became production admission')
        refusal_before = f.evidence_inventory(out); refused = {}
        for name, call in (
            ('route', lambda: p.check_result(out/'route/result.json')),
            ('completed_negative', lambda: p.check_rejected_routing_attempt(out/'route/result.json')),
            ('review', lambda: h.check_delivery_context(review)),
            ('review_copy', lambda: h.review_copy(out/'route/result.json', out/'default-review')),
            ('preview', lambda: view.check_experimental_preview(out/'review', review['preview'])),
            ('choice_intent', lambda: h.review_choice(out/'review/review.json', out/'default-choice', 'accept')),
            ('choice', lambda: ex.bind(out/'choice/choice.json')),
            ('export', lambda: ex.check_export(out/'export/export.json'))):
            try: call()
            except p.Rejected as exc: refused[name] = str(exc)
            else: raise p.Rejected('default consumer admitted experimental '+name)
        if f.evidence_inventory(out) != refusal_before: raise p.Rejected('default refusal mutated owned evidence')
        if current.get('production_admitted') is not False: raise p.Rejected('comparison export became production admission')
        if choice['human_pcb_approval_observed'] is not False or choice['applied'] is not False:
            raise p.Rejected('software intent became human approval/application')
        record.update(passed=True, status='completed', route_sha256=p.sha(out/'route/result.json'),
                      export_sha256=p.sha(out/'export/export.json'), native=exported['native'],
                      metrics=exported['metrics'], protected_routes=1, default_refusals=refused,
                      checked_route=route_current, checked_export=current, export_seconds=export_cap, review_layers=review['preview']['layers'],
                      route_and_export_have_own_native_proof=True)
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      passed=False, error=type(exc).__name__+': '+str(exc))
    for label in ('route','export'):
        receipt = out/label/('result.json' if label=='route' else 'export.json')
        if receipt.is_file():
            data = f.read_json(receipt)
            record[label+'_outcome'] = {key:data.get(key) for key in ('status','accepted','export_accepted','native','candidate_sha256','reason','error')}
    record['completed_evidence'] = f.evidence_inventory(out)
    def fresh():
        stable()
        if f.evidence_inventory(out) != record['completed_evidence']:
            raise p.Rejected('completed delivery evidence changed')
    def final_check():
        # Publication still ends in the complete central export checker. Its
        # own final byte and PRL guards run after all tool-bearing callbacks.
        # The stable callback above is only a material witness; repeating the
        # complete semantic checker at every publication seam adds no distinct
        # acceptance requirement. Never cache or bypass the final proof.
        fresh()
        if record['passed']:
            ex.check_export(out/'export/export.json', **ctx)
    def account():
        record.update(execution_wall_seconds=time.monotonic()-START,execution_full_cpu_seconds=cpu()-CPU0,
                      charged_preparation_wall_seconds=prep_wall,charged_preparation_full_cpu_seconds=prep_cpu,
                      wall_seconds=prep_wall+time.monotonic()-START,full_cpu_seconds=prep_cpu+cpu()-CPU0)
        if remaining() <= 0: record.update(passed=False, status='budget_exceeded')
        if record['status']!='completed':record['passed']=False
    f.publish(out, record, fresh, account, remaining,
              owned=lambda: h.owned_destination(owner), final_check=final_check)
    print(json.dumps({key:record.get(key) for key in ('passed','status','wall_seconds','full_cpu_seconds','error')}))
    return 0 if record['passed'] and record['status']=='completed' else 2

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-sha256', required=True)
    args=parser.parse_args()
    raise SystemExit(execute(args.protocol, args.protocol_sha256))
