from pathlib import Path
import copy,json,shutil,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,config as c,placement_clearance as pc
out=ROOT/'.runs/silkscreen-knockout-native-001';out.mkdir();start=time.monotonic();cpu0=time.process_time()+f.child_cpu();source=ROOT/'.runs/pour-only-native-probe-002/positive';before=pc.inventory(source)
uid='1c67fe84-58e4-4e84-95f6-6d6c28319869'
def text(tree):return next(x for x in sx.children(tree,'gr_text') if sx.unquote(sx.one(x,'uuid')[1])==uid)
original=sx.read(source/'usb_led.kicad_pcb');back=text(original)
p.save_json(out/'protocol.json',{'schema':1,'source_hashes':before,'tools':p.tool_manifest(),'controller_sha256':p.sha(Path(__file__)),'reuse_completed_back_serialization':'.runs/pour-only-native-probe-002/positive-refill','scope':'Derived front silk native save plus F/B native plots and nonknockout comparison; no native original stages rerun, engine, production pour admission or physical approval. All source text/effects/mirror/UUID attributes stay exact except explicit control layer/knockout edits.','wall_cpu_budget':90})
job=f.FloorJob(out/'job',90,lambda:max(0,min(90-(time.monotonic()-start),90-(time.process_time()+f.child_cpu()-cpu0))));record={'schema':1,'status':'failed','passed':False,'production_admission':False}
try:
 front=out/'front';shutil.copytree(source,front);board=front/'usb_led.kicad_pcb';tree=sx.read(board);sx.one(text(tree),'layer')[1]='"F.SilkS"';expected=copy.deepcopy(text(tree));sx.write(board,tree);p.check_edge_text_support(tree)
 job.native('front-roundtrip','roundtrip',board,out/'front-saved.kicad_pcb');assert text(sx.read(out/'front-saved.kicad_pcb'))==expected
 variants=[('front','F.SilkS',front),('back','B.SilkS',source)]
 off=out/'back-no-knockout';shutil.copytree(source,off);ob=off/'usb_led.kicad_pcb';ot=sx.read(ob);sx.one(text(ot),'layer').pop();sx.write(ob,ot);variants.append(('back-no-knockout','B.SilkS',off))
 plots={}
 for name,layer,base in variants:
  work=out/(name+'-plot-input');shutil.copytree(base,work);bb=pc.inventory(work);target=out/(name+'.svg')
  job.step(name+'-plot',[c.CLI,'pcb','export','svg','--mode-single','--layers',layer+',Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--output',target,work/'usb_led.kicad_pcb'])
  p.check_drc_project(bb,pc.inventory(work),'usb_led.kicad_pcb');assert target.stat().st_size>0;plots[name]={'sha256':p.sha(target),'bytes':target.stat().st_size,'layer':layer}
 assert plots['back']['sha256']!=plots['back-no-knockout']['sha256']
 record.update(status='observed',passed=True,front_saved_text_exact=True,back_saved_text_exact_from_completed_refill=True,plot_outputs=plots,visual_plot_inspection='pending; native plot generation and byte difference do not prove appearance')
except (Exception,KeyboardInterrupt) as exc:record.update(reason=type(exc).__name__+': '+str(exc))
record.update(steps=job.steps,source_unchanged=pc.inventory(source)==before,wall_seconds=time.monotonic()-start,full_cpu_seconds=time.process_time()+f.child_cpu()-cpu0)
record['within_budget']=max(record['wall_seconds'],record['full_cpu_seconds'])<=90
if not record['source_unchanged'] or not record['within_budget']:record['passed']=False
p.save_json(out/'result.json',record);print(json.dumps({k:record.get(k) for k in ('status','passed','reason','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
