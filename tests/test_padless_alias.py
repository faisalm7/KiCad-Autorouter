"""Authored source/DSN alias controls; no Native export or routing claim."""
import copy
import hashlib
import json
import unittest
from autorouter import adapter,padless_alias as a,sexpr as sx


def board(*,duplicate=True):
    tree=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','jumper']]]
    for i in (1,2):
        tree.append(['footprint','"OwnedArtwork"',['uuid',json.dumps(f'00000000-0000-4000-8000-{i:012d}')],
            ['property','"Reference"',json.dumps('ART' if duplicate else 'ART'+str(i)),['layer','"F.Fab"']],
            ['layer','"F.Cu"'],['at',str(i),'0'],['attr','board_only']])
    tree.append(['footprint','"OwnedConnector"',['uuid','"00000000-0000-4000-8000-000000000003"'],
        ['property','"Reference"','"J1"',['layer','"F.SilkS"']],['layer','"F.Cu"'],['at','0','0'],
        ['pad','"1"','thru_hole','circle'],['pad','"2"','thru_hole','circle']])
    return tree


def raw(tree):return (sx.dump(tree)+'\n').encode()


def dsn(source,binding):
    names={row['uuid']:row['alias'] for row in binding['aliases']}
    images=[['image','"art"'],['image','"connector"',['pin','"1"','"P"','0','0'],['pin','"2"','"P"','1','0']]]
    artwork=['component','"art"'];connector=['component','"connector"']
    for row in binding['footprints']:
        place=['place',json.dumps(names.get(row['uuid'],row['reference'])),'0','0','front','0']
        (artwork if row['reference']!='J1' else connector).append(place)
    tree=['pcb','"owned.dsn"',['parser',['string_quote',adapter._QUOTE_SENTINEL]],['unit','um'],['resolution','um','10'],
        ['placement',artwork,connector],['library',*images],['network',['net','"A"',['pins','"J1-1"']],['net','"B"',['pins','"J1-2"']]]]
    return tree


