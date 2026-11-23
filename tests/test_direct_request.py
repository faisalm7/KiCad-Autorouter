import copy
import unittest

from autorouter import direct_request


REQUEST = ('Move these two parts within the board outline, leave the others where they are, '
           'preserve the protected copper, and reconnect only the affected nets. Give routing 80 seconds.')
FOLLOW_UP = 'Give routing 90 seconds; keep the area and protections.'
SELECTED = ['R1', 'R2']
OUTLINE = [23_000_000, 24_500_000, 42_500_000, 43_500_000]
DRAWN = [25_000_000, 27_000_000, 39_000_000, 40_000_000]


class DirectRequest(unittest.TestCase):
    def parse(self, text, **changes):
        options = dict(selected_refs=SELECTED, region_nm=DRAWN, outline_nm=OUTLINE,
                       explicit_area=True, rebuild_copper=True)
        return direct_request.parse(text, **(options | changes))

    def test_frozen_request_and_follow_up_keep_selection_and_outline(self):
        proposal = self.parse(REQUEST, explicit_area=False, region_nm=None)
        self.assertEqual(proposal, dict(selected_refs=SELECTED, region_nm=OUTLINE, route_seconds=80))
        before = copy.deepcopy(proposal)
        revised = self.parse(FOLLOW_UP, previous=proposal)
        self.assertEqual(revised, before | {'route_seconds': 90})
        revised['selected_refs'].append('R3')
        revised['region_nm'][0] = 25_000_000
        self.assertEqual(proposal, before)
        self.assertEqual(SELECTED, ['R1', 'R2'])
        self.assertEqual(OUTLINE[0], 23_000_000)

    def test_natural_variants_use_exact_visible_context(self):
        variations = [
            'Place the selected components inside this area. Keep unselected parts fixed. '
            'Keep protected traces unchanged. Route only the affected unlocked nets. Allow 75 s for routing.',
            'Move both selected parts into the drawn area and leave everything else in place. '
            'Set the routing budget to 75 seconds.',
            'Please place the two parts I selected within the current region. '
            'Don’t move the other parts. Use 75 seconds to route.',
            'Move these 2 selected footprints in the marked rectangle\nLeave the rest unchanged\nGive routing 75 sec.',
        ]
        for request in variations:
            with self.subTest(request=request):
                self.assertEqual(self.parse(request),
                                 dict(selected_refs=SELECTED, region_nm=DRAWN, route_seconds=75))
        self.assertEqual(self.parse('Move this component into this area.', selected_refs=['R2']),
                         dict(selected_refs=['R2'], region_nm=DRAWN, route_seconds=None))

    def test_follow_up_can_change_the_area_while_retaining_the_previous_time(self):
        proposal = self.parse(REQUEST)
        self.assertEqual(self.parse('Use this area instead.', previous=proposal),
                         proposal | {'region_nm': DRAWN})

    def test_first_request_requires_known_selection_and_area(self):
        for request, changes, message in (
            ('Move these parts inside this area.', {'selected_refs': []}, 'Select the parts'),
            ('Move these three parts inside this area.', {}, 'does not match the 2 selected'),
            ('Move this part inside this area.', {}, 'does not match the 2 selected'),
            ('Move these parts inside this area.', {'explicit_area': False, 'region_nm': OUTLINE}, 'Draw or enter'),
            ('Move these parts.', {'explicit_area': False, 'region_nm': OUTLINE}, 'Draw or enter'),
            ('Move these parts within the previous area.', {}, 'Preview a placement request'),
            (FOLLOW_UP, {}, 'Preview a placement request'),
        ):
            with self.subTest(request=request, changes=changes), self.assertRaisesRegex(ValueError, message):
                self.parse(request, **changes)

    def test_explicit_rectangle_is_exact_and_requires_millimetres(self):
        result = self.parse('Place these parts in the rectangle from (25.000001, 27) to (39, 40.000002) mm.')
        self.assertEqual(result['region_nm'], [25_000_001, 27_000_000, 39_000_000, 40_000_002])
        for coordinates, message in (
            ('(25.0000001, 27) to (39, 40) mm', 'whole-nanometre'),
            ('(25, 27) to (39, 40) in', 'whole request'),
            ('(25, 27 to (39, 40) mm', 'whole request'),
            ('24, 27 to 39, 44 mm', 'inside the board outline'),
            ('25, 27 to 24, 40 mm', 'ordered movement rectangle'),
        ):
            with self.subTest(coordinates=coordinates), self.assertRaisesRegex(ValueError, message):
                self.parse('Move these parts inside ' + coordinates)

    def test_preserving_copper_cannot_grant_or_change_rebuild_permission(self):
        with self.assertRaisesRegex(ValueError, 'requires choosing Rebuild affected unlocked nets'):
            self.parse(REQUEST, rebuild_copper=False)
        keep = 'Move these parts inside this area. Preserve all existing copper.'
        self.assertEqual(self.parse(keep, rebuild_copper=False)['selected_refs'], SELECTED)
        with self.assertRaisesRegex(ValueError, 'conflicts with rebuilding'):
            self.parse(keep)
        with self.assertRaisesRegex(ValueError, 'conflicts with rebuilding'):
            self.parse(keep + ' Reconnect the affected nets.', rebuild_copper=False)

    def test_unknown_or_conflicting_words_refuse_the_whole_request(self):
        for extra in (
            'Adjust impedance to 50 ohms.',
            'Unlock R3 and move it too.',
            'Disable protected copper.',
            'Only route the other nets.',
            'Move the connectors instead.',
            'Give routing 80 seconds and remove a protected track.',
            'Give routing 1 minute.',
            'Give routing 9.5 seconds.',
        ):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, 'whole request'):
                self.parse('Move these parts inside this area. ' + extra)
        for extra, message in (
            ('Give routing 901 seconds.', 'from 5 to 900'),
            ('Give routing 0 seconds.', 'from 5 to 900'),
            ('Give routing 60 seconds. Give routing 85 seconds.', 'repeated or conflicting'),
            ('Use the board outline.', 'one movement area'),
            ('Keep the area and protections.', 'keep the previous area or use a different area'),
        ):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, message):
                self.parse('Move these parts inside this area. ' + extra)

    def test_passive_prior_values_require_the_current_selection_and_expected_fields(self):
        proposal = self.parse(REQUEST)
        with self.assertRaisesRegex(ValueError, 'selected parts changed'):
            self.parse(FOLLOW_UP, previous=proposal, selected_refs=['R2', 'R3'])
        with self.assertRaisesRegex(ValueError, 'Preview a placement request again'):
            self.parse(FOLLOW_UP, previous=proposal | {'approval_granted': True})
        with self.assertRaisesRegex(ValueError, 'previous routing time'):
            self.parse(FOLLOW_UP, previous=proposal | {'route_seconds': True})

    def test_text_and_geometry_are_bounded(self):
        for text in (' ', REQUEST + '\0', 'é' * 2049, '\ud800'):
            with self.subTest(text=repr(text)[:50]), self.assertRaisesRegex(ValueError, '4096 UTF-8 bytes'):
                self.parse(text)
        with self.assertRaisesRegex(ValueError, 'ordered movement rectangle'):
            self.parse('Move these parts within the board outline.', outline_nm=[True, 0, 0, 2])
        with self.assertRaisesRegex(ValueError, 'distinct component references'):
            self.parse(REQUEST, selected_refs=['R1', 'R1'])


if __name__ == '__main__':
    unittest.main()
