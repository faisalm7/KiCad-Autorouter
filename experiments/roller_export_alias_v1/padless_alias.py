"""Pure export-only aliases and strict padless SES placement removal.

No source/candidate writes, native imports or routing. In-memory aliases require
separately qualified native geometry/source/DSN/SES/DRC controls before use.
"""
import copy,hashlib,json,uuid
from collections import Counter
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn,_dump_dsn,_check_units
from experiments.pic_mixed_transport_probe_v1 import ses_checks as ses
from experiments.roller_support_v1.checks import inactive_default
POLICY='duplicate-padless-export-alias-v1'
MAX=4*1024**2

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def atom(node,key):
    value=sx.one(node,key)
    if value is None or len(value)!=2 or not isinstance(value[1],str):raise ValueError('unambiguous '+key+' required')
    return sx.unquote(value[1])
def reference(fp):
    refs=[n for n in sx.children(fp,'property') if len(n)>2 and sx.unquote(n[1])=='Reference']
    if len(refs)!=1:raise ValueError('one modern Reference property required')
    return refs[0]
def surfaces(node):
    if not isinstance(node,list) or not node:return
    if node[0] in ('gr_text','fp_text','gr_text_box','fp_text_box','dimension') or node[0]=='property' and sx.one(node,'layer') is not None:
        if any(isinstance(x,str) and any(marker in x for marker in ('${','%R','%V')) for x in node[1:]):raise ValueError('variable-dependent surface text outside alias scope')
    for x in node[1:]:surfaces(x)
def plan(source,namespace='A'):
    if type(source) is not bytes or not source or len(source)>sx.MAX_BYTES or namespace not in ('A','B'):raise ValueError('bounded captured source and fixed alias namespace required')
    tree=sx.parse(source.decode());surfaces(tree)
    if tree[0]!='kicad_pcb' or sx.one(tree,'version') not in (['version','20241229'],['version','20260206']) or sx.children(tree,'module'):raise ValueError('qualified modern footprint schema required')
    rows=[];fps={}
    for fp in sx.children(tree,'footprint'):
        uid=atom(fp,'uuid');uuid.UUID(uid);ref=sx.unquote(reference(fp)[2])
        if not ref or uid in fps:raise ValueError('nonempty references/unique UUIDs required')
        fps[uid]=fp;rows.append({'uuid':uid,'reference':ref,'pad_count':len(sx.children(fp,'pad'))})
    if not 1<=len(rows)<=512:raise ValueError('bounded footprint census required')
    counts=Counter(row['reference'] for row in rows);aliases=[];original_refs=set(counts)
    for row in sorted(rows,key=lambda x:x['uuid']):
        if counts[row['reference']]<2:continue
        fp=fps[row['uuid']];ref=reference(fp);layer=sx.one(ref,'layer');attributes=sx.one(fp,'attr',[])
        if row['pad_count'] or 'board_only' not in attributes:raise ValueError('every duplicate group member must be padless board-only')
        if layer is None or len(layer)!=2 or sx.unquote(layer[1]) not in ('F.Fab','B.Fab','F.SilkS','B.SilkS'):raise ValueError('copper/unknown Reference layer cannot be aliased')
        if sx.children(fp,'model'):raise ValueError('aliased footprint model dependence unqualified')
        name='KAR_PD_'+namespace+'_'+row['uuid'].replace('-','')
        if name in original_refs:raise ValueError('alias collides with original reference')
        aliases.append({**row,'alias':name,'fpid':sx.unquote(fp[1]),'footprint_ast_sha256':sha((sx.dump(fp)+'\n').encode())})
    if not aliases or len({row['alias'] for row in aliases})!=len(aliases):raise ValueError('bounded bijective duplicate alias population required')
    return {'schema':1,'policy':POLICY,'namespace':namespace,'source_sha256':sha(source),'footprints':sorted(rows,key=lambda r:r['uuid']),'aliases':aliases,'routing_accepted':False}
def require_plan(source,binding):
    if binding!=plan(source,binding.get('namespace')):raise ValueError('stale or altered alias/source contract')

def native_export(board,source,binding,exporter,observer):
    """Explicit temporary native mutation; restore BEFORE any board emission.

    Callbacks are ROOT-owned pinned native export/full-observation functions.
    Export callback must additionally compare copper geometry while aliases
    are active; before/after restoration alone is not that proof.
    This helper never loads/saves a board, writes a source, or imports a session.
    """
    require_plan(source,binding);fps=list(board.GetFootprints());by={str(fp.m_Uuid.AsString()):fp for fp in fps}
    pads=Counter(str(p.GetParentFootprint().m_Uuid.AsString()) for p in board.GetPads())
    actual=sorted([{'uuid':key,'reference':str(fp.GetReference()),'pad_count':pads.get(key,0)} for key,fp in by.items()],key=lambda r:r['uuid'])
    if len(by)!=len(fps) or set(pads)-set(by) or actual!=binding['footprints']:raise ValueError('native/source footprint census differs')
    before=copy.deepcopy(observer(board));changed=[];cause=None;result=None
    try:
        for row in binding['aliases']:
            fp=by[row['uuid']];changed.append((fp,row['reference']));fp.SetReference(row['alias'])
        result=exporter(board)
        if result is not True:raise ValueError('native alias export failed')
    except BaseException as exc:cause=exc
    finally:
        errors=[]
        for fp,ref in reversed(changed):
            try:fp.SetReference(ref)
            except BaseException as exc:errors.append(type(exc).__name__+': '+str(exc))
        try:
            if observer(board)!=before:errors.append('native board changed after alias restoration')
        except BaseException as exc:errors.append(type(exc).__name__+': '+str(exc))
        if errors:raise ValueError('alias restoration failed: '+'; '.join(errors)) from cause
    if cause is not None:raise cause
    return {'exported':True,'restored':True,'alias_count':len(changed),'routing_accepted':False}

