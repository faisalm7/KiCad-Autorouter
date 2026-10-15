"""Source-bound export-only aliases for duplicate padless board artwork.

Promotes the project-owned, Native-qualified diagnostic plan/restoration/DSN
checks. Fixed-placement import, original-design and Native DRC remain separate.
No runtime dependence on experiment code, external services or AI.
"""
import copy,hashlib,json,uuid
from collections import Counter
from pathlib import Path
from . import sexpr as sx
from .adapter import _parse_dsn,_check_units
POLICY='source-bound-padless-export-v1'
MAX_PROOF=16*1024**2

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
    tree=sx.parse(source.decode())
    if tree[0]!='kicad_pcb':raise ValueError('native board root required')
    rows=[];fps={}
    for fp in sx.children(tree,'footprint'):
        uid=atom(fp,'uuid');uuid.UUID(uid);ref=sx.unquote(reference(fp)[2])
        if uid in fps:raise ValueError('unique footprint UUIDs required')
        fps[uid]=fp;rows.append({'uuid':uid,'reference':ref,'pad_count':len(sx.children(fp,'pad'))})
    if len(rows)>10000:raise ValueError('bounded footprint census required')
    counts=Counter(row['reference'] for row in rows);aliases=[];original_refs=set(counts)
    duplicate=any(n>1 for n in counts.values())
    if duplicate:
        surfaces(tree)
        copper=[(sx.unquote(n[1]),n[2]) for n in sx.one(tree,'layers',[])[1:] if isinstance(n,list) and len(n)>2 and sx.unquote(n[1]).endswith('.Cu')]
        if (sx.one(tree,'version') not in (['version','20241229'],['version','20260206']) or sx.children(tree,'module')
                or not 1<=len(rows)<=512 or copper not in ([('F.Cu','signal'),('B.Cu','signal')],[('F.Cu','signal'),('B.Cu','jumper')])):
            raise ValueError('duplicate aliases require qualified modern two-layer scope')
    for row in sorted(rows,key=lambda x:x['uuid']):
        if counts[row['reference']]<2:continue
        if not row['reference']:raise ValueError('empty duplicate reference unqualified')
        fp=fps[row['uuid']];ref=reference(fp);layer=sx.one(ref,'layer');attributes=sx.one(fp,'attr',[])
        if row['pad_count'] or 'board_only' not in attributes:raise ValueError('every duplicate group member must be padless board-only')
        if layer is None or len(layer)!=2 or sx.unquote(layer[1]) not in ('F.Fab','B.Fab','F.SilkS','B.SilkS'):raise ValueError('copper/unknown Reference layer cannot be aliased')
        if sx.children(fp,'model'):raise ValueError('aliased footprint model dependence unqualified')
        name='KAR_PD_'+namespace+'_'+row['uuid'].replace('-','')
        if name in original_refs:raise ValueError('alias collides with original reference')
        aliases.append({**row,'alias':name,'fpid':sx.unquote(fp[1]),'footprint_ast_sha256':sha((sx.dump(fp)+'\n').encode())})
    if len({row['alias'] for row in aliases})!=len(aliases):raise ValueError('bounded bijective duplicate alias population required')
    return {'schema':1,'policy':POLICY,'namespace':namespace,'source_sha256':sha(source),'footprints':sorted(rows,key=lambda r:r['uuid']),'aliases':aliases,'routing_accepted':False}
def require_plan(source,binding):
    if binding!=plan(source,binding.get('namespace')):raise ValueError('stale or altered alias/source contract')

def native_footprint_census(board):
    fps=list(board.GetFootprints());by={str(fp.m_Uuid.AsString()):fp for fp in fps}
    pads=Counter(str(p.GetParentFootprint().m_Uuid.AsString()) for p in board.GetPads())
    actual=sorted([{'uuid':key,'reference':str(fp.GetReference()),'pad_count':pads.get(key,0)} for key,fp in by.items()],key=lambda r:r['uuid'])
    if len(by)!=len(fps) or set(pads)-set(by):raise ValueError('unique Native footprints and bound pad parents required')
    return by,actual

