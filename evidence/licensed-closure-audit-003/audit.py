"""Independent static audit of two completed acquisitions. No network/native jobs."""
from pathlib import Path
import collections,hashlib,json,re,sys
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as s
HERE=Path(__file__).resolve().parent
PLAN=ROOT/'.runs/licensed-expansion-research-003/retrieval-plan.json'
EXPOSURE=ROOT/'.runs/licensed-acquisition-003/exposure-decision.json'
PLAN_SHA='4ab6b6675eeb33b90a1296441f624a5ba3a293c246d65fa021f73d4c6fa79dae'
SLUGS=('pmod-to-qwiic','lipo-disconnector')
inputs={}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
 path=Path(path);assert path.is_relative_to(ROOT)and not any(x.is_symlink()for x in (path,*path.parents));assert path.stat().st_size<=5*1024**2
 with path.open('rb')as stream:raw=stream.read(5*1024**2+1)
 assert len(raw)<=5*1024**2;key=str(path.relative_to(ROOT));digest=sha(raw);assert key not in inputs or inputs[key]==digest;inputs[key]=digest;return raw
def jsonread(path):return json.loads(read(path))
def tree(root):
 files={};total=0;paths=list(root.rglob('*'));assert len(paths)<=200
 for path in sorted(paths):
  assert not path.is_symlink()
  if path.is_file():raw=read(path);total+=len(raw);assert total<=10*1024**2;files[str(path.relative_to(root))]=sha(raw)
  else:assert path.is_dir()
 return files,total
def val(node,key):
 x=s.one(node,key);return s.unquote(x[1])if x and len(x)>1 and isinstance(x[1],str)else None
def nodes(node):
 if isinstance(node,list):
  yield node
  for child in node:
   if isinstance(child,list):yield from nodes(child)
def references(tree):
 result=[]
 for node in nodes(tree):
  if node and node[0]in ('model','lib_id','extends','sheetfile','footprint')and len(node)>1:result.append({'kind':node[0],'value':s.unquote(node[1])})
  elif node and node[0]=='property'and len(node)>2 and s.unquote(node[1])in ('Footprint','Sheetfile','Sheet file','ki_fp_filters','Datasheet'):
   value=s.unquote(node[2])
   if value and value!='~':result.append({'kind':s.unquote(node[1]),'value':value})
 return result
