"""Constructed choice-publication seams; no actual Native/GUI approval claim."""
import json
import os
import stat
import sys
import unittest
from unittest.mock import patch
from autorouter import handoff as h, strategy as s, local_settings as local
from autorouter.pipeline import Rejected,sha
from tests import test_handoff_search_choice as fixture


class Native7ChoiceBoundaryTests(unittest.TestCase):
    def write(self):fixture.Controls.write(self)

    def setUp(self):
        fixture.Controls.setUp(self)
        native=self.run/'final-drc-input';native.mkdir();self.prl=native/'board.kicad_prl';self.prl.write_text('{}')
        fixture.Controls.review(self);self.check.reset_mock()

    def choose(self,choice='accept',name='choice'):
        return h.review_choice(self.root/'review/review.json',self.root/name,choice)

    def recognized(self,*_):
        self.assertEqual(self.check.call_count,1)
        return {'source-derived':'constructed boundary only'}

    def guarded(self,*args,**kwargs):kwargs['material']()

    def test_both_choices_keep_two_full_reads_and_postwrite_metadata(self):
        for choice in ('accept','reject'):
            with self.subTest(choice=choice):
                self.check.reset_mock();events=[];target=self.root/choice
                def guard(*args,**kwargs):
                    kwargs['material']();events.append((target/'choice.json').exists())
                with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=guard):
                    result=self.choose(choice,choice)
                self.assertEqual(self.check.call_count,2);self.assertTrue(events[-1])
                self.assertTrue(result['choice_recorded']);self.assertEqual(result['choice'],choice)
                self.assertFalse(result['routing_accepted']);self.assertFalse(result['applied'])
                self.assertEqual(h.SECONDS,30)

    def test_ordinary_choice_retains_three_full_reads(self):
        self.choose();self.assertEqual(self.check.call_count,3)

    def test_failed_first_full_read_never_selects_narrower_path(self):
        self.check.return_value['current']=False
        with patch.object(s,'native7_parent') as recognize:
            with self.assertRaises(Rejected):self.choose()
            recognize.assert_not_called()
        self.assertFalse((self.root/'choice').exists())

    def test_stale_second_full_read_does_not_record_choice(self):
        self.check.side_effect=[dict(self.check.return_value),Rejected('stale parent')]
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=self.guarded):
            with self.assertRaisesRegex(Rejected,'stale parent'):self.choose()
        self.assertFalse(json.loads((self.root/'choice/choice.json').read_text())['choice_recorded'])

    def test_accept_lock_still_refuses_before_selection_but_reject_remains(self):
        lock=self.root/'review/project/~board.kicad_pro.lck';lock.write_text('owned lock control')
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=self.guarded):
            with self.assertRaises(h.ReviewProjectOpen):self.choose()
            self.assertEqual(self.check.call_count,0)
            self.assertEqual(self.choose('reject','reject')['choice'],'reject')

    def test_source_mutation_after_choice_write_is_rejected(self):
        save=h.save_json
        def changed(path,record):
            save(path,record)
            if record['status']=='disposition_recorded':(self.source/'board.kicad_dru').write_text('relaxed')
        with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=self.guarded),patch.object(h,'save_json',side_effect=changed):
            with self.assertRaises(Rejected):self.choose()
        self.assertEqual(self.check.call_count,2)
        self.assertFalse(json.loads((self.root/'choice/choice.json').read_text())['choice_recorded'])

    @unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac flags required')
    def test_postwrite_flag_only_change_still_hits_final_shared_guard(self):
        prl=self.prl;before={prl.name:sha(prl)}
        event=dict(policy=local.POLICY,present=True,path=str(prl),sha256=before[prl.name],flags_before=0,flags_during=stat.UF_IMMUTABLE,flags_restored=True,bytes_unchanged=True)
        def guard(*a,**kw):kw['material']();local.check_preserved(prl,before,event)
        save=h.save_json
        def changed(path,record):
            save(path,record)
            if record['status']=='disposition_recorded':os.chflags(prl,stat.UF_IMMUTABLE,follow_symlinks=False)
        try:
            with patch.object(s,'native7_parent',side_effect=self.recognized),patch.object(h,'delivery_guards',side_effect=guard),patch.object(h,'save_json',side_effect=changed):
                with self.assertRaisesRegex(Rejected,'flags'):self.choose()
            self.assertFalse(json.loads((self.root/'choice/choice.json').read_text())['choice_recorded'])
        finally:os.chflags(prl,0,follow_symlinks=False)