def native_export(board,source,binding,exporter,observer):
    """Explicit temporary native mutation; restore BEFORE any board emission.

    Callbacks are ROOT-owned pinned native export/full-observation functions.
    Export callback must additionally compare copper geometry while aliases
    are active; before/after restoration alone is not that proof.
    This helper never loads/saves a board, writes a source, or imports a session.
    """
    require_plan(source,binding);by,actual=native_footprint_census(board)
    if actual!=binding['footprints']:raise ValueError('native/source footprint census differs')
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


def artifact_paths(output):
    output=Path(output)
    return {name:output.with_suffix(suffix) for name,suffix in (
        ('source_copy','.alias-source.kicad_pcb'),('proof','.alias-export.json'),
        ('before','.alias-before.kicad_pcb'),('after','.alias-after.kicad_pcb'))}


def export_board(board,source,output,pcbnew,*,mapping,before):
    """Export on the loaded board; retain the exact input before later routing.

    Zero aliases are an explicit rederivable census. An unsafe plan never falls
    back to the ordinary exporter. All temporary changes are restored in the
    separately qualified Native helper, before any Native board emission.
    """
    from .placement_clearance import read_bytes
    source=Path(source).absolute();output=Path(output).absolute()
    raw=read_bytes(source);project=read_bytes(source.with_suffix('.kicad_pro'))
    if before!=(sha(raw),sha(project)):raise ValueError('loaded export input changed')
    binding=plan(raw);paths=artifact_paths(output)
    _,native_footprints=native_footprint_census(board)
    if native_footprints!=binding['footprints']:raise ValueError('loaded Native/source footprint census differs')
    if (source.parent==output.parent or any(p.exists() or p.is_symlink() for p in (output,*paths.values()))):
        raise ValueError('fresh export artifacts outside input project required')
    with paths['source_copy'].open('xb') as stream:stream.write(raw)
    observation=None
    if binding['aliases']:
        if pcbnew.GetBuildVersion()!='10.0.0':raise ValueError('alias geometry requires qualified Native10.0.0')
        from .padless_alias_native import emit
        observation=emit(board,raw,binding,output,pcbnew)
    elif pcbnew.ExportSpecctraDSN(board,str(output)) is not True:
        raise ValueError('native DSN export failed')
    dsn=read_bytes(output,20*1024**2)
    if not dsn:raise ValueError('empty native DSN export')
    # This also checks all ordinary/aliased placements and electrical pin
    # identities on the explicit zero-alias branch.
    dsn_aliases(dsn,raw,binding)
    if read_bytes(source)!=raw or read_bytes(source.with_suffix('.kicad_pro'))!=project:
        raise ValueError('export changed original input files')
    if native_footprint_census(board)[1]!=native_footprints:raise ValueError('export changed Native footprint census')
    record=dict(schema=1,policy=POLICY,native_version=pcbnew.GetBuildVersion(),
        source=str(source),source_sha256=sha(raw),project_sha256=sha(project),
        output=str(output),dsn_sha256=sha(dsn),source_copy=paths['source_copy'].name,
        binding=binding,native_footprints=native_footprints,zero_alias=not binding['aliases'],native_classmap=mapping,
        observation=observation,board_saved=False,routing_accepted=False)
    # Polygon vertices repeat across four required observations. Compact JSON
    # preserves every value while avoiding indentation-driven output rejection.
    encoded=canonical(record)+b'\n'
    if len(encoded)>MAX_PROOF:raise ValueError('Native alias proof exceeds bounded output')
    with paths['proof'].open('xb') as stream:stream.write(encoded)
    return record


def check_exports(root,data,retained):
    from . import pipeline as p
    try:return _check_exports(root,data,retained)
    except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError) as exc:
        raise p.Rejected('invalid Native alias export evidence: '+str(exc)) from exc


