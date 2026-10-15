"""Authored alias export/SES receipt controls; no Native or routing evidence."""
import copy,json,shutil,tempfile,unittest,uuid
from pathlib import Path
from autorouter import adapter,floor_route as f,local_settings as ls,padless_alias as a,pipeline as p,placement_clearance as io,sexpr as sx
from tests.normal_prl_fixture import _authored_normal_export

ROOT=Path(__file__).resolve().parents[1]
def identity(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'owned-alias-policy:'+name))
def encoded(tree):return (sx.dump(tree)+'\n').encode()
def poly():return [{'outer':[[0,0],[1000,0],[0,1000]],'holes':[]}]


class ExportPolicy(unittest.TestCase):
    def setUp(self):
        (ROOT/'.cache').mkdir(exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.cache');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.build()

    def build(self,*,aliases=False,prl_declaration=True):
        folder=self.root/('alias' if aliases else 'zero')
        if folder.exists():folder=self.root/('extra-'+str(len(list(self.root.iterdir()))))
        folder.mkdir();source_dir=folder/'source';source_dir.mkdir();self.out=folder/'run';self.out.mkdir()
        tree=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal'],['49','"F.Fab"','user'],['44','"Edge.Cuts"','user']],['net','1','"GND"']]
        names=['LOGO','LOGO','J1'] if aliases else ['J1']
        for index,name in enumerate(names):
            fp=['footprint','"Test:mark"',['uuid',json.dumps(identity('fp'+str(index)))],['at','0','0'],
                ['property','"Reference"',json.dumps(name),['layer','"F.Fab"']]]
            if name=='LOGO':fp.append(['attr','board_only'])
            else:fp.append(['pad','"1"','smd','rect',['at','0','0'],['size','1','1'],['layers','"F.Cu"'],['net','1','"GND"'],['uuid',json.dumps(identity('pad'))]])
            tree.append(fp)
        tree.extend([
            ['segment',['start','0','0'],['end','1','0'],['width','0.2'],['layer','"F.Cu"'],['net','1'],['uuid',json.dumps(identity('route'))],['locked','yes']],
            ['zone',['net','1'],['net_name','"GND"'],['layer','"F.Cu"'],['uuid',json.dumps(identity('zone'))]],
            ['gr_line',['start','0','0'],['end','1','1'],['layer','"Edge.Cuts"'],['uuid',json.dumps(identity('drawing'))]]])
        self.source=source_dir/'owned.kicad_pcb';self.source.write_bytes(encoded(tree));self.source.with_suffix('.kicad_pro').write_text('{}\n')
        shutil.copytree(source_dir,self.out/'snapshot');shutil.copytree(source_dir,self.out/'candidate')
        self.candidate=self.out/'candidate'/self.source.name
        self.data=dict(schema=1,input_policy='native',source=str(self.source),source_hashes=p.tree_hash(source_dir),candidate=str(self.candidate),
            scope='whole_board_unlocked_routing',steps=[],tools={'implementation_sha256':{},'normal_native_export_alias_policy':a.POLICY})
        code=self.out/'code';code.mkdir()
        for path in (ROOT/'autorouter').glob('*.py'):
            if path.name=='pipeline.py' and not prl_declaration:
                # Separately authored from inception for this AST boundary,
                # never stripped/relabelled real captured or executed code.
                (code/path.name).write_text('NORMAL_NATIVE_EXPORT_ALIAS_POLICY='+repr(a.POLICY)+'\n')
            else:shutil.copy2(path,code/path.name)
            self.data['tools']['implementation_sha256']['autorouter/'+path.name]=p.sha(code/path.name)
        self.paths=a.artifact_paths(self.out/'task.dsn')
        if not aliases:_authored_normal_export(self.out,self.data)
        else:self.author_alias(tree)
        imported=self.out/'imported.kicad_pcb';shutil.copy2(self.candidate,imported)
        self.data['steps'].append(dict(name='import',cwd=str(self.out),argv=[str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'import',str(self.candidate),str(imported),str(self.out/'routes.ses')],status='success',exit_code=0,cleanup_complete=True))

    def author_alias(self,tree):
        raw=encoded(p.routing_task(tree,self.data['scope']));binding=a.plan(raw);placement=['placement'];library=['library']
        names={r['uuid']:r['alias'] for r in binding['aliases']}
        for index,row in enumerate(binding['footprints']):
            image=json.dumps('image'+str(index));placement.append(['component',image,['place',json.dumps(names.get(row['uuid'],row['reference'])),'0','0','front','0']])
            library.append(['image',image]+([['pin','"pad"','"1"','0','0']] if row['pad_count'] else []))
        output=self.out/'task.dsn';dsn=adapter._dump_dsn(['pcb',json.dumps(str(output)),['parser',['string_quote',adapter._QUOTE_SENTINEL]],['unit','um'],['resolution','um','10'],placement,library,['network',['net','GND',['pins','J1-1']]]]).encode()
        self.paths['source_copy'].write_bytes(raw);output.write_bytes(dsn);(self.out/'native.dsn').write_bytes(dsn)
        before=self.observation(binding,False);during=self.observation(binding,True)
        self.paths['before'].write_bytes(raw);self.paths['after'].write_bytes(raw)
        events=[dict(phase='before_alias',observation=before),dict(phase='during_alias',observation=during),
                dict(phase='after_export',observation=copy.deepcopy(during)),
                dict(phase='restored',observation=copy.deepcopy(before),result=dict(exported=True,restored=True,alias_count=len(binding['aliases']),routing_accepted=False))]
        observation=dict(schema=1,source_sha256=a.sha(raw),dsn_sha256=a.sha(dsn),events=events,
            before_board=self.paths['before'].name,after_board=self.paths['after'].name,
            before_board_sha256=p.sha(self.paths['before']),after_board_sha256=p.sha(self.paths['after']),accepted=False,production_support=False)
        proof=dict(schema=1,policy=a.POLICY,native_version='10.0.0',source=str(self.candidate),source_sha256=a.sha(raw),
            project_sha256=p.sha(self.candidate.with_suffix('.kicad_pro')),output=str(output),dsn_sha256=a.sha(dsn),source_copy=self.paths['source_copy'].name,
            binding=binding,native_footprints=binding['footprints'],zero_alias=False,native_classmap=None,observation=observation,board_saved=False,routing_accepted=False)
        p.save_json(self.paths['proof'],proof);log=self.out/'export.log';log.write_bytes(b'')
        process=dict(name='export',cwd=str(self.out),argv=[str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'export',str(self.candidate),str(output)],
            status='success',exit_code=0,cleanup_complete=True,log=str(log),log_bytes=0,log_truncated=False)
        p.save_json(self.out/'export-process.json',process);self.data['steps'].append(copy.deepcopy(process));self.data['task_sha256']=a.sha(raw)
        session=['session','"owned"',['base_design','"task"'],['placement'],['was_is'],['routes',['resolution','um','10'],['library_out'],['network_out']]]
        (self.out/'routes.ses').write_bytes(encoded(session))
        self.data['steps'].append(dict(name='engine',cwd=str(self.out),argv=p.engine_argv(self.out,p.engine_profile_settings('standard',80)['argv'])))

    def observation(self,binding,during):
        aliases={r['uuid']:r['alias'] for r in binding['aliases']};fps=[]
        for row in binding['footprints']:
            ref=aliases.get(row['uuid'],row['reference']) if during else row['reference']
            field=dict(name='Reference',uuid=identity(row['uuid']+'ref'),kind='PCB_FIELD',position_nm=[0,0],layer=36,locked=False,bbox_nm=[0,0,1,1],copper_polygons={},
                text=ref,shown=ref,angle=0,size_nm=[1,1],thickness_nm=1,visible=True,knockout=False)
            fps.append(dict(uuid=row['uuid'],reference=ref,value='mark',fpid='Test:mark',position_nm=[0,0],angle=0,layer=0,locked=False,model_count=0,fields=[field],graphics=[]))
        pad_fp=next(row for row in binding['footprints'] if row['pad_count'])
        return dict(footprints=fps,pads=[dict(uuid=identity('pad'),parent_uuid=pad_fp['uuid'],reference='J1',number='1',net='GND',netcode=1,position_nm=[0,0],angle=0,drill_nm=[0,0],drill_shape=0,copper_shapes={'F.Cu':poly()})],
            routes=[dict(uuid=identity('route'),net='GND',netcode=1,locked=True,width_nm=200000,kind='segment',start_nm=[0,0],end_nm=[1000000,0],layer='F.Cu')],
            zones=[dict(uuid=identity('zone'),net='GND',outline=poly(),fills={'F.Cu':[]})],
            drawings=[dict(uuid=identity('drawing'),kind='PCB_SHAPE',position_nm=[0,0],layer=44,locked=False,bbox_nm=[0,0,1000000,1000000],copper_polygons={})],
            layers_text=dict(layers=[dict(name=n,canonical=n,type='signal') for n in ('F.Cu','B.Cu')],copper_text=[],shape_semantics='authored text observation'),
            areas=dict(zones=[dict(uuid=identity('zone'),name='',parent='board',is_rule_area=False,placement_enabled=False,placement_source_type='SHEETNAME',placement_source='',
                disallow={k:False for k in ('tracks','vias','pads','copperpour','footprints')},layers=['F.Cu'],outlines_nm=[[[0,0],[1000,0],[0,1000]]],outline_closed=[True],holes=[0],arc_count=0)],footprint_zone_count=0,footprint_rulearea_count=0),
            shape_semantics='authored complete observation; no Native execution')

    def check(self):return a.check_exports(self.out,self.data,io.inventory(self.out,max_bytes=16*1024**2,max_files=2000))
    def reject(self):
        with self.assertRaises((p.Rejected,ValueError,OSError)):self.check()
    def mutate_proof(self,callback):
        proof=f.read_json(self.paths['proof']);callback(proof);p.save_json(self.paths['proof'],proof)

    def test_zero_alias_complete_source_project_dsn_proof_is_read_only(self):
        before=io.inventory(self.out);self.assertEqual(self.check()[0]['alias_count'],0);self.assertEqual(io.inventory(self.out),before)

    def test_zero_alias_missing_corrupt_or_unexpected_observation_fails(self):
        original=self.paths['proof'].read_bytes()
        for mode in ('missing','corrupt','false_zero','observation','extra'):
            with self.subTest(mode=mode):
                try:
                    if mode=='missing':self.paths['proof'].unlink()
                    elif mode=='corrupt':self.paths['proof'].write_bytes(b'{broken')
                    else:self.mutate_proof(lambda x:x.update(**({'zero_alias':False} if mode=='false_zero' else {'observation':{}} if mode=='observation' else {'extra':True})))
                    self.reject()
                finally:self.paths['proof'].write_bytes(original)

    def test_producer_helper_marker_and_project_pins_are_mandatory(self):
        for mode in ('native','missing_native','helper','marker','project','log','log_size','typed_exit'):
            with self.subTest(mode=mode):
                data=copy.deepcopy(self.data);before=io.inventory(self.out,contents=True)
                try:
                    if mode in ('native','helper'):(self.out/'code'/('native.py' if mode=='native' else 'padless_alias_native.py')).write_bytes(b'# changed\n')
                    elif mode=='missing_native':(self.out/'code/native.py').unlink()
                    elif mode=='marker':self.data['tools'].pop('normal_native_export_alias_policy')
                    elif mode=='project':self.candidate.with_suffix('.kicad_pro').write_text('{"rules":"changed"}')
                    elif mode=='log':(self.out/'export.log').write_bytes(b'not empty')
                    else:
                        process=f.read_json(self.out/'export-process.json');process['log_bytes' if mode=='log_size' else 'exit_code']=True
                        p.save_json(self.out/'export-process.json',process);self.data['steps'][0]=copy.deepcopy(process)
                    self.reject()
                finally:
                    for name,raw in before.items():(self.out/name).write_bytes(raw)
                    self.data=data

    def test_export_step_process_proof_total_deletion_cannot_hide_native_import(self):
        for mode in ('step','process','step_process','all_export','duplicate'):
            with self.subTest(mode=mode):
                data=copy.deepcopy(self.data);files={n:io.read_bytes(self.out/n) for n in ('export-process.json','export.log',self.paths['proof'].name,self.paths['source_copy'].name)}
                try:
                    if mode in ('step','step_process','all_export'):self.data['steps']=[s for s in self.data['steps'] if s['name']!='export']
                    if mode in ('process','step_process','all_export'):(self.out/'export-process.json').unlink()
                    if mode=='all_export':
                        for n in ('export.log',self.paths['proof'].name,self.paths['source_copy'].name):(self.out/n).unlink()
                    if mode=='duplicate':self.data['steps'].append(copy.deepcopy(self.data['steps'][0]))
                    self.reject()
                finally:
                    for name,raw in files.items():(self.out/name).write_bytes(raw)
                    self.data=data

    def test_orphan_sidecar_and_canonical_export_path_are_not_exempt(self):
        orphan=self.out/'orphan.alias-export.json';orphan.write_bytes(self.paths['proof'].read_bytes());self.reject();orphan.unlink()
        process=f.read_json(self.out/'export-process.json');process['argv'][4]=str(self.out/'candidate'/'task.dsn')
        p.save_json(self.out/'export-process.json',process);self.data['steps'][0]=copy.deepcopy(process);self.reject()

    def test_rehashed_task_copy_cannot_replace_original_task_reconstruction(self):
        raw=self.paths['source_copy'].read_bytes().replace(b'(at 0 0)',b'(at 1 0)',1);self.paths['source_copy'].write_bytes(raw)
        self.data['task_sha256']=a.sha(raw)
        self.mutate_proof(lambda x:x.update(source_sha256=a.sha(raw),binding=a.plan(raw)))
        self.reject()

    def test_new_native_policy_is_checked_before_missing_prl_declaration_return(self):
        self.build(prl_declaration=False);self.assertEqual(ls.check_normal_policy(self.out,self.data),None)
        self.paths['proof'].unlink()
        with self.assertRaises(p.Rejected):ls.check_normal_policy(self.out,self.data)

    def test_drc_only_current_capture_needs_marker_but_no_export(self):
        self.data['steps']=[]
        for name in ('task.dsn','native.dsn','export-process.json','export.log',self.paths['proof'].name,self.paths['source_copy'].name):(self.out/name).unlink()
        self.assertEqual(self.check(),[]);self.data['tools'].pop('normal_native_export_alias_policy');self.reject()

    def test_alias_full_observations_and_actual_engine_stem_pass(self):
        self.build(aliases=True);before=io.inventory(self.out);self.assertEqual(self.check()[0]['alias_count'],2);self.assertEqual(io.inventory(self.out),before)
        session=sx.read(self.out/'routes.ses');name=f.read_json(self.paths['proof'])['binding']['aliases'][0]['alias']
        sx.one(session,'placement').append(['component','"image"',['place',json.dumps(name),'0','0','front','0']])
        (self.out/'routes.ses').write_bytes(encoded(session));self.assertEqual(self.check()[0]['alias_count'],2)

    def test_consistently_truncated_all_four_observations_fail(self):
        self.build(aliases=True);self.assertEqual(self.check()[0]['alias_count'],2);original=self.paths['proof'].read_bytes()
        for kind in ('schema','footprints','pads','zones','routes','drawings','pad_uid_only','zone_uid_only','route_uid_only','drawing_uid_only',
                     'pad_empty_map','pad_empty_polygon','zone_empty_outline','areas_empty_outline'):
            with self.subTest(kind=kind):
                try:
                    def truncate(proof):
                        for event in proof['observation']['events']:
                            value=event['observation']
                            if kind=='schema':event['observation']={'footprints':[]}
                            elif kind=='pad_empty_map':value['pads'][0]['copper_shapes']={}
                            elif kind=='pad_empty_polygon':value['pads'][0]['copper_shapes']={'F.Cu':[]}
                            elif kind=='zone_empty_outline':value['zones'][0]['outline']=[]
                            elif kind=='areas_empty_outline':value['areas']['zones'][0]['outlines_nm']=[]
                            elif kind.endswith('_uid_only'):
                                key={'pad':'pads','zone':'zones','route':'routes','drawing':'drawings'}[kind.split('_')[0]];value[key]=[{'uuid':r['uuid']} for r in value[key]]
                            else:value[kind]=[]
                    self.mutate_proof(truncate);self.reject()
                finally:self.paths['proof'].write_bytes(original)

    def test_alias_raw_ses_leak_wrong_base_and_ambiguous_engine_input_fail(self):
        self.build(aliases=True);self.assertEqual(self.check()[0]['alias_count'],2);raw=(self.out/'routes.ses').read_bytes();data=copy.deepcopy(self.data)
        for mode in ('net','parser','base_absolute','engine_input','duplicate_de'):
            with self.subTest(mode=mode):
                try:
                    session=sx.parse(raw.decode());alias=f.read_json(self.paths['proof'])['binding']['aliases'][0]['alias']
                    if mode=='net':sx.one(sx.one(session,'routes'),'network_out').append(['net',json.dumps(alias)])
                    elif mode=='parser':sx.one(session,'routes').append(['parser',['name',json.dumps('prefix'+alias+'suffix')]])
                    elif mode=='base_absolute':sx.one(session,'base_design')[1]=json.dumps(str(self.out/'task.dsn'))
                    else:
                        argv=next(s['argv'] for s in self.data['steps'] if s['name']=='engine')
                        if mode=='engine_input':argv[argv.index('-de')+1]=str(self.out/'other.dsn')
                        else:argv.extend(['-de',str(self.out/'task.dsn')])
                    (self.out/'routes.ses').write_bytes(encoded(session));self.reject()
                finally:(self.out/'routes.ses').write_bytes(raw);self.data=copy.deepcopy(data)


if __name__=='__main__':unittest.main()
