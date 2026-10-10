"""Static original-source census only; no source writes, CAD, network or routing."""
import copy,hashlib,json,os,stat,sys,uuid
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx
SOURCE=ROOT/'.data/boards/kicad-pic-programmer';HERE=Path(__file__).resolve().parent
FIELD='AutorouterDiagnosticParity';MATCH='PIC_FIELD_MATCH_001';MISMATCH='PIC_FIELD_MISMATCH_001'
def content(p,cap=2*1024**2):
    info=p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size>cap:raise ValueError('bounded regular input')
    with p.open('rb')as f:raw=f.read(cap+1)
    if len(raw)!=info.st_size or len(raw)>cap:raise ValueError('source changed/grew')
    return raw
def pin(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def inventory(root):
    out={};stack=[root];entries=0;total=0
    while stack:
        with os.scandir(stack.pop())as it:
            for e in it:
                entries+=1
                if entries>64 or e.is_symlink():raise ValueError('source scope')
                p=Path(e.path)
                if e.is_dir(follow_symlinks=False):stack.append(p)
                elif e.is_file(follow_symlinks=False):
                    raw=content(p);total+=len(raw)
                    if total>2*1024**2:raise ValueError('source cap')
                    out[str(p.relative_to(root))]=pin(raw)
                else:raise ValueError('special path')
    return dict(sorted(out.items()))
def props(row):
    out={}
    for p in sx.children(row,'property'):
        k=sx.unquote(p[1])
        if k in out:raise ValueError('duplicate property '+k)
        out[k]=sx.unquote(p[2])
    return out
def uid(row):return sx.unquote(sx.one(row,'uuid')[1])
def save(name,data):
    with(HERE/name).open('x')as f:f.write(json.dumps(data,indent=2,sort_keys=True)+'\n')
def main():
    before=inventory(SOURCE);assert len(before)==15
    board=sx.parse(content(SOURCE/'pic_programmer.kicad_pcb').decode());schs={n:sx.parse(content(SOURCE/n).decode())for n in ('pic_programmer.kicad_sch','pic_sockets.kicad_sch')}
    fps=sx.children(board,'footprint');byref={props(fp)['Reference']:fp for fp in fps};assert len(fps)==len(byref)==63
    placed=[];sheets=[]
    for filename,tree in schs.items():
        for sheet in sx.children(tree,'sheet'):sheets.append({'file':filename,'uuid':uid(sheet),'properties':props(sheet)})
        for symbol in sx.children(tree,'symbol'):
            p=props(symbol)
            if sx.one(symbol,'on_board')[1]=='yes' and not p['Reference'].startswith('#'):placed.append((filename,symbol,p))
    assert len(placed)==66 and len({p['Reference']for _,_,p in placed})==63 and set(byref)=={p['Reference']for _,_,p in placed}
    assert len(sheets)==1 and sheets[0]['properties']['Sheetfile']=='pic_sockets.kicad_sch'
    rows=[]
    for filename,symbol,p in placed:
        fp=byref[p['Reference']];bp=props(fp)
        fields={k:p[k]==bp[k]for k in ('Reference','Value','Datasheet','Description')};fields['Footprint']=p['Footprint']==sx.unquote(fp[1]);assert all(fields.values())
        rows.append({'schematic':filename,'reference':p['Reference'],'unit':sx.one(symbol,'unit')[1],'symbol_uuid':uid(symbol),'footprint_uuid':uid(fp),'checked_fields_match':fields})
    r1=[(filename,s,p)for filename,s,p in placed if p['Reference']=='R1'];assert len(r1)==1
    filename,symbol,p=r1[0];fp=byref['R1'];assert filename=='pic_programmer.kicad_sch'and sx.one(symbol,'unit')==['unit','1']
    assert uid(symbol)=='00000000-0000-0000-0000-0000442a4cf4' and uid(fp)=='00000000-0000-0000-0000-00005a22ac23'
    assert sx.one(fp,'path')==['path','"/'+uid(symbol)+'"']
    assert FIELD not in props(symbol)and FIELD not in props(fp)
    fpfield=copy.deepcopy(next(x for x in sx.children(fp,'property')if sx.unquote(x[1])=='Description'))
    schfield=copy.deepcopy(next(x for x in sx.children(symbol,'property')if sx.unquote(x[1])=='Description'))
    for field in (fpfield,schfield):field[1]='"'+FIELD+'"';field[2]='"'+MATCH+'"'
    fuid=str(uuid.uuid5(uuid.UUID('7c7ed68c-0ced-4f91-a35c-78ea0d278cdb'),'PIC:R1:AutorouterDiagnosticParity:PCB'))
    sx.one(fpfield,'uuid')[1]='"'+fuid+'"'
    assert sx.one(fpfield,'hide')==['hide','yes']and sx.one(schfield,'hide')==['hide','yes']
    # Only an in-memory metadata derivation. No board/schematic file is emitted or changed.
    positive_board=copy.deepcopy(board);positive_sch=copy.deepcopy(schs[filename])
    targetfp=next(x for x in sx.children(positive_board,'footprint')if uid(x)==uid(fp));targetsymbol=next(x for x in sx.children(positive_sch,'symbol')if uid(x)==uid(symbol))
    targetfp.append(fpfield);targetsymbol.append(schfield)
    negative_board=copy.deepcopy(positive_board);negativefp=next(x for x in sx.children(negative_board,'footprint')if uid(x)==uid(fp));negativefield=next(x for x in sx.children(negativefp,'property')if sx.unquote(x[1])==FIELD);negativefield[2]='"'+MISMATCH+'"'
    fixed=copy.deepcopy(negative_board);fpfixed=next(x for x in sx.children(fixed,'footprint')if uid(x)==uid(fp));next(x for x in sx.children(fpfixed,'property')if sx.unquote(x[1])==FIELD)[2]='"'+MATCH+'"';assert fixed==positive_board
    targetfp.remove(fpfield);targetsymbol.remove(schfield);assert positive_board==board and positive_sch==schs[filename]
    project=json.loads(content(SOURCE/'pic_programmer.kicad_pro'));severities=project['board']['design_settings']['rule_severities'];assert severities['footprint_symbol_field_mismatch']=='warning'
    source_documents=[]
    receipts=[('.runs/pic-severity-scope-review-001/source-receipt.json','.runs/pic-severity-scope-review-001/source'),('.runs/support-scope-review-001/source-receipt.json','.runs/support-scope-review-001/source')]
    wanted={'pcbnew/drc/drc_test_provider_schematic_parity.cpp','pcbnew/pcbnew_jobs_handler.cpp','pcbnew/drc/drc_item.cpp','pcbnew/pcb_marker.cpp','pcbnew/board_design_settings.cpp','pcbnew/drc/drc_report.cpp'}
    receipt_bindings={}
    for receipt_rel,base in receipts:
        raw=content(ROOT/receipt_rel);receipt_bindings[receipt_rel]=pin(raw);receipt=json.loads(raw);assert receipt['commit']=='0feeca2a807f428ad2b3fa7c1e39625cb769f02c'
        for row in receipt['files']:
            if row['path']in wanted and 'sha256'in row:
                path=ROOT/base/row['path'];p=pin(content(path));assert p=={k:row[k]for k in ('bytes','sha256')}
                source_documents.append({'cached_path':str(path.relative_to(ROOT)),'repository_path':row['path'],'url':row['url'],**p,'new_network':False})
    assert len(source_documents)==6
    recipe={'schema':1,'native_executed':False,'implementation_status':'source/recipe design only; no derived project emitted','source_board':str((SOURCE/'pic_programmer.kicad_pcb').relative_to(ROOT)),'source_inventory':before,'source_bytes':sum(p['bytes']for p in before.values()),'source_files':15,'target':{'reference':'R1','symbol_uuid':uid(symbol),'footprint_uuid':uid(fp),'schematic_path':filename,'schematic_root_uuid':uid(schs[filename]),'board_position_mm':sx.one(fp,'at')[1:],'source_symbol_path':sx.one(fp,'path')[1],'field_name':FIELD,'matched_value':MATCH,'mismatch_value':MISMATCH,'new_pcb_field_uuid':fuid,'positive_schematic_property':schfield,'positive_pcb_property':fpfield,'negative_only_delta':['R1',FIELD,'value',MATCH,MISMATCH]},'cases':[{'id':'original_parity','changes':'none; complete original15-file copy byte-identical','required_parity_findings':0},{'id':'matched_custom_field','changes':'add the declared hidden field to copied R1 schematic instance and copied R1 footprint; no library edits','required_parity_findings':0},{'id':'mismatched_custom_field','changes':'only the same PCB field value differs from matched_custom_field','required_parity_findings':1,'expected_type':'footprint_symbol_field_mismatch','expected_severity':'warning','expected_item_uuids':[uid(fp)]}],'project_rule_changes':False,'production_gate_changes':False,'original_field_severity':severities['footprint_symbol_field_mismatch'],'original_explicit_ignored':sorted(k for k,v in severities.items()if v=='ignore'),'derived_tree_reversal_assertions_passed':True,'native_parity_qualified':False,'geometry_routing_qualified':False,'network_requests':0}
    census={'schema':1,'source_inventory':before,'board_footprints':63,'on_board_symbol_units':66,'unique_symbol_references':63,'multi_unit_references':{k:v for k,v in Counter(p['Reference']for _,_,p in placed).items()if v>1},'board_references_exact_match':True,'checked_fields':['Reference','Value','Footprint','Datasheet','Description'],'all_checked_fields_match':True,'sheets':sheets,'symbol_rows':rows,'limits':'Static source equality only; native netlist export, inherited/custom field propagation, connectivity parity and fully annotated hierarchy are not established.'}
    assert before==inventory(SOURCE)
    save('recipe.json',recipe);save('static-census.json',census);save('source-bindings.json',{'source_commit':'0feeca2a807f428ad2b3fa7c1e39625cb769f02c','source_documents':source_documents,'receipts':receipt_bindings,'parser':{'path':'autorouter/sexpr.py',**pin(content(ROOT/'autorouter/sexpr.py'))},'original_source_unchanged':True,'network_requests':0})
    print(json.dumps({'static_checks_passed':True,'native_executed':False,'source_files':15,'source_bytes':recipe['source_bytes'],'matched_references':63,'on_board_units':66,'cases_proposed':3,'source_documents_rehashed':6,'network_requests':0}))
if __name__=='__main__':main()
