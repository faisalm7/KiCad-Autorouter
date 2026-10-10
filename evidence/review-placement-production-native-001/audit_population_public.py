"""Offline all16 reporting and selected-public byte audit; no native/engine work."""
from pathlib import Path
import hashlib,json
import audit_fixture as a
from autorouter import pipeline as p
ROOT,HERE=a.ROOT,a.HERE
NAMES=['placement-production-native-001','placement-production-controls-native-001','placement-production-controls-native-002','placement-production-cancellation-int-001','placement-production-cancellation-term-001','placement-production-receipt-controls-001','placement-production-multichannel-001']
def main():
    reportdir=ROOT/'evidence/placement-production-qualification-001';report_before=a.inventory(reportdir)
    summary=a.read(reportdir/'summary.json');prior=a.read(ROOT/'evidence/development-outcomes-003/index.json');extension=a.read(ROOT/'evidence/licensed-acquisition-003/population-extension.json')
    a.ok('reproducedsummary exactbytes',a.sha(reportdir/'summary.json')==a.sha(HERE/'reproduced-qualification-summary.json'))
    a.ok('immutable oldindex exactreviewedhash',summary['predecessors'][0]=={'path':'evidence/development-outcomes-003/index.json','sha256':'3f8005c3ba6a23954b21cb7fc055418ed3e103bbcc129f7e1aa78373e99a9023'} and a.sha(ROOT/summary['predecessors'][0]['path'])==summary['predecessors'][0]['sha256'])
    a.ok('exacttwoacquisition extension retained',a.sha(ROOT/summary['predecessors'][1]['path'])==summary['predecessors'][1]['sha256'] and len(extension['records'])==2)
    rows=summary['boards'];a.ok('sixteenuniqueboards allprior14 plus2 acquired',len(rows)==len(prior['boards'])+len(extension['records'])==16 and len({x['board'] for x in rows})==16)
    accepted_prior=set();accepted_sources=[];priorrefs={}
    for i,b in enumerate(prior['boards']):
        row=rows[i]
        a.ok('prior rowcomplete andunchanged '+str(i),row['prior_row']==i and all(row[k]==b.get(k) for k in ('board','source_sha256','input_completeness','static_eligible_at_recorded_gate','unsupported_reason')))
        accepted=False
        for ex in b['native_experiments']:
            rawpath=ROOT/ex['evidence'];expected=a.sha(rawpath);a.ok('prior recordedexperiment exactsha '+ex['evidence'],expected==ex['sha256']);priorrefs[str(rawpath)]=expected
            for arm in ex.get('arms',[]):
                if arm.get('accepted') is not True:continue
                experiment=a.read(rawpath);matches=[x for x in experiment['results'] if x['id']==arm['id']]
                a.ok('prior accepted row matchescanonical experiment '+arm['id'],len(matches)==1 and matches[0]['accepted'] is True and matches[0]['status']==arm['status'])
                match=matches[0];selected=match.get('selected') if arm['id']=='B2_portfolio' else match
                path=Path(selected['result']);raw=a.read(path);a.ok('prior actualaccepted productionreceipt '+arm['id'],a.sha(path)==selected['result_sha256'] and raw['accepted'] is True and raw['status']=='routing_accepted' and raw['source_hashes'][Path(raw['source']).name]==b['source_sha256'])
                verdict=p.check_result(path);a.ok('prior savednative positiveconsistency '+arm['id'],verdict['current'] is True and verdict['candidate_sha256']==raw['candidate_sha256'])
                accepted=True;accepted_sources.append({'board':b['board'],'arm':arm['id'],'receipt':str(path.relative_to(ROOT)),'receipt_sha256':a.sha(path),'candidate_sha256':raw['candidate_sha256']})
        if accepted:accepted_prior.add(b['board'])
        a.ok('prior acceptance deriveexact '+str(i),row['prior_production_accepted'] is accepted)
    a.ok('two priorproductionaccepted inputs no diagnosticincluded',len(accepted_prior)==2 and {Path(x).name for x in accepted_prior}=={'sonde xilinx.kicad_pcb','interf_u.kicad_pcb'})
    for row,old in zip(rows[14:],extension['records']):
        a.ok('acquired unsupportedrow exact '+row['board'],row['board']==old['source'] and row['source_sha256']==old['board_sha256'] and row['static_eligible_at_recorded_gate'] is old['routing_supported'] is False and row['unsupported_reason']==old['preflight_rejection'] and row['prior_row'] is None and row['production_accepted'] is False and row['prior_production_accepted'] is False)
    full=a.read(ROOT/'.runs/placement-production-multichannel-001/result.json');new=[r for r in rows if r['production_accepted']!=r['prior_production_accepted']]
    a.ok('sole gainedproductioninput multichannel matchedsource',len(new)==1 and new[0]['source_sha256']==full['source_hashes']['multichannel_mixer.kicad_pcb'] and new[0]['new_production_result']==summary['multichannel']['evidence'])
    for row in rows:a.ok('actualboard bytes '+row['board'],a.sha(ROOT/row['board'])==row['source_sha256'])
    a.ok('complete/incomplete countsderivedfrom retainedrecords',sum(r['input_completeness']=='manifested complete project' for r in rows)==7 and sum(r['input_completeness']!='manifested complete project' for r in rows)==9)
    a.ok('fullpopulationcounts precise unchangedstaticgate',summary['counts']=={'acquired_boards':16,'complete_inputs':7,'incomplete_inputs':9,'recorded_static_eligible':sum(r['static_eligible_at_recorded_gate'] for r in rows),'unsupported_or_incomplete':sum(not r['static_eligible_at_recorded_gate'] for r in rows),'inputs_with_actual_routing_attempts':3,'inputs_with_at_least_one_accepted_production_policy':3,'independent_families_established':None,'untouched_final_evaluation':0} and sum(r['production_accepted'] for r in rows)==3 and sum(r['static_eligible_at_recorded_gate'] for r in rows)==3)
    for name,run in [('fixture','placement-production-native-001'),('multichannel','placement-production-multichannel-001')]:
        data=a.read(ROOT/'.runs'/run/'result.json');obs=summary[name]
        a.ok(name+': exactfresh record costsandnativeoutcomes',obs['evidence']=={'path':'.runs/'+run+'/result.json','sha256':a.sha(ROOT/'.runs'/run/'result.json')} and obs['git_head']==data['tools']['git_head'] and obs['accepted'] is True and obs['candidate_sha256']==data['candidate_sha256'] and obs['metrics']==data['metrics'] and obs['native']=={k:data['native'][k] for k in ('opens','blocking','warnings','exclusions')} and obs['stored_wall_seconds']==data['wall_seconds'] and obs['stored_total_cpu_seconds']==data['total_cpu_seconds'] and obs['budget_seconds']==data['budget_seconds'])
    referenced=[summary['native_controls']['evidence'],summary['failed_pre_native_attempt'],summary['receipt_controls'],*[x['evidence'] for x in summary['cancellations']]]
    for ref in referenced:a.ok('eachactualcontrolref bound '+ref['path'],a.sha(ROOT/ref['path'])==ref['sha256'])
    receipt=a.read(ROOT/summary['receipt_controls']['path']);a.ok('receiptcontrols strictlypure13passed',receipt['status']=='passed' and receipt['passed'] is True and len(receipt['cases'])==13 and all(x['passed'] is True for x in receipt['cases']) and receipt['native_executed'] is False and receipt['engine_executed'] is False)
    public=[];count=0;size=0;omitted=0;manifests={}
    generated={'kicad-config','kicad-cache','kicad-documents','engine-config','tmp'}
    for name in NAMES:
        selected=ROOT/'evidence'/name;raw=ROOT/'.runs'/name;initial=a.inventory(selected);rawinitial=a.inventory(raw);rows_manifest=a.read(selected/'files.json');listed={r['path'] for r in rows_manifest};a.ok(name+': publicmanifest unique',len(listed)==len(rows_manifest))
        for row in rows_manifest:
            rel=Path(row['path']);a.ok(name+': exactselectedrawbytes '+row['path'],not rel.is_absolute() and '..' not in rel.parts and (selected/rel).stat().st_size==(raw/rel).stat().st_size==row['bytes'] and a.sha(selected/rel)==a.sha(raw/rel)==row['sha256'])
            count+=1;size+=row['bytes']
        extras={'files.json','PUBLIC_SCOPE.md'};omitted_set=set()
        if (selected/'omitted-source-dependencies.json').exists():
            extras.add('omitted-source-dependencies.json')
            for row in a.read(selected/'omitted-source-dependencies.json'):
                rel=row['path'];omitted_set.add(rel);omitted+=1
                a.ok(name+': exact declaredomission '+rel,rel not in listed and not (selected/rel).exists() and (raw/rel).stat().st_size==row['bytes'] and a.sha(raw/rel)==row['sha256'])
        a.ok(name+': everypublicpayload listed',set(initial)==listed|extras)
        missing=set(rawinitial)-listed-omitted_set
        if name=='placement-production-receipt-controls-001':
            known_cases={x['case'] for x in receipt['cases']}
            a.ok(name+': omittedonlydeclared disposablecopies orprogress',all(rel=='progress.json' or (len(Path(rel).parts)>3 and Path(rel).parts[0]=='cases' and Path(rel).parts[1] in known_cases and Path(rel).parts[2] in ('run','source')) for rel in missing))
            a.ok(name+': exactpublicsubset limitation','Full disposable source/run copies remain local' in (selected/'PUBLIC_SCOPE.md').read_text())
        else:
            a.ok(name+': remainingomissions onlydeclared generateddirs',all(any(part in generated for part in Path(rel).parts) for rel in missing))
            a.ok(name+': publicsubset not falselyrelocatedrunnable','not a relocated runnable receipt' in (selected/'PUBLIC_SCOPE.md').read_text())
        a.ok(name+': originalandselected trees unchanged',a.inventory(selected)==initial and a.inventory(raw)==rawinitial)
        manifests[name]=a.sha(selected/'files.json');public.append({'run':name,'selected_files':len(rows_manifest),'selected_bytes':sum(r['bytes'] for r in rows_manifest),'omitted_dependency_files':len(omitted_set),'generated_directory_files_omitted':len(missing),'files_manifest_sha256':manifests[name]})
    a.ok('reporterandpublic summaryunchangedduringaudit',report_before==a.inventory(reportdir) and all(a.sha(Path(k))==v for k,v in priorrefs.items()))
    result={'schema':1,'audit_passed':True,'check_count':len(a.CHECKS),'checks':a.CHECKS,'native_engine_network_executed':False,'generator_sha256':a.sha(reportdir/'generate.py'),'summary_sha256':a.sha(reportdir/'summary.json'),'reproduced_summary_sha256':a.sha(HERE/'reproduced-qualification-summary.json'),'counts':summary['counts'],'prior_production_acceptance':accepted_sources,'public_copies':public,'selected_files_total':count,'selected_bytes_total':size,'omitted_dependency_files':omitted,'scope':'Actual frozen records verified, not a general adversarial reporter proof. All16 retained;3 accepted inputs across differentpolicies, no pooledsuccessrate. Publicsubsets not standalone relocatable receipts; complete local originals remain backup responsibility.'}
    with (HERE/'population-public-audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','prior_production_acceptance','public_copies')},indent=2))
if __name__=='__main__':main()
