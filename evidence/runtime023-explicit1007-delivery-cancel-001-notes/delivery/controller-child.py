"""One owned caller-pinned delivery slice; product helpers remain authority."""
import time, resource
START = time.monotonic()
def cpu():
    return sum(x.ru_utime + x.ru_stime for x in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import argparse, hashlib, json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, handoff as h, review_export as ex, config as c

def execute(protocol, pin):
    plan = f.read_json(protocol)
    if p.sha(protocol) != pin or c.ROOT != ROOT or Path(sys.executable) != ROOT / '.venv/bin/python':
        raise p.Rejected('frozen caller protocol and curated interpreter required')
    if Path(sys.prefix).resolve() != ROOT / '.venv' or sys.prefix == sys.base_prefix:
        raise p.Rejected('independent copied venv required')
    nt = p.ExperimentalNativeToolchain.from_record(plan['native_toolchain'])
    ctx = dict(native_toolchain=nt, experimental_schematic_parity=True)
    out = ROOT / '.runs/runtime023-explicit1007-delivery-001'
    if out.exists(): raise p.Rejected('fresh delivery destination required')
    out.mkdir(); owner = {}; h.capture_destination(owner, out)
    tools = p.tool_manifest(native_toolchain=nt)
    if tools != plan['runtime_tools']: raise p.Rejected('frozen runtime/tool context differs')
    constants = (c.CLI, c.PYTHON, c.PCBNEW, c.JAVA, c.JAR)
    source = out / 'source'; source.mkdir()
    for name, text in plan['fixture_files'].items():
        if Path(name).name != name: raise p.Rejected('one flat owned packet required')
        (source / name).write_bytes(text.encode())
    name = plan['board_name']
    if (type(name) is not str or Path(name).name != name or Path(name).suffix != '.kicad_pcb'
            or name not in plan['fixture_files'] or name not in plan['fixture_sha256']):
        raise p.Rejected('exact flat owned PCB name required')
    board = source / name; original = p.tree_hash(source)
    if original != plan['fixture_sha256']: raise p.Rejected('fresh fixture differs from frozen packet')
    record = dict(schema=1, accepted=False, passed=False, status='failed',
                  production_admitted=False, actual_GUI=False, human_review=False,
                  source_head=plan['source_head'], tools=tools, protocol_sha256=pin)
    prep_wall=plan['preparation_wall_seconds']+plan['preparation_publication_budget_charge_seconds']
    prep_cpu=plan['preparation_full_cpu_seconds']+plan['preparation_publication_budget_charge_seconds']
    def remaining(): return min(172-prep_wall-(time.monotonic()-START),172-prep_cpu-(cpu()-CPU0))
    def stable():
        h.owned_destination(owner)
        if (p.sha(protocol) != pin or p.tool_manifest(native_toolchain=nt) != tools
                or constants != (c.CLI, c.PYTHON, c.PCBNEW, c.JAVA, c.JAR)
                or p.tree_hash(source) != original):
            raise p.Rejected('source/runtime/protocol changed')
    try:
        if remaining() < 150: raise p.Rejected('insufficient frozen whole-slice reserve')
        route = p.route(board, out/'route', seconds=120, **ctx)
        if route.get('accepted') is not True: raise p.Rejected('fresh route refused: '+str(route.get('reason', route.get('status'))))
        if route.get('source') != str(board) or route.get('source_hashes') != original:
            raise p.Rejected('route source differs from fresh owned packet')
        if route['source_drc']['opens'] != 1: raise p.Rejected('source-open prediction differs')
        for key, value in dict(opens=0, blocking=0, warnings=6, exclusions=0).items():
            if route['native'][key] != value: raise p.Rejected('route population prediction differs: '+key)
        if route['metrics']['version'] != '10.0.7': raise p.Rejected('actual metrics version differs')
        protected = p.protected_for_record(route, p.sx.read(board))
        if len(protected) != 1 or not p.locked(protected[0]): raise p.Rejected('owned KEEP prediction differs')
        if remaining() < 80: raise p.Rejected('review/export delivery reserve unavailable')
        review = h.review_copy(out/'route/result.json', out/'review', render=True, **ctx)
        choice = h.review_choice(out/'review/review.json', out/'choice', 'accept', **ctx)
        export_cap = min(60, remaining()-12)
        if export_cap < 30: raise p.Rejected('fresh export minimum/reserve unavailable')
        exported = ex.export(out/'choice/choice.json', out/'export', seconds=export_cap, **ctx)
        current = ex.check_export(out/'export/export.json', **ctx)
        if current.get('current') is not True: raise p.Rejected('fresh export current proof refused')
        refused = {}
        for name, call in (
            ('route', lambda: p.check_result(out/'route/result.json')),
            ('review', lambda: h.check_delivery_context(review)),
            ('choice', lambda: ex.bind(out/'choice/choice.json')),
            ('export', lambda: ex.check_export(out/'export/export.json'))):
            try: call()
            except p.Rejected as exc: refused[name] = str(exc)
            else: raise p.Rejected('default consumer admitted experimental '+name)
        if choice['human_pcb_approval_observed'] is not False or choice['applied'] is not False:
            raise p.Rejected('software intent became human approval/application')
        record.update(passed=True, status='completed', route_sha256=p.sha(out/'route/result.json'),
                      export_sha256=p.sha(out/'export/export.json'), native=exported['native'],
                      metrics=exported['metrics'], protected_routes=1, default_refusals=refused,
                      checked_export=current, review_layers=review['preview']['layers'],
                      route_and_export_have_own_native_proof=True)
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      passed=False, error=type(exc).__name__+': '+str(exc))
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
