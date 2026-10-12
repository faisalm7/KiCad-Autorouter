"""Pure geometry/receipt/fake-native lifecycle controls; never calls native tools."""
import copy,json,os,signal,tempfile,unittest
from pathlib import Path
from unittest import mock
import driver as d,fixture as fx,checks

def raw(case):
    r={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':fx.BOARD,'included_severities':['error','warning','exclusion'],'violations':[{'type':'lib_footprint_issues','severity':'warning','description':'Fixed library warning','items':[{'uuid':fx.FP}]}],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[{'key':x}for x in checks.IGNORED]}
    if case=='mismatched_custom_field':r['schematic_parity']=[{'type':checks.KIND,'severity':'warning','description':f"Field '{fx.FIELD}' differs (PCB: '{fx.MISMATCH}', Schematic: '{fx.MATCH}')",'items':[{'uuid':fx.FP}]}]
    return r

def log(r):return 'Found 1 violations\nFound 0 unconnected items\nFound '+str(len(r['schematic_parity']))+' schematic parity issues\n'

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board=d.io.read_bytes(d.SOURCE);cls.sch=d.io.read_bytes(d.SOURCE.parent/fx.SCH);cls.original=d.sx.parse(cls.board.decode())
        cls.hashes,cls.total=d.source_binding()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=d.HERE,prefix='pure-');self.addCleanup(self.temp.cleanup);self.tmp=Path(self.temp.name)
    def result(self,case,r=None,text=None,base=None):
        r=raw(case)if r is None else r
        if base is None and case!='original_parity':base=checks.predicate('original_parity',raw('original_parity'),log(raw('original_parity')))['ordinary_fingerprint']
        return checks.predicate(case,r,log(r)if text is None else text,base)
    def test_parser_body_exact_production_parity(self):d.parser_parity()
    def test_actual_original_census_and_exact_three_deltas(self):
        original=fx.prepare(self.board,self.sch,'original_parity');self.assertEqual(original,{fx.BOARD:self.board,fx.SCH:self.sch})
        positive=fx.prepare(self.board,self.sch,'matched_custom_field');negative=fx.prepare(self.board,self.sch,'mismatched_custom_field')
        self.assertEqual(negative[fx.SCH],positive[fx.SCH]);self.assertEqual(negative[fx.BOARD].replace(fx.MISMATCH.encode(),fx.MATCH.encode()),positive[fx.BOARD])
        for filename,kind,identity,raw0 in [(fx.BOARD,'footprint',fx.FP,self.board),(fx.SCH,'symbol',fx.SYMBOL,self.sch)]:
            tree=d.sx.parse(positive[filename].decode());node=next(n for n in d.sx.children(tree,kind)if fx.uid(n)==identity);field=fx.properties(node)[fx.FIELD];self.assertEqual(d.sx.one(field,'hide'),['hide','yes']);node.remove(field);self.assertEqual(tree,d.sx.parse(raw0.decode()))
    def test_duplicate_reference_uuid_field_and_wrong_source_reject(self):
        for mode in ('duplicate','ref','uuid','preexisting'):
            tree=copy.deepcopy(self.original);node=fx.target(tree,'footprint',fx.FP)
            if mode=='duplicate':tree.append(copy.deepcopy(node))
            elif mode=='ref':fx.properties(node)['Reference'][2]='"R2"'
            elif mode=='uuid':d.sx.one(node,'uuid')[1]='"wrong"'
            else:node.append(['property','"'+fx.FIELD+'"','"already"'])
            with self.assertRaises((ValueError,KeyError)):fx.prepare(d.sx.dump(tree).encode(),self.sch,'matched_custom_field')
    def test_hierarchy_and_nonhidden_presentation_reject(self):
        tree=d.sx.parse(self.sch.decode());node=fx.target(tree,'symbol',fx.SYMBOL);d.sx.one(fx.properties(node)['Description'],'hide')[1]='no'
        with self.assertRaises(ValueError):fx.prepare(self.board,d.sx.dump(tree).encode(),'matched_custom_field')
        tree=d.sx.parse(self.sch.decode());d.sx.one(tree,'uuid')[1]='"wrong"'
        with self.assertRaises(ValueError):fx.prepare(self.board,d.sx.dump(tree).encode(),'matched_custom_field')
    def test_all_three_expected_predicates(self):
        for case in fx.CASES:self.assertTrue(self.result(case)['predicate_met'])
    def test_no_parity_log_wrong_count_and_skip_reject(self):
        for text in ('Found 0 violations\n','Found 1 schematic parity issues\n','Found 0 schematic parity issues\nFound 0 schematic parity issues\n','No netlist provided, skipping schematic parity tests.\nFound 0 schematic parity issues\n'):
            with self.assertRaises(ValueError):self.result('original_parity',text=text)
    def test_missing_negative_and_positive_unexpected_finding_fail(self):
        r=raw('mismatched_custom_field');r['schematic_parity']=[];self.assertFalse(self.result('mismatched_custom_field',r)['predicate_met'])
        self.assertFalse(self.result('original_parity',raw('mismatched_custom_field'))['predicate_met'])
    def test_exact_target_type_severity_uuid_value_and_exclusion(self):
        for mode in ('type','severity','uuid','field','pcb','sch','description_suffix','excluded','extra_item','extra_finding'):
            r=raw('mismatched_custom_field');row=r['schematic_parity'][0]
            if mode in ('type','severity'):row[mode]='wrong'
            elif mode=='uuid':row['items'][0]['uuid']='wrong'
            elif mode=='field':row['description']=row['description'].replace(fx.FIELD,fx.FIELD+'Other')
            elif mode=='pcb':row['description']=row['description'].replace(fx.MISMATCH,fx.MATCH)
            elif mode=='sch':row['description']=row['description'].replace(fx.MATCH,'different')
            elif mode=='description_suffix':row['description']+=' stale'
            elif mode=='excluded':row['excluded']=True
            elif mode=='extra_item':row['items'].append({'uuid':'other'})
            else:r['schematic_parity'].append(copy.deepcopy(row))
            try:self.assertFalse(self.result('mismatched_custom_field',r)['predicate_met'])
            except d.p.Rejected:pass
    def test_excluded_bool_schema_unknown_ignored_and_omitted_severity_reject(self):
        for mode in ('excluded','ignored','severity'):
            r=raw('original_parity')
            if mode=='excluded':r['violations'][0]['excluded']=1
            elif mode=='ignored':r['ignored_checks'].append({'key':'unknown'})
            else:r['included_severities']=['warning']
            with self.assertRaises((ValueError,d.p.Rejected)):self.result('original_parity',r)
    def test_no_relaxation_for_other_findings_or_ordinary_change(self):
        for mode in ('unknown','error','open','changed_description'):
            r=raw('matched_custom_field')
            if mode=='unknown':r['violations'][0]['type']='unknown'
            elif mode=='error':r['violations'][0]['severity']='error'
            elif mode=='open':r['unconnected_items']=[{'type':'unconnected_items','severity':'error','items':[]}]
            else:r['violations'][0]['description']='different'
            with self.assertRaises(ValueError):self.result('matched_custom_field',r)
    def test_finding_order_normalized_without_losing_full_records(self):
        original=raw('original_parity');other=copy.deepcopy(original['violations'][0]);other['items'][0]['uuid']='another';other['description']='Other fixed warning';original['violations'].append(other)
        baseline=self.result('original_parity',original)['ordinary_fingerprint']
        changed=copy.deepcopy(original);changed['violations'].reverse();changed['ignored_checks'].reverse();changed['included_severities'].reverse()
        self.assertTrue(self.result('matched_custom_field',changed,base=baseline)['predicate_met'])
        for mode in ('extra','missing','description','uuid','position','excluded'):
            bad=copy.deepcopy(changed)
            if mode=='extra':bad['violations'].append(copy.deepcopy(bad['violations'][0]))
            elif mode=='missing':bad['violations'].pop()
            elif mode=='description':bad['violations'][0]['description']+=' altered'
            elif mode=='uuid':bad['violations'][0]['items'][0]['uuid']='wrong'
            elif mode=='position':bad['violations'][0]['items'][0]['pos']={'x':1,'y':2}
            else:bad['violations'][0]['excluded']=False
            with self.assertRaises(ValueError):self.result('matched_custom_field',bad,base=baseline)
    def test_process_log_and_guard_mismatch_rejected(self):
        result,_,out=self.flow();self.assertTrue(result['controls_passed']);row=result['cases'][0];caseout=out/row['case']
        class Job:pass
        job=Job();job.out=caseout;job.captured=dict(row['stage_evidence']);job.steps=copy.deepcopy(row['steps'])
        path=caseout/'parity-drc-process.json';old=d.read(path)
        for key,value in [('log_bytes',123),('log_truncated',True),('resource_guards',{}),('cpu_seconds',float('inf')),('sampled_peak_group_rss_bytes',3*1024**3),('sampled_peak_workdir_bytes',d.LIMIT+1)]:
            bad=copy.deepcopy(old);bad[key]=value
            if value==float('inf'):
                path.write_text(json.dumps(bad))
            else:d.p.save_json(path,bad)
            job.steps=[bad];job.captured['parity-drc-process.json']=d.digest(path);row['stage_evidence']=dict(job.captured)
            with self.assertRaises((ValueError,d.p.Rejected)):d.validate_case(job,row,None)
        d.p.save_json(path,old)
    def test_bounded_strict_json_duplicate_and_nonfinite(self):
        p=self.tmp/'x.json'
        for text in ('{"a":1,"a":2}','{"a":NaN}'):
            p.write_text(text)
            with self.assertRaises((ValueError,d.p.Rejected)):d.read(p)
    def test_exact_argv_has_parity_no_save_or_dsn(self):
        argv=d.drc_argv(self.tmp);self.assertIn('--schematic-parity',argv);self.assertNotIn('--save-board',argv);self.assertEqual(argv[:3],d.f.SANDBOX);self.assertEqual(argv[-1],str(self.tmp/'project'/fx.BOARD))
    def test_case_colliding_inventory_names_reject(self):
        with mock.patch.object(d.io,'inventory',return_value={'A':'a','a':'b'}):
            with self.assertRaises(d.p.Rejected):d.inventory(self.tmp)
    def test_run_requires_explicit_flag(self):
        with self.assertRaises(d.p.Rejected):d.experiment(self.tmp/'run')

    def flow(self,mode=None):
        out=self.tmp/'run';calls=[];real_owned=d.owned;real_save=d.p.save_json;real_pred=checks.predicate;original_validate=d.validate_case
        runtime={'git_head':'a'*40,'implementation_sha256':{},'files':{}};witness={'head':'a'*40,'HEAD_sha256':'b'*64,'ref_sha256':'c'*64}
        def owned(p,output=False):
            if output:
                if Path(p).exists():raise d.p.Rejected('fresh output')
                return Path(p)
            return real_owned(p)
        def snapshot(path,*_):
            (path/'code').mkdir();(path/'code'/'marker').write_text('frozen');return {}
        def fake(argv,*,cwd,log:Path,**kwargs):
            case=cwd.name;calls.append(case);r=raw(case)
            if mode=='baseline_failure'and case==fx.CASES[0]:r['schematic_parity']=raw(fx.CASES[-1])['schematic_parity']
            if mode=='matched_failure'and case==fx.CASES[1]:r['schematic_parity']=raw(fx.CASES[-1])['schematic_parity']
            if mode=='native_crash':raise RuntimeError('fake native launch failure')
            if mode=='cancel_native':raise KeyboardInterrupt
            d.p.save_json(cwd/'parity-drc.json',r);log.write_text(globals()['log'](r))
            return {'argv':argv,'cwd':str(cwd),'log':str(log),'log_bytes':log.stat().st_size,'log_truncated':False,'exit_code':5,'status':'nonzero_exit','cleanup_complete':True,'cpu_seconds':.01,'monitor_cpu_seconds':0,'wall_seconds':.01,'pid':999,'sampled_peak_group_rss_bytes':1000,'sampled_peak_workdir_bytes':1000,'resource_guards':{'max_group_rss_bytes':2*1024**3,'max_workdir_bytes':d.LIMIT,'os_enforced':False}}
        def pred(case,r,log,base=None):
            got=real_pred(case,r,log,base)
            if mode=='raw_after_parse'and case==fx.CASES[0]and len(calls)==1:
                path=out/case/'parity-drc.json';bad=d.read(path);bad['date']='late mutation';real_save(path,bad)
            return got
        def save(path,value):
            result=real_save(path,value)
            if path==out/'summary.json'and value.get('controls_passed')is True:
                if mode=='after_write_interrupt':raise KeyboardInterrupt
                if mode=='after_write_error':raise OSError('publication error')
                if mode=='record_tamper':value['cases'][0]['control_passed']=False
            return result
        with mock.patch.object(d,'owned',owned),mock.patch.object(d,'snapshot',snapshot),mock.patch.object(d,'head_witness',return_value=witness),mock.patch.object(d.p,'tool_manifest',return_value=runtime),mock.patch.object(d.p,'check_storage'),mock.patch.object(d,'run',fake),mock.patch.object(d.p,'save_json',save),mock.patch.object(checks,'predicate',pred):
            result=d.experiment(out,run_native=True)
        return result,calls,out
    def test_whole_fake_native_positive_all_three(self):
        result,calls,out=self.flow();self.assertTrue(result['controls_passed']);self.assertEqual(calls,list(fx.CASES));self.assertEqual(d.read(out/'summary.json'),result);self.assertFalse(result['routing_accepted']);self.assertEqual(d.inventory(d.SOURCE.parent),self.hashes)
    def test_prerequisite_original_failure_stops_and_preserves_rows(self):
        result,calls,_=self.flow('baseline_failure');self.assertFalse(result['controls_passed']);self.assertEqual(calls,[fx.CASES[0]]);self.assertEqual([r['status']for r in result['cases'][1:]],['not_attempted','not_attempted'])
    def test_prerequisite_matched_failure_stops_negative(self):
        result,calls,_=self.flow('matched_failure');self.assertFalse(result['controls_passed']);self.assertEqual(calls,list(fx.CASES[:2]));self.assertEqual(result['cases'][-1]['status'],'not_attempted')
    def test_raw_after_parse_invalidates(self):
        result,calls,_=self.flow('raw_after_parse');self.assertFalse(result['controls_passed']);self.assertEqual(calls,[fx.CASES[0]])
    def test_crash_retains_all_outcomes_no_later_attempt(self):
        result,calls,_=self.flow('native_crash');self.assertFalse(result['controls_passed']);self.assertEqual(calls,[fx.CASES[0]]);self.assertIn('fake native launch failure',result['cases'][0]['error'])
    def test_native_cancellation_no_later_attempt(self):
        result,calls,_=self.flow('cancel_native');self.assertFalse(result['controls_passed']);self.assertEqual(calls,[fx.CASES[0]]);self.assertEqual(result['status'],'cancelled')
    def test_positive_publication_interrupt_vacates(self):
        result,_,out=self.flow('after_write_interrupt');self.assertFalse(result['controls_passed']);self.assertEqual(result['status'],'cancelled');self.assertFalse(d.read(out/'summary.json')['controls_passed']);self.assertTrue(list(out.glob('invalidated-*')))
    def test_positive_publication_ordinary_error_vacates(self):
        result,_,out=self.flow('after_write_error');self.assertFalse(result['controls_passed']);self.assertFalse(d.read(out/'summary.json')['controls_passed']);self.assertTrue(list(out.glob('invalidated-*')))
    def test_in_memory_record_tamper_invalidates(self):
        result,_,out=self.flow('record_tamper');self.assertFalse(result['controls_passed']);self.assertFalse(d.read(out/'summary.json')['controls_passed'])
    def publication(self,mode):
        out=self.tmp/'pub';out.mkdir();record={'status':'controls_passed','controls_passed':True,**d.FALSE_CLAIMS};clock=[1]
        def size(path):
            if mode=='summary_tamper':d.p.save_json(out/'summary.json',{**record,'controls_passed':False})
            if mode=='deadline':clock[0]=0
            if mode=='interrupt':raise KeyboardInterrupt
            return 0
        with mock.patch.object(d,'size',size):result=d.publish(out,record,lambda:None,lambda:None,lambda:clock[0])
        self.assertFalse(result['controls_passed']);self.assertFalse(d.read(out/'summary.json')['controls_passed'])
    def test_final_size_tamper_rejected(self):self.publication('summary_tamper')
    def test_final_size_budget_exhaustion_rejected(self):self.publication('deadline')
    def test_final_size_interrupt_rejected(self):self.publication('interrupt')
    def test_self_int_term_scoped_handlers_restore(self):
        for sig in (signal.SIGINT,signal.SIGTERM):
            before={s:signal.getsignal(s)for s in (signal.SIGINT,signal.SIGTERM)}
            def experiment(*_,**__):os.kill(os.getpid(),sig)
            with mock.patch.object(d,'experiment',experiment):
                with self.assertRaises(KeyboardInterrupt):d.main(['--run-native','--output',str(self.tmp/'unused')])
            self.assertEqual({s:signal.getsignal(s)for s in before},before)
if __name__=='__main__':unittest.main()
