"""Reuse existing exact-copy curation for this raw run and its compact review only."""
from pathlib import Path
import hashlib,json,sys
SCRIPT=Path(__file__).resolve();ROOT=SCRIPT.parents[2];OUT=SCRIPT.parent
helper=ROOT/'.runs/curate-pic-selective-routing-001.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='43995cd694824e31f109fa629cc47d3ad225e851417f9782a047d44c2b206d30'
ns={'__file__':str(helper),'__name__':'curation_helpers'}
exec(compile(helper.read_text().split('results=[]')[0],str(helper),'exec'),ns)
raw,meta,write,fresh,copy,close,inventory=[ns[x] for x in ('raw','meta','write','fresh','copy','close','inventory')]
assert sys.argv[1:] in (['raw'],['review'])
if sys.argv[1]=='raw':
 name='pic-low-via-routing-001';source=ROOT/'.runs'/name;summary=json.loads(raw(source/'summary.json'));audit=json.loads(raw(OUT/'audit.json'))
 before=inventory(source,max_bytes=ns['LIMIT'],max_files=2000,max_entries=4000)
 assert before==json.loads(raw(OUT/'run-inventory.json')) and before['summary.json']==audit['bindings']['summary.json']
 assert all(before[k]==v for k,v in summary['frozen_evidence'].items())
 original=summary['runtime']['original'];assert inventory(ROOT/'.data/boards/kicad-pic-programmer')==inventory(source/'observe-input')==original
 assert summary['status']=='observed-incomplete' and not summary['routing_accepted'] and summary['native_process_executed'] and summary['routing_executed'] and summary['ses_executed']
 native=summary['native_routing'];final=source/'routing-native/candidate/pic_programmer.kicad_pcb'
 assert meta(final)['sha256']==native['candidate_sha256']==audit['candidate_sha256']
 dest=fresh(name);copied={};duplicates={'prepared.json','local-basis-observations.json','selective-basis-observations.json'}
 selected={x.name for x in source.iterdir() if x.is_file() and x.name not in duplicates}
 selected.update(str(x.relative_to(source)) for x in (source/'routing-native').iterdir() if x.is_file())
 selected.update(str(x.relative_to(source)) for x in final.parent.rglob('*') if x.is_file())
 for directory in ('observe-input','task-project','routing-native/task-project','routing-native/raw-project','routing-native/generated-raw-drc-input','routing-native/refill','routing-native/final-drc-input'):
  for suffix in ('kicad_pcb','kicad_pro','kicad_prl'):
   rel=directory+'/pic_programmer.'+suffix
   if rel in before:selected.add(rel)
 for rel in sorted(selected):copied[rel]=copy(source/rel,dest/rel)
 for rel in ('run-'+name+'.py',name+'-execution.json',name+'-command.log'):copied[rel]=copy(ROOT/'.runs'/rel,dest/rel)
 write(dest/'omissions.json',{rel:{'sha256':digest,'bytes':(source/rel).stat().st_size,'reason':'Duplicate basis, original/source/code/native cache or compiled/runtime data retained locally. Complete final candidate project and every differing native stage board/rules/report/binding are selected.'} for rel,digest in sorted(before.items()) if rel not in selected})
 (dest/'PUBLIC_SCOPE.md').write_text('''Actual low-via25/3 diagnostic at467f7bb9f2fb751a17a3560d2531225b6f6eb676 remains observed-incomplete/rejected:5opens,0blocking findings,41lib_footprint_issues warnings,0exclusions. It produced176engine traces /335ordinary native segments,0vias and1803.1552047465532mm. All eight stages ran: compile, fresh router/SES, and six native import/refill/final-check/metric stages. Exact engine→SES→native final ordinary geometry matches; original custom pads, zone intent, footprints, stackup and original project/rules remain authoritative and unchanged. This is not production support or native routing acceptance.

The previous default50/5 result also had5opens,0vias and no blocking findings. There is no completion gain. Both candidates are incomplete, so length is descriptive rather than an admissible route-quality comparison. This invocation's stored15.882476500wall/19.651377CPU samples precede final publication; outer16.179194583wall/19.897275waited-childCPU covers the invocation. The180wall/fullCPU caps apply. The earlier default native001 was a continuation after separately charged routing001, so its native-only cost is not interchangeable with this fresh eight-stage invocation. Cached prerequisite costs remain explicitly listed in the raw summary.

Selected raw files are byte-identical. The complete final candidate project includes all original dependencies, license and notices. Other stage projects are selected subsets, not independent complete projects; native binding inventories preserve their full original-rule provenance. Omissions are hash-bound, including repeated basis/code/original files, native cache and compiled classes. No binaries or downloaded engine/source payloads are included. Curation and independent readback ran no native/JVM/solver/network commands. Subsequent working-tree UI edits are separately recorded by the reviewer; they do not rewrite this captured source snapshot.

PIC-derived files originate from official KiCad pic_programmer69cafb907ebc09e7722a2a464b1d466fc2e3608d under CC BY-SA4.0. Exact original license and notices are in routing-native/candidate/_licenses. Project-authored scripts are GPL-3.0. This exposed development attempt is not a family-generalization or algorithmic-improvement claim.
''')
 assert inventory(source,max_bytes=ns['LIMIT'],max_files=2000,max_entries=4000)==before and inventory(ROOT/'.data/boards/kicad-pic-programmer')==original
 write(dest/'curation.json',{'scope':'Offline exact-copy curation following independent stored-record/invariant readback','source':str(source.relative_to(ROOT)),'source_summary_sha256':before['summary.json'],'source_head':summary['runtime']['git']['head'],'full_run_files':len(before),'frozen_files':len(summary['frozen_evidence']),'original_files_unchanged':len(original),'full_run_unchanged':True,'candidate_sha256':native['candidate_sha256'],'final_report_sha256':native['final_bound_report_sha256'],'native_counts':audit['reports']['final-drc']['counts'],'routing_accepted':False,'exact_generated_segments':335,'completion_gain':False,'curation_script_sha256':hashlib.sha256(SCRIPT.read_bytes()).hexdigest()})
 result=close(dest,copied);write(OUT/'raw-curation.json',result)
else:
 name='review-pic-low-via-actual-001';manifest=json.loads(raw(OUT/'manifest.json'));selection=json.loads(raw(OUT/'selection.json'))
 assert all(meta(OUT/n)==m for n,m in manifest['files'].items())
 dest=fresh(name);copied={}
 for n in (*selection['files'],'selection.json','manifest.json'):copied[n]=copy(OUT/n,dest/n)
 (dest/'PUBLIC_SCOPE.md').write_text('Exact selected independent readback and curation metadata. All15 original files, captured runtime/source/tool/basis/process/rules/report/geometry bindings were checked without new native or JVM execution. Initial current-census checks failed because ROOT separately added review_view.py and edited handoff.py/__main__.py after the run; both checks and old scripts are retained. Final review uses the actual captured code and records declared current divergence. Actual result stays incomplete:5opens/0blocking/41warnings/0exclusions. No completion or valid-route quality gain. Review scripts are project-authored GPL-3.0.\n')
 assert all(meta(OUT/n)==m for n,m in manifest['files'].items())
 result=close(dest,copied)
print(json.dumps(result,indent=2))
