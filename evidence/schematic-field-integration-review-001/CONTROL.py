"""Authored pure seams, no real KiCad/JVM/Git or input writes."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys,types
from unittest import mock
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import autorouter
from autorouter import pipeline as p,schematic_field_evidence as evidence
from autorouter import floor_route as f,placement_clearance as pc,sexpr as sx
spec=importlib.util.spec_from_file_location('autorouter.schematic_fields',HERE/'draft-schematic-fields.py')
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
def sha(raw):return hashlib.sha256(raw).hexdigest()
source=Path('/__owned_field_control__/final-drc-input/owned.kicad_pcb')
uid='00000000-0000-0000-0000-000000000001'
warning={'type':policy.KIND,'severity':'warning','items':[{'uuid':uid,'description':'Footprint D1'}],'description':policy.DESCRIPTION}
library={'type':'lib_footprint_issues','severity':'warning','items':[{'uuid':uid,'description':'Footprint D1'}],'description':'Authored diagnostic library warning'}
raw_report={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':source.name,
    'included_severities':['error','warning','exclusion'],'ignored_checks':[],
    'violations':[library],'unconnected_items':[],'schematic_parity':[warning]}
netlist=('(export (version E) (design (source "'+str(source.with_suffix('.kicad_sch'))+'") (tool "Eeschema 10.0.0")) '
    '(components (comp (ref D1) (fields (field (name "Footprint") "owned:part") (field (name "Datasheet")) (field (name "Description") "same")))))')
observer={'schema':1,'native_version':'10.0.0','source':str(source),'board_sha256':'0'*64,'project_sha256':'1'*64,'schematic_sha256':'2'*64,'board_saved':False,
    'footprints':[{'uuid':uid,'reference':'D1','fields':{'Datasheet':'~','Description':'same'}}]}
qualification=policy.derive(netlist,observer,raw_report)
native={'opens':0,'blocking':0,'warnings':2,'exclusions':0,'ignored_checks':[],
    'findings':[warning,library],'field_parity':{'schema':1,'policy':evidence.POLICY,'qualification':qualification}}
results=[]
with mock.patch.dict(sys.modules,{'autorouter.schematic_fields':policy}),mock.patch.object(autorouter,'schematic_fields',policy,create=True):
    assert p.native_rejection_reasons(native)==[]
    results.append({'control':'complete_field_plus_library_positive','outcome':'accepted_warning_scope_only'})
    # Before-fix wrapper supplied the entire finding population to an API
    # intentionally checking only the field-warning family.
    assert policy.qualified(qualification,native['findings']) is False
    assert policy.qualified(qualification,[warning]) is True
    results.append({'control':'reconstructed_all_findings_wrapper','outcome':'false_rejection_demonstrated'})
    for key in ('footprint_symbol_field_mismatch','net_conflict','track_width'):
        row=copy.deepcopy(native);row['ignored_checks']=[{'key':key}]
        assert p.native_rejection_reasons(row)
        results.append({'control':'ignored_'+key,'outcome':'rejected'})
    for label,change in [('error',{'severity':'error'}),('excluded',{'excluded':True}),
        ('url',{'description':"Field 'Datasheet' differs (PCB: 'https://example.invalid/part', Schematic: '')"}),
        ('other_field',{'description':"Field 'Description' differs (PCB: 'wrong', Schematic: 'same')"})]:
        row=copy.deepcopy(native);row['findings'][0].update(change)
        assert p.native_rejection_reasons(row)
        results.append({'control':label,'outcome':'rejected'})
    for label,obs in [('duplicate_uuid',copy.deepcopy(observer)),('duplicate_reference',copy.deepcopy(observer))]:
        added=copy.deepcopy(obs['footprints'][0]);obs['footprints'].append(added)
        if label=='duplicate_uuid':added['reference']='D2'
        else:added['uuid']='00000000-0000-0000-0000-000000000002'
        try:policy.derive(netlist,obs,raw_report)
        except ValueError:results.append({'control':label,'outcome':'rejected'})
        else:raise AssertionError(label)
    assert policy.compare({'Datasheet':'','Description':'same'},{'Datasheet':'~','Description':'same','extra':'preserved'})
    results.append({'control':'extra_PCB_only_field','outcome':'preserved_without_false_rejection'})
    # Exact production expected-stage expression, isolated from unrelated
    # original-rule/native guards. No stage or CPU evidence is fabricated.
    env={'qualify':lambda board:[],'original':[], 'contract':None,'candidate':source,
        'p':types.SimpleNamespace(netclass_policy=lambda board:None),'fields':evidence,'data':{'native':native}}
    exec(compile((HERE/'captured-export-expected.py').read_text(),'<captured_export_stage_expression>','exec'),env)
    expected=['refill-drc','final-drc',*evidence.names('final-drc'),'metrics']
    assert env['expected_names']==expected
    assert expected!=['refill-drc','final-drc','metrics']
    results.append({'control':'field_export_stage_history','outcome':'both_new_workers_required'})

    # Complete native observations with a case-alias source property. The
    # pinned legacy parser folds mandatory names then overwrites their IDs.
    directory=source.parent.parent;board=['kicad_pcb',['footprint','"owned"',['property','"Datasheet"','"~"']]]
    canonical_board=(sx.dump(board)+'\n').encode();project=b'{}'
    normal=['kicad_sch',['version','20250114'],['symbol',['property','"Datasheet"','"~"']]]
    alias=['kicad_sch',['version','20250114'],['symbol',['property','"Datasheet"','"https://example.invalid/part"'],['property','"datasheet"','"~"']]]
    captured_globals=dict(vars(evidence));captured_globals.update(__package__='autorouter')
    exec(compile((HERE/'reconstructed-pre-fix-derive.py').read_text(),'<reconstructed_pre_fix_source_guard>','exec'),captured_globals)
    captured_derive=captured_globals['derive']
    for label,schematic in [('flat_positive',normal),('mandatory_case_alias',alias),('newer_schema',['kicad_sch',['version','20260206']]),('hierarchy',['kicad_sch',['version','20250114'],['sheet']])]:
        sch=(sx.dump(schematic)+'\n').encode();blobs={source:canonical_board,source.with_suffix('.kicad_pro'):project,source.with_suffix('.kicad_sch'):sch,directory/'final-drc-fields.net':netlist.encode()}
        after={source.name:sha(canonical_board),source.with_suffix('.kicad_pro').name:sha(project),source.with_suffix('.kicad_sch').name:sha(sch)}
        obs=copy.deepcopy(observer);obs.update(board_sha256=sha(canonical_board),project_sha256=sha(project),schematic_sha256=sha(sch))
        binding={'input':str(source),'after':after}
        def read_json(path):
            return binding if str(path).endswith('-binding.json') else obs
        def digest_path(path):return sha(blobs.get(Path(path),b'owned-source-metadata'))
        with mock.patch.object(pc,'read_bytes',lambda path,*a,**k:blobs[Path(path)]),mock.patch.object(p,'tree_hash',lambda path:after),mock.patch.object(p,'sha',digest_path),mock.patch.object(f,'read_json',read_json):
            proof=captured_derive(directory,'final-drc',raw_report)
            accepted=proof['qualification'].get('qualified') is True
            assert accepted==(label in ('flat_positive','mandatory_case_alias'))
            results.append({'control':'captured_'+label,'outcome':'qualified' if accepted else 'unqualified','native_execution':False})
            if label=='mandatory_case_alias':
                final=evidence.derive(directory,'final-drc',raw_report)
                results.append({'control':'current_mandatory_case_alias','outcome':'qualified' if final['qualification'].get('qualified') is True else 'unqualified'})

print(json.dumps({'schema':1,'pure_control_only':True,'native_jvm_git_network_execution':False,'results':results},indent=2))
