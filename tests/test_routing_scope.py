"""Pure selected-net controls. None establishes native routing acceptance."""
import copy
import hashlib
import unittest
import uuid

from autorouter import pipeline as p, routing_scope as rs, sexpr as sx


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-routing-scope/' + name))


def segment(name, net, *, lock=None, kind='segment'):
    mid = '(mid 1 1)' if kind == 'arc' else ''
    route = sx.parse(f'({kind} (start 0 0) {mid} (end 2 0) (width .2) '
                     f'(layer "F.Cu") (net {net}) (uuid "{uid(name)}"))')
    if lock is not None:
        route.append(lock)
    return route


def via(name, net):
    return sx.parse(f'(via (at 2 0) (size .8) (drill .4) (layers "F.Cu" "B.Cu") '
                    f'(net {net}) (uuid "{uid(name)}"))')


def board(*, modern=False):
    nets = '' if modern else '(net 0 "") (net 1 "GND") (net 2 "LED") (net 3 "OTHER")'
    pad = '(net "LED")' if modern else '(net 2 "LED")'
    tree = sx.parse(f'(kicad_pcb (version 20260206) (uuid "{uid("board")}") '
                    f'{nets} (setup (pad_to_mask_clearance 0)) '
                    f'(footprint "Owned" (uuid "{uid("footprint")}") '
                    f'(pad "1" smd rect {pad} (uuid "{uid("pad")}"))) '
                    '(zone (net "GND") (polygon (pts (xy 0 0) (xy 2 0) (xy 2 2))) '
                    '(filled_polygon (pts (xy 0 0) (xy 1 1))) (fill_segments (xy 0 0))))')
    tree.extend([segment('protected', '"GND"' if modern else '1'),
                 segment('selected', '"LED"' if modern else '2'),
                 via('selected-via', '"LED"' if modern else '2')])
    return tree


def raw(tree):
    return (sx.dump(tree) + '\n').encode()


