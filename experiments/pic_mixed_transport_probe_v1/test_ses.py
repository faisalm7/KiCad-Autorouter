"""Pure falsifiers over a constructed SES from retained original DSN; no native pass claim."""
import copy,json,re,unittest
from pathlib import Path
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn
from experiments.pic_mixed_transport_probe_v1 import ses_checks as c,ses_native
ROOT=Path(__file__).resolve().parents[2]

class SesChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=ROOT/'evidence/pic-local-clearance-transport-001'
        cls.raw=(src/'mixed.dsn').read_bytes();cls.expected=json.loads((src/'expectations.json').read_bytes())
        cls.source=sx.read(ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb')
        dsn=_parse_dsn(cls.raw.decode());place=['placement',['resolution','um','10']]
        def scaled(x):return str(c.number(x)*10)
        for node in sx.children(sx.one(dsn,'placement'),'component'):
            comp=['component',json.dumps(re.sub(r'::[0-9]+$', '', sx.unquote(node[1])))]
            for x in sx.children(node,'place'):comp.append(['place',x[1],scaled(x[2]),scaled(x[3]),x[4],str(c.number(x[5])%360)])
            place.append(comp)
        wiring=sx.one(dsn,'wiring');network=['network_out'];nets={};via_names=set()
        for x in wiring[1:]:
            n=sx.unquote(sx.one(x,'net')[1]);net=nets.setdefault(n,['net',json.dumps(n)])
            node=copy.deepcopy(x);node[:]=[v for v in node if not isinstance(v,list) or v[0] not in ('net','type')]
            if node[0]=='via':
                via_names.add(c.imported_name(sx.unquote(node[1])));node[1]=json.dumps(re.sub(r'::[0-9]+$', '', sx.unquote(node[1])));node[2:4]=list(map(scaled,node[2:4]))
            else:
                shape=node[1];shape[2:]=list(map(scaled,shape[2:]))
            net.append(node)
        network.extend(nets.values());lib=['library_out']
        for x in sx.children(sx.one(dsn,'library'),'padstack'):
            if c.imported_name(sx.unquote(x[1])) not in via_names:continue
            node=copy.deepcopy(x);node[1]=json.dumps(re.sub(r'::[0-9]+$', '', sx.unquote(node[1])))
            for shape in sx.children(node,'shape'):shape[1][2:]=list(map(scaled,shape[1][2:]));shape[1].extend(['0','0'])
            lib.append(node)
        # Pure positive fixture uses exactly the DSN's integer-um retained copper.
        # The real source's sub-um coordinates are separately expected to reject.
        cls.exact_source=copy.deepcopy(cls.source)
        cls.exact_source[:]=[n for n in cls.exact_source if not isinstance(n,list) or n[0] not in ('segment','via','arc')]
        layer={'top_layer':'F.Cu','bottom_layer':'B.Cu'}
        for wire in sx.children(wiring,'wire'):
            path=sx.one(wire,'path')
            if not path:continue
            points=c.pairs(path[3:]);net=sx.one(wire,'net')[1]
            for a,b in zip(points,points[1:]):
                cls.exact_source.append(['segment',['start',str(a[0]/1000),str(-a[1]/1000)],['end',str(b[0]/1000),str(-b[1]/1000)],['width',str(c.number(path[2])/1000)],['layer',json.dumps(layer[sx.unquote(path[1])])],['net',net]])
        cls.exact_source.extend(copy.deepcopy(sx.children(cls.source,'via')))
        cls.tree=['session','"original-mixed.ses"',['base_design','"original-mixed.dsn"'],place,['was_is'],
            ['routes',['resolution','um','10'],['parser',['host_cad','"KiCad\'s Pcbnew"'],['host_version','"10.0.0"']],lib,network]]
    def audit(self,tree):return c.audit((sx.dump(tree)+'\n').encode(),self.raw,self.expected,self.exact_source)
    def net(self,tree,name):return next(n for n in sx.children(sx.one(sx.one(tree,'routes'),'network_out'),'net') if sx.unquote(n[1])==name)
    def polygon(self,tree):return next(w for n in sx.children(sx.one(sx.one(tree,'routes'),'network_out'),'net') for w in sx.children(n,'wire') if sx.one(w,'polygon'))
    def test_constructed_exact(self):
        _,r=self.audit(self.tree);c.require_faithful(r);self.assertEqual(r['ses_segments'],370);self.assertEqual(r['ses_vias'],6)
    def test_package_namespace_and_negative_angle_are_exact(self):
        source=['placement',['component','"Pkg.50::2"',['place','REF','10','20','front','-90']]]
        session=['placement',['component','"Pkg.50"',['place','REF','100','200','front','270']]]
        self.assertEqual(c.placements(source,1,True),c.placements(session,10))
        session[1][1]='"Pkg.50::99"'
        self.assertNotEqual(c.placements(source,1,True),c.placements(session,10))
    def test_original_export_quantization_stays_failed(self):
        _,r=c.audit((sx.dump(self.tree)+'\n').encode(),self.raw,self.expected,self.source)
        self.assertFalse(r['native_to_dsn']['equal']);self.assertTrue(r['dsn_to_ses']['equal'])
        with self.assertRaises(ValueError):c.require_faithful(r)
    def test_polygon_mutations(self):
        for change in ('ring','extra','net','missing','hole'):
            with self.subTest(change=change):
                t=copy.deepcopy(self.tree);w=self.polygon(t)
                if change=='ring':sx.one(w,'polygon')[3]=str(c.number(sx.one(w,'polygon')[3])+1)
                elif change=='extra':self.net(t,'VCC').append(copy.deepcopy(w))
                elif change=='net':
                    self.net(t,'VCC').remove(w);self.net(t,'VPP').append(w)
                elif change=='missing':self.net(t,'VCC').remove(w)
                elif change=='hole':w.append(['window',['polygon','bottom_layer','0','0','0','1','0','1','1']])
                with self.assertRaises(ValueError):self.audit(t)
    def test_placement_resolution_and_net_duplicates(self):
        for mutation in ('placement','package','angle','resolution','duplicate','unknown','swap'):
            t=copy.deepcopy(self.tree)
            if mutation=='placement':sx.children(sx.children(sx.one(t,'placement'),'component')[0],'place')[0][2]='0'
            elif mutation=='package':sx.children(sx.one(t,'placement'),'component')[0][1]='UNKNOWN_PACKAGE'
            elif mutation=='angle':sx.children(sx.children(sx.one(t,'placement'),'component')[0],'place')[0][5]='0.000001'
            elif mutation=='resolution':sx.one(sx.one(t,'routes'),'resolution')[2]='100'
            elif mutation=='duplicate':sx.one(sx.one(t,'routes'),'network_out').append(copy.deepcopy(self.net(t,'VCC')))
            elif mutation=='unknown':self.net(t,'VCC')[1]='UNKNOWN'
            elif mutation=='swap':sx.one(t,'was_is').append(['pins','a','b'])
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.audit(t)
    def test_removed_altered_ordinary_copper_never_faithful(self):
        for key in ('path','via'):
            for action in ('delete','move'):
                t=copy.deepcopy(self.tree);network=sx.one(sx.one(t,'routes'),'network_out')
                parent,node=next((n,x) for n in sx.children(network,'net') for x in n if isinstance(x,list) and (x[0]=='via' if key=='via' else x[0]=='wire' and sx.one(x,'path')))
                if action=='delete':parent.remove(node)
                elif key=='via':node[2]=str(c.number(node[2])+1)
                else:sx.one(node,'path')[3]=str(c.number(sx.one(node,'path')[3])+1)
                _,r=self.audit(t)
                with self.subTest(key=key,action=action),self.assertRaises(ValueError):c.require_faithful(r)
    def test_negative_only_named_ordinary_routes(self):
        raw,recipe=c.disconnected(self.tree,self.source,self.expected);tree=sx.parse(raw.decode());_,r=self.audit(tree)
        self.assertEqual(recipe['terminal_count'],11);self.assertEqual(r['exact_custom_polygons'],2)
        with self.assertRaises(ValueError):c.require_faithful(r)
        old=copy.deepcopy(self.tree);new=copy.deepcopy(tree)
        oldnet=self.net(old,recipe['net']);newnet=self.net(new,recipe['net'])
        oldnet[:]=[x for x in oldnet if not isinstance(x,list) or x[0]!='via' and not (x[0]=='wire' and sx.one(x,'path'))]
        self.assertEqual(old,new);self.assertTrue(any(sx.one(x,'polygon') for x in sx.children(newnet,'wire')))
    def test_exact_engine_geometry_witness_falsifiers(self):
        item={'id':1,'kind':'app.freerouting.board.trace.PolylineTrace','first_layer':0,'last_layer':0}
        row={**item,'layer_index':0,'layer':'top_layer','half_width_board_units':2500,'width_um':500,
            'corner_count':2,'corners_board_integer':[[0,0],[100,0]],'corners_um':[[0,0],[10,0]],'corner_classes':['IntPoint','IntPoint']}
        state={'board_units_per_um':10,'board_origin_dsn_um':[0,0],'items':[item],'census':{'traces':1,'vias':0},'layers':['top_layer','bottom_layer']}
        geometry={'traces':[row],'vias':[]}
        c.geometry_check(geometry,state)
        fractional=copy.deepcopy(geometry);fractional['traces'][0].update(half_width_board_units=2159,width_um=431.8)
        c.geometry_check(fractional,state)
        fractional['traces'][0]['width_um']=431.800001
        with self.assertRaises(ValueError):c.geometry_check(fractional,state)
        for key,value in [('corners_board_integer',[[0,0],None]),('corners_um',[[0,0],[11,0]]),('width_um',501),('corner_count',3),('layer','bottom_layer')]:
            changed=copy.deepcopy(geometry);changed['traces'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.geometry_check(changed,state)
        changed=copy.deepcopy(geometry);changed['traces']=[]
        with self.assertRaises(ValueError):c.geometry_check(changed,state)

    def test_negative_requires_new_raw_error_on_original_terminal(self):
        finding={'type':'unconnected_items','severity':'error','items':[{'uuid':'pad','description':'Pad [NET]'}]}
        baseline={'opens':0,'findings':[]};bad={'opens':1};raw={'unconnected_items':[finding]}
        self.assertEqual(ses_native.negative_findings(baseline,bad,raw,{'pad'},'NET'),[finding])
        for field,value in [('severity','warning'),('severity','exclusion'),('excluded',True)]:
            changed=copy.deepcopy(finding);changed[field]=value
            self.assertEqual(ses_native.negative_findings(baseline,bad,{'unconnected_items':[changed]},{'pad'},'NET'),[])
        self.assertEqual(ses_native.negative_findings(baseline,bad,{'unconnected_items':[],'violations':[finding]},{'pad'},'NET'),[])
        self.assertEqual(ses_native.negative_findings({'opens':0,'findings':[finding]},bad,raw,{'pad'},'NET'),[])
        self.assertEqual(ses_native.negative_findings(baseline,bad,raw,{'different'},'NET'),[])

    def test_raw_immutable_and_warnings_reject(self):
        changed=copy.deepcopy(self.source);sx.children(changed,'footprint')[0].append(['clearance','0.1'])
        self.assertFalse(ses_native.semantic_diff(self.source,changed)['equal'])
        self.assertTrue(ses_native.semantic_diff(self.source,self.source)['equal'])
        row={'opens':0,'blocking':0,'warnings':1,'exclusions':0,'ignored_checks':[],'findings':[{'type':'anything','description':'a'}]}
        other=copy.deepcopy(row);other['findings'][0]['description']='b'
        self.assertFalse(ses_native.same_findings(row,other))

class NativeContinuation(unittest.TestCase):
    def test_validation_uses_original_rules_and_exact_imported_board_only(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';source.mkdir();raw=root/'raw';raw.mkdir()
            (source/'board.kicad_pcb').write_text('original-board')
            (source/'board.kicad_pro').write_text('original-rules')
            (source/'rules.kicad_dru').write_text('original-custom-rules')
            (raw/'board.kicad_pcb').write_text('actual-import')
            (raw/'board.kicad_pro').write_text('changed-rules')
            (raw/'board.kicad_prl').write_text('generated')
            board=ses_native.validation_copy(source/'board.kicad_pcb',root/'validation',raw/'board.kicad_pcb')
            self.assertEqual(board.read_text(),'actual-import')
            self.assertEqual((board.parent/'board.kicad_pro').read_text(),'original-rules')
            self.assertEqual((board.parent/'rules.kicad_dru').read_text(),'original-custom-rules')
            self.assertFalse((board.parent/'board.kicad_prl').exists())
            self.assertEqual((source/'board.kicad_pcb').read_text(),'original-board')
            self.assertEqual((raw/'board.kicad_pro').read_text(),'changed-rules')

    def test_cached_baseline_and_positive_actual_binding_and_falsifiers(self):
        from unittest.mock import patch
        from experiments.pic_mixed_transport_probe_v1 import driver
        proto=driver.base.decode(driver.base.content(driver.HERE/'SES_FINISH_PROTOCOL.json'))
        before=driver.runtime(proto);cached=driver.ROOT/proto['reuse_positive']
        inventory=before['cached_positive_inventory'];read=ses_native.floor.read_json
        baseline,raw,binding=ses_native.cached_positive(cached,before,inventory)
        self.assertEqual(baseline['warnings'],41);self.assertEqual(baseline['opens'],0)
        self.assertFalse(binding['new_baseline_execution']);self.assertFalse(binding['new_positive_import_execution'])
        self.assertEqual(binding['raw_board_sha256'],ses_native.p.sha(raw))
        for kind in ('status','frozen','tool','worker','binding','report','process','cleanup','truncated','extra-stage'):
            def mutated(path):
                data=copy.deepcopy(read(path))
                if path.name=='summary.json':
                    if kind=='status':data['status']='completed'
                    elif kind=='frozen':data['frozen_evidence']['raw.ses']='0'*64
                    elif kind=='tool':data['runtime']['tools']['native_cli']['sha256']='0'*64
                    elif kind=='worker':data['runtime']['sources']['autorouter/native.py']['sha256']='0'*64
                    elif kind=='report':data['native_ses']['baseline']['warnings']=0
                    elif kind=='extra-stage':data['steps'].append(copy.deepcopy(data['steps'][0]))
                elif path.name=='baseline-binding.json' and kind=='binding':data['saved']=True
                elif path.name=='ses-import-positive-process.json':
                    if kind=='process':data['argv'][-1]='different.ses'
                    elif kind=='cleanup':data['cleanup_complete']=False
                    elif kind=='truncated':data['log_truncated']=True
                return data
            with self.subTest(kind=kind),patch.object(ses_native.floor,'read_json',side_effect=mutated),self.assertRaises(ValueError):
                ses_native.cached_positive(cached,before,inventory)

if __name__=='__main__':unittest.main()
