"""Pure verifier controls; authored observations are not native qualification."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
try:from autorouter import schematic_fields as m
except ImportError:
    spec=importlib.util.spec_from_file_location('autorouter.schematic_fields',HERE/'schematic_fields.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
s=m.sx
UID='00000000-0000-0000-0000-000000000001'
def scene():
    tree=s.parse('(export (version "E") (design (source "/owned/board.kicad_sch") (tool "Eeschema 10.0.0")) (components (comp (ref "D1") (fields (field (name "Footprint") "Library:LED") (field (name "Datasheet")) (field (name "Description") "LED") (field (name "LCSC Part #") "C123")))))')
    obs={'schema':1,'native_version':'10.0.0','source':'/owned/board.kicad_pcb','board_sha256':'1'*64,'project_sha256':'2'*64,'schematic_sha256':'3'*64,'board_saved':False,'footprints':[{'reference':'D1','uuid':UID,'fields':{'Datasheet':'~','Description':'LED','LCSC Part #':'C123'}}]}
    warning={'type':m.KIND,'description':m.DESCRIPTION,'severity':'warning','items':[{'uuid':UID,'description':'Footprint D1','pos':{'x':1,'y':2}}]}
    report={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':'board.kicad_pcb','included_severities':['error','warning','exclusion'],'ignored_checks':[],'violations':[],'unconnected_items':[],'schematic_parity':[warning]}
    return tree,obs,report

def prove(c):return m.derive(s.dump(c[0]),c[1],c[2])
def schfield(c,name):return next(n for n in s.one(s.children(s.one(c[0],'components'),'comp')[0],'fields')[1:] if s.unquote(s.one(n,'name')[1])==name)
class Controls(unittest.TestCase):
    def reject(self,c):
        with self.assertRaises(ValueError):prove(c)
    def test_exact_placeholder_proof_preserves_all_inputs_and_binds_warning(self):
        c=scene();before=copy.deepcopy(c);q=prove(c)
        self.assertEqual(c,before);self.assertTrue(q['qualified']);self.assertEqual(q['component_count'],1);self.assertEqual(q['compared_field_count'],3)
        self.assertEqual(q['warning_uuids'],[UID]);self.assertTrue(m.qualified(q,c[2]['schematic_parity']))
        self.assertEqual(q['comparison_map'][0]['pcb_fields']['LCSC Part #'],'C123')
    def test_later_custom_changed_or_missing_rejects_unchanged_first_warning(self):
        for where in ('sch_change','pcb_change','pcb_missing'):
            c=scene();warning=copy.deepcopy(c[2]['schematic_parity'])
            if where=='sch_change':schfield(c,'LCSC Part #')[2]='"DIFFERENT"'
            elif where=='pcb_change':c[1]['footprints'][0]['fields']['LCSC Part #']='DIFFERENT'
            else:del c[1]['footprints'][0]['fields']['LCSC Part #']
            self.assertEqual(c[2]['schematic_parity'],warning)
            with self.subTest(where=where):self.reject(c)
    def test_pcb_only_fields_are_preserved_and_do_not_invent_a_parity_mismatch(self):
        c=scene();c[1]['footprints'][0]['fields']['ki_fp_filters']='LED*';before=copy.deepcopy(c)
        q=prove(c);self.assertEqual(c,before);self.assertEqual(q['comparison_map'][0]['pcb_fields']['ki_fp_filters'],'LED*')
        self.assertTrue(m.qualified(q,c[2]['schematic_parity']))
    def test_real_url_and_reverse_or_whitespace_sentinel_never_waived(self):
        for pcb,sch in [('https://real.example/doc',''),('~','https://real.example/doc'),('','~'),(' ~',''),('~',' ')]:
            c=scene();c[1]['footprints'][0]['fields']['Datasheet']=pcb;schfield(c,'Datasheet').append('"'+sch+'"')
            with self.subTest(pcb=pcb,sch=sch):self.reject(c)
    def test_matching_real_url_has_no_placeholder_warning(self):
        c=scene();schfield(c,'Datasheet').append('"https://example.test/doc"');c[1]['footprints'][0]['fields']['Datasheet']='https://example.test/doc';c[2]['schematic_parity']=[]
        q=prove(c);self.assertEqual(q['warning_uuids'],[]);self.assertTrue(m.qualified(q,[]))
    def test_exact_skips_only(self):
        c=scene();fields=s.one(s.children(s.one(c[0],'components'),'comp')[0],'fields')
        for name in ('Reference','Value','Component Class'):fields.append(['field',['name','"'+name+'"'],'"ignored"']);c[1]['footprints'][0]['fields'][name]='different'
        q=prove(c);self.assertEqual(q['compared_field_count'],3)
        fields.append(['field',['name','"value"'],'"CUSTOM"']);self.reject(c)
    def test_duplicate_component_field_and_case_collisions_rejected(self):
        for mode in ('component','field','case'):
            c=scene();comps=s.one(c[0],'components')
            if mode=='field':s.one(comps[1],'fields').append(copy.deepcopy(schfield(c,'Datasheet')))
            else:
                dup=copy.deepcopy(comps[1])
                if mode=='case':s.one(dup,'ref')[1]='"d1"'
                comps.append(dup)
            with self.subTest(mode=mode):self.reject(c)
    def test_duplicate_or_missing_observed_footprints_or_uuid_rejected(self):
        for mode in ('missing','duplicate_ref','duplicate_uuid','unknown_ref','bad_uuid'):
            c=scene();rows=c[1]['footprints']
            if mode=='missing':rows.clear()
            elif mode in ('duplicate_ref','duplicate_uuid'):
                dup=copy.deepcopy(rows[0])
                if mode=='duplicate_uuid':dup['reference']='D2'
                rows.append(dup)
            elif mode=='unknown_ref':rows[0]['reference']='D2'
            else:rows[0]['uuid']='unknown'
            with self.subTest(mode=mode):self.reject(c)
    def test_stale_source_tool_export_schema_or_hash_rejected(self):
        for mode in ('source','tool','version','hash','saved','observer_schema'):
            c=scene()
            if mode=='source':s.one(s.one(c[0],'design'),'source')[1]='"/other/board.kicad_sch"'
            elif mode=='tool':s.one(s.one(c[0],'design'),'tool')[1]='"Eeschema 9.0.0"'
            elif mode=='version':s.one(c[0],'version')[1]='"D"'
            elif mode=='hash':del c[1]['project_sha256']
            elif mode=='saved':c[1]['board_saved']=True
            else:c[1]['schema']=True
            with self.subTest(mode=mode):self.reject(c)
    def test_missing_effective_empty_field_or_unknown_value_schema_rejected(self):
        for mode in ('absent','unknown','escape'):
            c=scene();field=schfield(c,'Datasheet')
            if mode=='absent':s.one(s.children(s.one(c[0],'components'),'comp')[0],'fields').remove(field)
            elif mode=='unknown':field.append(['value','~'])
            else:schfield(c,'LCSC Part #')[2]='"unsafe\\nvalue"'
            with self.subTest(mode=mode):self.reject(c)
    def test_error_excluded_disabled_incomplete_or_description_warning_rejected(self):
        for mode in ('error','excluded','ignored','coverage','description','missing','duplicate','wrong_uuid','wrong_ref'):
            c=scene();r=c[2];w=r['schematic_parity'][0]
            if mode=='error':w['severity']='error'
            elif mode=='excluded':w['excluded']=True
            elif mode=='ignored':r['ignored_checks'].append({'key':m.KIND})
            elif mode=='coverage':r['included_severities'].remove('exclusion')
            elif mode=='description':w['description']+=' trailing'
            elif mode=='missing':r['schematic_parity']=[]
            elif mode=='duplicate':r['schematic_parity'].append(copy.deepcopy(w))
            elif mode=='wrong_uuid':w['items'][0]['uuid']='00000000-0000-0000-0000-000000000002'
            else:w['items'][0]['description']='Footprint D2'
            with self.subTest(mode=mode):self.reject(c)
    def test_datasheet_warning_plus_value_or_fpid_warning_cannot_qualify(self):
        for description in ('Value differs','Footprint identifier differs','DNP differs'):
            c=scene();c[2]['schematic_parity'].append({'type':'footprint_symbol_mismatch','severity':'warning','description':description,'items':[{'uuid':UID}]})
            with self.subTest(description=description):self.reject(c)
    def test_qualified_rejects_modified_finding_hidden_fields_or_incomplete_proof(self):
        c=scene();q=prove(c)
        changed=copy.deepcopy(c[2]['schematic_parity']);changed[0]['items'][0]['pos']['x']=2;self.assertFalse(m.qualified(q,changed))
        changed=copy.deepcopy(q);changed['comparison_map'][0]['pcb_fields']['LCSC Part #']='hidden';self.assertFalse(m.qualified(changed,c[2]['schematic_parity']))
        changed=copy.deepcopy(q);del changed['observer_sha256'];self.assertFalse(m.qualified(changed,c[2]['schematic_parity']))
        self.assertFalse(m.qualified(q,c[2]['schematic_parity']+[{'type':'other','severity':'warning'}]))
    def test_retained_actual_fields_diagnostic_is_not_old_candidate_acceptance(self):
        raw=(ROOT/'.runs/effective-fields-probe-001/effective.net').read_text();obs=json.loads((ROOT/'.runs/effective-fields-probe-continuation-001/fields.json').read_text());report=json.loads((ROOT/'.runs/nus-native-paired-001/run/B1/final-drc.json').read_text())
        q=m.derive(raw,obs,report);self.assertEqual((q['component_count'],q['compared_field_count'],len(q['warning_uuids'])),(6,19,5))
        self.assertTrue(m.qualified(q,report['schematic_parity']));self.assertNotIn('routing_accepted',q)
if __name__=='__main__':unittest.main(verbosity=2)