class RoutingScopeTests(unittest.TestCase):
    def assert_rejected(self, original, changed, names=None):
        with self.assertRaises((ValueError, p.Rejected)):
            rs.audit(original, changed, names or ['LED'])

    def test_request_is_bounded_exact_unique_and_fresh(self):
        for value in (None, True, 'LED', (), [], [''], [' '], ['0'], ['LED', 'LED'],
                      [True], [1], ['LED\n'], ['a' * 1025], ['N' + str(i) for i in range(65)]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                rs.validate_names(value)
        names = [' LED ', 'other', 'Ω']
        captured = rs.validate_names(names)
        self.assertEqual(captured, names)
        self.assertIsNot(captured, names)
        self.assertEqual(len(rs.validate_names(['N' + str(i) for i in range(64)])), 64)

    def test_legacy_and_modern_tasks_keep_source_and_protection_exact(self):
        for modern in (False, True):
            with self.subTest(modern=modern):
                original = board(modern=modern)
                before = copy.deepcopy(original)
                task = rs.task(original, ['LED'])
                self.assertEqual(original, before)
                self.assertEqual(p.immutable(task), p.immutable(original))
                self.assertEqual(p.routes(task), [p.routes(original)[0]])
                self.assertEqual(sx.children(sx.one(task, 'zone'), 'filled_polygon'), [])
                self.assertEqual(sx.children(sx.one(task, 'zone'), 'fill_segments'), [])
                proof = rs.audit(original, task, ['LED'])
                self.assertEqual(proof['protected_count'], 1)
                self.assertFalse(proof['routing_accepted'])
                self.assertFalse(proof['native_validation_performed'])
                protected = rs.protected_routes(original, ['LED'])
                protected[0][1][1] = '999'
                self.assertEqual(original, before)

    def test_locked_selected_and_unknown_or_unnamed_original_routes_retained(self):
        for modern, lock in ((False, 'locked'), (True, ['locked']), (True, ['locked', 'yes'])):
            original = board(modern=modern)
            p.routes(original)[1].append(copy.deepcopy(lock))
            unknown = segment('unknown', '""' if modern else '999')
            unnamed = segment('unnamed', '""' if modern else '0')
            unnamed[:] = [field for field in unnamed if not (isinstance(field, list) and field[0] == 'net')]
            original.extend([unknown, unnamed])
            task = rs.task(original, ['LED'])
            expected = [p.routes(original)[i] for i in (0, 1, 3, 4)]
            self.assertEqual(p.routes(task), expected)
            self.assertTrue(rs.audit(original, task, ['LED'])['scope_passed'])
            changed = copy.deepcopy(task)
            changed.remove(p.routes(changed)[1])
            self.assert_rejected(original, changed)

    def test_modern_terminal_only_and_route_only_names_are_known(self):
        original = board(modern=True)
        original[:] = [node for node in original if node not in p.routes(original)]
        self.assertEqual(rs.bind(raw(original), ['LED'])['source_net_mapping'], 'modern_names')
        original.append(segment('route-only', '"ONLY_ROUTE"'))
        self.assertEqual(p.routes(rs.task(original, ['ONLY_ROUTE'])), [])
        for names in (['led'], ['UNKNOWN'], ['GND']):
            with self.subTest(names=names), self.assertRaises(p.Rejected):
                rs.task(original, names)

    def test_duplicate_or_inconsistent_legacy_mapping_rejected(self):
        for mode in ('code', 'name', 'net0', 'terminal_code', 'terminal_name', 'terminal_duplicate'):
            original = board()
            if mode == 'code':
                original.append(['net', '1', '"EXTRA"'])
            elif mode == 'name':
                original.append(['net', '4', '"LED"'])
            elif mode == 'net0':
                sx.children(original, 'net')[0][2] = '"ZERO"'
            else:
                pad = sx.one(sx.one(original, 'footprint'), 'pad')
                if mode == 'terminal_code':
                    sx.one(pad, 'net')[1] = '99'
                elif mode == 'terminal_name':
                    sx.one(pad, 'net')[2] = '"OTHER"'
                else:
                    pad.append(copy.deepcopy(sx.one(pad, 'net')))
            with self.subTest(mode=mode), self.assertRaises(p.Rejected):
                rs.task(original, ['LED'])

    def test_new_selected_segments_arcs_and_vias_allowed_only_in_scope(self):
        for modern in (False, True):
            original = board(modern=modern)
            task = rs.task(original, ['LED'])
            net = '"LED"' if modern else '2'
            task.extend([segment('new-segment', net), segment('new-arc', net, kind='arc'),
                         via('new-via', net)])
            self.assertEqual(rs.audit(original, task, ['LED'])['selected_route_count'], 3)
            for wrong in (('"OTHER"', '"NEW_UNKNOWN"', '""', '0') if modern else ('1', '3', '999', '0')):
                changed = copy.deepcopy(task)
                changed.append(segment('bad-new', wrong))
                self.assert_rejected(original, changed)

    def test_changed_selected_can_be_replaced_but_never_change_its_scope(self):
        original = board()
        candidate = copy.deepcopy(original)
        sx.one(p.routes(candidate)[1], 'start')[1] = '5'
        self.assertTrue(rs.audit(original, candidate, ['LED'])['scope_passed'])
        for net in ('1', '3', '999', '0'):
            changed = copy.deepcopy(candidate)
            sx.one(p.routes(changed)[1], 'net')[1] = net
            self.assert_rejected(original, changed)

    def test_protected_full_record_uuid_geometry_and_population_exact(self):
        original = board()
        for mode in ('delete', 'geometry', 'net', 'uuid', 'field_order', 'add_nonselected', 'lock'):
            changed = copy.deepcopy(original)
            route = p.routes(changed)[0]
            if mode == 'delete':
                changed.remove(route)
            elif mode == 'geometry':
                sx.one(route, 'end')[1] = '10'
            elif mode == 'net':
                sx.one(route, 'net')[1] = '2'
            elif mode == 'uuid':
                sx.one(route, 'uuid')[1] = '"' + uid('changed') + '"'
            elif mode == 'field_order':
                route[1:] = route[1:][::-1]
            elif mode == 'add_nonselected':
                changed.append(segment('extra-ground', '1'))
            else:
                route.append('locked')
            with self.subTest(mode=mode):
                self.assert_rejected(original, changed)
        changed = copy.deepcopy(original)
        routes = p.routes(changed)
        changed[:] = [node for node in changed if node not in routes] + routes[::-1]
        self.assertTrue(rs.audit(original, changed, ['LED'])['scope_passed'])

    def test_duplicate_invalid_or_immutable_collision_uuids_rejected(self):
        original = board()
        for mode in ('duplicate', 'case_duplicate', 'invalid', 'nil', 'pad_collision', 'duplicate_field'):
            changed = copy.deepcopy(original)
            route = p.routes(changed)[1]
            if mode == 'duplicate':
                changed.append(copy.deepcopy(route))
            elif mode == 'case_duplicate':
                second = copy.deepcopy(route)
                sx.one(second, 'uuid')[1] = '"' + uid('selected').upper() + '"'
                changed.append(second)
            elif mode == 'invalid':
                sx.one(route, 'uuid')[1] = '"not-a-uuid"'
            elif mode == 'nil':
                sx.one(route, 'uuid')[1] = '"00000000-0000-0000-0000-000000000000"'
            elif mode == 'pad_collision':
                sx.one(route, 'uuid')[1] = '"' + uid('pad') + '"'
            else:
                route.append(copy.deepcopy(sx.one(route, 'uuid')))
            with self.subTest(mode=mode):
                self.assert_rejected(original, changed)
        original.append(copy.deepcopy(p.routes(original)[0]))
        with self.assertRaises(p.Rejected):
            rs.task(original, ['LED'])

    def test_immutable_pad_zone_intent_and_rules_never_mutated(self):
        original = board()
        for mode in ('pad', 'zone', 'setup', 'header', 'net_table'):
            changed = copy.deepcopy(original)
            if mode == 'pad':
                sx.one(sx.one(original, 'footprint'), 'pad')
                sx.one(sx.one(changed, 'footprint'), 'pad')[1] = '"2"'
            elif mode == 'zone':
                sx.one(sx.one(changed, 'zone'), 'polygon')[1][1][1] = '99'
            elif mode == 'setup':
                sx.one(changed, 'setup').append(['clearance', '0'])
            elif mode == 'header':
                sx.one(changed, 'version')[1] = '20241229'
            else:
                sx.children(changed, 'net')[2][2] = '"RELABELLED"'
            with self.subTest(mode=mode):
                self.assert_rejected(original, changed)
        changed = copy.deepcopy(original)
        zone = sx.one(changed, 'zone')
        sx.one(zone, 'filled_polygon')[1][1][1] = '123'
        self.assertTrue(rs.audit(original, changed, ['LED'])['scope_passed'])

    def test_locks_cannot_be_ambiguous_or_added_to_generated_routes(self):
        for lock in (['locked', 'no'], ['locked', 'yes', 'extra'], 'locked'):
            original = board()
            route = p.routes(original)[1]
            route.extend([lock, copy.deepcopy(lock)])
            with self.subTest(lock=lock), self.assertRaises(p.Rejected):
                rs.task(original, ['LED'])
        original = board()
        changed = rs.task(original, ['LED'])
        changed.append(segment('locked-new', '2', lock='locked'))
        self.assert_rejected(original, changed)

    def test_binding_captures_raw_bytes_selection_order_and_fresh_records(self):
        original = board()
        source = raw(original)
        names = ['LED', 'OTHER']
        binding = rs.bind(source, names)
        self.assertEqual(binding['source_sha256'], hashlib.sha256(source).hexdigest())
        self.assertEqual(binding['requested_names'], names)
        self.assertNotEqual(binding['binding_sha256'], rs.bind(source, names[::-1])['binding_sha256'])
        self.assertNotEqual(binding['binding_sha256'], rs.bind(source + b'\n', names)['binding_sha256'])
        names[0] = 'changed'
        self.assertEqual(binding['requested_names'], ['LED', 'OTHER'])
        binding['protected_routes'][0]['uuid'] = 'changed'
        self.assertNotEqual(binding, rs.bind(source, ['LED', 'OTHER']))
        for bad in (None, b'', 'not bytes'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                rs.bind(bad, ['LED'])


if __name__ == '__main__':
    unittest.main()
