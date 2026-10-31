"""Explicit comparison delivery software controls, never Native qualification.

Reuse the existing authored Native/plot worker seams. Central routing acceptance
and runtime identity plus the original Route semantic PRL seam are stubbed;
comparison policy, copies, export/plot process readback,
fresh-export validation logic, publication, budgets and PRL guards remain real.
No external process, Git, JVM or KiCad is executed.
"""
import copy
from contextlib import ExitStack
import json
import os
from pathlib import Path
import shutil
import tempfile
import stat
import unittest
from unittest.mock import patch

from autorouter import comparison as cmp, config as c, floor_route as f, handoff as h
from autorouter import pipeline as p, provenance as pv, review_export as e, review_view as view, sexpr as sx
from tests import test_review_export as export_fixture, test_review_view as plot_fixture

PROJECT=Path(__file__).resolve().parents[1]


class ComparisonDeliveryControls(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(dir=PROJECT/'.cache');self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();self.runtime=self.root/'runtime'
        self.parent=self.runtime/'.runs'/(cmp.PREFIX+'delivery-control');self.run=self.parent/'route'
        self.source=self.root/'source';self.source.mkdir();self.candidate=self.run/'candidate';self.candidate.mkdir(parents=True)
        tree=sx.parse('(kicad_pcb (version 20241229) (layers (0 "F.Cu" signal) (31 "B.Cu" signal)) (net 1 "SIG"))')
        self.protected=sx.parse('(segment (start 2 0) (end 3 0) (width 0.25) (layer "F.Cu") (net 1) (uuid "7ff4a242-b8a5-4397-9bc3-57db4d46ea38") (locked yes))')
        track=sx.parse('(segment (start 0 0) (end 1 0) (width 0.25) (layer "F.Cu") (net 1) (uuid "6e62cb01-0d92-4145-b651-83eb4e220594"))')
        for folder,routes in ((self.source,[self.protected]),(self.candidate,[self.protected,track])):
            sx.write(folder/'board.kicad_pcb',tree+routes)
            (folder/'board.kicad_pro').write_text('{}')
            (folder/'board.kicad_sch').write_text('(kicad_sch (version 20250114))')
            (folder/'board.kicad_prl').write_text('{"owned":"preserve exactly"}')
        (self.run/'code').mkdir();(self.runtime/'autorouter').mkdir()
        implementation={}
        for file in (PROJECT/'autorouter').glob('*.py'):
            shutil.copy2(file,self.run/'code'/file.name);shutil.copy2(file,self.runtime/'autorouter'/file.name)
            implementation['autorouter/'+file.name]=p.sha(file)
        shutil.copy2(PROJECT/'toolchain.lock.json',self.runtime/'toolchain.lock.json')
        args={};files={}
        for role in ('CLI','PYTHON','PCBNEW'):
            file=self.root/('authored-'+role);file.write_text('inert owned tool '+role)
            args[role]=file;files[str(file)]=p.sha(file)
        self.tools=dict(kicad='10.0.7',files=files,implementation_sha256=implementation,
            comparison_route_policy=cmp.POLICY,source_provenance=dict(kind=pv.KIND,native_version='10.0.7'),
            normal_drc_local_settings_policy=p.NORMAL_DRC_LOCAL_SETTINGS_POLICY,
            normal_native_export_alias_policy=p.NORMAL_NATIVE_EXPORT_ALIAS_POLICY)
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.multiple(c,ROOT=self.runtime,NATIVE_VERSION='10.0.7',**args))
        self.stack.enter_context(patch.object(c,'current_native_selection',return_value={'version':'10.0.7','tools':{}}))
        def tools():
            if any(p.sha(path)!=digest for path,digest in self.tools['files'].items()):raise p.Rejected('authored tool drift')
            return copy.deepcopy(self.tools)
        self.stack.enter_context(patch.object(p,'tool_manifest',side_effect=tools))
        cli=args['CLI'];pin=dict(path=str(cli),sha256=p.sha(cli),bytes=cli.stat().st_size)
        self.stack.enter_context(patch.object(p,'selected_tool_pins',return_value={'kicad_cli':pin}))
        self.context=cmp.Context(self.source/'board.kicad_pcb',self.run,'tuned',120,copy.deepcopy(self.tools),p.tree_hash(self.source))
        self.ctx={'comparison_context':self.context}
        self.warning={'type':'lib_footprint_mismatch','severity':'warning','description':'authored seam warning','items':[{'uuid':'warning-item','description':'pure seam'}]}
        self.native={'opens':0,'blocking':0,'warnings':1,'exclusions':0,'ignored_checks':[],'findings':[self.warning]}
        self.metrics=dict(version='10.0.7',pads=0,footprints=0,zones=0,vias=0,track_length_mm=2.,copper_layers=2)
        self.report=dict(schema=1,accepted=True,status='routing_accepted',source=str(self.context.source),
            source_hashes=p.tree_hash(self.source),candidate=str(self.candidate/'board.kicad_pcb'),
            candidate_sha256=p.sha(self.candidate/'board.kicad_pcb'),tools=copy.deepcopy(self.tools),
            adapter='both',engine_profile='tuned',baseline=p.engine_baseline('tuned','both'),scope='whole_board_unlocked_routing',
            scoring_variant=None,budget_seconds=120,cpu_budget_seconds=120,schematic_parity='checked by final native DRC',native=self.native,metrics=self.metrics)
        cmp.bind(self.run,self.report,self.context);self.receipt=self.run/'result.json';p.save_json(self.receipt,self.report)
        self.identity=dict(current=True,applied=False,candidate=self.report['candidate'],candidate_sha256=self.report['candidate_sha256'],production_admitted=False)
        def central(path,**kwargs):
            self.assertEqual(Path(path),self.receipt);self.assertEqual(kwargs,self.ctx)
            cmp.check_record(self.run,f.read_json(path),kwargs['comparison_context'])
            return copy.deepcopy(self.identity)
        self.central=self.stack.enter_context(patch.object(h,'check_result',side_effect=central))
        self.stack.enter_context(patch.object(p,'check_result',side_effect=central))
        self.real_semantic=p.check_experimental_local_settings
        def semantic(folder,data,nt):
            if Path(folder)==self.run:
                self.assertIsNone(nt);cmp.check_record(self.run,data,self.context)
            else:self.real_semantic(folder,data,nt)
        self.semantic=semantic
        self.stack.enter_context(patch.object(p,'check_experimental_local_settings',side_effect=semantic))
        self.native_mode='valid';self.calls=[];self.plot_calls=[]
        self.stack.enter_context(patch.object(e,'run',side_effect=self.native_run))
        self.stack.enter_context(patch.object(p,'run',side_effect=self.plot_run))
        self.review=self.parent/'review';self.choice=self.parent/'choice'/'choice.json';self.output=self.parent/'export'
        self.before=p.tree_hash(self.source)

    def native_run(self,argv,*,cwd,log,**kwargs):
        if self.native_mode=='cancel':
            # The real runner returns cleanup evidence before the Job raises.
            # A signal thrown inside a mock before that row cannot prove PRL
            # cleanup and is correctly a rejection instead of this control.
            self.calls.append((argv,kwargs));log.write_bytes(b'')
            return dict(argv=argv,cwd=str(cwd),log=str(log),log_bytes=0,log_truncated=False,
                status='cancelled',exit_code=-15,cleanup_complete=True,wall_seconds=0.,cpu_seconds=0.,monitor_cpu_seconds=0.)
        row=export_fixture.ExportControls.native_run(self,argv,cwd=cwd,log=log,**kwargs)
        if log.stem in ('refill-drc','final-drc'):
            path=Path(argv[argv.index('--output')+1]);data=f.read_json(path);data['kicad_version']='10.0.7';p.save_json(path,data)
            if '--schematic-parity' in argv:
                log.write_bytes(b'Found 0 schematic parity issues\n');row['log_bytes']=log.stat().st_size
        return row

    def plot_run(self,argv,*,cwd,log,**kwargs):
        worker=plot_fixture.PlotCopyControls.plot_worker(self,self.review/'before',self.review/'project',lambda *a:None,self.plot_calls)
        return worker(argv,cwd=cwd,log=log,**kwargs)

    def prepare(self,*,render=False,choice='accept'):
        result=h.review_copy(self.receipt,self.review,render=render,**self.ctx)
        h.review_choice(self.review/'review.json',self.choice.parent,choice,**self.ctx)
        return result

    def test_render_choice_fresh_export_and_readback_keep_nonadmitting_context(self):
        review=self.prepare(render=True);result=e.export(self.choice,self.output,120,**self.ctx)
        checked=e.check_export(self.output/'export.json',**self.ctx)
        for record in (review,review['preview'],f.read_json(self.choice),result,checked):
            self.assertFalse(record['production_admitted'])
            self.assertEqual(record['comparison_delivery_context'],cmp.delivery_record(self.context)['comparison_delivery_context'])
        self.assertEqual(len(self.plot_calls),4);self.assertEqual(len(self.calls),3)
        self.assertTrue(result['export_accepted']);self.assertTrue(checked['current'])
        self.assertEqual(review['budget_seconds'],h.REVIEW_SECONDS);self.assertEqual(result['budget_seconds'],120)
        self.assertIn(self.protected,p.routes(sx.read(Path(result['candidate']))))
        self.assertEqual(p.tree_hash(self.source),self.before)
        self.assertTrue(all('--experimental-native' not in argv for argv,_ in self.calls))
        self.assertTrue(all(call.kwargs==self.ctx for call in self.central.call_args_list))

    def test_application_context_never_enters_worker_kwargs_and_shape_is_required(self):
        self.assertEqual(h.delivery_kwargs(),{});self.assertEqual(h.application_kwargs(comparison_context=self.context),self.ctx)
        for bad in ({},object()):
            with self.assertRaises(p.Rejected):h.application_kwargs(comparison_context=bad)
        for args in ((object(),False),(None,True)):
            with self.assertRaises(p.Rejected):h.application_kwargs(*args,comparison_context=self.context)
        with self.assertRaises(p.Rejected):h.delivery_guards(self.receipt,self.report,object(),**self.ctx)
        route_only=cmp.Context(self.context.source,self.parent/'other','tuned',120,copy.deepcopy(self.tools),p.tree_hash(self.source))
        with self.assertRaises(p.Rejected):cmp.delivery_record(route_only)
        for path in (self.run/'review',self.root/'review',self.parent/'different-review'):
            with self.subTest(path=path),self.assertRaises(p.Rejected):h.review_copy(self.receipt,path,**self.ctx)
            self.assertFalse(path.exists())
        self.assertEqual(self.calls,[]);self.assertEqual(self.plot_calls,[])

    def test_default_and_wrong_callers_refuse_even_after_combined_marker_deletion(self):
        self.prepare();e.export(self.choice,self.output,**self.ctx)
        for path in (self.review/'review.json',self.choice,self.output/'export.json'):
            data=f.read_json(path);data.pop('comparison_delivery_context');data.pop('production_admitted');p.save_json(path,data)
        for call in (lambda:h.review_choice(self.review/'review.json',self.parent/'choice2','accept'),
                     lambda:e.bind(self.choice),lambda:e.check_export(self.output/'export.json')):
            with self.assertRaises(p.Rejected):call()
        other=cmp.Context(self.context.source,self.run,'standard',120,copy.deepcopy(self.tools),p.tree_hash(self.source))
        with self.assertRaises(p.Rejected):e.check_export(self.output/'export.json',comparison_context=other)

    def test_direct_helpers_require_the_same_context_and_no_alternate_contract(self):
        review=self.prepare(render=True);binding,report=e.bind(self.choice,**self.ctx)
        # Copied marked reports must refuse even outside the reserved directory,
        # before a low-level helper needs a complete ordinary binding.
        for call in (lambda:e.check_class_evidence(self.root/'ordinary',{}, {},report),
                     lambda:e.check_stage(self.root/'ordinary',{}, {},report,None,None,None)):
            with self.assertRaisesRegex(p.Rejected,'explicit caller context'):call()
        for call in (lambda:view.check_experimental_preview(self.review,review['preview']),
                     lambda:e.lineage(binding,report),
                     lambda:e.check_class_evidence(self.output/'validation',{},binding,report),
                     lambda:e.check_stage(self.output/'validation',{},binding,report,None,None,None)):
            with self.assertRaises(p.Rejected):call()
        data=cmp.delivery_record(self.context)
        with self.assertRaisesRegex(p.Rejected,'strategy or layer'):
            e.check_stage(self.output/'validation',data,binding,report,Path('alternate'),{},None,**self.ctx)
        missing=copy.deepcopy(review['preview']);missing.pop('comparison_delivery_context')
        with self.assertRaises(p.Rejected):view.check_experimental_preview(self.review,missing,**self.ctx)
        stripped=copy.deepcopy(review['preview']);stripped.pop('comparison_delivery_context');stripped.pop('production_admitted')
        with self.assertRaises(p.Rejected):view.check_experimental_preview(self.root/'ordinary-preview',stripped)
        stripped=copy.deepcopy(report);stripped.pop('comparison_route');stripped.pop('production_admitted')
        with self.assertRaisesRegex(p.Rejected,'render inputs require'):
            view.render(self.root/'ordinary-render',self.review/'before/board.kicad_pcb',self.review/'project/board.kicad_pcb',stripped,lambda:30,lambda:None)
        self.assertFalse((self.root/'ordinary-render').exists())

    def test_late_source_change_invalidates_review_publication(self):
        save=h.save_json;fired=False
        def publish(path,record):
            nonlocal fired
            save(path,record)
            if path.name=='review.json' and record.get('status')=='ready_for_manual_review' and not fired:
                fired=True;self.context.source.with_suffix('.kicad_pro').write_bytes(b'{"changed":true}')
        with patch.object(h,'save_json',side_effect=publish),self.assertRaises(p.Rejected):h.review_copy(self.receipt,self.review,**self.ctx)
        self.assertTrue(fired);self.assertNotEqual(f.read_json(self.review/'review.json')['status'],'ready_for_manual_review')

    def test_reject_invalid_fresh_native_and_cancel_never_export_positive(self):
        self.prepare(choice='reject')
        with self.assertRaises(p.Rejected):e.export(self.choice,self.output,**self.ctx)
        self.assertEqual(self.calls,[])

    def test_invalid_fresh_native_is_not_hidden_by_comparison_context(self):
        self.prepare();self.native_mode='invalid'
        with self.assertRaises(p.Rejected):e.export(self.choice,self.output,**self.ctx)
        self.assertFalse(f.read_json(self.output/'export.json')['export_accepted']);self.assertEqual(p.tree_hash(self.source),self.before)

    def test_cancellation_keeps_false_context_bound_export_receipt(self):
        self.prepare();self.native_mode='cancel'
        with self.assertRaises(p.Rejected):e.export(self.choice,self.output,**self.ctx)
        result=f.read_json(self.output/'export.json')
        self.assertEqual(result['status'],'cancelled');self.assertFalse(result['export_accepted']);self.assertFalse(result['production_admitted'])
        self.assertEqual(p.tree_hash(self.source),self.before)

    def test_export_budget_and_tool_drift_refuse_before_native(self):
        self.prepare()
        for seconds in (5,29,121,420,True):
            with self.subTest(seconds=seconds),self.assertRaises(p.Rejected):e.export(self.choice,self.output,seconds,**self.ctx)
            self.assertFalse(self.output.exists())
        c.CLI.write_bytes(b'drift')
        with self.assertRaises(p.Rejected):e.bind(self.choice,**self.ctx)
        self.assertEqual(self.calls,[])

    def test_flagged_schematic_class_scope_remains_unsupported(self):
        context=p.class_context_for_record(self.report,self.run,input_policy='native')
        self.assertIsNone(context)
        self.context.source.with_suffix('.kicad_sch').write_text('(kicad_sch (version 20250114) (netclass_flag))')
        with self.assertRaisesRegex(p.Rejected,'netclass_flag unsupported'):
            p.check_schematic_class_support(self.context.source,class_context=context)
        self.assertEqual(self.calls,[])

    @unittest.skipUnless(hasattr(os,'chflags') and hasattr(stat,'UF_IMMUTABLE'),'owned Mac metadata control')
    def test_last_tool_callback_cannot_hide_plot_or_additional_prl_flags(self):
        review=self.prepare(render=True);data=e.export(self.choice,self.output,**self.ctx)
        validation=self.output/'validation'
        targets=(self.review/'plot-work/before-F.Cu-input/board.kicad_prl',validation/'final-drc-input/board.kicad_prl')
        for target in targets:
            with self.subTest(target=target):
                state={'armed':False,'fired':False};manifest=p.tool_manifest
                def semantic(folder,record,nt):
                    self.semantic(folder,record,nt)
                    if Path(folder)==validation:state['armed']=True
                def tools():
                    value=manifest()
                    if state['armed'] and not state['fired']:
                        os.chflags(target,stat.UF_IMMUTABLE,follow_symlinks=False);state['fired']=True
                    return value
                try:
                    with patch.object(p,'check_experimental_local_settings',side_effect=semantic),patch.object(p,'tool_manifest',side_effect=tools),self.assertRaises(p.Rejected):
                        h.delivery_guards(self.receipt,self.report,None,review['preview'],self.review,
                            additional=((validation,data),),**self.ctx)
                    self.assertTrue(state['fired'])
                finally:
                    if target.exists() and target.stat().st_flags:os.chflags(target,0,follow_symlinks=False)
        # A retained-export return must not perform a fresh tool callback after
        # that common final metadata replay. The previous return expression did.
        target=targets[-1];state={'armed':False,'fired':False};guard=h.delivery_guards;manifest=p.tool_manifest
        def guarded(*args,**kwargs):
            guard(*args,**kwargs)
            if kwargs.get('additional'):state['armed']=True
        def tool_after_guard():
            value=manifest()
            if state['armed']:
                os.chflags(target,stat.UF_IMMUTABLE,follow_symlinks=False);state['fired']=True
            return value
        try:
            with patch.object(h,'delivery_guards',side_effect=guarded),patch.object(p,'tool_manifest',side_effect=tool_after_guard):
                self.assertTrue(e.check_export(self.output/'export.json',**self.ctx)['current'])
            self.assertTrue(state['armed']);self.assertFalse(state['fired'])
        finally:
            if target.exists() and target.stat().st_flags:os.chflags(target,0,follow_symlinks=False)


if __name__=='__main__':unittest.main()
