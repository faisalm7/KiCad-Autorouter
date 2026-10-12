"""Fixed field-only source-span insertions; never saves/loads native CAD."""
import copy
from autorouter import sexpr as sx
CASES=('original_parity','matched_custom_field','mismatched_custom_field')
BOARD='pic_programmer.kicad_pcb';SCH='pic_programmer.kicad_sch'
FIELD='AutorouterDiagnosticParity';MATCH='PIC_FIELD_MATCH_001';MISMATCH='PIC_FIELD_MISMATCH_001'
FP='00000000-0000-0000-0000-00005a22ac23';SYMBOL='00000000-0000-0000-0000-0000442a4cf4'
ROOT_UUID='2e45d1d2-c73f-46e5-98d6-3a9dc360bff5';FIELD_UUID='0749c3dc-55b9-5452-93d3-9ed189a3266d'
def uid(node):return sx.unquote(sx.one(node,'uuid')[1])
def properties(node):
    result={}
    for row in sx.children(node,'property'):
        key=sx.unquote(row[1])
        if key in result:raise ValueError('duplicate field')
        result[key]=row
    return result
def target(tree,kind,identity):
    rows=sx.children(tree,kind);matches=[r for r in rows if uid(r)==identity]
    refs=[r for r in rows if sx.unquote(properties(r)['Reference'][2])=='R1']
    if len(matches)!=1 or len(refs)!=1 or refs[0]is not matches[0]:raise ValueError('unique R1/UUID required')
    node=matches[0];props=properties(node)
    if FIELD in props or sx.unquote(props['Value'][2])!='10K':raise ValueError('original target/field changed')
    if kind=='symbol':
        if tree[0]!='kicad_sch' or uid(tree)!=ROOT_UUID or sx.one(node,'unit')!=['unit','1']:raise ValueError('original root/unit changed')
        if sx.one(node,'instances')!=['instances',['project','"pic_programmer"',['path','"/'+ROOT_UUID+'"',['reference','"R1"'],['unit','1']]]]:raise ValueError('target hierarchy changed')
    elif sx.one(node,'path')!=['path','"/'+SYMBOL+'"'] or sx.one(node,'at')!=['at','87.63','118.11']:raise ValueError('original footprint identity/position changed')
    return node

def insert(raw,kind,identity,value):
    text=raw.decode();tree=sx.parse(text);node=target(tree,kind,identity);description=properties(node)['Description']
    prop=copy.deepcopy(description);prop[1]='"'+FIELD+'"';prop[2]='"'+value+'"'
    if sx.one(prop,'hide')!=['hide','yes']:raise ValueError('hidden field presentation required')
    if kind=='footprint':sx.one(prop,'uuid')[1]='"'+FIELD_UUID+'"'
    if FIELD in text or FIELD_UUID in text:raise ValueError('diagnostic identity already present')
    depth=0;start=None;spans=[]
    for token in sx.TOKEN.finditer(text):
        t=token.group()
        if t=='(':
            if depth==1:start=token.start()
            depth+=1
        elif t==')':
            depth-=1
            if depth==1 and start is not None:
                child=sx.parse(text[start:token.end()])
                if child[0]==kind and uid(child)==identity:spans.append((start,token.end()))
                start=None
    if len(spans)!=1:raise ValueError('ambiguous target source span')
    end=spans[0][1]-1;out=(text[:end]+'\n\t\t'+sx.dump(prop)+'\n\t'+text[end:]).encode()
    expected=copy.deepcopy(tree);target(expected,kind,identity).append(prop)
    if sx.parse(out.decode())!=expected:raise ValueError('undeclared source delta')
    return out

def prepare(board,schematic,case):
    if case not in CASES:raise ValueError('unknown fixed case')
    target(sx.parse(board.decode()),'footprint',FP);target(sx.parse(schematic.decode()),'symbol',SYMBOL)
    if case=='original_parity':return {BOARD:board,SCH:schematic}
    pcb=insert(board,'footprint',FP,MISMATCH if case=='mismatched_custom_field'else MATCH)
    sch=insert(schematic,'symbol',SYMBOL,MATCH)
    if case=='mismatched_custom_field':
        positive=insert(board,'footprint',FP,MATCH)
        if pcb.count(MISMATCH.encode())!=1 or pcb.replace(MISMATCH.encode(),MATCH.encode(),1)!=positive:raise ValueError('negative is not sole value replacement')
    return {BOARD:pcb,SCH:sch}
