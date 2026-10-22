"""Explicit10.0.7 same-BOARD observer/export for two frozen owned scenes only.

Bundled Native Python only. Positional CLI: RUNTIME MANIFEST_SHA PREPARATION
PREP_SHA CASE SOURCE SOURCE_SHA TRACKS(0|2) OUTPUT_JSON OUTPUT_DSN. Observation
is not acceptance; caller binds process success, code and final material. No save.
"""
import argparse,hashlib,json,os,re,sys
from pathlib import Path
PREPARATION_SHA='dd77c0a61885362ff25414c47f361486332aea70f7ae5e4e2c286f908fff36fb'
CASES=('back90-positive','back90-false_hull')
REPOSITORY=Path(__file__).resolve().parents[2]
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for name in ('runtime','manifest_sha','preparation','prep_sha','case','source','source_sha','tracks','output','dsn'):ap.add_argument(name)
 a=ap.parse_args()
 if a.case not in CASES or a.tracks not in ('0','2') or (a.tracks=='0' and a.case!='back90-positive') or a.prep_sha!=PREPARATION_SHA:raise ValueError('exact owned scene/preparation/track role required')
 if any(re.fullmatch('[0-9a-f]{64}',value) is None for value in (a.manifest_sha,a.prep_sha,a.source_sha)):raise ValueError('explicit SHA256 pins required')
 runtime=Path(a.runtime)
 if not runtime.is_absolute() or runtime.resolve()!=runtime:raise ValueError('canonical explicit runtime required')
 sys.dont_write_bytecode=True;sys.path[:0]=[str(runtime),str(REPOSITORY)]
 from autorouter import config as c,provenance as pv,placement_clearance as io,pipeline as p,sexpr as sx
 from autorouter import native as n
 import pcbnew,_pcbnew
 # Borrow only the explicit-layer geometry callback, never floor_context.collect.
 from experiments.pic_custom_native_controls_v1 import worker as geometry
 sys.path[:0]=[str(runtime)]
 if Path(c.__file__).resolve().parent.parent!=runtime or Path(n.__file__).resolve().parent.parent!=runtime:raise ValueError('runtime module origin differs')
 if c.NATIVE_VERSION!='10.0.7' or pcbnew.GetBuildVersion()!='10.0.7' or Path(sys.executable).resolve()!=c.PYTHON.resolve() or Path(_pcbnew.__file__).resolve()!=c.PCBNEW.resolve():raise ValueError('pinned10.0.7 Native Python/pcbnew identity differs')
 digest=lambda path:pv.file_digest(pv.canonical(Path(path)),128*1024**2)[0]
 manifest=runtime/'runtime-distribution.json';prep=pv.canonical(Path(a.preparation))
 if digest(manifest)!=a.manifest_sha or digest(prep)!=a.prep_sha:raise ValueError('runtime/preparation pin differs')
 plan=json.loads(pv.read_bytes(prep,1024**2),object_pairs_hook=pv._strict_object);rows=plan['cases']
 if plan['status']!='PREPARED_ONLY' or len(rows)!=2 or {r['case'] for r in rows}!=set(CASES):raise ValueError('two-scene frozen source census required')
 row=next(r for r in rows if r['case']==a.case);frozen=pv.canonical(Path(row['source']));expected={k:v['sha256'] for k,v in row['source_files'].items()}
 source,output,dsn=map(lambda x:pv.canonical(Path(x)),(a.source,a.output,a.dsn))
 if source.name!='pic_programmer.kicad_pcb' or output==dsn or output.parent!=dsn.parent or output.parent in (source.parent,frozen) or any(os.path.lexists(x) for x in (output,dsn)):raise ValueError('fresh separate run-local outputs required')
 def owner(path):
  info=path.stat()
  if not path.is_dir() or info.st_uid!=os.getuid():raise ValueError('owned real directory required')
  return info.st_dev,info.st_ino,info.st_uid
 owners={path:owner(path) for path in (source.parent,frozen,output.parent)}
 def inventory(path):return io.inventory(path,max_bytes=1024**2,max_files=4,max_entries=4)
 if inventory(frozen)!=expected:raise ValueError('frozen fixture changed')
 before=inventory(source.parent)
 if set(before)!=set(expected) or any(before[k]!=v for k,v in expected.items() if not k.endswith('.kicad_pcb')) or before[source.name]!=a.source_sha:raise ValueError('complete source copy or caller PCB hash differs')
 original=sx.parse(io.read_bytes(frozen/source.name).decode());task=sx.parse(io.read_bytes(source).decode());count=int(a.tracks)
 want=original if count==2 else p.routing_task(original,'whole_board_unlocked_routing')
 if task!=want or len(p.routes(task))!=count or any(x[0]!='segment' or p.locked(x) for x in p.routes(task)):raise ValueError('source is not exact frozen two-track scene or zero-reference-route task')
 if count==2 and before!=expected:raise ValueError('two-track scene bytes differ from frozen fixture')
 tools=c.current_native_selection();actual_tools={}
 for role,pin in tools['tools'].items():
  path=Path(pin['path']).resolve();observed,size=pv.file_digest(pv.canonical(path),128*1024**2)
  if observed!=pin['sha256'] or size!=pin['bytes']:raise ValueError('actual Native tool bytes differ')
  actual_tools[role]=dict(path=str(path),sha256=observed,bytes=size)
 code={path:digest(path) for path in (Path(__file__).resolve(),Path(geometry.__file__).resolve(),Path(n.__file__).resolve())}
 def fresh():
  if digest(manifest)!=a.manifest_sha or digest(prep)!=a.prep_sha or inventory(frozen)!=expected or inventory(source.parent)!=before:raise ValueError('runtime/fixture/source inputs changed')
  if any(owner(path)!=identity for path,identity in owners.items()) or any(digest(path)!=pin for path,pin in code.items()):raise ValueError('owned directory or observer implementation changed')
  if c.current_native_selection()!=tools or any(digest(Path(pin['path']))!=pin['sha256'] for pin in actual_tools.values()):raise ValueError('Native selection/tool changed')
 def routes(board):
  found=[]
  for track in board.GetTracks():
   if len(found)>=count or isinstance(track,(pcbnew.PCB_ARC,pcbnew.PCB_VIA)) or not isinstance(track,pcbnew.PCB_TRACK):raise ValueError('exact segment-only Native track census required')
   found.append(dict(kind='segment',uuid=str(track.m_Uuid.AsString()),net=str(track.GetNetname()),start_nm=geometry.point(track.GetStart()),end_nm=geometry.point(track.GetEnd()),width_nm=geometry.integer(track.GetWidth()),layer=str(pcbnew.LayerName(track.GetLayer()))))
  if len(found)!=count or any(x['width_nm']<=0 or x['net'] not in ('CONTACT','FOREIGN') or x['layer']!='B.Cu' for x in found):raise ValueError('Native track width/net/layer census differs')
  return sorted(found,key=lambda x:x['uuid'])
 fresh();board=pcbnew.LoadBoard(str(source))
 if not board or board.GetCopperLayerCount()!=2:raise ValueError('exact two-copper BOARD required')
 hashes=(before[source.name],before[source.with_suffix('.kicad_pro').name])
 mapping=n.netclasses(board,str(source),hashes,source_all_layers=True)
 first=geometry.observe(board,pcbnew);first_routes=routes(board)
 terminals=first['all_terminals'];wanted={(r['reference'],r['number'],r['net']) for r in row['terminals']}
 if len(terminals)!=4 or {(x['reference'],x['number'],x['net']) for x in terminals}!=wanted or len(first['all_footprints'])!=4 or len(first['pads'])!=2:raise ValueError('actual Native4terminal/4footprint/2custom census differs')
 if len(mapping['nets'])!=2 or {x['name'] for x in mapping['nets']}!={'CONTACT','FOREIGN'} or any(x['class']!='Default' or x['copper_pad_count']!=2 for x in mapping['nets']):raise ValueError('actual two-net Default scalar census differs')
 fresh()
 if os.path.lexists(dsn) or not pcbnew.ExportSpecctraDSN(board,str(dsn)):raise ValueError('fresh raw Native DSN export failed')
 raw=io.read_bytes(dsn,1024**2)
 if not raw:raise ValueError('empty Native DSN')
 second=geometry.observe(board,pcbnew);second_routes=routes(board);after_mapping=n.netclasses(board,str(source),hashes,source_all_layers=True)
 if first!=second or first_routes!=second_routes or mapping!=after_mapping:raise ValueError('export changed same-loaded geometry/routes/scalar context')
 fresh();after=inventory(source.parent)
 record=dict(context_schema=1,native_version='10.0.7',units='integer nanometres',mode='export',source=str(source),board_sha256=hashes[0],project_sha256=hashes[1],dsn_sha256=hashlib.sha256(raw).hexdigest(),
  input_hashes_before=before,input_hashes_after=after,observation_before_export=first,observation_after_export=second,same_loaded_board=True,board_saved=False,mapping=mapping,pads=terminals,routes=first_routes,nets=mapping['nets'],
  footprints=first['all_footprints'],actual_track_count=len(first_routes),expected_track_count=count,mapping_unchanged_after_export=True,case=a.case,preparation_sha256=a.prep_sha,frozen_source=str(frozen),frozen_source_hashes=expected,task_derivation='exact-whole-reference-routes-removed' if count==0 else 'exact-frozen-source',
  runtime=str(runtime),runtime_manifest_sha256=a.manifest_sha,actual_native_paths=actual_tools,actual_python=str(Path(sys.executable).resolve()),actual_pcbnew=str(Path(_pcbnew.__file__).resolve()),implementation_sha256={str(k):v for k,v in code.items()},
  routing_accepted=False,geometry_qualified=False,production_admitted=False,authority='Observation only; require the successful bound Native process and final input/material guards.')
 encoded=(json.dumps(record,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
 if len(encoded)>1024**2:raise ValueError('bounded context output required')
 fresh()
 with output.open('xb') as stream:stream.write(encoded)
 fresh()
 if io.read_bytes(output,1024**2)!=encoded or io.read_bytes(dsn,1024**2)!=raw:raise ValueError('context or raw DSN changed at publication')
if __name__=='__main__':main()
