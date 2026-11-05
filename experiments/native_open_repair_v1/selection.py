"""Pure, deliberately narrow Native pad-pair selector; not a Native verifier.

Caller must first replay the complete hash-bound, completed-negative proof.
No descriptions, electrical-name heuristics, partial selection or rerouting.
"""
import hashlib
import uuid

from autorouter import board_floor as g, pipeline as p, routing_scope as rs, sexpr as sx


def derive(candidate_bytes, native, *, candidate_sha256, report_sha256):
    if (type(candidate_bytes) is not bytes or not candidate_bytes
            or hashlib.sha256(candidate_bytes).hexdigest() != candidate_sha256
            or type(report_sha256) is not str or len(report_sha256) != 64
            or any(c not in '0123456789abcdef' for c in report_sha256)):
        raise p.Rejected('exact candidate/report hashes required')
    reasons = p.native_rejection_reasons(native)
    if type(native) is not dict:
        raise p.Rejected('complete Native summary required')
    if (type(native.get('opens')) is not int or native['opens'] <= 0
            or set(reasons) != {'native opens=' + str(native['opens']),
                'native error finding: unconnected_items',
                'policy-critical native finding: unconnected_items (error)'}
            or native['blocking'] != 0 or native['exclusions'] != 0):
        raise p.Rejected('qualified opens-only completed negative required')
    tree = sx.parse(candidate_bytes.decode('utf-8'))
    pads = g.task_pads(tree)
    opens = [row for row in native['findings'] if row['type'] == 'unconnected_items']
    if len(opens) != native['opens']:
        raise p.Rejected('all Native open findings must be represented')
    names = set(); witnesses = []; pairs = set()
    for finding in opens:
        items = finding['items']
        if (finding['severity'] != 'error' or finding.get('excluded', False)
                or len(items) != 2):
            raise p.Rejected('only unexcluded two-pad Native open witnesses qualify')
        endpoints = []
        for item in items:
            identity = item.get('uuid')
            try: canonical = str(uuid.UUID(identity))
            except (ValueError, TypeError, AttributeError):
                raise p.Rejected('canonical Native endpoint UUID required') from None
            if identity != canonical or identity not in pads:
                raise p.Rejected('Native open endpoint must resolve to an exact source pad UUID')
            pad = pads[identity]
            if not pad['net'] or not pad['copper_layers']:
                raise p.Rejected('Native endpoint must have a named copper pad net')
            endpoints.append(dict(uuid=identity, **pad))
        pair = tuple(sorted(x['uuid'] for x in endpoints))
        if pair[0] == pair[1] or pair in pairs or endpoints[0]['net'] != endpoints[1]['net']:
            raise p.Rejected('distinct unique same-net pad pairs required')
        pairs.add(pair); names.add(endpoints[0]['net']); witnesses.append(endpoints)
    names = rs.validate_names(sorted(names)); mapping = rs._net_mapping(tree)
    if any(rs._net_name(route, mapping) in names for route in p.routes(tree)):
        raise p.Rejected('open-net repair requires zero existing copper on every selected net')
    # Existing scope helper also rejects ambiguous IDs, locks and malformed nets.
    protected = rs.protected_routes(tree, names)
    if protected != p.routes(tree):
        raise p.Rejected('all existing candidate copper must remain protected')
    return dict(schema=1, policy='native-open-pad-pairs-empty-nets-v1',
        candidate_sha256=candidate_sha256, native_report_sha256=report_sha256,
        names=names, all_open_witnesses=witnesses, protected_count=len(protected),
        scope_binding=rs.bind(candidate_bytes, names), native_validation_performed=False)
