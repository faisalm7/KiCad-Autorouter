"""Pure fixed-placement Roller diagnostic transforms; no Native acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import uuid
from autorouter import adapter, pipeline as p, sexpr as sx
from experiments.roller_export_alias_v1.padless_alias import dsn_aliases


def task(original):
    """Remove unlocked routing and derived fill only; retain every source rule."""
    if any(p.locked(row) for row in p.routes(original)):
        raise p.Rejected('whole-unrouted diagnostic cannot remove locked copper')
    result=copy.deepcopy(original)
    result[:]=[row for row in result if row not in p.routes(result)]
    for zone in sx.children(result,'zone'):
        zone[:]=[row for row in zone if not isinstance(row,list) or not row or row[0] not in p.DERIVED_ZONE]
    if p.routes(result) or p.immutable(result)!=p.immutable(original):
        raise p.Rejected('task changed nonrouting source intent')
    return result


def session(raw,dsn,source,binding,*,engine_input_name):
    """Aliases may occur only in omitted placement; routing AST stays exact.

    There is intentionally no SES/DSN placement-coordinate equality check:
    placement is never applied by the shared fixed-placement Native importer.
    """
    tree,_=dsn_aliases(dsn,source,binding)
    filtered,record=adapter.fixed_placement_session(raw)
    parsed=sx.parse(raw.decode());base=sx.one(parsed,'base_design')
    if (type(engine_input_name)is not str or Path(engine_input_name).name!=engine_input_name
            or '/' in engine_input_name or '\\' in engine_input_name or Path(engine_input_name).stem in ('','.','..')
            or not engine_input_name.endswith('.dsn') or not 5<=len(engine_input_name)<=128):
        raise p.Rejected('bounded engine input filename required')
    if sx.unquote(base[1])!=Path(engine_input_name).stem:raise p.Rejected('SES base design differs from exact engine input')
    aliases={row['alias'] for row in binding['aliases']}
    def mentions(node):
        if isinstance(node,list):return any(mentions(x) for x in node)
        return isinstance(node,str) and any(sx.unquote(node)==name or sx.unquote(node).startswith(name+'-') for name in aliases)
    if mentions(sx.parse(filtered.decode())):raise p.Rejected('padless alias occurs outside removable SES placement')
    record.update(alias_policy=binding['policy'],alias_source_sha256=binding['source_sha256'],
        alias_count=len(aliases),engine_input_name=engine_input_name,expected_base_design=Path(engine_input_name).stem,dsn_sha256=hashlib.sha256(dsn).hexdigest(),alias_outside_placement=False)
    return filtered,record


def bridge(candidate,context):
    """One deterministic physical different-net pad-center bridge, never relabeling.

    Exact Native pad centers/layers select the fault. A fresh original-rule
    Native rejection is required separately; this is not a geometric proof.
    """
    rows=context.get('pads');nets=context.get('nets')
    if not isinstance(rows,list) or not 2<=len(rows)<=128 or not isinstance(nets,list):raise p.Rejected('bounded Native pads/nets required')
    records={row['name']:row for row in nets}
    if len(records)!=len(nets):raise p.Rejected('ambiguous Native net map')
    seen=set();pads=[]
    for row in rows:
        uid=row.get('uuid');uuid.UUID(uid)
        if uid in seen:raise p.Rejected('duplicate Native pad identity')
        seen.add(uid);xy=row.get('position_nm');layers=row.get('copper_layers')
        if (not isinstance(xy,list) or len(xy)!=2 or any(type(x)is not int or abs(x)>10**12 for x in xy)
                or not isinstance(layers,list) or len(layers)!=len(set(layers)) or not set(layers)<={'F.Cu','B.Cu'}):raise p.Rejected('unqualified Native pad geometry')
        if row.get('net') in records and layers:pads.append(row)
    pads.sort(key=lambda row:row['uuid'])
    for i,a in enumerate(pads):
        for b in pads[i+1:]:
            common=sorted(set(a['copper_layers'])&set(b['copper_layers']))
            if a['net']==b['net'] or a['position_nm']==b['position_nm'] or not common:continue
            row=records[a['net']];width=row.get('width_nm')
            if type(width)is not int or width<=0:raise p.Rejected('positive exact native width required')
            names={sx.unquote(n[2]):n[1] for n in sx.children(candidate,'net')}
            net=names.get(a['net'],json.dumps(a['net']))
            def mm(v):
                sign='-' if v<0 else '';q,r=divmod(abs(v),1000000)
                return sign+str(q)+'.'+str(r).zfill(6)
            token=hashlib.sha256((sx.dump(candidate)+a['uuid']+b['uuid']+common[0]).encode()).hexdigest()
            identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'roller-physical-bridge:'+token))
            if any(sx.one(r,'uuid')==['uuid',json.dumps(identity)] for r in p.routes(candidate)):raise p.Rejected('fault UUID collision')
            new=['segment',['start',*map(mm,a['position_nm'])],['end',*map(mm,b['position_nm'])],
                ['width',mm(width)],['layer',json.dumps(common[0])],['net',net],['uuid',json.dumps(identity)]]
            result=copy.deepcopy(candidate);result.append(new)
            return result,dict(kind='physical_different_net_pad_bridge',uuid=identity,pad_uuids=[a['uuid'],b['uuid']],
                net_names=[a['net'],b['net']],layer=common[0],endpoints_nm=[a['position_nm'],b['position_nm']],routing_accepted=False)
    raise p.Rejected('no exact different-net Native pad pair for physical fault')