class PadlessAliasControls(unittest.TestCase):
    def test_duplicate_padless_plan_is_bound_bijective_and_nonmutating(self):
        source=raw(board());before=bytes(source);binding=a.plan(source)
        self.assertEqual(source,before);self.assertEqual(binding['source_sha256'],hashlib.sha256(source).hexdigest())
        self.assertEqual(binding['policy'],a.POLICY);self.assertEqual(len(binding['aliases']),2)
        self.assertEqual(len({row['alias'] for row in binding['aliases']}),2)
        self.assertTrue(all(row['pad_count']==0 and row['reference']=='ART' for row in binding['aliases']))
        self.assertFalse(binding['routing_accepted']);a.require_plan(source,binding)
        other=a.plan(source,'B');self.assertEqual(other['source_sha256'],binding['source_sha256'])
        self.assertTrue({row['alias'] for row in other['aliases']}.isdisjoint(row['alias'] for row in binding['aliases']))
        tree=dsn(source,binding);before_tree=copy.deepcopy(tree)
        parsed,slots=a.dsn_aliases(adapter._dump_dsn(tree).encode(),source,binding)
        self.assertEqual(tree,before_tree);self.assertEqual(parsed,tree);self.assertEqual(len(slots),2)

    def test_zero_alias_is_explicit_and_ordinary_electrical_footprints_remain(self):
        source=raw(board(duplicate=False));binding=a.plan(source)
        self.assertEqual(binding['aliases'],[]);self.assertEqual(len(binding['footprints']),3)
        self.assertEqual(next(row['pad_count'] for row in binding['footprints'] if row['reference']=='J1'),2)
        a.require_plan(source,binding)
        _,slots=a.dsn_aliases(adapter._dump_dsn(dsn(source,binding)).encode(),source,binding)
        self.assertEqual(slots,[])
        # Eligibility/version/pad/rule admission belongs to the caller. With no
        # duplicates this helper does not create aliases or normalize legacy data.
        legacy=board(duplicate=False);sx.one(legacy,'version')[1]='20240108'
        self.assertEqual(a.plan(raw(legacy))['aliases'],[])

    def test_stale_source_policy_namespace_or_alias_record_cannot_be_reused(self):
        source=raw(board());binding=a.plan(source)
        for mutation in ('source','policy','namespace','missing','record','forged-zero'):
            with self.subTest(mutation=mutation):
                captured=source;changed=copy.deepcopy(binding)
                if mutation=='source':captured=source.replace(b'20260206',b'20241229')
                elif mutation=='policy':changed['policy']='old-policy'
                elif mutation=='namespace':changed['namespace']='B'
                elif mutation=='missing':changed['aliases'].pop()
                elif mutation=='record':changed['aliases'][0]['footprint_ast_sha256']='0'*64
                else:changed['aliases']=[]
                with self.assertRaises(ValueError):a.require_plan(captured,changed)

    def test_electrical_mixed_missing_board_only_model_and_copper_reference_refuse(self):
        for mutation in ('one-pad','all-electrical','board-only','model','copper-reference','unknown-reference-layer','reference-knockout','missing-reference','duplicate-reference-property','empty-reference','duplicate-uuid'):
            with self.subTest(mutation=mutation):
                tree=board();fps=sx.children(tree,'footprint');fp=fps[0];reference=a.reference(fp)
                if mutation=='one-pad':fp.append(['pad','"1"','smd','rect'])
                elif mutation=='all-electrical':
                    for item in fps[:2]:item.append(['pad','"1"','smd','rect'])
                elif mutation=='board-only':fp.remove(sx.one(fp,'attr'))
                elif mutation=='model':fp.append(['model','"owned.step"'])
                elif mutation=='copper-reference':sx.one(reference,'layer')[1]='"F.Cu"'
                elif mutation=='unknown-reference-layer':sx.one(reference,'layer')[1]='"Margin"'
                elif mutation=='reference-knockout':sx.one(reference,'layer').append('knockout')
                elif mutation=='missing-reference':fp.remove(reference)
                elif mutation=='duplicate-reference-property':fp.append(copy.deepcopy(reference))
                elif mutation=='empty-reference':
                    for item in fps[:2]:a.reference(item)[2]='""'
                else:sx.one(fps[1],'uuid')[1]=sx.one(fp,'uuid')[1]
                with self.assertRaises(ValueError):a.plan(raw(tree))

    def test_variable_surface_text_alias_collision_and_duplicate_scope_refuse(self):
        for kind,text in (('gr_text','${REFERENCE}'),('fp_text','%R'),('fp_text_box','prefix%V'),('gr_text_box','${VALUE}'),('dimension','%R')):
            with self.subTest(kind=kind):
                tree=board();item=[kind,json.dumps(text),['layer','"B.Cu"']]
                (tree if kind.startswith('gr_') else sx.children(tree,'footprint')[0]).append(item)
                with self.assertRaisesRegex(ValueError,'variable-dependent'):a.plan(raw(tree))
        tree=board();fp=sx.children(tree,'footprint')[0];alias='KAR_PD_A_'+a.atom(fp,'uuid').replace('-','')
        a.reference(sx.children(tree,'footprint')[2])[2]=json.dumps(alias)
        with self.assertRaisesRegex(ValueError,'collides'):a.plan(raw(tree))
        for mutation in ('legacy','four-layer','unknown-type'):
            tree=board()
            if mutation=='legacy':sx.one(tree,'version')[1]='20240108'
            elif mutation=='four-layer':sx.one(tree,'layers').insert(2,['1','"In1.Cu"','signal'])
            else:sx.one(tree,'layers')[2][2]='power'
            with self.subTest(mutation=mutation),self.assertRaisesRegex(ValueError,'two-layer scope'):a.plan(raw(tree))

    def test_dsn_census_electrical_pins_and_alias_leakage_refuse(self):
        source=raw(board());binding=a.plan(source);alias=binding['aliases'][0]['alias']
        for mutation in ('missing-placement','duplicate-placement','unknown-placement','missing-image','duplicate-image','electrical-alias','terminal-alias','other-alias','missing-pins'):
            with self.subTest(mutation=mutation):
                tree=dsn(source,binding);placement=sx.one(tree,'placement');art=sx.children(placement,'component')[0];library=sx.one(tree,'library');network=sx.one(tree,'network')
                if mutation=='missing-placement':art.pop()
                elif mutation=='duplicate-placement':art.append(copy.deepcopy(art[2]))
                elif mutation=='unknown-placement':art[2][1]='"UNKNOWN"'
                elif mutation=='missing-image':library.remove(sx.children(library,'image')[0])
                elif mutation=='duplicate-image':library.append(copy.deepcopy(sx.children(library,'image')[0]))
                elif mutation=='electrical-alias':sx.children(library,'image')[0].append(['pin','"1"','"P"','0','0'])
                elif mutation=='terminal-alias':sx.one(sx.children(network,'net')[0],'pins')[1]=json.dumps(alias+'-1')
                elif mutation=='other-alias':tree.append(['comment',json.dumps(alias)])
                else:sx.children(network,'net')[0].remove(sx.one(sx.children(network,'net')[0],'pins'))
                with self.assertRaises(ValueError):a.dsn_aliases(adapter._dump_dsn(tree).encode(),source,binding)
        # Zero aliases still require the complete source placement population.
        source=raw(board(duplicate=False));binding=a.plan(source);tree=dsn(source,binding)
        sx.children(sx.one(tree,'placement'),'component')[0].pop()
        with self.assertRaisesRegex(ValueError,'incomplete'):a.dsn_aliases(adapter._dump_dsn(tree).encode(),source,binding)

if __name__=='__main__':unittest.main()
