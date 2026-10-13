"""Authored, in-memory controls; never import or execute real KiCad/JVM/Git.

The before-fix bodies are explicitly reconstructed snapshots. Native geometry
is a controlled shim, so these are binding regressions, not native proof.
No production files, input boards or test temporaries are written.
"""
from pathlib import Path
import copy, hashlib, json, sys, types
from unittest import mock

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,pour_rule_area as policy
from autorouter import pour_rule_area_native as native,floor_context as context
from autorouter import floor_route as f,placement_clearance as pc,sexpr as sx

def digest(raw):return hashlib.sha256(raw).hexdigest()
def reconstructed(name,globals):
    namespace=dict(globals);namespace['__name__']='owned_pure_reconstruction'
    exec(compile((HERE/name).read_text(),str(HERE/name),'exec'),namespace)
    return namespace

aid='00000000-0000-0000-0000-000000000001'
zid='00000000-0000-0000-0000-000000000002'
area=['zone',['net','0'],['net_name','""'],['uuid','"'+aid+'"'],['layer','"F.Cu"'],
    ['keepout',*[[flag,'not_allowed' if flag=='copperpour' else 'allowed'] for flag in policy.FLAGS]],
    ['polygon',['pts',['xy','10','10'],['xy','15','10'],['xy','15','15'],['xy','10','15']]]]
zone=['zone',['net','1'],['uuid','"'+zid+'"'],['layer','"F.Cu"'],
    ['filled_polygon',['layer','"F.Cu"'],['pts',['xy','20','20'],['xy','21','20'],['xy','21','21'],['xy','20','21']]]]
tree=['kicad_pcb',['layers',['0','"F.Cu"','signal'],['31','"B.Cu"','signal']],area,zone]
good=(sx.dump(tree)+'\n').encode();changed=copy.deepcopy(tree)
sx.one(sx.one(sx.children(changed,'zone')[1],'filled_polygon'),'pts')[1:]=[
    ['xy','11','11'],['xy','12','11'],['xy','12','12'],['xy','11','12']]
bad=(sx.dump(changed)+'\n').encode();project_bytes=b'{}'
source=Path('/__owned_pure_binding_control__/owned.kicad_pcb')
project=source.with_suffix('.kicad_pro')
areas=policy.qualify(tree)

class UID:
    def __init__(self,value):self.value=value
    def AsString(self):return self.value
class Poly:
    def __init__(self,other=None):self.count=1
    def OutlineCount(self):return self.count
    def BooleanIntersection(self,outline):self.count=0
class Zone:
    def __init__(self,value):self.m_Uuid=UID(value)
    def IsOnLayer(self,layer):return layer==0
    def GetFilledPolysList(self,layer):return Poly()
    def Outline(self):return Poly()
class Board:
    def Zones(self):return [Zone(aid),Zone(zid)]

shim=types.SimpleNamespace(SHAPE_POLY_SET=Poly,F_Cu=0,B_Cu=31,GetBuildVersion=lambda:'10.0.0')
observed=[{key:value for key,value in row.items() if key!='source_zone_ast_sha256'} for row in areas]
before=(digest(good),digest(project_bytes))
old_native=reconstructed('reconstructed_pre_fix_native_audit.py',{})['audit']
results=[]
for label,raw in [('matched_positive',good),('changed_during_load',bad)]:
    with mock.patch.dict(sys.modules,{'pcbnew':shim}),mock.patch.object(Path,'read_bytes',lambda self:raw if self==source else project_bytes),mock.patch.object(context,'observe_areas',lambda *args:{'footprint_zone_count':0,'zones':observed}):
        if label=='changed_during_load':
            record=old_native(Board(),source)
            assert record['passed'] is True and record['board_sha256']==digest(bad)
            results.append({'control':'reconstructed_pre_fix_stale_board','outcome':'accepted_bad_bytes','expected':True})
        try:record=native.audit(Board(),source,before)
        except ValueError as exc:
            assert label=='changed_during_load' and str(exc)=='source changed across native board load'
            results.append({'control':label,'outcome':'rejected','reason':str(exc),'expected':True})
        else:
            assert label=='matched_positive' and record['passed'] is True
            results.append({'control':label,'outcome':'accepted','expected':True})

# Isolate only stock-input lineage. Source/preserved-candidate, native audit and
# saved-refill stage seams are controlled positives; no routing acceptance.
directory=Path('/__owned_pure_stock_lineage_control__');candidate=directory/'candidate'/'owned.kicad_pcb'
raw_dsn=b'(pcb "authored" (structure (keepout "" (polygon F.Cu 0 10000 -10000 15000 -10000 15000 -15000 10000 -15000 10000 -10000))))\n'
corrected_dsn=b'(pcb "authored" (structure))\n'
old_stock=reconstructed('reconstructed_pre_fix_check_pour_evidence.py',vars(p))['check_pour_evidence']
for scope in ('whole_board_unlocked_routing','selected_nets'):
    for label,engine_input,extra,fn in [
        ('reconstructed_pre_fix_stock_downgrade',corrected_dsn,{},old_stock),
        ('stock_positive',raw_dsn,{},p.check_pour_evidence),
        ('stock_corrected_input',corrected_dsn,{},p.check_pour_evidence),
        ('stock_adapter_marker',raw_dsn,{'adapter_transformations':{}},p.check_pour_evidence)]:
        data={'adapter':'none','baseline':'B0_stock','scope':scope,
            'steps':[{'name':'engine','cwd':str(directory)}],
            'source_hashes':{'owned.kicad_pcb':digest(good)},**extra}
        def read(path,*args,**kwargs):
            path=Path(path)
            if path==directory/'native.dsn':return raw_dsn
            if path in (directory/'task.dsn',directory/'routing-scope-input.dsn'):return engine_input
            if path in (directory/'pour-before-refill.kicad_pcb',candidate):return good
            raise AssertionError('unplanned controlled read: '+str(path))
        with mock.patch.object(pc,'read_bytes',read),mock.patch.object(p,'sha',lambda path:digest(good)),mock.patch.dict(old_stock.__globals__,{'sha':lambda path:digest(good)}),mock.patch.object(f,'read_json',lambda path:{}),mock.patch.object(policy,'verify_native_record',lambda *args:True),mock.patch.object(f,'process_check',lambda *args,**kwargs:None),mock.patch.object(f,'check_drc_stage',lambda *args,**kwargs:None),mock.patch.object(sx,'read',lambda path:copy.deepcopy(tree)):
            try:fn(directory,data,tree,candidate)
            except p.Rejected as exc:
                assert label in ('stock_corrected_input','stock_adapter_marker')
                results.append({'control':label,'scope':scope,'outcome':'rejected','reason':str(exc),'expected':True})
            else:
                assert label in ('stock_positive','reconstructed_pre_fix_stock_downgrade')
                results.append({'control':label,'scope':scope,'outcome':'accepted','expected':True})

large=['kicad_pcb']
large.extend(['zone',['net','1'],['uuid','"00000000-0000-0000-0000-'+str(n).zfill(12)+'"']] for n in range(20))
assert policy.qualify(large)==[]
results.append({'control':'twenty_ordinary_zones_no_pour','outcome':'compatible','expected':True})
print(json.dumps({'schema':1,'pure_binding_controls_only':True,'real_native_jvm_git_network_execution':False,
    'production_edits':False,'results':results,'control_count':len(results)},indent=2))
