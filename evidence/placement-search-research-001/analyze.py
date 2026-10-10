"""Read-only stored search/transport diagnosis; no native/engine execution."""
from pathlib import Path
from decimal import Decimal
from collections import Counter
import sys,json,re,hashlib,zipfile
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx,board_floor as g
HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-routing-pair-001/arm-1';read=lambda x:json.loads(x.read_text())
def nm(x,m=1000000):
 v=Decimal(x)*m;assert v==v.to_integral_value();return int(v)
def main():
 before=p.tree_hash(RUN);data=read(RUN/'result.json');candidate=Path(data['candidate']);board=sx.read(candidate);source=Path(data['source']);source_before=p.tree_hash(source.parent);original=sx.read(source);report=read(RUN/'final-drc.json');ses=sx.read(RUN/'routes.ses');routes=sx.one(ses,'routes');network=sx.one(routes,'network_out');assert sx.one(routes,'resolution')==['resolution','um','10']
 _,resolve=g.source_net_identity(board)
 canon=lambda net,layer,width,a,b:(net,layer,width,*sorted((tuple(a),tuple(b))))
 expected=[];ses_stats={}
 for net in network[1:]:
  name=sx.unquote(net[1]);counts={'segments':0,'vias':0}
  for wire in sx.children(net,'wire'):
   path=sx.one(wire,'path');layer=sx.unquote(path[1]);width=nm(path[2],100);points=[[nm(path[i],100),-nm(path[i+1],100)] for i in range(3,len(path),2)]
   for a,b in zip(points,points[1:]):expected.append(canon(name,layer,width,a,b));counts['segments']+=1
  counts['vias']=len(sx.children(net,'via'));ses_stats[name]=counts
 actual=[];byuuid={}
 for r in p.routes(board):
  uid=sx.unquote(sx.one(r,'uuid')[1]);name=resolve(sx.one(r,'net'));byuuid[uid]={'kind':r[0],'net':name,'node':r}
  if r[0]=='segment':actual.append(canon(name,sx.unquote(sx.one(r,'layer')[1]),nm(sx.one(r,'width')[1]),[nm(v) for v in sx.one(r,'start')[1:]],[nm(v) for v in sx.one(r,'end')[1:]]))
 assert Counter(actual)==Counter(expected),'SES to final segment multiset mismatch'
 source_pads={}
 for fp in sx.children(original,'footprint'):
  ref=next(sx.unquote(x[2]) for x in sx.children(fp,'property') if sx.unquote(x[1])=='Reference')
  for pad in sx.children(fp,'pad'):
   source_pads[sx.unquote(sx.one(pad,'uuid')[1])]={'kind':'pad','reference':ref,'number':sx.unquote(pad[1]),'net':sx.unquote(sx.one(pad,'net')[-1]) if sx.one(pad,'net') else '', 'size_mm':sx.one(pad,'size')[1:]}
 items=[];counts=Counter()
 for finding in report['unconnected_items']:
  endpoints=[]
  for item in finding['items']:
   uid=item['uuid'];entry=byuuid.get(uid,source_pads.get(uid));assert entry is not None
   endpoints.append({'uuid':uid,'description':item['description'],'native_position_mm':item['pos'],**{k:v for k,v in entry.items() if k!='node'}})
  assert len({x['net'] for x in endpoints})==1
  name=endpoints[0]['net'];counts[name]+=1;items.append({'net':name,'endpoints':endpoints,'ses_geometry_present':all(x['kind']=='pad' or x['uuid'] in byuuid for x in endpoints)})
 log=(RUN/'engine.log').read_text();passes=[{'pass':int(m[0]),'wall_seconds':float(m[1]),'score':float(m[2]),'unrouted':int(m[3]),'violations':int(m[4])} for m in re.findall(r'Auto-routing pass #(\d+).*?completed in ([0-9.]+) seconds with score ([0-9.]+) \((\d+) unrouted and (\d+) violations\)',log)]
 assert len(passes)==19 and passes[8]['unrouted']==9 and passes[-1]['unrouted']==24
 assert 'since pass #9. Stopping the auto-router after 19 passes (9 items still unconnected)' in log
 probe_path=ROOT/'.runs/baseline-strength-review-001/prototype/profile-probe/actual-settings.json';probe=read(probe_path);selected=[x for x in probe['profiles'] if x['name'] in ('via_default_remaining_120_strict_True','via_low_remaining_120_strict_True','via_high_remaining_120_strict_True')]
 assert len(selected)==3
 cli_evidence=[]
 for x in selected:
  cli_evidence.append({'profile':x['name'],'argv':[v for v in x['argv'] if v.startswith('--router.scoring.')],'effective_settings':{k:v for k,v in x['effective_requested_settings'].items() if k.startswith('router.scoring.')}})
 jar=ROOT/'.tools/freerouting-2.5.0.jar';lock=read(ROOT/'toolchain.lock.json');assert p.sha(jar)==lock['tools']['freerouting']['sha256']
 jar_fields={}
 with zipfile.ZipFile(jar) as z:
  for name,tokens in {'app/freerouting/settings/RoutingCostSettings.class':['via_costs','plane_via_costs','start_ripup_costs'],'app/freerouting/autoroute/pipeline/BatchAutorouter.class':['STAGNATION_PASS_LIMIT','STAGNATION_SCORE_THRESHOLD'],'app/freerouting/settings/sources/CliSettings.class':['router.','applyRouterSetting'],'app/freerouting/util/ReflectionUtil.class':['setFieldValue','getFieldByNameOrSerializedName']}.items():
   raw=z.read(name);assert all(t.encode() in raw for t in tokens);jar_fields[name]={'class_sha256':hashlib.sha256(raw).hexdigest(),'constant_pool_tokens_observed':tokens}
 assert p.tree_hash(RUN)==before and p.tree_hash(source.parent)==source_before
 result={'schema':1,'native_or_engine_executed':False,'input_sha256':{str(path.relative_to(ROOT)):p.sha(path) for path in (RUN/'result.json',candidate,RUN/'routes.ses',RUN/'final-drc.json',RUN/'engine.log',source,jar,probe_path)},'original_inputs_unchanged':True,'native_opens':len(items),'native_open_net_counts':dict(counts),'open_items':items,'ses_to_final_segment_multiset_equal':True,'ses_segments':len(expected),'candidate_segments':len(actual),'ses_per_open_net':{k:ses_stats[k] for k in counts},'passes':passes,'last_log_airline_net':'GND','log_report_caveat':'Pinned source builds current-board report before best-history restoration. It is not the final native open list.','existing_actual_jar_cost_probe':cli_evidence,'read_only_jar_field_evidence':jar_fields,'no_cli_execution_in_this_review':True,'limitations':['Direct segment transport equality does not itself prove electrical connectivity; fresh stored native report is authoritative.','Nine internal incompletes versus eight native opens need not have identical semantics; no one-to-one attribution is proved.','Class constant strings support field existence, not newly observed CLI runtime application; only cached via-cost settings have actual-JAR merge evidence.']}
 with (HERE/'analysis.json').open('x') as s:json.dump(result,s,indent=2);s.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','open_items','passes','read_only_jar_field_evidence')},indent=2))
if __name__=='__main__':main()