def _check_exports(root,data,retained):
    """Re-derive every current export, including explicit zero-alias exports.

    Native input is captured separately: the candidate is subsequently replaced
    by routed/refilled bytes. Raw DSN is either the still-original output or the
    normal pipeline's native.dsn copy. Neither receipt flags nor the presence of
    a sidecar alone decides whether this check is required.
    """
    import re
    from . import pipeline as p
    from .floor_route import read_json,canonical as encode,SANDBOX
    from .local_settings import canonical as path,policy_declaration
    from .placement_clearance import read_bytes
    root=path(Path(root));pins=data.get('tools',{}).get('implementation_sha256',{})
    pipeline=read_bytes(root/'code/pipeline.py',1024**2)
    if sha(pipeline)!=pins.get('autorouter/pipeline.py'):raise p.Rejected('alias pipeline provenance differs')
    declaration=policy_declaration(pipeline,name='NORMAL_NATIVE_EXPORT_ALIAS_POLICY',expected=POLICY)
    marker=data.get('tools',{}).get('normal_native_export_alias_policy')
    producer=root/'code/native.py'
    native_policy=None
    if producer.exists():
        native_raw=read_bytes(producer,1024**2)
        if sha(native_raw)!=pins.get('autorouter/native.py'):raise p.Rejected('alias Native producer provenance differs')
        native_policy=policy_declaration(native_raw,name='EXPORT_ALIAS_POLICY',expected=POLICY)
    suffixes=('.alias-export.json','.alias-source.kicad_pcb','.alias-before.kicad_pcb','.alias-after.kicad_pcb')
    def project_copy(name):
        return any(part in {'snapshot','candidate','original','refill'} or part.endswith('-input')
                   for part in Path(name).parts[:-1])
    artifacts={name for name in retained if name.endswith(suffixes) and not project_copy(name)}
    if declaration is None and native_policy is None:
        if marker is not None or artifacts:raise p.Rejected('alias policy source declaration missing')
        return []  # Genuine older producer, checked by its existing contracts.
    if declaration!=POLICY or native_policy!=POLICY or marker!=POLICY:
        raise p.Rejected('alias export producer and tool policies differ')
    def command(argv,action):
        if type(argv) is not list:return None
        args=argv[len(SANDBOX):] if argv[:len(SANDBOX)]==SANDBOX else argv
        if len(args)<3 or type(args[1]) is not str or Path(args[1]).name!='native.py' or args[2]!=action:return None
        if (len(args) not in ((5,6) if action=='export' else (6,))
                or any(type(a) is not str for a in args)
                or args[:2]!=[str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py')]):
            raise p.Rejected('unqualified alias Native command')
        return args
    census={name[:-len('-process.json')] for name in retained if name.endswith('-process.json')
            and command(read_json(root/name).get('argv'),'export') is not None}
    exports=[(s,command(s.get('argv'),'export')) for s in data.get('steps',[])
             if command(s.get('argv'),'export') is not None]
    # Normal fixed-placement import always consumes the export from the same
    # candidate/cwd. This closes deletion of ALL export rows and sidecars.
    if type(data.get('schema')) is int and data['schema']==1 and data.get('input_policy','native')=='native':
        for step in data.get('steps',[]):
            args=command(step.get('argv'),'import')
            if args is None:continue
            cwd=path(Path(step['cwd']))
            if args[4:]==[str(cwd/'imported.kicad_pcb'),str(cwd/'routes.ses')]:
                matches=[a for s,a in exports if s.get('cwd')==str(cwd)
                         and a[3:5]==[args[3],str(cwd/'task.dsn')]]
                if len(matches)!=1:raise p.Rejected('normal import lost its exact Native export')
    if not exports and not census and not artifacts:return []  # DRC-only or floor-context workers.
    for name in ('padless_alias.py','padless_alias_native.py','floor_context.py','adapter.py','sexpr.py','placement_clearance.py'):
        if sha(read_bytes(root/'code'/name,1024**2))!=pins.get('autorouter/'+name):
            raise p.Rejected('alias helper provenance differs')
    declared=set();expected_artifacts=set();checked=[]
    for step,args in exports:
        cwd=path(Path(step['cwd']));name=step.get('name')
        if (cwd!=root and root not in cwd.parents) or type(name) is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,128}',name) is None:
            raise p.Rejected('alias export worker escaped evidence')
        identity=str((cwd/name).relative_to(root))
        if identity in declared:raise p.Rejected('duplicate alias export worker')
        declared.add(identity);process=read_json(cwd/(name+'-process.json'))
        annotations=set(step)-set(process)
        if (process.get('name')!=name or process.get('cwd')!=str(cwd) or process.get('argv')!=step.get('argv')
                or any(encode(step.get(k))!=encode(v) for k,v in process.items())
                or (annotations and (annotations!={'phase'} or step['phase']!='incumbent'))
                or process.get('status')!='success' or type(process.get('exit_code')) is not int
                or process['exit_code']!=0 or process.get('cleanup_complete') is not True):
            raise p.Rejected('alias export worker lineage differs')
        log=cwd/(name+'.log');log_bytes=read_bytes(log,1024**2)
        if (process.get('log')!=str(log) or type(process.get('log_bytes')) is not int
                or process['log_bytes']!=len(log_bytes) or process.get('log_truncated') is not False):
            raise p.Rejected('alias export worker log differs')
        source,output=(path(Path(n)) for n in args[3:5])
        if (any(root not in n.parents for n in (source,output)) or output.parent!=cwd
                or source.parent==cwd or source.parent in cwd.parents):
            raise p.Rejected('alias export paths escaped owned evidence')
        paths=artifact_paths(output);read_bytes(paths['proof'],MAX_PROOF);proof=read_json(paths['proof'])
        raw=read_bytes(paths['source_copy']);binding=plan(raw)
        pro=source.with_suffix('.kicad_pro');project=read_bytes(pro)
        raw_candidates=[read_bytes(n,20*1024**2) for n in {output,cwd/'native.dsn'} if n.is_file()]
        matching=[v for v in raw_candidates if sha(v)==proof.get('dsn_sha256')]
        if not matching:raise p.Rejected('exact raw Native alias DSN missing')
        dsn=matching[0];dsn_aliases(dsn,raw,binding)
        mapping=None
        if len(args)==6:
            mapping_path=path(Path(args[5]))
            if mapping_path.parent!=cwd:raise p.Rejected('alias Native classmap escaped worker')
            mapping=read_json(mapping_path)
            if (mapping.get('source')!=str(source) or mapping.get('board_sha256')!=sha(raw)
                    or mapping.get('project_sha256')!=sha(project) or mapping.get('board_saved') is not False):
                raise p.Rejected('alias classmap source differs')
        expected=dict(schema=1,policy=POLICY,native_version='10.0.0',source=str(source),
            source_sha256=sha(raw),project_sha256=sha(project),output=str(output),dsn_sha256=sha(dsn),
            source_copy=paths['source_copy'].name,binding=binding,native_footprints=binding['footprints'],zero_alias=not binding['aliases'],
            native_classmap=mapping,observation=proof.get('observation'),board_saved=False,routing_accepted=False)
        if encode(proof)!=encode(expected):raise p.Rejected('alias export proof differs from source and Native worker')
        expected_artifacts.update(str(paths[k].relative_to(root)) for k in ('source_copy','proof'))
        # Bind ordinary normal tasks to the frozen original, also for nested C
        # incumbents. A standalone diagnostic has no normal routing receipt.
        owner=data if cwd==root else read_json(cwd/'result.json')
        if type(owner.get('schema')) is int and owner['schema']==1 and owner.get('input_policy','native')=='native':
            if (source!=cwd/'candidate'/Path(owner['source']).name or owner.get('source_hashes')!=data.get('source_hashes')
                    or owner.get('task_sha256')!=sha(raw)):
                raise p.Rejected('alias input differs from original normal task')
            original=read_bytes(cwd/'snapshot'/Path(owner['source']).name)
            if sha(original)!=owner['source_hashes'].get(Path(owner['source']).name):raise p.Rejected('alias original snapshot differs')
            task=p.routing_task(sx.parse(original.decode()),owner.get('scope'),p.selected_scope_names(owner))
            if (sx.dump(task)+'\n').encode()!=raw:raise p.Rejected('alias export task reconstruction differs')
            if sha(project)!=owner['source_hashes'].get(pro.name):raise p.Rejected('alias original project rules differ')
        observation=proof['observation']
        if binding['aliases']:
            _check_observation(observation,paths,raw,dsn,binding)
            expected_artifacts.update(str(paths[k].relative_to(root)) for k in ('before','after'))
            _check_sessions(cwd,data,command,binding,source,output)
        elif observation is not None:raise p.Rejected('zero-alias export contains mutation observations')
        checked.append({'cwd':str(cwd),'name':name,'source':str(source),'output':str(output),'alias_count':len(binding['aliases'])})
    if census!=declared:raise p.Rejected('retained Native alias export population differs from steps')
    if artifacts!=expected_artifacts:raise p.Rejected('orphan or missing Native alias export artifacts')
    return checked


def _check_observation(observation,paths,raw,dsn,binding):
    from . import pipeline as p
    from .floor_route import canonical as encode
    from .placement_clearance import read_bytes
    from .padless_alias_native import without_authorized_reference_display as normalize
    if type(observation) is not dict:raise p.Rejected('Native alias observations missing')
    events=observation.get('events')
    if (type(events) is not list or len(events)!=4
            or [e.get('phase') for e in events]!=['before_alias','during_alias','after_export','restored']
            or any(set(e)!=({'phase','result','observation'} if i==3 else {'phase','observation'}) for i,e in enumerate(events))):
        raise p.Rejected('Native alias observation phases differ')
    before,during,after,restored=[e['observation'] for e in events]
    for index,value in enumerate((before,during,after,restored)):
        _observation_census(value,raw,binding,during=index in (1,2))
    if (encode(before)!=encode(restored) or encode(during)!=encode(after)
            or encode(normalize(before,binding))!=encode(normalize(during,binding,True))
            or encode(events[-1]['result'])!=encode(dict(exported=True,restored=True,alias_count=len(binding['aliases']),routing_accepted=False))):
        raise p.Rejected('Native alias geometry or restoration differs')
    before_raw=read_bytes(paths['before']);after_raw=read_bytes(paths['after'])
    if sx.parse(before_raw.decode())!=sx.parse(after_raw.decode()):raise p.Rejected('Native alias restored emission differs')
    expected=dict(schema=1,source_sha256=sha(raw),dsn_sha256=sha(dsn),events=events,
        before_board=paths['before'].name,after_board=paths['after'].name,
        before_board_sha256=sha(before_raw),after_board_sha256=sha(after_raw),accepted=False,production_support=False)
    if encode(observation)!=encode(expected):raise p.Rejected('Native alias emission hashes differ')


def _observation_census(value,raw,binding,*,during):
    """A matching pair of truncated observations is never a geometry proof."""
    from . import pipeline as p
    expected_keys={'layers_text','areas','footprints','pads','routes','zones','drawings','shape_semantics'}
    if type(value) is not dict or set(value)!=expected_keys:raise p.Rejected('Native alias observation schema differs')
    for key in ('footprints','pads','routes','zones','drawings'):
        if type(value[key]) is not list or len(value[key])>10000 or any(type(row) is not dict for row in value[key]):
            raise p.Rejected('Native alias observation bounded population missing')
    source=sx.parse(raw.decode());aliases={r['uuid']:r for r in binding['aliases']}
    expected_fps={r['uuid']:{'reference':aliases[r['uuid']]['alias'] if during and r['uuid'] in aliases else r['reference'],
                            'pad_count':r['pad_count']} for r in binding['footprints']}
    fps=value['footprints'];observed_fps={r['uuid']:r for r in fps}
    if len(observed_fps)!=len(fps) or set(observed_fps)!=set(expected_fps):raise p.Rejected('Native alias footprint census differs')
    fp_keys={'uuid','reference','value','fpid','position_nm','angle','layer','locked','model_count','fields','graphics'}
    for uid,expected in expected_fps.items():
        row=observed_fps[uid]
        if (set(row)!=fp_keys or row['reference']!=expected['reference']
                or type(row['fields']) is not list or not row['fields'] or type(row['graphics']) is not list):
            raise p.Rejected('Native alias footprint observation incomplete')
    def identities(nodes):return {atom(n,'uuid') for n in nodes}
    def census(key,nodes):
        rows=value[key];actual={r['uuid'] for r in rows};wanted=identities(nodes)
        if len(actual)!=len(rows) or actual!=wanted:raise p.Rejected('Native alias '+key+' census differs')
    pads=[pad for fp in sx.children(source,'footprint') for pad in sx.children(fp,'pad')]
    census('pads',pads);census('routes',p.routes(source));census('zones',sx.children(source,'zone'))
    drawings=[n for n in source if isinstance(n,list) and n and (str(n[0]).startswith('gr_') or n[0] in ('dimension','target'))]
    census('drawings',drawings)
    text=value['layers_text'];areas=value['areas']
    if (type(text) is not dict or set(text)!={'layers','copper_text','shape_semantics'}
            or type(text['layers']) is not list or len(text['layers'])!=2 or type(text['copper_text']) is not list):
        raise p.Rejected('Native alias copper text/layers observation incomplete')
    copper=[{'name':sx.unquote(n[1]),'canonical':sx.unquote(n[1]),'type':n[2]}
            for n in sx.one(source,'layers',[])[1:] if isinstance(n,list) and len(n)>2 and sx.unquote(n[1]) in ('F.Cu','B.Cu')]
    if text['layers']!=copper:raise p.Rejected('Native alias source copper layers differ')
    texts=[n for n in sx.children(source,'gr_text') if sx.unquote(sx.one(n,'layer')[1]) in ('F.Cu','B.Cu')]
    if {r['uuid'] for r in text['copper_text']}!=identities(texts) or len(text['copper_text'])!=len(texts):
        raise p.Rejected('Native alias copper text census differs')
    text_keys={'uuid','text','layer','knockout','position_nm','bbox_nm','shape_outlines'}
    for row in text['copper_text']:
        if set(row)!=text_keys or type(row['shape_outlines']) is not list or not row['shape_outlines']:raise p.Rejected('Native alias copper glyph geometry incomplete')
        _vector(row['position_nm']);_vector(row['bbox_nm'],4)
        for outline in row['shape_outlines']:
            if (type(outline) is not dict or set(outline)!={'points_nm','holes'} or type(outline['points_nm']) is not list
                    or not 3<=len(outline['points_nm'])<=10000 or type(outline['holes']) is not int or outline['holes']<0):raise p.Rejected('Native alias copper glyph outline incomplete')
            for point in outline['points_nm']:_vector(point)
    if (type(areas) is not dict or set(areas)!={'zones','footprint_zone_count','footprint_rulearea_count'}
            or type(areas['zones']) is not list or type(areas['footprint_zone_count']) is not int or areas['footprint_zone_count']!=0
            or type(areas['footprint_rulearea_count']) is not int or areas['footprint_rulearea_count']!=0
            or {r['uuid'] for r in areas['zones']}!=identities(sx.children(source,'zone'))
            or len(areas['zones'])!=len(sx.children(source,'zone'))):
        raise p.Rejected('Native alias area census differs')
    area_keys={'uuid','name','parent','is_rule_area','placement_enabled','placement_source_type','placement_source','disallow','layers','outlines_nm','outline_closed','holes','arc_count'}
    for row in areas['zones']:
        if (set(row)!=area_keys or type(row['disallow']) is not dict
                or set(row['disallow'])!={'tracks','vias','pads','copperpour','footprints'}
                or any(type(flag) is not bool for flag in row['disallow'].values())
                or type(row['outlines_nm']) is not list or not row['outlines_nm'] or type(row['outline_closed']) is not list or type(row['holes']) is not list
                or not len(row['outlines_nm'])==len(row['outline_closed'])==len(row['holes'])):
            raise p.Rejected('Native alias area geometry incomplete')
        for points in row['outlines_nm']:
            if type(points) is not list or not 3<=len(points)<=10000:raise p.Rejected('Native alias area outline incomplete')
            for point in points:_vector(point)
    pad_counts=Counter(row['parent_uuid'] for row in value['pads'])
    if set(pad_counts)-set(expected_fps) or any(pad_counts.get(uid,0)!=r['pad_count'] for uid,r in expected_fps.items()):
        raise p.Rejected('Native alias parent/pad census differs')
    # Also require every field/footprint graphic from the source. Native adds
    # standard fields, so their names may be a superset, but cannot omit one.
    graphic_keys={'uuid','kind','position_nm','layer','locked','bbox_nm','copper_polygons'}
    pad_keys={'uuid','parent_uuid','reference','number','net','netcode','position_nm','angle','drill_nm','drill_shape','copper_shapes'}
    route_keys={'uuid','net','netcode','locked','width_nm','kind'}
    pad_sources={atom(n,'uuid'):n for n in pads};zone_sources={atom(n,'uuid'):n for n in sx.children(source,'zone')}
    for row in value['pads']:
        if set(row)!=pad_keys:raise p.Rejected('Native alias pad geometry incomplete')
        source_pad=pad_sources[row['uuid']]
        _shape_map(row['copper_shapes'],required=_copper_layers(source_pad));_vector(row['position_nm']);_vector(row['drill_nm'])
    for row in value['routes']:
        extra={'position_nm','drill_nm','via_type'} if row.get('kind')=='via' else {'start_nm','end_nm','layer'}
        if row.get('kind') not in ('via','segment') or set(row)!=route_keys|extra:raise p.Rejected('Native alias route geometry incomplete')
        for key in ('position_nm','start_nm','end_nm'):
            if key in row:_vector(row[key])
    for row in value['zones']:
        if set(row)!={'uuid','net','outline','fills'}:raise p.Rejected('Native alias zone geometry incomplete')
        source_zone=zone_sources[row['uuid']]
        if not row['outline']:raise p.Rejected('Native alias zone outline absent')
        _polygon_rows(row['outline'])
        filled={sx.unquote(sx.one(n,'layer')[1]) for n in sx.children(source_zone,'filled_polygon')}
        # KiCad retains allocated, empty per-layer containers even when the
        # source has no filled_polygon. Keep those keys; absence of derived
        # fill is legitimate and distinct from erasing the zone outline.
        _shape_map(row['fills'],required=_copper_layers(source_zone),allow_empty=True)
        if any(not row['fills'].get(layer) for layer in filled):raise p.Rejected('Native alias source zone fill absent')
    def graphic(row,source_node):
        text_keys={'text','shown','angle','size_nm','thickness_nm','visible','knockout'} if row.get('kind') in ('PCB_TEXT','PCB_FIELD') or str(row.get('kind','')).startswith('PCB_DIM_') else set()
        if set(row)!=graphic_keys|text_keys:raise p.Rejected('Native alias graphic geometry incomplete')
        _vector(row['position_nm']);_vector(row['bbox_nm'],4);_shape_map(row['copper_polygons'],required=_copper_layers(source_node))
        if text_keys:_vector(row['size_nm'])
    drawing_sources={atom(n,'uuid'):n for n in drawings}
    for row in value['drawings']:graphic(row,drawing_sources[row['uuid']])
    for fp in sx.children(source,'footprint'):
        row=observed_fps[atom(fp,'uuid')]
        fields=row['fields'];names={f['name'] for f in fields}
        # Plain properties such as ki_fp_filters are source metadata, not
        # PCB_FIELD objects. Their bytes remain in the captured source and
        # original-design checks; only display properties enter this census.
        wanted={sx.unquote(n[1]) for n in sx.children(fp,'property') if len(n)>2
                and any(sx.children(n,key) for key in ('layer','effects','at'))}
        if len(names)!=len(fields) or not wanted<=names or any(not graphic_keys<=set(f) for f in fields):
            raise p.Rejected('Native alias field census differs')
        field_sources={sx.unquote(n[1]):n for n in sx.children(fp,'property') if len(n)>2}
        for field in fields:graphic({k:v for k,v in field.items() if k!='name'},field_sources.get(field['name'],[]))
        graphics=row['graphics'];wanted_graphics=identities([n for n in fp if isinstance(n,list) and n and str(n[0]).startswith('fp_')])
        if {g['uuid'] for g in graphics}!=wanted_graphics or len({g['uuid'] for g in graphics})!=len(graphics):
            raise p.Rejected('Native alias footprint graphic census differs')
        graphic_sources={atom(n,'uuid'):n for n in fp if isinstance(n,list) and n and str(n[0]).startswith('fp_')}
        for g in graphics:graphic(g,graphic_sources[g['uuid']])


def _vector(value,size=2):
    if type(value) is not list or len(value)!=size or any(type(n) is not int for n in value):
        raise ValueError('complete integer-nanometre vector required')


def _polygon_rows(value):
    if type(value) is not list or len(value)>512:raise ValueError('bounded Native polygon rows required')
    for row in value:
        if type(row) is not dict or set(row)!={'outer','holes'} or type(row['holes']) is not list:
            raise ValueError('complete Native polygon geometry required')
        for points in [row['outer'],*row['holes']]:
            if type(points) is not list or not 3<=len(points)<=100000:raise ValueError('bounded nonempty Native polygon points required')
            for point in points:_vector(point)


def _shape_map(value,*,required=None,allow_empty=False):
    if type(value) is not dict or set(value)-{'F.Cu','B.Cu'}:raise ValueError('complete Native copper shape map required')
    if required is not None and set(value)!=required:raise ValueError('Native copper shape source layers differ')
    if not allow_empty and any(not rows for rows in value.values()):raise ValueError('nonempty Native copper geometry required')
    for polygons in value.values():_polygon_rows(polygons)


def _copper_layers(node):
    layers=sx.one(node,'layers') or sx.one(node,'layer') or ['layers']
    names={sx.unquote(n) for n in layers[1:]}
    return {'F.Cu','B.Cu'} if names&{'*.Cu','F&B.Cu'} else names&{'F.Cu','B.Cu'}


def _check_sessions(cwd,data,command,binding,source,output):
    from . import pipeline as p
    from .adapter import fixed_placement_session
    from .floor_route import SANDBOX
    from .placement_clearance import read_bytes
    aliases={a['alias'] for a in binding['aliases']}
    def scan(node):
        return any(scan(x) for x in node) if isinstance(node,list) else isinstance(node,str) and any(a in sx.unquote(node) for a in aliases)
    imports=[a for s in data.get('steps',[]) if s.get('cwd')==str(cwd)
             and (a:=command(s.get('argv'),'import')) is not None and a[3]==str(source)]
    for args in imports:
        session=Path(args[5]);filtered,_=fixed_placement_session(read_bytes(session))
        tree=sx.parse(filtered.decode())
        if scan(tree):raise p.Rejected('padless alias leaked into imported SES routing')
        engines=[]
        for step in data.get('steps',[]):
            if step.get('cwd')!=str(cwd):continue
            argv=step.get('argv',[]);argv=argv[len(SANDBOX):] if argv[:len(SANDBOX)]==SANDBOX else argv
            if type(argv) is not list or any(type(a) is not str for a in argv):raise p.Rejected('invalid alias engine arguments')
            if '-de' in argv and '-do' in argv:
                if argv.count('-de')!=1 or argv.count('-do')!=1 or max(argv.index('-de'),argv.index('-do'))>=len(argv)-1:
                    raise p.Rejected('ambiguous alias engine paths')
                if argv[argv.index('-do')+1]==str(session):engines.append(argv)
        base=sx.one(tree,'base_design')
        if (len(engines)!=1 or engines[0][engines[0].index('-de')+1]!=str(output)
                or base is None or len(base)!=2 or sx.unquote(base[1])!=output.stem):
            raise p.Rejected('alias SES base differs from actual engine DSN input')
