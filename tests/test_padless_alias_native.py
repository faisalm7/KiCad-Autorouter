"""Pure observation/restoration controls; these do not establish Native support."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from autorouter import padless_alias_native as native

IDS=['00000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000002']


def observation(ref='LOGO'):
    return {'footprints':[{'uuid':IDS[0],'reference':ref,'position_nm':[0,0],
        'fields':[{'name':'Reference','text':ref,'shown':ref,'bbox_nm':[0,0,1,1],
                   'position_nm':[0,0],'layer':36,'visible':True,'copper_polygons':{}},
                  {'name':'Value','text':'mark','copper_polygons':{}}]}],
        'pads':[{'uuid':'pad','position_nm':[10,20],'net':'GND'}],
        'routes':[],'zones':[],'drawings':[]}


def binding():return {'aliases':[{'uuid':IDS[0],'reference':'LOGO','alias':'KAR_PD_A_0001'}]}


class Comparison(unittest.TestCase):
    def normalized(self,value,during=False):
        return native.without_authorized_reference_display(value,binding(),during)

    def test_only_authorized_noncopper_reference_display_changes(self):
        before=observation();during=observation('KAR_PD_A_0001')
        during['footprints'][0]['fields'][0]['bbox_nm']=[0,0,50,1]
        self.assertEqual(self.normalized(before),self.normalized(during,True))
        self.assertEqual(before['footprints'][0]['fields'][0]['text'],'LOGO')

    def test_other_geometry_and_fields_remain_exact(self):
        before=observation();base=self.normalized(before)
        for kind in ('footprint','pad','value','font_layer','visibility'):
            with self.subTest(kind=kind):
                changed=observation('KAR_PD_A_0001');fp=changed['footprints'][0]
                if kind=='footprint':fp['position_nm'][0]+=1
                elif kind=='pad':changed['pads'][0]['net']='SIGNAL'
                elif kind=='value':fp['fields'][1]['text']='different'
                elif kind=='font_layer':fp['fields'][0]['layer']=37
                else:fp['fields'][0]['visible']=False
                self.assertNotEqual(base,self.normalized(changed,True))

    def test_unauthorized_reference_or_copper_mask_refused(self):
        for kind in ('reference','field','copper','duplicate_field'):
            with self.subTest(kind=kind):
                changed=observation('KAR_PD_A_0001');fp=changed['footprints'][0]
                if kind=='reference':fp['reference']='OTHER'
                elif kind=='field':fp['fields'][0]['text']='OTHER'
                elif kind=='copper':fp['fields'][0]['copper_polygons']={'F.Cu':[]}
                else:fp['fields'].append(copy.deepcopy(fp['fields'][0]))
                with self.assertRaises(ValueError):self.normalized(changed,True)


class Emission(unittest.TestCase):
    def fixture(self,directory):
        from autorouter import padless_alias
        raw=('(kicad_pcb (version 20241229) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) '+''.join(
            '(footprint "Test:mark" (uuid "'+uid+'") (property "Reference" "LOGO" (layer "F.Fab")) (attr board_only))'
            for uid in IDS)+')\n').encode()
        source=directory/'input'/'board.kicad_pcb';source.parent.mkdir();source.write_bytes(raw)
        class Footprint:
            def __init__(self,uid):
                self.m_Uuid=SimpleNamespace(AsString=lambda:uid);self.reference='LOGO'
            def GetReference(self):return self.reference
            def SetReference(self,value):self.reference=value
        fps=[Footprint(uid) for uid in IDS]
        board=SimpleNamespace(GetFileName=lambda:str(source),GetFootprints=lambda:fps,GetPads=lambda:[])
        observed=lambda value,api:{'references':[fp.GetReference() for fp in value.GetFootprints()]}
        return raw,padless_alias.plan(raw),source,board,observed

    def test_success_emits_only_original_reference_boards_and_full_events(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary).resolve();raw,plan,source,board,_=self.fixture(directory);saved=[]
            def observed(value,api):
                rows=[]
                for fp in value.GetFootprints():
                    row=observation(fp.GetReference())['footprints'][0];row['uuid']=str(fp.m_Uuid.AsString());rows.append(row)
                return {'footprints':rows,'pads':[],'routes':[],'zones':[],'drawings':[]}
            def save(path,value):
                refs=[fp.GetReference() for fp in value.GetFootprints()];saved.append(refs)
                self.assertEqual(refs,['LOGO','LOGO']);Path(path).write_text('(kicad_pcb)\n');return True
            def export(value,path):
                self.assertTrue(all(fp.GetReference().startswith('KAR_PD_A_') for fp in value.GetFootprints()))
                self.assertEqual(path,str(directory/'native.dsn'));Path(path).write_text('(pcb "test")\n');return True
            with patch.object(native,'observe',side_effect=observed):
                result=native.emit(board,raw,plan,directory/'native.dsn',SimpleNamespace(SaveBoard=save,ExportSpecctraDSN=export))
            self.assertEqual([row['phase'] for row in result['events']],['before_alias','during_alias','after_export','restored'])
            self.assertEqual(result['events'][0]['observation'],result['events'][-1]['observation'])
            self.assertEqual(result['events'][1]['observation'],result['events'][2]['observation'])
            self.assertEqual(saved,[['LOGO','LOGO'],['LOGO','LOGO']]);self.assertFalse(result['accepted'])
            self.assertEqual(source.read_bytes(),raw)

    def test_export_exception_restores_real_core_aliases_without_aliased_save(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary).resolve();raw,plan,source,board,observed=self.fixture(directory);saved=[]
            def save(path,value):
                saved.append([fp.GetReference() for fp in value.GetFootprints()]);Path(path).write_text('(kicad_pcb)\n');return True
            def export(value,path):
                self.assertTrue(all(fp.GetReference().startswith('KAR_PD_A_') for fp in value.GetFootprints()))
                raise RuntimeError('deliberate exporter failure')
            api=SimpleNamespace(SaveBoard=save,ExportSpecctraDSN=export)
            # The comparator remains exercised separately above. This authored
            # API stub isolates the real pure helper's finally/restoration path.
            with patch.object(native,'observe',side_effect=observed),patch.object(native,'without_authorized_reference_display',side_effect=lambda value,*a: {'same':True}):
                with self.assertRaisesRegex(RuntimeError,'deliberate exporter failure'):
                    native.emit(board,raw,plan,directory/'native.dsn',api)
            self.assertEqual([fp.GetReference() for fp in board.GetFootprints()],['LOGO','LOGO'])
            self.assertEqual(saved,[['LOGO','LOGO']]);self.assertEqual(source.read_bytes(),raw)
            self.assertFalse((directory/'native.alias-after.kicad_pcb').exists())

    def test_output_collision_refused_before_any_native_emission(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary).resolve();raw,plan,source,board,_=self.fixture(directory)
            (directory/'native.alias-after.kicad_pcb').write_bytes(b'keep')
            with self.assertRaisesRegex(ValueError,'fresh exclusive'):
                native.emit(board,raw,plan,directory/'native.dsn',SimpleNamespace())
            self.assertEqual((directory/'native.alias-after.kicad_pcb').read_bytes(),b'keep')

    def test_after_restoration_save_cannot_hide_changed_geometry(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary).resolve();raw,plan,source,board,_=self.fixture(directory);board.geometry=0;saves=[]
            def observed(value,api):return {'references':[fp.GetReference() for fp in value.GetFootprints()],'geometry':value.geometry}
            def save(path,value):
                saves.append(path);Path(path).write_text('(kicad_pcb)\n')
                if len(saves)==2:value.geometry=1
                return True
            def export(value,path):Path(path).write_text('(pcb "test")\n');return True
            with patch.object(native,'observe',side_effect=observed),patch.object(native,'without_authorized_reference_display',side_effect=lambda value,*a:{'geometry':value['geometry']}):
                with self.assertRaisesRegex(ValueError,'during restored emission'):
                    native.emit(board,raw,plan,directory/'native.dsn',SimpleNamespace(SaveBoard=save,ExportSpecctraDSN=export))
            self.assertEqual([fp.GetReference() for fp in board.GetFootprints()],['LOGO','LOGO'])
            self.assertEqual(source.read_bytes(),raw)

    def test_input_project_output_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary).resolve();raw,plan,source,board,_=self.fixture(directory)
            with self.assertRaisesRegex(ValueError,'external canonical'):
                native.emit(board,raw,plan,source.parent/'native.dsn',SimpleNamespace())


if __name__=='__main__':unittest.main()
