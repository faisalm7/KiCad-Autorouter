"""Byte-check selected raw public copy and cross-check authored summary."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
OUT=Path(__file__).resolve().parent;public=ROOT/'evidence/layer-preferences-native-001'
j=lambda path:json.loads(path.read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
manifest=j(public/'manifest.json');count=0;total=0
for name,pin in manifest['files'].items():
 path=public/name;raw=path.read_bytes();assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],name
 total+=len(raw)
 if name=='summary.json':continue
 if name=='protocol.json':original=ROOT/'.runs/layer-native-input-001/protocol.json'
 elif name.startswith('preview/'):original=ROOT/'.runs/layer-native-preview-001'/Path(name).name
 else:original=ROOT/'.runs'/name
 assert raw==original.read_bytes(),name
 count+=1
summary=j(public/'summary.json')
for row in summary['cases']:
 run=Path(row['run']);r=j(run/'result.json');outer=j(ROOT/'.runs'/(run.name+'-execution.json'))
 assert row['result_sha256']==sha(run/'result.json') and row['candidate_sha256']==r['candidate_sha256']
 for key in ('status','accepted','native','metrics','layer_binding','layer_audit'):assert row[key]==r[key],(row['id'],key)
 assert row['stored_wall_seconds']==r['wall_seconds'] and row['stored_full_cpu_seconds']==r['total_cpu_seconds']
 assert row['outer_wall_seconds']==outer['wall_seconds'] and row['outer_waited_child_cpu_seconds']==outer['waited_child_cpu_seconds']
 assert summary['retained_run_hashes'][str(run)]==p.tree_hash(run)
assert summary['disallowed_layer_native_control']==j(ROOT/'.runs/layer-negative-native-001/summary.json')
assert summary['broader_supported_families_added']==0 and summary['human_review'] is False and summary['physical_electrical_validation'] is False
record={'all_passed':True,'public_manifest_sha256':sha(public/'manifest.json'),'manifest_files':len(manifest['files']),'manifest_bytes':total,'exact_raw_original_copies':count,'derived_summary_files':1,'all_five_summary_cases_match_raw_receipts_and_outer_costs':True,'negative_summary_exact':True,'notes':'Summary is authored metadata checked against raw receipts, not mislabeled as a copied original. Manifest and any scope metadata are outside their own file inventory.'}
(OUT/'public-check.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
