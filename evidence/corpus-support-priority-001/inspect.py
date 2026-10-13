"""Small offline existing-population screen; hashes are similarity leads only."""
from pathlib import Path
from collections import Counter,defaultdict
from decimal import Decimal
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import sexpr as sx,pipeline as p,placement_clearance as pc


def raw(path):return pc.read_bytes(ROOT/path)
def load(path):return json.loads(raw(path))
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def norm(value):
 if isinstance(value,list):return [norm(x) for x in value]
 value=sx.unquote(value)
 if re.fullmatch(r'-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)',value):return format(Decimal(value).normalize(),'f')
 return value
EXCLUDE={'net','uuid','tstamp','pinfunction','pintype'}
def pad_geometry(pad,number=True):
 fields=sorted([norm(x) for x in pad[4:] if not isinstance(x,list) or not x or x[0] not in EXCLUDE],key=canonical)
 return [norm(x) for x in (pad[1:4] if number else pad[2:4])]+fields

old=load('evidence/placement-production-qualification-001/summary.json');extension=load('evidence/licensed-acquisition-004/population-extension.json');paw=load('evidence/paw3395-static-audit-001/audit.json')
rows=[dict(x) for x in old['boards']]
rows.extend({'board':x['source_path'],'source_sha256':x['sha256'],'input_completeness':x['dependency_closure']} for x in extension['new_boards'])
rows.append({'board':'.data/expansion005/paw3395/paw3395.kicad_pcb','source_sha256':'c2e8cebd0da804eb3912c6559ad6b3e725c1b29f744d616e1ebb22f1229f7740','input_completeness':'complete acquired original repository; external editing/model identity closure incomplete'})
if len(rows)!=20 or len({x['board'] for x in rows})!=20:raise ValueError('existing logical population differs')
result=[]
for record in rows:
 path=record['board'];board=raw(path)
 if hashlib.sha256(board).hexdigest()!=record['source_sha256']:raise ValueError('stored original hash differs: '+path)
 tree=sx.parse(board.decode());fps=[*sx.children(tree,'footprint'),*sx.children(tree,'module')];pads=[pad for fp in fps for pad in sx.children(fp,'pad')]
 netnames={n[1]:sx.unquote(n[2]) for n in sx.children(tree,'net') if len(n)==3}
 def net(pad):
  node=sx.one(pad,'net');return netnames.get(node[1],sx.unquote(node[2] if len(node)>2 else node[1])) if node else ''
 netcounts=Counter(net(pad) for pad in pads if net(pad))
 fp_signatures=[digest(sorted([pad_geometry(pad) for pad in sx.children(fp,'pad')],key=canonical)) for fp in fps]
 # Bipartite footprint↔net colored multigraph: no net/ref/UUID names and no
 # routing/board-placement data. Preserve pad number and local pad geometry.
 adjacency=defaultdict(list);colors={}
 for i,(fp,signature) in enumerate(zip(fps,fp_signatures)):
  fid=('fp',i);colors[fid]=digest(['fp',signature])
  for pad in sx.children(fp,'pad'):
   name=net(pad)
   if not name:continue
   nid=('net',name);edge=digest(pad_geometry(pad));adjacency[fid].append((nid,edge));adjacency[nid].append((fid,edge))
 for name,count in netcounts.items():colors[('net',name)]=digest(['net',count])
 for _ in range(3):colors={node:digest([colors[node],sorted([[edge,colors[neighbor]] for neighbor,edge in adjacency[node]],key=canonical)]) for node in colors}
 try:p.preflight(ROOT/path);reason=None
 except (p.Rejected,ValueError) as exc:reason=type(exc).__name__+': '+str(exc)
 project=ROOT/path;project=project.with_suffix('.kicad_pro');settings=json.loads(pc.read_bytes(project)) if project.is_file() else None
 severities=settings.get('board',{}).get('design_settings',{}).get('rule_severities',{}) if settings else {}
 layers=sx.one(tree,'layers',[])
 zones=sx.children(tree,'zone');classes=settings.get('net_settings',{}).get('classes',[]) if settings else []
 facts={'board':path,'source_sha256':record['source_sha256'],'format':sx.one(tree,'version')[1],
 'footprints':len(fps),'pads':len(pads),'connected_pad_terminals':sum(netcounts.values()),'named_nets_used_by_pads':len(netcounts),
 'pad_shapes':dict(sorted(Counter(pad[3] for pad in pads).items())),
 'net_degree_histogram':dict(sorted(Counter(netcounts.values()).items())),
 'footprint_pad_count_histogram':dict(sorted(Counter(len(sx.children(fp,'pad')) for fp in fps).items())),
 'copper_layers':[sx.unquote(x[1]) for x in layers[1:] if isinstance(x,list) and len(x)>1 and re.fullmatch(r'(F|B|In[0-9]+)\.Cu',sx.unquote(x[1]))],
 'route_counts':dict(sorted(Counter(route[0] for route in p.routes(tree)).items())),'zones':len(zones),
 'custom_pad_count':sum(pad[3]=='custom' for pad in pads),'net_tie_footprints':sum(bool(sx.children(fp,'net_tie_pad_groups')) for fp in fps),
 'project_exists':settings is not None,'project_sha256':hashlib.sha256(pc.read_bytes(project)).hexdigest() if settings else None,
 'class_names':[row.get('name') for row in classes],'class_patterns':settings.get('net_settings',{}).get('netclass_patterns') if settings else None,
 'unknown_severity_keys':sorted(set(severities)-p.KNOWN_CHECKS),'existing_ignored_checks':sorted(k for k,v in severities.items() if v=='ignore'),
 'current_static_unsupported_reason':reason,'stored_completeness':record.get('input_completeness'),'stored_predecessor_reason':record.get('unsupported_reason'),
 'terminal_geometry_multiset_sha256':digest(sorted([pad_geometry(pad,False) for pad in pads],key=canonical)),
 'footprint_local_pad_geometry_multiset_sha256':digest(sorted(fp_signatures)),
 'connectivity_wl3_screen_sha256':digest(sorted(colors.values())),
 'footprint_library_ids':dict(sorted(Counter(sx.unquote(fp[1]) for fp in fps).items()))}
 result.append(facts)
 groups={key:[] for key in ('terminal_geometry_multiset_sha256','footprint_local_pad_geometry_multiset_sha256','connectivity_wl3_screen_sha256')}
