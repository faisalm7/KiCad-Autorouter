"""DRAFT pure pad-component normalization; never routing acceptance."""
import hashlib, json, re
MAX_PADS, MAX_NETS, MAX_ITEMS, MAX_TOTAL_RETURNED, MAX_OUTPUT = 256, 128, 4000, 50000, 1024**2
UUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")
def need(value, reason):
    if not value: raise ValueError(reason)
def normalize(rows, reachable):
    need(type(rows) is list and 1 <= len(rows) <= MAX_PADS, 'bounded complete pad census required')
    by = {}
    for row in rows:
        need(type(row) is dict and set(row) == {'uuid','footprint_uuid','reference','number','net','netcode','layers','attribute','eligible','excluded_reason'}, 'pad row schema differs')
        for name in ('uuid','footprint_uuid'):
            need(type(row[name]) is str and UUID.fullmatch(row[name]), 'canonical native UUID required')
        need(row['uuid'] not in by, 'duplicate pad UUID')
        need(all(type(row[k]) is str and len(row[k].encode()) <= 1024 and '\x00' not in row[k] for k in ('reference','number','net','excluded_reason')), 'bounded exact pad identity required')
        need(type(row['netcode']) is int and row['netcode'] >= 0 and bool(row['net']) == (row['netcode'] > 0), 'null/positive net identity differs')
        need(type(row['eligible']) is bool and type(row['layers']) is list and row['layers'] in ([], ['F.Cu'], ['B.Cu'], ['F.Cu','B.Cu']), 'unqualified copper layer declaration')
        need(row['eligible'] == (row['attribute'] in ('pth','smd') and bool(row['layers']) and row['netcode'] > 0), 'eligibility differs')
        need(bool(row['excluded_reason']) != row['eligible'], 'missing exclusion explanation')
        by[row['uuid']] = row
    names = {r['net'] for r in rows if r['netcode'] > 0}
    need(1 <= len(names) <= MAX_NETS, 'bounded positive-net population required')
    identities = {(r['net'],r['netcode']) for r in rows if r['netcode'] > 0}
    need(len(identities) == len(names) == len({code for name,code in identities}), 'native net name/code mapping is not bijective')
    eligible = {u for u,r in by.items() if r['eligible']}
    need(eligible and type(reachable) is dict and set(reachable) == eligible, 'missing or extra queried pad')
    groups = {}
    for seed, members in reachable.items():
        need(type(members) is list and 1 <= len(members) <= MAX_PADS and len(members) == len(set(members)), 'duplicate/unbounded reachable pad list')
        need(seed in members and set(members) <= eligible, 'seed missing or unknown/ineligible returned pad')
        need(all(by[u]['net'] == by[seed]['net'] and by[u]['netcode'] == by[seed]['netcode'] for u in members), 'mixed-net returned pads')
        groups[seed] = sorted(members)
    for seed, group in groups.items():
        need(all(groups[u] == group for u in group), 'asymmetric or nontransitive pad components')
    components = []
    for members in sorted({tuple(v) for v in groups.values()}):
        components.append({'pad_uuids':list(members), 'net':by[members[0]]['net'], 'netcode':by[members[0]]['netcode'],
            'membership_sha256':hashlib.sha256(json.dumps(members,separators=(',',':')).encode()).hexdigest()})
    return {'pad_census':sorted(rows,key=lambda r:r['uuid']), 'reachable_pad_uuids':dict(sorted(groups.items())),
        'components':components, 'positive_net_count':len(names), 'queried_pad_count':len(eligible),
        'excluded_pad_uuids':sorted(set(by)-eligible)}
