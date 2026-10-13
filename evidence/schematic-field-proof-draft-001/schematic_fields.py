"""Pure native effective-field proof; caller binds processes and current inputs.

Narrow exact Datasheet placeholder qualification; no report rewrite or acceptance.
"""
import hashlib,json,re
from pathlib import PurePosixPath
from autorouter import sexpr as sx
POLICY='datasheet-effective-empty-v1'
KIND='footprint_symbol_field_mismatch'
DESCRIPTION="Field 'Datasheet' differs (PCB: '~', Schematic: '')"
SKIP={'Reference','Value','Footprint','Component Class'}
SHA=re.compile(r'[0-9a-f]{64}')
UUID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')

def fail(message):raise ValueError(message)
def canonical(value):
    try:raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    except (TypeError,ValueError):fail('invalid proof JSON')
    if len(raw)>sx.MAX_BYTES:fail('proof JSON byte ceiling')
    return raw

def digest(raw):return hashlib.sha256(raw).hexdigest()
def text(value):
    if not isinstance(value,str):fail('field text must be a string')
    return value

def atom(value):
    text(value);i=0
    while i<len(value):
        if value[i]=='\\':
            if i+1==len(value) or value[i+1] not in '\\"':fail('unqualified native string escape')
            i+=2
        else:i+=1
    return sx.unquote(value)

def singleton(node,key):
    row=sx.one(node,key)
    if row is None or len(row)!=2:fail('missing or malformed '+key)
    return atom(row[1])

def compare(sch,pcb):
    if not isinstance(sch,dict) or not isinstance(pcb,dict):fail('complete field maps required')
    for fields in (sch,pcb):
        if any(not isinstance(k,str) or not k or not isinstance(v,str) for k,v in fields.items()):fail('invalid field map')
    if not set(sch)<=set(pcb) or not {'Datasheet','Description'}<=set(sch):fail('effective field census differs or missing')
    placeholder=False
    for name in sorted(sch):
        if sch[name]==pcb[name]:continue
        if name!='Datasheet' or pcb[name]!='~' or sch[name]!='':fail('unqualified field mismatch: '+name)
        placeholder=True
    return placeholder

def components(raw_text,observer):
    if not isinstance(raw_text,str):fail('native kicadsexpr text required')
    tree=sx.parse(raw_text)
    if tree[0]!='export' or singleton(tree,'version')!='E':fail('native export schema differs')
    design=sx.one(tree,'design')
    if design is None or singleton(design,'tool')!='Eeschema 10.0.0':fail('native exporter identity differs')
    source=PurePosixPath(observer['source'])
    if singleton(design,'source')!=str(source.with_suffix('.kicad_sch')):fail('source schematic/PCB pairing differs')
    section=sx.one(tree,'components')
    if section is None or not section[1:] or any(not isinstance(c,list) or not c or c[0]!='comp' for c in section[1:]):fail('complete components required')
    result={};folded=set()
    for comp in section[1:]:
        ref=singleton(comp,'ref')
        if not ref or ref.casefold() in folded:fail('duplicate or colliding component reference')
        folded.add(ref.casefold());fields=sx.one(comp,'fields');values={}
        if fields is None:fail('effective component fields absent')
        for field in fields[1:]:
            if not isinstance(field,list) or len(field) not in (2,3) or field[0]!='field':fail('unknown effective field schema')
            name=singleton(field,'name')
            if not name or name in values:fail('duplicate effective field name')
            values[name]=atom(field[2]) if len(field)==3 else ''
        if not {'Footprint','Datasheet','Description'}<=set(values):fail('native default field census incomplete')
        result[ref]={k:v for k,v in values.items() if k not in SKIP}
    return result

