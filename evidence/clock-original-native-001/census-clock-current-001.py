from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from experiments.licensed_acquisition_v1 import fetch
exec(compile((ROOT/'.runs/curate-legacy-zone-actual-001.py').read_text().split('results=[]')[0],'shared-curation','exec'))
prior=json.loads((ROOT/'experiments/licensed_acquisition_v6/existing-data-inventory.json').read_text());receipt=json.loads((ROOT/'.runs/licensed-acquisition-009-run-001/receipt.json').read_text())
added={row['destination']:{k:row[k] for k in ('bytes','sha256')} for row in receipt['files']}
expected=fetch.extend(prior,added,destination_root='expansion009');actual=fetch.inventory(ROOT/'.data',expected)
old=json.loads((ROOT/'evidence/corpus-population-008-current-003/population.json').read_text());names=[row['board'] for row in old['boards'] if row['board']!='.data/corpus-audit-coldfire-001/project/kit-dev-coldfire-xilinx_5213.kicad_pcb']+['.data/expansion009/als311-clock/hardware/hardware.kicad_pcb'];assert len(names)==24 and len(set(names))==23
all_pcbs={'.data/'+name for name in actual['files'] if name.endswith('.kicad_pcb')};duplicate='.data/corpus-audit-coldfire-001/project/kit-dev-coldfire-xilinx_5213.kicad_pcb';canonical='.data/boards/kicad-coldfire-xilinx/kit-dev-coldfire-xilinx_5213.kicad_pcb';assert all_pcbs==set(names)|{duplicate} and p.sha(ROOT/duplicate)==p.sha(ROOT/canonical)
rows=[]
for name in sorted(names):
 path=ROOT/name;row={'board':name,'sha256':p.sha(path),'bytes':path.stat().st_size,'statically_eligible':False,'unsupported_reason':None,'native_acceptance':None}
 try:p.preflight(path);row['statically_eligible']=True
 except p.Rejected as exc:row['unsupported_reason']=str(exc)
 rows.append(row)
out=ROOT/'.runs/corpus-population-009-current-001';out.mkdir();p.save_json(out/'population.json',{'schema':1,'kind':'full acquired population current static census','git_head':p.tool_manifest()['git_head'],'implementation_sha256':p.tool_manifest()['implementation_sha256'],'complete_acquisition_inventory_verified':True,'files_observed':actual['file_count'],'bytes':actual['bytes'],'physical_boards':len(all_pcbs),'canonical_boards':len(rows),'exact_audit_duplicate':{'board':duplicate,'canonical':canonical,'sha256':p.sha(ROOT/duplicate)},'boards':rows,'statically_eligible':sum(r['statically_eligible'] for r in rows),'statically_unsupported':sum(not r['statically_eligible'] for r in rows),'all_development_exposed':True,'independent_pedigrees_proven':0,'claims_limit':'Static scope only; no new native run or accepted output, no holdout or family superiority. Earlier audit_corpus-only original7-board subset retained separately, never used as full denominator.'})
p.save_json(out/'inputs.json',{'prior_population_sha256':p.sha(ROOT/'evidence/corpus-population-008-current-003/population.json'),'preexisting_inventory_sha256':p.sha(ROOT/'experiments/licensed_acquisition_v6/existing-data-inventory.json'),'acquisition_receipt_sha256':p.sha(ROOT/'.runs/licensed-acquisition-009-run-001/receipt.json'),'producer_sha256':p.sha(Path(__file__))})

from autorouter import floor_route as f
clock=f.read_json(ROOT/'.runs/als311-original-native-001/result.json');pop=f.read_json(out/'population.json');row=next(r for r in pop['boards'] if r['board'].startswith('.data/expansion009/'));row['original_native_observation']={'opens':clock['parity_native']['opens'],'blocking':clock['parity_native']['blocking'],'warnings':clock['parity_native']['warnings'],'source_field_scope_qualified':False,'accepted':False,'reason':'Original3opens/43Datasheet warnings/4realvalue mismatches/1USBFP mismatch; hierarchy bridge unqualified, source preserved.'};p.save_json(out/'population.json',pop)
dest=fresh('corpus-population-009-current-001');copied={}
for file in out.iterdir():copied[file.name]=copy(file,dest/file.name)
print(close(dest,copied))
