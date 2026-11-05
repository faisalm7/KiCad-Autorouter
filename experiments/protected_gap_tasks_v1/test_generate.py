"""Tiny owned geometric controls; these are not real-board/Native evidence."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import pipeline as p, placement_clearance as pc, sexpr as sx
from experiments.protected_gap_tasks_v1 import generate as g


def fixture():
    tree = ['kicad_pcb', ['version', '20260206'], ['generator', 'owned-test'],
        ['net', '0', '""'], *[['net', str(i), json.dumps(name)] for i, name in enumerate(('A','B','C','D','E'),1)],
        ['zone', ['net','0'], ['fill', ['thermal_gap','0.3']], ['filled_polygon', ['layer','"F.Cu"']]],
        ['gr_line', ['start','0','0'], ['end','10','0'], ['layer','"Edge.Cuts"']]]
    for i in range(1,6):
        tree.append(['segment', ['start', str(i), '1'], ['end', str(i), '2'], ['width','0.3'],
            ['layer','"F.Cu"'], ['net',str(i)], ['uuid',json.dumps('route-'+str(i))]])
    return tree


class ProtectedGapControls(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve();self.source=self.root/'original';self.source.mkdir()
        self.board=self.source/'fixture.kicad_pcb';sx.write(self.board,fixture())
        for name, raw in {'fixture.kicad_pro':b'{"owned_fixture":true}\n',
                          'fixture.kicad_sch':b'(kicad_sch (owned "fixture"))\n',
                          'fixture.kicad_prl':b'{"owned_settings":true}\n',
                          'README.md':b'Owned tiny source notice; not a real PCB.\n'}.items():
            (self.source/name).write_bytes(raw)
        self.before=pc.inventory(self.source);self.output=self.root/'task'

    def test_fixed_seed_half_mask_is_deterministic_independent_of_route_order(self):
        original=fixture();unchanged=copy.deepcopy(original)
        task,facts=g.derive(original);again,other=g.derive(original)
        self.assertEqual((task,facts),(again,other));self.assertEqual(original,unchanged)
        expected=sorted(('A','B','C','D','E'),key=lambda name:(hashlib.sha256((g.SEED+'\0'+name).encode()).hexdigest(),name))
        self.assertEqual(g.SEED,'protected-gap-v1-20261105')
        self.assertEqual(facts['eligible_groups_ranked'],['D','E','C','A','B'])
        self.assertEqual(facts['removed_groups'],expected[:3]);self.assertEqual(facts['retained_route_count'],2)
        reordered=copy.deepcopy(original);routes=p.routes(reordered)
        reordered[:]=[row for row in reordered if row not in routes]+list(reversed(routes))
        self.assertEqual(g.derive(reordered)[1]['removed_groups'],facts['removed_groups'])
        self.assertEqual(p.immutable(task),p.immutable(original))
        self.assertFalse(sx.children(sx.one(task,'zone'),'filled_polygon'))

    def test_entire_original_locked_group_is_excluded_and_locks_are_preserved(self):
        original=fixture();locked=p.routes(original)[0];locked.append(['locked','yes'])
        sibling=sx.clone(locked);sibling.pop();sibling[1]=['start','9','9'];original.append(sibling)
        task,facts=g.derive(original)
        self.assertEqual(facts['excluded_original_locked_groups'],['A'])
        self.assertNotIn('A',facts['removed_groups']);self.assertIn(locked,p.routes(task))
        self.assertTrue(all(p.locked(row) for row in p.routes(task)))
        new=sx.clone(sibling);new.append(['locked','yes']);self.assertIn(new,p.routes(task))

    def test_no_eligible_group_ambiguous_lock_net_and_arc_refuse(self):
        original=fixture()
        for row in p.routes(original):row.append(['locked','yes'])
        with self.assertRaisesRegex(ValueError,'no eligible'):g.derive(original)
        for change in ('zero','duplicate','lock','conflicting-lock','arc'):
            original=fixture();row=p.routes(original)[0]
            if change=='zero':sx.one(row,'net')[1]='0'
            elif change=='duplicate':row.append(['net','2'])
            elif change=='lock':row.append(['locked','no'])
            elif change=='conflicting-lock':row.extend([['locked','yes'],['locked','no']])
            else:row[0]='arc'
            with self.subTest(change=change),self.assertRaises(ValueError):g.derive(original)

    def test_no_protected_routing_remaining_is_not_a_protected_gap_task(self):
        original=fixture();routes=p.routes(original)
        original[:]=[row for row in original if row not in routes]+[routes[0]]
        with self.assertRaisesRegex(ValueError,'requires retained protected routing'):
            g.derive(original)

    def test_fresh_copy_preserves_source_sidecars_and_keeps_provenance_outside_inputs(self):
        facts=g.generate(self.board,self.output,self.before)
        self.assertEqual(pc.inventory(self.source),self.before)
        after=pc.inventory(self.output/'project')
        self.assertEqual(set(after),set(self.before))
        for name in self.before:
            if name!=self.board.name:self.assertEqual(after[name],self.before[name])
        task,mask=g.derive(sx.read(self.board))
        self.assertEqual(sx.read(self.output/'project'/self.board.name),task)
        self.assertEqual(facts['removed_groups'],mask['removed_groups'])
        self.assertEqual(json.loads((self.output/'provenance.json').read_text()),facts)
        self.assertFalse((self.output/'project'/'provenance.json').exists())
        self.assertFalse(facts['ready_for_comparison']);self.assertFalse(facts['Native_executed'])
        self.assertFalse(facts['reference_route_geometry_in_algorithm_inputs'])

    def test_existing_symlink_overlapping_and_wrong_inventory_outputs_refuse(self):
        self.output.mkdir();(self.output/'retain').write_bytes(b'unfinished owned work')
        with self.assertRaises(p.Rejected):g.generate(self.board,self.output,self.before)
        self.assertEqual((self.output/'retain').read_bytes(),b'unfinished owned work')
        link=self.root/'link';link.symlink_to(self.source,target_is_directory=True)
        for source,output in ((link/self.board.name,self.root/'new'),(self.board,link/'new'),
                              (self.board,self.source/'new'),(self.board,self.root/'wrong')):
            hashes={} if output.name=='wrong' else self.before
            with self.subTest(source=source,output=output),self.assertRaises(p.Rejected):g.generate(source,output,hashes)
        self.assertFalse((self.root/'wrong').exists())

    def test_source_reference_backup_and_descendant_symlink_are_not_inputs(self):
        for name in ('saved.kicad_pcb','saved.kicad_pcb-bak','source.zip'):
            extra=self.source/name;extra.write_bytes(b'owned reference-like payload')
            with self.subTest(name=name),self.assertRaisesRegex(p.Rejected,'reference routing/archives'):
                g.generate(self.board,self.output,pc.inventory(self.source))
            self.assertFalse(self.output.exists());extra.unlink()
        (self.source/'linked-notice').symlink_to(self.source/'README.md')
        with self.assertRaises(p.Rejected):g.generate(self.board,self.output,self.before)

    def test_headroom_refusal_occurs_before_copy_and_changed_sidecar_retains_failed_output(self):
        with patch.object(g,'require_headroom',side_effect=RuntimeError('insufficient forecast')):
            with self.assertRaisesRegex(RuntimeError,'insufficient forecast'):g.generate(self.board,self.output,self.before)
        self.assertFalse(self.output.exists())
        original_copy=pc.copy_project
        def corrupt(*args,**kwargs):
            copied=original_copy(*args,**kwargs)
            (args[1]/'fixture.kicad_pro').write_bytes(b'changed sidecar')
            return copied
        with patch.object(pc,'copy_project',side_effect=corrupt):
            with self.assertRaisesRegex(p.Rejected,'sidecar'):g.generate(self.board,self.output,self.before)
        self.assertTrue(self.output.is_dir());self.assertFalse((self.output/'provenance.json').exists())
        self.assertEqual(pc.inventory(self.source),self.before)


if __name__=='__main__':unittest.main()