for key in groups:
 by=defaultdict(list)
 for row in result:by[row[key]].append(row['board'])
 groups[key]=[{'sha256':sha,'boards':names} for sha,names in by.items() if len(names)>1]
inputs=['evidence/placement-production-qualification-001/summary.json','evidence/licensed-acquisition-004/population-extension.json','evidence/licensed-acquisition-003/population-extension.json','evidence/licensed-closure-audit-003/audit.json','evidence/licensed-closure-audit-004/compact-records.json','evidence/paw3395-static-audit-001/audit.json','data/sources.json','autorouter/pipeline.py','autorouter/sexpr.py','autorouter/placement_clearance.py']
output={'schema':1,'scope':'Existing20development-exposed logical inputs, not every duplicate PCB path; offline static read only. No native/engine/network/Git.',
 'normalization':'Terminal geometry excludes pad names, net/pin labels and UUIDs; footprint local pad geometry retains pad numbers and relative coordinates but excludes absolute board placement. Connectivity screen is three-round colored bipartite footprint/net multigraph refinement with pad labels; removes refdes/netnames/UUIDs/routes. This is a coarse screen, not graph-isomorphism proof, rotation-invariant geometry proof or ancestry evidence.',
 'boards':result,'counts':{'population':20,'current_statically_eligible':sum(r['current_static_unsupported_reason'] is None for r in result),'native_new':0,'proven_independent_ancestry':0},
 'matching_screens':groups,'source_bindings':{path:hashlib.sha256(raw(path)).hexdigest() for path in inputs}}
(OUT/'facts.json').write_text(json.dumps(output,indent=2)+'\n')
for row in result:print(json.dumps({key:row[key] for key in ('board','format','footprints','pads','named_nets_used_by_pads','custom_pad_count','net_tie_footprints','current_static_unsupported_reason')}))
print(json.dumps({'matching_screens':groups,'counts':output['counts']}))
