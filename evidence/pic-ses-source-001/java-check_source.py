"""Source-only reverse comparison and captured API declaration check; no JVM."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;R=D.parents[1]
p=R/'experiments/pic_mixed_transport_probe_v1/MixedClassProbe.java'
new=p.read_text();old=(D/'MixedClassProbe-before-ses.java').read_text()
s=new.replace('/** Retained-route observation; optional bounded SES save, never routing or optimization. */','/** Original retained-route import only. No scheduler, autorouter, optimizer or SES writer. */')
a=s.index('  /** Separate route geometry');b=s.index('  static void run(',a);s=s[:a]+s[b:]
s=s.replace('boolean local250,Path sesPath)throws Exception{','boolean local250)throws Exception{')
s=s.replace('    if(sesPath!=null){var geometry=map();row.put("route_geometry_before_local",geometry);routeGeometry(board,geometry);}\n','')
s=s.replace('''    var state=map();row.put("state",state);observe(board,state);
    if(sesPath!=null){
      var geometry=map();row.put("route_geometry",geometry);routeGeometry(board,geometry);
      if(flag)writeSes(manager,board,sesPath,row);
    }
    row.put("status","observed");''','    var state=map();row.put("state",state);observe(board,state);row.put("status","observed");')
s=s.replace('if(args.length!=2&&(args.length!=3||!("local250".equals(args[2])||"local250-ses".equals(args[2]))))','if(args.length!=2&&(args.length!=3||!"local250".equals(args[2])))')
s=s.replace('"input DSN, output JSON and optional literal local250 or local250-ses required"','"input DSN, output JSON and optional literal local250 required"')
a=s.index('    Path sesPath=');b=s.index('    if(Files.isSymbolicLink(input)',a);s=s[:a]+s[b:]
s=s.replace('''try{run(raw,flag,row,local250,sesPath);}catch(Exception e){row.put("error",sesPath==null?e.getClass().getName()+": "+e.getMessage():boundedError(e));}
      if(sesPath!=null&&row.get("ses") instanceof Map<?,?> ses&&Boolean.TRUE.equals(ses.get("write_completed")))result.put("ses_executed",true);''','try{run(raw,flag,row,local250);}catch(Exception e){row.put("error",e.getClass().getName()+": "+e.getMessage());}')
assert s==old,'unexpected preexisting-path source change'
api={'.runs/pic-clearance-api-observation-001/javap.log':['public boolean saveAsSpecctraSessionSes(java.io.OutputStream, java.lang.String);'],'.runs/custom-pad-area-api-inspection-005/app.freerouting.board.trace.PolylineTrace.txt':['public int cornerCount();','public app.freerouting.geometry.planar.Polyline polyline();'],'.runs/custom-pad-area-api-inspection-005/app.freerouting.geometry.planar.Polyline.txt':['public app.freerouting.geometry.planar.Point corner(int);'],'.runs/custom-pad-area-api-inspection-002/app.freerouting.board.model.items.Trace.txt':['public int getHalfWidth();','public int getLayer();'],'.runs/custom-pad-area-api-inspection-002/app.freerouting.board.model.items.DrillItem.txt':['public app.freerouting.geometry.planar.Point getCenter();','public abstract app.freerouting.core.library.Padstack getPadstack();']}
for name,values in api.items():
 text=(R/name).read_text()
 for value in values:assert value in text,(name,value)
print(json.dumps({'scope':'Source reverse comparison and existing declarations only; not compile/runtime tests','old_modes_reverse_source_equal':True,'captured_required_apis_present':True,'java_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'compilation_executed':False,'jvm_executed':False},indent=2))