def audit(slug,plan):
 project=next(x for x in plan['projects']if x['slug']==slug);base=ROOT/'.data/expansion003'/slug;receipt_path=ROOT/'.runs/licensed-acquisition-003'/(slug+'-001')/'receipt.json';receipt=jsonread(receipt_path)
 assert receipt['status']=='acquired_unqualified'and receipt['split']=='development'and receipt['source_plan_sha256']==PLAN_SHA
 before,total=tree(base);expected={str(Path(x['destination']).relative_to(slug)):x['sha256']for x in receipt['files']};assert before==expected and total==receipt['bytes_verified']==project['proposed_bytes_before_standard_library_closure']
 planned={x['destination']:x for x in project['proposed_fetch_files']};assert len(planned)==len(receipt['files'])
 rights=[]
 for file in receipt['files']:
  row=planned[file['destination']];raw=read(ROOT/file['local_path']);assert len(raw)==row['bytes']and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha1']
  assert all(file[k]==row[k]for k in row if k not in ('sha256','payload_acquired_by_this_research'))
  assert file['payload_acquired_by_this_research']is True
  local=str(Path(file['destination']).relative_to(slug));scope='MIT dependency notice'if local.startswith(('modules/','library/'))else'publisher CERN-OHL-1.2 root notice; third-party provenance exceptions separately retained'
  notice=base/('modules/LICENSE'if local.startswith('modules/')else'library/LICENSE'if local.startswith('library/')else'LICENSE.md')
  text=raw.decode('utf8',errors='replace');hits=[]
  if Path(local).suffix.lower()not in ('.jpg','.jpeg','.png'):
   for no,line in enumerate(text.splitlines(),1):
    if re.search(r'copyright|licen[sc]e|all rights reserved|trademark|\u00a9',line,re.I):hits.append({'line':no,'text':line[:300]})
  rights.append({'path':local,'sha256':sha(raw),'bytes':len(raw),'source_repository':file['repository'],'source_commit':file['commit'],'git_blob_sha1':file['git_blob_sha1'],'source_url':file['raw_url'],'published_notice_scope':scope,'notice_path':str(notice.relative_to(ROOT)),'notice_sha256':sha(read(notice)),'inline_notice_hits':hits,'utf8_replacement_count':text.count('\ufffd')if Path(local).suffix.lower()not in ('.jpg','.jpeg','.png')else None,'redistribution_cleared_for_complete_project':False})
 boards=list(base.rglob('*.kicad_pcb'));assert len(boards)==1;board=boards[0];boardtree=s.parse(read(board).decode());project_path=board.with_suffix('.kicad_pro');proj=jsonread(project_path)
 schematic=board.with_suffix('.kicad_sch');sch=s.parse(read(schematic).decode());fps=s.children(boardtree,'footprint')+s.children(boardtree,'module')
 copper=[s.unquote(x[1])for x in s.one(boardtree,'layers')[1:]if re.fullmatch(r'(F|B|In[0-9]+)\.Cu',s.unquote(x[1]))];assert copper==['F.Cu','B.Cu']
 footprint_rows=[];model_refs=[]
 for fp in fps:
  identity=s.unquote(fp[1]);reference=next((s.unquote(x[2])for x in s.children(fp,'fp_text')if x[1]=='reference'),None);pads=s.children(fp,'pad')
  models=[]
  for model in s.children(fp,'model'):
   name=s.unquote(model[1]);entry={'reference':name,'hidden':'hide'in model,'owner_reference':reference,'owner_footprint':identity}
   if name.startswith('${KIPRJMOD}/'):
    local=name[len('${KIPRJMOD}/'):];entry.update(kind='project-local model',relative_path=local,present=(base/local).is_file())
   else:entry.update(kind='unresolved original stock/environment alias',present=False)
   models.append(entry);model_refs.append(entry)
  local=None
  if identity.startswith('Symbols_Extra:'):local=Path('modules/Symbols_Extra.pretty')/(identity.split(':',1)[1]+'.kicad_mod')
  footprint_rows.append({'identity':identity,'reference':reference,'uuid':val(fp,'tstamp')or val(fp,'uuid'),'pads':len(pads),'pad_types':dict(collections.Counter((x[2]+':'+x[3])for x in pads)),'models':models,'authentic_project_local_library_file':str(local)if local else None,'local_library_present':bool(local and(base/local).is_file()),'local_library_sha256':before.get(str(local))if local else None,'embedded_only_graphic':':'not in identity and not pads,'attributes':s.one(fp,'attr'),'schematic_path':val(fp,'path'),'native_library_parity_qualified':False})
 symbols=[]
 for node in s.children(sch,'symbol'):
  symbols.append({'lib_id':val(node,'lib_id'),'uuid':val(node,'uuid'),'properties':{s.unquote(v[1]):s.unquote(v[2])for v in s.children(node,'property')},'instances':s.one(node,'instances')})
 cached=s.one(sch,'lib_symbols');embedded_symbols=[s.unquote(x[1])for x in s.children(cached,'symbol')];symbol_refs=sorted({x['lib_id']for x in symbols if x['lib_id']})
 assert set(symbol_refs)<=set(embedded_symbols)
 table=s.parse(read(base/'fp-lib-table').decode());table_rows=[{key:val(x,key)for key in ('name','type','uri','options','descr')}for x in s.children(table,'lib')]
 extra_refs=[]
 for path in sorted(base.rglob('*')):
  if path.is_file() and path.suffix in ('.kicad_sym','.kicad_mod'):
   obj=s.parse(read(path).decode());extra_refs.append({'path':str(path.relative_to(base)),'references':references(obj)})
  elif path.is_file()and path.suffix=='.lib':
   txt=read(path).decode();extra_refs.append({'path':str(path.relative_to(base)),'legacy_F2_F3':re.findall(r'^F[23] .*$',txt,re.M)})
 rules=proj['board']['design_settings'];unsupported=None
 try:p.preflight(board)
 except p.Rejected as exc:unsupported=str(exc)
 assert unsupported is not None
 prefix='pmod'if slug=='pmod-to-qwiic'else'lipo';module_tree=jsonread(ROOT/f'.runs/licensed-expansion-research-003/{prefix}-modules-tree.json');module_nodes={x['path']:x for x in module_tree['tree']};missing=[]
 for ref in model_refs:
  if ref['kind']=='project-local model'and not ref['present']:
   name=str(Path(ref['relative_path']).relative_to('modules'));node=module_nodes.get(name);missing.append({**ref,'pinned_tree_entry':node,'rights':'not audited: blob content/embedded/vendor notice not acquired; repository MIT must not be assumed to resolve all upstream model rights'})
 after,total_after=tree(base);assert after==before and total_after==total
 return {'project':slug,'split':'development','source_repository':project['source'],'source_commit':project['commit'],'acquisition_receipt':str(receipt_path.relative_to(ROOT)),'acquisition_receipt_sha256':sha(read(receipt_path)),'files':len(before),'bytes':total,'complete_pinned_root':True,'complete_declared_submodule_repository':False,'root_file_count':project['complete_root_files'],'source_inventory':before,'source_unchanged':True,'board':str(board.relative_to(ROOT)),'board_sha256':before[board.name],'board_format_version':val(boardtree,'version'),'schematic_format_version':val(sch,'version'),'project_meta':proj['meta'],'same_basename_project_exists':True,'layers':copper,'layer_count':len(copper),'net_declarations':[x[1:]for x in s.children(boardtree,'net')],'pads':sum(len(s.children(fp,'pad'))for fp in fps),'edge_geometry_counts':dict(collections.Counter(x[0]for x in boardtree if isinstance(x,list)and val(x,'layer')=='Edge.Cuts')),'tracks':len(s.children(boardtree,'segment')),'vias':len(s.children(boardtree,'via')),'zone_count':len(s.children(boardtree,'zone')),'rule_area_count':sum(s.one(x,'keepout')is not None for x in s.children(boardtree,'zone')),'footprints':footprint_rows,'symbol_references':symbol_refs,'embedded_symbol_definitions':embedded_symbols,'schematic_instances':symbols,'original_symbol_instances_table':s.one(sch,'symbol_instances'),'schematic_sheet_count':len(s.children(sch,'sheet')),'schematic_original_references':references(sch),'project_fp_table':table_rows,'project_sym_table_present':(base/'sym-lib-table').exists(),'project_local_missing_models':missing,'stock_models':sorted({x['reference']for x in model_refs if x['kind']!='project-local model'}),'stock_footprints':sorted({x['identity']for x in footprint_rows if ':'in x['identity']and not x['identity'].startswith('Symbols_Extra:')}),'extra_dependency_file_reference_audit':extra_refs,'drc_exclusions':rules.get('drc_exclusions'),'original_rule_severities':rules['rule_severities'],'unknown_legacy_severity_keys':sorted(set(rules['rule_severities'])-p.KNOWN_CHECKS),'original_rule_minima':rules['rules'],'original_net_settings':proj['net_settings'],'static_preflight_eligible':False,'static_preflight_reason':unsupported,'native_executed':False,'native_validity':None,'dependency_complete':False,'file_rights_audit':rights,'independent_family_established':False,'family_group_for_leakage':'solderparty-connector-adapter-group-unresolved-ancestry','scope_limits':['Full table-referenced15-logo directory+notice is acquired; not the whole95/193MB module repository.','Schematic embedded symbols and board embedded footprints do not prove exact upstream version/library closure.','Stock aliases and model references remain unchanged and unresolved; current installed libraries are not silently substituted.','fp-info-cache is retained whole as original metadata, not treated as an instruction to fetch every cached global library.','No symbols/library table links the extra PMOD symbol repository to actual schematic refs; that complete dependency repository is present but current symbols use stock power/Connector_Generic names.','No source scripts, native tools, engines, network calls or file edits occurred.']}

