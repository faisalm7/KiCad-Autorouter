"""Tiny real-function fixtures. No Native/tool subprocess, Git, GUI or installation.

Writes only newly created owned miniature test trees. Synthetic role bytes
use an explicit test-only known-hash table; this does not qualify real tools.
Pipeline controls import the whole product module with explicit controlled dependencies.
"""
import importlib
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
PROPOSED=ROOT
sys.path.insert(0,str(ROOT))
import autorouter


def load(path,name,file=None):
    mod=types.ModuleType(name);mod.__file__=str(file or path)
    exec(compile(path.read_text(),str(path),'exec'),mod.__dict__)
    return mod


def digest(raw):return hashlib.sha256(raw).hexdigest()


class RuntimeTransportControls(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base=Path(self.temporary.name).resolve()
        self.pv=load(PROPOSED/'autorouter/provenance.py','owned_provenance')
        self.real_lock=json.loads((ROOT/'toolchain.lock.json').read_text())
        self.bytes={role:('owned '+role+'\n').encode() for role in ('kicad_cli','kicad_python','pcbnew','java')}
        self.pv._NATIVE_HASHES={version:tuple(digest(self.bytes[role]) for role in self.pv._NATIVE_SUFFIXES) for version in ('10.0.0','10.0.7')}
        with patch.object(autorouter,'provenance',self.pv,create=True),patch.dict(sys.modules,{'autorouter.provenance':self.pv}):
            before=list(sys.path)
            self.build=load(PROPOSED/'scripts/prepare_runtime.py','owned_installer')
            sys.path[:]=before
        self.lock=copy.deepcopy(self.real_lock)
        for version,records in [('10.0.0',self.lock['tools']),('10.0.7',self.lock['native_profiles']['10.0.7'])]:
            for role in self.pv._NATIVE_SUFFIXES:
                records[role]['sha256']=digest(self.bytes[role]);records[role]['bytes']=len(self.bytes[role])
        self.lock['tools']['java'].update(sha256=digest(self.bytes['java']),bytes=len(self.bytes['java']))
        self.engine=b'owned tiny never-executed engine\n'
        self.lock['tools']['freerouting']={'path':self.pv.ENGINE_PATH,'sha256':digest(self.engine),'bytes':len(self.engine)}
        self.paths={role:str(self.base/'Tools with spaces'/'Owned.app'/'Contents'/suffix) for role,suffix in self.pv._NATIVE_SUFFIXES.items()}
        self.paths['java']=str(self.base/'Tools with spaces'/'jdk'/'bin/java')
        for role,value in self.paths.items():
            path=Path(value);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(self.bytes[role]);path.chmod(0o700)

    def artifact(self,schema=2,*,binding_capable=True):
        root=self.base/'artifact original';root.mkdir()
        for name in (*self.pv.FIXED_FILES,'autorouter/__init__.py','autorouter/provenance.py','autorouter/worker.py',self.pv.README):
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(('# owned '+name+'\n').encode())
        if binding_capable:
            for name in ('autorouter/config.py','autorouter/provenance.py','autorouter/pipeline.py'):
                (root/name).write_bytes((PROPOSED/name).read_bytes())
        (root/'toolchain.lock.json').write_text(json.dumps(self.lock))
        engine=root/self.pv.ENGINE_PATH;engine.parent.mkdir();engine.write_bytes(self.engine)
        expected={name:digest((root/name).read_bytes()) for name in (*self.pv.FIXED_FILES,*self.pv.module_paths(root),self.pv.README)}
        record={'schema':schema,'kind':self.pv.KIND,'root':str(root),'build_source':{'kind':'git-checkout','git_head':'a'*40,'files_sha256':{k:v for k,v in expected.items() if k!=self.pv.README}},'immutable_files_sha256':expected,'mutable_directories':list(self.pv.MUTABLE_DIRECTORIES),'local_engine':{**self.lock['tools']['freerouting'],'publication_authorized':False}}
        if schema>=2:record['native_version']='10.0.7'
        (root/self.pv.MANIFEST).write_text(json.dumps(record))
        return root,digest((root/self.pv.MANIFEST).read_bytes())

    def implementation(self,root):return {name:digest((root/name).read_bytes()) for name in self.pv.module_paths(root)}

    def config(self,root):
        with patch.dict(sys.modules,{'autorouter.provenance':self.pv}):
            return load(PROPOSED/'autorouter/config.py','owned_config',root/'autorouter/config.py')

    def rewrite(self,root,change):
        path=root/self.pv.MANIFEST;value=json.loads(path.read_text());change(value);path.write_text(json.dumps(value))

    def test_known_real_pin_binding_changes_only_paths(self):
        real=load(PROPOSED/'autorouter/provenance.py','real_pure_pins')
        before=copy.deepcopy(self.real_lock)
        value=real.bound_tool_selection(self.real_lock,'10.0.7',self.paths)
        for role,pin in {**value['tools'],'java':value['java']}.items():
            old=self.real_lock['tools']['java'] if role=='java' else self.real_lock['native_profiles']['10.0.7'][role]
            self.assertEqual(pin,{**old,'path':self.paths[role]})
        self.assertEqual(self.real_lock,before)

    def test_partial_unknown_alias_and_mixed_bundle_bindings_refuse(self):
        bads=[{'java':self.paths['java']},{**self.paths,'shell':'/bin/sh'},[]]
        for value in ('relative/java','//host/java','/bad/../java','/bad/./java','/bad//java','/bad/java\n'):
            bads.append({**self.paths,'java':value})
        bads += [{**self.paths,'kicad_cli':str(self.base/'Other.app/Contents/MacOS/kicad-cli')},{**self.paths,'pcbnew':self.paths['pcbnew']+'.bad'}]
        alias=self.base/'Alias';alias.symlink_to(self.base/'Tools with spaces',target_is_directory=True)
        bads.append({k:v.replace(str(self.base/'Tools with spaces'),str(alias)) for k,v in self.paths.items()})
        for value in bads:
            with self.subTest(paths=value),self.assertRaises(ValueError):self.pv.bound_tool_selection(self.lock,'10.0.7',value)
        with self.assertRaises(ValueError):self.pv.bound_tool_selection(self.lock,'10.0.8',self.paths)

    def test_schema3_globals_and_fresh_binding_drift_refuse(self):
        root,_=self.artifact();self.rewrite(root,lambda x:x.update(schema=3,host_paths=self.paths))
        config=self.config(root)
        self.assertEqual(config.JAVA,Path(self.paths['java']))
        self.assertEqual(config.current_native_selection()['tools']['pcbnew']['path'],self.paths['pcbnew'])
        self.rewrite(root,lambda x:x['host_paths'].update(java=str(self.base/'different/bin/java')))
        with self.assertRaises(ValueError):config.current_native_selection()
        self.rewrite(root,lambda x:x.update(host_paths=self.paths));config=self.config(root)
        config.JAVA=Path('/different/java')
        with self.assertRaises(ValueError):config.current_native_selection()

    def test_original_v1_v2_selection_unchanged_and_schema3_closed(self):
        root,_=self.artifact(schema=1);config=self.config(root)
        self.assertEqual(config.NATIVE_VERSION,'10.0.0');self.assertNotIn('java',config.current_native_selection())
        self.rewrite(root,lambda x:x.update(schema=2,native_version='10.0.7'));config=self.config(root)
        self.assertEqual(config.NATIVE_VERSION,'10.0.7');self.assertNotIn('java',config.current_native_selection())
        self.rewrite(root,lambda x:x.update(schema=3,host_paths=self.paths,unknown=True))
        with self.assertRaises(ValueError):self.pv._runtime_identity(root,self.implementation(root))
        self.rewrite(root,lambda x:(x.pop('unknown'),x.pop('host_paths')))
        with self.assertRaises(ValueError):self.config(root)

    def test_transport_requires_explicit_mode_and_live_root_stays_strict(self):
        root,pin=self.artifact();(root/'.runs').mkdir();(root/'.runs/old').write_bytes(b'excluded')
        (root/'.venv').mkdir();(root/'.venv/old').write_bytes(b'excluded')
        original=(root/self.pv.MANIFEST).read_bytes();moved=self.base/'transported source';root.rename(moved)
        with self.assertRaises(ValueError):self.pv._runtime_identity(moved,self.implementation(moved))
        with self.assertRaises(ValueError):self.build.install_existing(moved,self.base/'default refuses',expected_manifest_sha256=pin)
        self.assertFalse((self.base/'default refuses').exists())
        with patch.object(self.pv,'_git',side_effect=AssertionError('No Git for artifact')):
            result=self.build.install_existing(moved,self.base/'installed',expected_manifest_sha256=pin,import_artifact=True)
        dest=Path(result['root']);record=json.loads((dest/self.pv.MANIFEST).read_text())
        self.assertEqual(record,{**json.loads(original),'root':str(dest)})
        self.assertFalse((dest/'.venv').exists());self.assertFalse((dest/'.runs/old').exists())
        self.assertEqual((moved/self.pv.MANIFEST).read_bytes(),original)
        self.pv._runtime_identity(dest,self.implementation(dest))

    def test_transport_wrong_pin_changed_payload_and_extra_entry_refuse(self):
        root,pin=self.artifact();impl=self.implementation(root)
        with self.assertRaises(ValueError):self.pv.transport_identity(root,impl,expected_manifest_sha256='0'*64)
        target=root/'autorouter/worker.py';old=target.read_bytes();target.write_bytes(b'tampered')
        with self.assertRaises(ValueError):self.pv.transport_identity(root,impl,expected_manifest_sha256=pin)
        target.write_bytes(old);(root/'extra').write_bytes(b'not allowed')
        with self.assertRaises(ValueError):self.pv.transport_identity(root,impl,expected_manifest_sha256=pin)

    def test_legacy_product_cannot_gain_binding_from_manifest_metadata(self):
        root,pin=self.artifact(binding_capable=False)
        with self.assertRaisesRegex(ValueError,'requires a compatible reviewed product build'):
            self.build.install_existing(root,self.base/'old code refuses',expected_manifest_sha256=pin,host_paths=self.paths)
        self.assertFalse((self.base/'old code refuses').exists())
        result=self.build.install_existing(root,self.base/'old code transport',expected_manifest_sha256=pin,import_artifact=True)
        self.assertEqual(json.loads((Path(result['root'])/self.pv.MANIFEST).read_text())['schema'],2)

    def test_bound_install_verifies_real_tiny_bytes_and_preserves_lock(self):
        root,pin=self.artifact();original=(root/'toolchain.lock.json').read_bytes()
        result=self.build.install_existing(root,self.base/'bound installed',expected_manifest_sha256=pin,host_paths=self.paths)
        dest=Path(result['root']);record=json.loads((dest/self.pv.MANIFEST).read_text())
        self.assertEqual((record['schema'],record['native_version'],record['host_paths']),(3,'10.0.7',self.paths))
        self.assertEqual((dest/'toolchain.lock.json').read_bytes(),original)
        self.assertEqual(self.config(dest).JAVA,Path(self.paths['java']))
        self.pv._runtime_identity(dest,self.implementation(dest))

    def test_first_setup_uses_explicit_engine_and_unmodified_tool_lock(self):
        root, _ = self.artifact()
        record = json.loads((root / self.pv.MANIFEST).read_bytes())
        payload = {name: (root / name).read_bytes() for name in record['build_source']['files_sha256']}
        source = self.base / 'reviewed source without local tools'
        source.mkdir()
        engine = self.base / 'pinned engine.jar'
        engine.write_bytes(self.engine)
        destination = self.base / 'first install'
        args = dict(native_version='10.0.7', freerouting_jar=engine, host_paths=self.paths)
        previous_payload = {**payload, 'autorouter/config.py': b'# Older binding reader'}
        with patch.object(self.pv, 'committed_snapshot', return_value=('a' * 40, previous_payload)):
            with self.assertRaisesRegex(ValueError, 'requires a compatible reviewed product build'):
                self.build.prepare(source, destination, **args)
        self.assertFalse(destination.exists())
        with patch.object(self.pv, 'committed_snapshot', return_value=('a' * 40, payload)):
            engine.write_bytes(b'wrong engine')
            with self.assertRaisesRegex(ValueError, 'does not match original lock'):
                self.build.prepare(source, destination, **args)
            self.assertFalse(destination.exists())
            engine.write_bytes(self.engine)
            java = Path(self.paths['java'])
            java.chmod(0o600)
            with self.assertRaisesRegex(ValueError, 'unavailable: java'):
                self.build.prepare(source, destination, **args)
            self.assertFalse(destination.exists())
            java.chmod(0o700)
            result = self.build.prepare(source, destination, **args)
        self.assertTrue(result['local_engine_copied'])
        self.assertEqual((destination / self.pv.ENGINE_PATH).read_bytes(), self.engine)
        self.assertEqual(engine.read_bytes(), self.engine)
        self.assertFalse((source / self.pv.ENGINE_PATH).exists())
        self.assertEqual((destination / 'toolchain.lock.json').read_bytes(), payload['toolchain.lock.json'])
        installed = json.loads((destination / self.pv.MANIFEST).read_bytes())
        self.assertEqual((installed['schema'], installed['host_paths']), (3, self.paths))
        self.assertEqual(self.config(destination).JAVA, java)

    def test_changed_missing_hardlinked_dependencies_refuse_before_output(self):
        root,pin=self.artifact();target=Path(self.paths['java']);original=target.read_bytes()
        for label in ('changed','missing','hardlink'):
            target.write_bytes(original);target.chmod(0o700)
            other=self.base/('link '+label)
            if label=='changed':target.write_bytes(b'wrong')
            elif label=='missing':target.unlink()
            else:os.link(target,other)
            destination=self.base/label
            with self.subTest(case=label),self.assertRaises((ValueError,OSError)):
                self.build.install_existing(root,destination,expected_manifest_sha256=pin,host_paths=self.paths)
            self.assertFalse(destination.exists())
            if other.exists():other.unlink()

    def test_dependency_changes_after_writer_retains_refused_output(self):
        root,pin=self.artifact();writer=self.build._write_runtime
        def changed(*args,**kwargs):
            result=writer(*args,**kwargs);Path(self.paths['java']).write_bytes(b'late tamper');return result
        with patch.object(self.build,'_write_runtime',side_effect=changed),self.assertRaises(ValueError):
            self.build.install_existing(root,self.base/'late refused',expected_manifest_sha256=pin,host_paths=self.paths)
        self.assertTrue((self.base/'late refused'/self.pv.MANIFEST).is_file())

    def test_transport_late_payload_mutation_refuses_without_git_fallback(self):
        root,pin=self.artifact();moved=self.base/'moved';root.rename(moved)
        writer=self.build._write_runtime
        def changed(*args,**kwargs):
            result=writer(*args,**kwargs);(moved/'autorouter/worker.py').write_bytes(b'late mutation');return result
        with patch.object(self.pv,'_git',side_effect=AssertionError('No fallback')),patch.object(self.build,'_write_runtime',side_effect=changed),self.assertRaises(ValueError):
            self.build.install_existing(moved,self.base/'refused late source',expected_manifest_sha256=pin,import_artifact=True)
        self.assertTrue((self.base/'refused late source'/self.pv.MANIFEST).is_file())

    def test_transport_malformed_pinned_json_and_source_alias_refuse(self):
        root,pin=self.artifact();manifest=root/self.pv.MANIFEST
        for raw in (b'{"schema":NaN}',b'{"schema":1,"schema":1}',b'['*2000+b']'*2000):
            manifest.write_bytes(raw)
            with self.subTest(raw=raw[:30]),self.assertRaises(ValueError):
                self.pv.transport_identity(root,self.implementation(root),expected_manifest_sha256=digest(raw))
        alias=self.base/'source alias';alias.symlink_to(root,target_is_directory=True)
        with self.assertRaises(ValueError):self.build.install_existing(alias,self.base/'alias destination',expected_manifest_sha256=pin,import_artifact=True)
        self.assertFalse((self.base/'alias destination').exists())

    def test_binding_never_uses_environment_and_tool_alias_change_refuses(self):
        root,_=self.artifact();self.rewrite(root,lambda x:x.update(schema=3,host_paths=self.paths))
        with patch.dict(os.environ,{'JAVA_HOME':'/wrong','KICAD_HOME':'/wrong','AUTOROUTER_JAVA':'/wrong'}):
            config=self.config(root)
        self.assertEqual(config.JAVA,Path(self.paths['java']))
        target=Path(self.paths['java']);saved=target.with_name('saved java');target.rename(saved);target.symlink_to(saved)
        with self.assertRaises(ValueError):config.current_native_selection()

    def test_executable_exemption_is_pcbnew_role_not_java_basename(self):
        root,pin=self.artifact()
        Path(self.paths['pcbnew']).chmod(0o600)  # The shared library need not execute.
        renamed=self.base/'renamed Java'/'_pcbnew.so'
        renamed.parent.mkdir();renamed.write_bytes(self.bytes['java']);renamed.chmod(0o600)
        paths=dict(self.paths,java=str(renamed))
        refused=self.base/'nonexecutable Java refuses'
        with self.assertRaisesRegex(ValueError,'pinned host tool'):
            self.build.install_existing(root,refused,expected_manifest_sha256=pin,host_paths=paths)
        self.assertFalse(refused.exists())
        renamed.chmod(0o700)
        result=self.build.install_existing(root,self.base/'executable Java accepted',expected_manifest_sha256=pin,host_paths=paths)
        self.assertEqual(self.config(Path(result['root'])).JAVA,renamed)

    def transported_schema3(self):
        root,_=self.artifact();self.rewrite(root,lambda x:x.update(schema=3,host_paths=self.paths))
        raw=(root/self.pv.MANIFEST).read_bytes();pin=digest(raw)
        moved=self.base/'transported schema3';root.rename(moved)
        old=Path(self.paths['java']);saved=old.with_name('saved old Java')
        old.rename(saved);old.symlink_to(saved)
        replacement=self.base/'new host'/'bin/java';replacement.parent.mkdir(parents=True)
        replacement.write_bytes(self.bytes['java']);replacement.chmod(0o700)
        return moved,pin,raw,dict(self.paths,java=str(replacement))

    def test_transport_schema3_old_alias_is_provenance_new_live_binding_stays_strict(self):
        moved,pin,raw,paths=self.transported_schema3()
        impl=self.implementation(moved)
        with self.assertRaises(ValueError):self.pv._runtime_identity(moved,impl)
        identity=self.pv.transport_identity(moved,impl,expected_manifest_sha256=pin)
        self.assertEqual(identity['manifest_sha256'],pin)
        result=self.build.install_existing(moved,self.base/'new bound host',
            expected_manifest_sha256=pin,import_artifact=True,host_paths=paths)
        dest=Path(result['root']);self.pv._runtime_identity(dest,self.implementation(dest))
        self.assertEqual((moved/self.pv.MANIFEST).read_bytes(),raw)
        config=self.config(dest);current=Path(paths['java']);saved=current.with_name('saved new Java')
        current.rename(saved);current.symlink_to(saved)
        with self.assertRaises(ValueError):config.current_native_selection()
        with self.assertRaises(ValueError):self.pv._runtime_identity(dest,self.implementation(dest))

    def test_transport_schema3_rebind_refuses_new_alias_nonexecutable_or_changed_bytes(self):
        moved,pin,_,paths=self.transported_schema3();current=Path(paths['java'])
        saved=current.with_name('saved replacement');current.rename(saved);current.symlink_to(saved)
        for label in ('alias','nonexecutable','changed'):
            if label=='nonexecutable':
                current.unlink();current.write_bytes(self.bytes['java']);current.chmod(0o600)
            elif label=='changed':
                current.write_bytes(b'changed bytes');current.chmod(0o700)
            destination=self.base/('new binding refuses '+label)
            with self.subTest(label=label),self.assertRaises(ValueError):
                self.build.install_existing(moved,destination,expected_manifest_sha256=pin,
                    import_artifact=True,host_paths=paths)
            self.assertFalse(destination.exists())

    def test_transported_schema3_still_refuses_noncanonical_recorded_paths(self):
        root,_=self.artifact()
        self.rewrite(root,lambda x:x.update(schema=3,host_paths=dict(self.paths,java='/bad/../java')))
        pin=digest((root/self.pv.MANIFEST).read_bytes());moved=self.base/'malformed transported schema3';root.rename(moved)
        with self.assertRaisesRegex(ValueError,'canonical absolute'):
            self.pv.transport_identity(moved,self.implementation(moved),expected_manifest_sha256=pin)

    def test_whole_pipeline_module_binds_actual_selected_paths(self):
        root,pin=self.artifact();result=self.build.install_existing(root,self.base/'bound',expected_manifest_sha256=pin,host_paths=self.paths)
        dest=Path(result['root'])
        name='owned_install_overlay_'+self.base.name
        package=types.ModuleType(name)
        package.__path__=[str(dest/'autorouter'),str(ROOT/'autorouter')]
        package.__file__=str(dest/'autorouter/__init__.py')
        # The entire real pipeline/config modules import from the fixture payload;
        # unchanged parser/runner modules resolve through the source package path.
        # Only the explicit fixture verifier/hash table is substituted as a dependency.
        with patch.object(autorouter,'provenance',self.pv,create=True),patch.dict(sys.modules,{
                name:package,name+'.provenance':self.pv,'autorouter.provenance':self.pv}), \
                patch('subprocess.run',side_effect=AssertionError('No subprocess in fixture')), \
                patch('subprocess.Popen',side_effect=AssertionError('No process in fixture')):
            pipeline=importlib.import_module(name+'.pipeline')
            self.assertEqual(Path(pipeline.__file__).resolve(),dest/'autorouter/pipeline.py')
            self.assertEqual((dest/'autorouter/pipeline.py').read_bytes(),(PROPOSED/'autorouter/pipeline.py').read_bytes())
            self.assertEqual(Path(pipeline.c.__file__).resolve(),dest/'autorouter/config.py')
            self.assertEqual(Path(pipeline.sx.__file__).resolve(),ROOT/'autorouter/sexpr.py')
            with patch.object(pipeline,'run',side_effect=AssertionError('No Native/engine run')):
                tools=pipeline.tool_manifest()
                self.assertEqual(set(tools['files']),set(self.paths.values())|{str(dest/self.pv.ENGINE_PATH)})
                pipeline.check_recorded_tool_pins(tools)
                old=copy.deepcopy(tools);old['files'].pop(self.paths['java'])
                with self.assertRaises(pipeline.Rejected):pipeline.check_recorded_tool_pins(old)
                Path(self.paths['java']).write_bytes(b'tampered')
                with self.assertRaises(pipeline.Rejected):pipeline.tool_manifest()


if __name__=='__main__':unittest.main(verbosity=2)