def dsn_aliases(raw,source,binding):
    require_plan(source,binding)
    if type(raw) is not bytes or not raw or len(raw)>20*1024**2:raise ValueError('bounded DSN required')
    tree=_parse_dsn(raw.decode());_check_units(tree);placement=sx.one(tree,'placement');library=sx.one(tree,'library');network=sx.one(tree,'network')
    if any(x is None for x in (placement,library,network)):raise ValueError('complete DSN placement/library/network required')
    images={sx.unquote(n[1]):n for n in sx.children(library,'image')}
    if len(images)!=len(sx.children(library,'image')):raise ValueError('duplicate DSN image')
    aliases={row['alias']:row for row in binding['aliases']};wanted={r['reference'] for r in binding['footprints'] if r['uuid'] not in {a['uuid'] for a in aliases.values()}}|set(aliases)
    found={};slots=[]
    for comp in sx.children(placement,'component'):
        image=images.get(sx.unquote(comp[1]))
        if image is None:raise ValueError('missing DSN image')
        for place in sx.children(comp,'place'):
            name=sx.unquote(place[1])
            if name not in wanted or name in found:raise ValueError('unknown/duplicate DSN placed reference')
            found[name]=place
            if name in aliases:
                if sx.children(image,'pin'):raise ValueError('aliased DSN footprint has electrical pins')
                slots.append(place)
    if set(found)!=wanted:raise ValueError('incomplete DSN placement population')
    for net in sx.children(network,'net'):
        pins=sx.one(net,'pins')
        if pins is None:raise ValueError('missing DSN pin list')
        if any(sx.unquote(token).startswith(name+'-') for token in pins[1:] for name in aliases):raise ValueError('alias occurs in DSN terminal map')
    other=copy.deepcopy(tree)
    for comp in sx.children(sx.one(other,'placement'),'component'):
        for place in sx.children(comp,'place'):
            if sx.unquote(place[1]) in aliases:place[1]='REMOVED_ALIAS_SLOT'
    def scan(node):
        if isinstance(node,list):return any(scan(x) for x in node)
        return isinstance(node,str) and sx.unquote(node) in aliases
    if scan(other):raise ValueError('alias occurs outside DSN placement identity')
    return tree,slots

def normalize_dsn(raw,source,binding):
    tree,slots=dsn_aliases(raw,source,binding);by={r['alias']:r for r in binding['aliases']}
    for place in slots:place[1]=json.dumps('KAR_UUID_'+by[sx.unquote(place[1])]['uuid'])
    return _dump_dsn(tree).encode()

def strip_ses_placements(raw,dsn_raw,source,binding):
    dsn,_=dsn_aliases(dsn_raw,source,binding)
    if type(raw) is not bytes or not raw or len(raw)>MAX:raise ValueError('bounded SES required')
    tree=sx.parse(raw.decode());ses.children_only(tree,{'base_design','placement','was_is','routes'},2)
    if tree[0]!='session' or sx.one(tree,'was_is')!=['was_is']:raise ValueError('session/pin-swapping grammar unqualified')
    placement=sx.one(tree,'placement');routes=sx.one(tree,'routes');base=sx.one(tree,'base_design')
    if placement is None or routes is None or base is None or len(base)!=2 or sx.unquote(base[1])!=sx.unquote(dsn[1]):raise ValueError('bound SES design/placement/routes required')
    ses.children_only(placement,{'resolution','component'},1)
    res=sx.one(placement,'resolution')
    if res!=sx.one(routes,'resolution') or res!=sx.one(dsn,'resolution') or res is None or res[1]!='um' or len(res)!=3:raise ValueError('exact shared SES/DSN resolution required')
    scale=ses.number(res[2])
    if scale<=0 or scale>10000 or scale!=scale.to_integral_value():raise ValueError('bounded positive integer SES resolution required')
    if ses.placements(placement,scale)!=ses.placements(sx.one(dsn,'placement'),1,True):raise ValueError('complete fixed SES placement differs from DSN')
    aliases={row['alias'] for row in binding['aliases']};out=copy.deepcopy(tree);removed=[]
    placeout=sx.one(out,'placement')
    for comp in list(sx.children(placeout,'component')):
        for place in list(sx.children(comp,'place')):
            if sx.unquote(place[1]) in aliases:removed.append(copy.deepcopy(place));comp.remove(place)
        if not sx.children(comp,'place'):placeout.remove(comp)
    if len(removed)!=len(aliases):raise ValueError('missing SES alias placement')
    def mentions(node):
        if isinstance(node,list):return any(mentions(x) for x in node)
        return isinstance(node,str) and any(sx.unquote(node)==name or sx.unquote(node).startswith(name+'-') for name in aliases)
    if mentions(out):raise ValueError('alias occurs outside SES removable placement')
    return (sx.dump(out)+'\n').encode(),{'policy':POLICY,'removed_padless_placements':len(removed),'removed_sha256':sha(canonical(removed)),'source_sha256':binding['source_sha256'],'original_ses_sha256':sha(raw),'dsn_sha256':sha(dsn_raw),'routing_accepted':False}

def unused_class_proof(source,project,context,dsn_raw):
    if context.get('board_sha256')!=sha(source) or context.get('project_sha256')!=sha(project):raise ValueError('native class source/project binding differs')
    return inactive_default(json.loads(project),context,dsn_raw.decode())
