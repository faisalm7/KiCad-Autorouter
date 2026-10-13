from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from experiments.licensed_acquisition_v1 import fetch
exec(compile((ROOT/'.runs/curate-legacy-zone-actual-001.py').read_text().split('results=[]')[0],'shared-curation','exec'))
prior=json.loads((ROOT/'experiments/licensed_acquisition_v5/existing-data-inventory.json').read_text());receipt=json.loads((ROOT/'.runs/licensed-acquisition-008-run-001/receipt.json').read_text())
added={row['destination']:{k:row[k] for k in ('bytes','sha256')} for row in receipt['files']}
expected=fetch.extend(prior,added,destination_root='expansion008');actual=fetch.inventory(ROOT/'.data',expected)
old=json.loads((ROOT/'evidence/corpus-population-007-current-001/population.json').read_text());names=[row['board'] for row in old['boards'] if row['board']!='.data/corpus-audit-coldfire-001/project/kit-dev-coldfire-xilinx_5213.kicad_pcb']+['.data/expansion008/nus-usb-led/src/usb_led.kicad_pcb'];assert len(names)==23 and len(set(names))==23
all_pcbs={'.data/'+name for name in actual['files'] if name.endswith('.kicad_pcb')};duplicate='.data/corpus-audit-coldfire-001/project/kit-dev-coldfire-xilinx_5213.kicad_pcb';canonical='.data/boards/kicad-coldfire-xilinx/kit-dev-coldfire-xilinx_5213.kicad_pcb';assert all_pcbs==set(names)|{duplicate} and p.sha(ROOT/duplicate)==p.sha(ROOT/canonical)
rows=[]
for name in sorted(names):
 path=ROOT/name;row={'board':name,'sha256':p.sha(path),'bytes':path.stat().st_size,'statically_eligible':False,'unsupported_reason':None,'native_acceptance':None}
 try:p.preflight(path);row['statically_eligible']=True
 except p.Rejected as exc:row['unsupported_reason']=str(exc)
 rows.append(row)
out=ROOT/'.runs/corpus-population-008-current-003';out.mkdir();p.save_json(out/'population.json',{'schema':1,'kind':'full acquired population current static census','git_head':p.tool_manifest()['git_head'],'implementation_sha256':p.tool_manifest()['implementation_sha256'],'complete_acquisition_inventory_verified':True,'files_observed':actual['file_count'],'bytes':actual['bytes'],'physical_boards':len(all_pcbs),'canonical_boards':len(rows),'exact_audit_duplicate':{'board':duplicate,'canonical':canonical,'sha256':p.sha(ROOT/duplicate)},'boards':rows,'statically_eligible':sum(r['statically_eligible'] for r in rows),'statically_unsupported':sum(not r['statically_eligible'] for r in rows),'all_development_exposed':True,'independent_pedigrees_proven':0,'claims_limit':'Static scope only; no new native run or accepted output, no holdout or family superiority. Earlier audit_corpus-only original7-board subset retained separately, never used as full denominator.'})
p.save_json(out/'inputs.json',{'prior_population_sha256':p.sha(ROOT/'evidence/corpus-population-007-current-001/population.json'),'preexisting_inventory_sha256':p.sha(ROOT/'experiments/licensed_acquisition_v5/existing-data-inventory.json'),'acquisition_receipt_sha256':p.sha(ROOT/'.runs/licensed-acquisition-008-run-001/receipt.json'),'producer_sha256':p.sha(Path(__file__))})
dest=fresh('corpus-population-008-current-003');copied={}
for path in out.iterdir():copied[path.name]=copy(path,dest/path.name)
print(json.dumps(close(dest,copied)))
dest=fresh('nus-b2-continuation-001');copied={}
for base_name in ('nus-b2-portfolio-continuation-001','nus-additive-comparison-001'):
 base=ROOT/'.runs'/base_name
 for path in sorted(base.rglob('*')):
  if not path.is_file():continue
  rel=path.relative_to(base)
  if path.suffix not in {'.json','.log'} or any(x in {'frozen-code','candidate','snapshot','refill','kicad-config','engine-config','tmp'} or x.endswith('-input') for x in rel.parts):continue
  copied[base_name+'/'+str(rel)]=copy(path,dest/base_name/rel)
for name in ('run-nus-b2-portfolio-continuation-001.py','nus-b2-portfolio-continuation-001-protocol.json','close-nus-additive-comparison-001.py','census-and-curate-nus-continuation-002.py'):
 copied[name]=copy(ROOT/'.runs'/name,dest/name)
(dest/'SCOPE.md').write_text('Actual continuation atd610a2c retains completed default exactly and runs only fixed low/high. Default71.769712028mm2vias accepted, low69.986373mm2vias rejected1open, high80.420732mm2vias accepted; all10warnings. StrongB2selects default. Cown-incumbent24GNDsegment pruning35.128656244mm2vias improves36.641055784mm versusstrongB2 and36.755668677mm versusB1, same0/0/10warning signatures and unchangedoriginalconstraints. Newwhole41.960499250wall42.691900CPU plus oldwhole19.7235585/19.945710 arecharged. Freshadditive finalreadback verifiesallpositives andnegative original/native/field/pour/protection proofs; entire bounded25second wall/fullCPU finalaudit/emission allowance chargedconservativelytoEACHarm, actualaudit~2s. B2charged88.112877wall90.472093CPU, C58.214645wall57.272633CPU under120caps; wholecalendar gapdisclosed, notcontinuous120elapsed. Originalinvalidatedpaired/defaultreceipts unchanged, no completedstage repeated. One exposed tutorialboard, differently published/circuit but no provenpedigree, no broadcompletion/holdout/electrical/physical/generalized claim. Raw complete original/native/projects remainlocal.\n')
print(json.dumps(close(dest,copied)))
