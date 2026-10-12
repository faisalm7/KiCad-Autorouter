"""Reuse the prior exact-copy curation helpers for two explicit frozen subsets."""
from pathlib import Path
import hashlib,json
SCRIPT=Path(__file__).resolve();ROOT=SCRIPT.parents[2]
helper=ROOT/'.runs/curate-pic-selective-routing-001.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='43995cd694824e31f109fa629cc47d3ad225e851417f9782a047d44c2b206d30'
ns={'__file__':str(helper),'__name__':'curation_helpers'}
exec(compile(helper.read_text().split('results=[]')[0],str(helper),'exec'),ns)
raw,meta,write,fresh,copy,close,inventory=[ns[x] for x in ('raw','meta','write','fresh','copy','close','inventory')]
LIMIT=ns['LIMIT'];results=[]
name='pic-corrected-adapter-routing-001';source=ROOT/'.runs'/name
before=inventory(source,max_bytes=LIMIT,max_files=2000,max_entries=4000);summary=json.loads(raw(source/'summary.json'))
assert all(before.get(k)==v for k,v in summary['frozen_evidence'].items())
original=summary['runtime']['original'];assert inventory(ROOT/'.data/boards/kicad-pic-programmer')==inventory(source/'observe-input')==original
assert summary['status']=='failed' and summary['error']=='ValueError: corrected adapter changed other imported constraints'
assert summary['routing_executed'] is True and summary['ses_executed'] is True and summary['native_process_executed'] is False and summary['routing_accepted'] is False
obs=json.loads(raw(source/'observations.json'));prepared=json.loads(raw(source/'prepared.json'))
assert prepared['case']==obs['case'] and obs['final_geometry']['trace_count']==176 and obs['final_geometry']['via_count']==0
assert all(n.endswith('IntPoint') for t in obs['final_geometry']['traces'] for n in t['corner_classes'])
duplicates={'prepared.json':'Complete before-pipeline case repeated exactly in observations.json; raw prepared bytes retained locally.', 'local-basis-observations.json':'Previously exposed local250 prerequisite, retained locally and bound by failed summary.', 'selective-basis-observations.json':'Previously exposed selective002 prerequisite, retained locally and bound by failed summary.'}
selected={p.name for p in source.iterdir() if p.is_file()}-set(duplicates)
selected.update('observe-input/_licenses/'+n for n in ('LICENSE.CC-BY-SA-4.0','LICENSE.README'))
dest=fresh(name);copied={}
for rel in sorted(selected):copied[rel]=copy(source/rel,dest/rel)
for rel in ('run-'+name+'.py',name+'-execution.json',name+'-command.log'):copied[rel]=copy(ROOT/'.runs'/rel,dest/rel)
outer=json.loads(raw(ROOT/'.runs'/(name+'-execution.json')))
assert outer['log_sha256']==meta(ROOT/'.runs'/(name+'-command.log'))['sha256']
assert outer['wrapper_sha256']==meta(ROOT/'.runs'/('run-'+name+'.py'))['sha256']
assert outer['git_head']==summary['runtime']['git']['head']
write(dest/'omissions.json',{rel:{'bytes':(source/rel).stat().st_size,'sha256':digest,'reason':duplicates.get(rel,'Complete original/code/native cache, compiled class or isolated runtime artifact retained locally; no binary or duplicate whole project selected.')} for rel,digest in before.items() if rel not in selected})
(dest/'PUBLIC_SCOPE.md').write_text('Actual corrected-adapter001 remains FAILED at its Python cross-import static comparison after successful compile/import/solver/SES. Final engine representation has176traces/0vias,33 ordinary obstacles and2 protected custom bodies; zero parser warnings. All513 captured corners are exact IntPoint(z=1), so actual RationalPoint capture is not exercised. No fresh native stage ran and routing_accepted=false.\n\nThe separately retained posthoc audit diagnoses only internal GND/VCC numbering1↔2 and verifies named constraints/terminal memberships. Later strict engine-to-SES equality is a new offline fact, not a rewritten historical run status or production acceptance. Adapter scope is B1_adapter_only; the original one native zone remains unchanged even though its engine plane was suppressed. All19 original/snapped PCB_TEXT boxes and the entire adapter receipt are retained.\n\nSelected raw files are byte-identical; whole-invocation/prior cached costs remain in the failed summary and outer receipt. All107 frozen artifacts, the complete108-file run and15 original project files are verified unchanged. Omitted whole projects/code/classes and repeated prerequisite/prepared payloads remain local and explicitly hash-bound in omissions.json. This is a selected subset, not a complete replay checkout.\n\nPIC-derived material originates from official KiCad pic_programmer commit69cafb907ebc09e7722a2a464b1d466fc2e3608d, CC BY-SA4.0. Exact original notices/license appear under observe-input/_licenses. Project-authored scripts are GPL-3.0. No downloaded engine/source binaries or private inputs are included. Curation executed no native/JVM/compiler/solver.\n')
assert inventory(source,max_bytes=LIMIT,max_files=2000,max_entries=4000)==before and inventory(ROOT/'.data/boards/kicad-pic-programmer')==original
write(dest/'curation.json',{'source':str(source.relative_to(ROOT)),'scope':'Exact-copy/frozen-inventory work only','source_summary_sha256':before['summary.json'],'source_head':summary['runtime']['git']['head'],'raw_status':'failed','full_run_files':len(before),'frozen_files':len(summary['frozen_evidence']),'original_files_unchanged':len(original),'full_run_unchanged':True,'routing_accepted':False,'native_executed':False,'curation_script_sha256':hashlib.sha256(SCRIPT.read_bytes()).hexdigest()})
results.append(close(dest,copied))
name='review-pic-adapter-actual-001';source=ROOT/'.runs'/name;manifest=json.loads(raw(source/'manifest.json'))
assert all(meta(source/rel)==pin for rel,pin in manifest.items())
dest=fresh(name);copied={}
for rel in [*manifest,'manifest.json']:copied[rel]=copy(source/rel,dest/rel)
(dest/'PUBLIC_SCOPE.md').write_text('Exact frozen offline actual001 diagnosis and shared-checker readback, including full111 prior/current named-net mapping. The historical failure is preserved. Corrected checker success is not a fresh native verdict, routing acceptance, or proof of unchanged routed connectivity. Original15file project and complete108file run remain unchanged; no source/engine binary is included. Project-authored audit script follows GPL-3.0.\n')
assert all(meta(source/rel)==pin for rel,pin in manifest.items())
results.append(close(dest,copied))
print(json.dumps({'curation':'complete','directories':results,'total_copied_files':sum(r['copied_files'] for r in results),'total_copied_bytes':sum(r['copied_bytes'] for r in results),'script_sha256':hashlib.sha256(SCRIPT.read_bytes()).hexdigest()},indent=2))