def main():
 planraw=read(PLAN);assert sha(planraw)==PLAN_SHA;plan=json.loads(planraw);exposure=jsonread(EXPOSURE);assert exposure['projects']==list(SLUGS)and exposure['retrieval_plan_sha256']==PLAN_SHA
 records=[audit(slug,plan)for slug in SLUGS]
 modules=[{f['path']:f['sha256']for f in record['file_rights_audit']if f['path'].startswith('modules/Symbols_Extra.pretty/')}for record in records]
 assert modules[0]==modules[1]and len(modules[0])==15
 result={'schema':1,'kind':'independent static original source/license/dependency audit; not native qualification','prior_acquired_inputs':14,'new_acquired_boards':2,'resulting_acquired_inputs':16,'recorded_static_eligible':3,'recorded_static_unsupported':13,'complete_inputs':7,'incomplete_inputs':9,'production_policy_accepted_inputs_unchanged':2,'diagnostic_accepted_inputs_unchanged':1,'exposure_decision':str(EXPOSURE.relative_to(ROOT)),'exposure_sha256':sha(read(EXPOSURE)),'plan_sha256':PLAN_SHA,'pipeline_sha256':sha(read(ROOT/'autorouter/pipeline.py')),'sexpr_sha256':sha(read(ROOT/'autorouter/sexpr.py')),'records':records,'shared_templates':{'identical_logo_dependency_files':15,'same_MIT_notice':True,'family_independence_proven':False,'interpretation':'Sharedpublisher/logolibrary indicates common templates; distinct functions/repositories do not establish independent circuit ancestry. Both remain development and conservatively grouped pending ancestry review.'},'inputs':inputs,'native_jobs':0,'engine_jobs':0,'network_requests':0,'tracked_edits':False}
 for name,digest in list(inputs.items()):assert sha(read(ROOT/name))==digest
 (HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['new_acquired_boards','resulting_acquired_inputs','recorded_static_eligible','recorded_static_unsupported','complete_inputs','incomplete_inputs','native_jobs','engine_jobs','network_requests']},indent=2))
if __name__=='__main__':main()