def derive(raw_netlist_text,observer,raw_drc_report):
    """Return a field-only proof; ValueError means unqualified, never a waiver."""
    canonical(observer);canonical(raw_drc_report)
    required={'schema','native_version','source','board_sha256','project_sha256','schematic_sha256','board_saved','footprints'}
    if not isinstance(observer,dict) or set(observer)!=required or type(observer['schema']) is not int or observer['schema']!=1 or observer['board_saved'] is not False:fail('native field observation schema differs')
    version=text(observer['native_version'])
    if version!='10.0.0' and not version.startswith('10.0.0 '):fail('native field observer version differs')
    source=PurePosixPath(text(observer['source']))
    if not source.is_absolute() or '..' in source.parts or source.suffix!='.kicad_pcb':fail('absolute native PCB source required')
    if any(not isinstance(observer[k],str) or SHA.fullmatch(observer[k]) is None for k in ('board_sha256','project_sha256','schematic_sha256')):fail('native input hash missing')
    report=raw_drc_report
    if (not isinstance(report,dict) or report.get('$schema')!='https://schemas.kicad.org/drc.v1.json'
            or report.get('kicad_version')!='10.0.0' or report.get('source')!=source.name):fail('native DRC identity differs')
    if report.get('included_severities')!=['error','warning','exclusion']:fail('native severity coverage differs')
    if not isinstance(report.get('ignored_checks'),list) or any(not isinstance(r,dict) or not isinstance(r.get('key'),str) or r['key']==KIND for r in report['ignored_checks']):fail('field check disabled or metadata absent')
    if any(not isinstance(report.get(k),list) for k in ('violations','unconnected_items','schematic_parity')):fail('native DRC coverage absent')
    findings=report['violations']+report['unconnected_items']+report['schematic_parity']
    if any(not isinstance(r,dict) or r.get('type')=='footprint_symbol_mismatch' for r in findings):fail('other symbol mismatch or malformed finding')
    sch=components(raw_netlist_text,observer);pcb={};ids=set();folded=set()
    if not isinstance(observer['footprints'],list):fail('complete native footprint census absent')
    for row in observer['footprints']:
        if not isinstance(row,dict) or set(row)!={'reference','uuid','fields'}:fail('native footprint schema differs')
        ref=text(row['reference']);uid=text(row['uuid'])
        if not ref or ref.casefold() in folded or UUID.fullmatch(uid) is None or uid in ids:fail('duplicate or colliding footprint identity')
        folded.add(ref.casefold());ids.add(uid)
        if not isinstance(row['fields'],dict):fail('native field map absent')
        if any(not isinstance(k,str) or not k or not isinstance(v,str) for k,v in row['fields'].items()):fail('malformed native field map')
        pcb[ref]={'uuid':uid,'fields':{k:v for k,v in row['fields'].items() if k not in SKIP}}
    if set(sch)!=set(pcb):fail('component/footprint census incomplete')
    matrix=[];needed=set()
    for ref in sorted(sch):
        fp=pcb[ref];placeholder=compare(sch[ref],fp['fields'])
        if placeholder:needed.add(fp['uuid'])
        matrix.append({'reference':ref,'uuid':fp['uuid'],'schematic_fields':sch[ref],'pcb_fields':fp['fields']})
    warnings=[r for r in findings if r.get('type')==KIND];seen=set()
    for row in warnings:
        items=row.get('items')
        if row not in report['schematic_parity'] or row.get('description')!=DESCRIPTION or row.get('severity')!='warning' or row.get('excluded',False) is not False or not isinstance(items,list) or len(items)!=1 or not isinstance(items[0],dict):fail('unqualified native field warning')
        uid=items[0].get('uuid')
        if not isinstance(uid,str) or uid not in needed or uid in seen:fail('field warning UUID differs or repeats')
        ref=next(r['reference'] for r in matrix if r['uuid']==uid)
        if items[0].get('description')!='Footprint '+ref:fail('field warning reference differs')
        seen.add(uid)
    if seen!=needed:fail('placeholder warnings absent or incomplete')
    return {'qualified':True,'policy':POLICY,'component_count':len(matrix),'compared_field_count':sum(len(r['schematic_fields']) for r in matrix),'comparison_map':matrix,'warning_uuids':sorted(needed),'warning_hashes':sorted(digest(canonical(r)) for r in warnings),'native_export_sha256':digest(raw_netlist_text.encode()),'observer_sha256':digest(canonical(observer)),'drc_report_sha256':digest(canonical(report))}

def qualified(qualification,findings):
    """True only for the exact derived field-warning subset; no other findings."""
    try:
        q=qualification
        if not isinstance(q,dict) or q.get('qualified') is not True or q.get('policy')!=POLICY or not isinstance(findings,list):return False
        keys={'qualified','policy','component_count','compared_field_count','comparison_map','warning_uuids','warning_hashes','native_export_sha256','observer_sha256','drc_report_sha256'}
        if set(q)!=keys or any(type(q[k]) is not int for k in ('component_count','compared_field_count')) or any(not isinstance(q[k],str) or SHA.fullmatch(q[k]) is None for k in ('native_export_sha256','observer_sha256','drc_report_sha256')):return False
        matrix=q['comparison_map'];needed={r['uuid'] for r in matrix if compare(r['schematic_fields'],r['pcb_fields'])}
        if q['component_count']!=len(matrix) or q['compared_field_count']!=sum(len(r['schematic_fields']) for r in matrix) or q['warning_uuids']!=sorted(needed):return False
        if any(not isinstance(r,dict) or r.get('type')!=KIND or r.get('severity')!='warning' or r.get('excluded',False) is not False or r.get('description')!=DESCRIPTION for r in findings):return False
        return sorted(digest(canonical(r)) for r in findings)==q['warning_hashes'] and len(findings)==len(needed)
    except (ValueError,KeyError,TypeError):return False
