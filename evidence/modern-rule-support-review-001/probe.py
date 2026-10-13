"""Owned pure parser/policy controls, no native/process/Git/network work."""
from pathlib import Path
import sys,json,copy,hashlib,ast
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
from autorouter import pipeline as p,sexpr as sx
SOURCE=ROOT/'autorouter/pipeline.py';TEST=ROOT/'tests/test_modern_rule_support.py'
def main():
 before={str(x.relative_to(ROOT)):p.sha(x) for x in (SOURCE,TEST)};rows=[];tree=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal']]];base={'board':{'design_settings':{'rule_severities':{'hole_to_hole':'warning','hole_near_hole':'error','hole_clearance':'error','clearance':'error','text_on_edge_cuts':'error'}}},'net_settings':{'classes':[]}}
 def check(name,extra,project=base,expect=True):
  folder=HERE/'cases'/name;folder.mkdir(parents=True);board=folder/'owned.kicad_pcb';sx.write(board,tree+extra);(folder/'owned.kicad_pro').write_text(json.dumps(project));hashes=p.tree_hash(folder)
  try:p.preflight(board);accepted=True;error=None
  except (p.Rejected,ValueError,TypeError) as exc:accepted=False;error=type(exc).__name__+': '+str(exc)
  assert accepted is expect,(name,accepted,error);assert p.tree_hash(folder)==hashes;rows.append({'case':name,'preflight_admitted':accepted,'reason':error,'files_unchanged':True})
 check('positive-off-edge-literal',[['gr_text','"Edge.Cuts"',['layer','"Dwgs.User"']],['footprint','"Owned"',['property','"Reference"','"Edge.Cuts"',['at','1','1'],['layer','"F.Fab"']],['property','"Sheetname"','"Edge.Cuts"']]])
 for key in ('gr_text','fp_text','gr_text_box','fp_text_box','property','dimension'):
  for severity in ('error','warning','ignore','missing'):
   project=copy.deepcopy(base)
   if severity=='missing':project['board']['design_settings']['rule_severities'].pop('text_on_edge_cuts')
   else:project['board']['design_settings']['rule_severities']['text_on_edge_cuts']=severity
   item=[key,'"label"',['at','1','1'],['layer','"Edge.Cuts"'],['hide']]
   check(key+'-'+severity,[['footprint','"Owned"',item]] if key in {'fp_text','fp_text_box','property'} else [item],project,False)
 check('nested-dimension-text',[['dimension',['layer','"Dwgs.User"'],['gr_text','"label"',['layer','"Edge.Cuts"']]]],expect=False)
 for name,fields in [('missing',[]),('duplicate',[['layer','"F.Fab"'],['layer','"Edge.Cuts"']]),('list-value',[['layer',['nested','Edge.Cuts']]]),('extra-value',[['layer','"F.Fab"','extra']]),('missing-value',[['layer']])]:check('malformed-'+name,[['gr_text','"label"',*fields]],expect=False)
 # Concrete grammar limits remain visible; native parsing/validation is not run here.
 for name,layer in [('empty','""'),('unknown','"MadeUp.Layer"'),('numeric','25')]:check('unqualified-layer-'+name,[['gr_text','"label"',['layer',layer]]],expect=True)
 for key,severity in [('hole_to_hole','ignore'),('hole_near_hole','warning'),('hole_clearance','warning'),('clearance','warning')]:
  project=copy.deepcopy(base);project['board']['design_settings']['rule_severities'][key]=severity;check('critical-'+key+'-'+severity,[],project,False)
 clean={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[]};assert p.native_accepted(clean)
 warning=dict(clean,warnings=1,findings=[{'type':'hole_to_hole','severity':'warning','items':[]}]);ignored=dict(clean,ignored_checks=[{'key':'hole_to_hole'}]);assert not p.native_accepted(warning) and not p.native_accepted(ignored)
 old=ast.parse((ROOT/'.runs/installation-010/checkout/autorouter/pipeline.py').read_text());current=ast.parse(SOURCE.read_text());same=[]
 for name in ('parse_report','native_rejection_reasons','native_accepted'):
  find=lambda t:next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
  assert ast.dump(find(old),include_attributes=False)==ast.dump(find(current),include_attributes=False);same.append(name)
 for name in ('CRITICAL_CHECKS','CRITICAL_FINDINGS'):
  find=lambda t:next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets))
  assert ast.dump(find(old),include_attributes=False)==ast.dump(find(current),include_attributes=False)
 identity=p._readback_live_identity((p,sx))
 with patch.object(p,'KNOWN_CHECKS',p.KNOWN_CHECKS|{'owned_review_policy_marker'}):assert p._readback_live_identity((p,sx))!=identity
 with patch.object(p,'check_edge_text_support',lambda tree:None):assert p._readback_live_identity((p,sx))!=identity
 assert p._readback_live_identity((p,sx))==identity
 assert all(p.sha(ROOT/n)==v for n,v in before.items())
 output={'schema':1,'status':'pure_controls_verified','source_sha256':before,'rows':rows,'critical_sets_and_native_acceptance_bodies_exact_to_prechange_installation':same,'live_cache_identity_changes_on_known_policy_or_guard_replacement':True,'live_cache_identity_restored':True,'native_field_dimension_or_layer_behavior_qualified':False,'native_subprocess_JVM_Git_network_executed':False,'source_files_unchanged':True,'grammar_observation':'Empty/unknown/numeric scalar layer values are admitted by static guard; actual native acceptance was not tested and is not claimed. The guard currently validates selector shape/uniqueness only, not layer-table membership.'};(HERE/'probe.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n');print(json.dumps({'controls':len(rows),'source_stable':True,'grammar_limit':output['grammar_observation']}))
if __name__=='__main__':main()
