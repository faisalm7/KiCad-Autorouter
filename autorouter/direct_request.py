"""Bounded local wording for the existing placement constraint fields."""

import re

from .placement_transform import nm


_COUNT_WORDS = {word: index for index, word in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen'.split())}
_COUNT_WORDS['both'] = 2
_COUNT = '|'.join(_COUNT_WORDS) + '|[0-9]{1,2}'
_PART = r'(?:parts?|components?|footprints?)'
_TARGET = (
    rf'(?:these|those|this)\s+(?:(?:{_COUNT})\s+)?(?:selected\s+)?{_PART}'
    rf'|(?:the\s+)?(?:(?:{_COUNT}|all)\s+)?(?:currently\s+)?selected\s+{_PART}'
    rf'|(?:the\s+)?(?:{_COUNT})\s+{_PART}\s+i\s+selected'
    rf'|the\s+{_PART}\s+i\s+selected|both\s+(?:the\s+)?{_PART}|them'
)
_RECTANGLE = r'(?:area|region|rectangle)'
_OUTLINE = r'(?:the\s+)?(?:board\s+outline|outline\s+of\s+the\s+board)'
_VISIBLE = rf'(?:this|the\s+(?:drawn|selected|marked|current))\s+{_RECTANGLE}'
_EARLIER = rf'(?:the\s+)?(?:same|previous)\s+{_RECTANGLE}'
_NUMBER = r'-?[0-9]{1,7}(?:\.[0-9]{1,12})?'
_PAIR = rf'{_NUMBER}\s*,\s*{_NUMBER}'
_POINT = rf'(?:\(\s*{_PAIR}\s*\)|{_PAIR})'
_COORDINATES = rf'(?P<start>{_POINT})\s+to\s+(?P<end>{_POINT})\s+mm'
_EXACT = rf'(?:(?:the\s+)?{_RECTANGLE}\s+)?(?:from\s+)?{_COORDINATES}'
_AREA = rf'(?:{_OUTLINE}|{_VISIBLE}|{_EARLIER}|{_EXACT})'
_OTHERS = rf'(?:(?:the\s+)?others|the\s+rest|everything\s+else|(?:all\s+)?(?:the\s+)?(?:other|unselected|remaining)\s+{_PART})'
_PROTECTIONS = r'(?:the\s+)?(?:protections|protected\s+(?:copper|routing|tracks|traces))'
_AFFECTED = r'(?:the\s+)?affected\s+(?:unlocked\s+)?(?:nets|connections)'
_SECONDS = r'(?:s|sec(?:onds?)?)'
_END = r'(?=\s*(?:$|[,.;!?\n]|\b(?:and|then)\s+))'
_JOIN = re.compile(r'(?:\s*[,.;!?\n]\s*(?:(?:and|then)\s+)?|\s+(?:and|then)\s+)', re.IGNORECASE)
_REF = re.compile(r'[A-Za-z][A-Za-z0-9_+.-]{0,63}')

_CLAUSES = tuple((role, re.compile(rf'(?:please\s+)?(?:{body}){_END}', re.IGNORECASE)) for role, body in (
    ('move', rf'(?:move|place)\s+(?P<parts>{_TARGET})(?:\s+(?:within|inside|in|into)\s+(?P<area>{_AREA}))?'),
    ('area', rf'(?:(?:use|choose)\s+|(?:change|set)\s+(?:the\s+)?(?:movement\s+)?{_RECTANGLE}\s+to\s+)'
             rf'(?P<area>{_AREA})(?:\s+instead)?'),
    ('time', rf'(?:(?:give|allow)\s+routing\s+(?P<seconds>[0-9]{{1,4}})\s+{_SECONDS}'
             rf'|(?:give|allow|use)\s+(?P<duration>[0-9]{{1,4}})\s+{_SECONDS}\s+(?:for\s+routing|to\s+route)'
             rf'|(?:set|change)\s+(?:the\s+)?routing\s+(?:budget|time)\s+to\s+(?P<budget>[0-9]{{1,4}})\s+{_SECONDS})'
             r'(?:\s+instead)?'),
    ('hold_area', rf'(?:keep|retain)\s+(?:the\s+)?(?:same\s+)?{_RECTANGLE}(?:\s+and\s+{_PROTECTIONS})?'),
    ('fixed', rf'(?:keep|leave|hold)\s+{_OTHERS}\s+(?:where\s+(?:they\s+are|it\s+is)|in\s+(?:place|their\s+(?:current\s+)?positions)|fixed|unchanged)'
              rf'|(?:do\s+not|don[\'’]t)\s+move\s+{_OTHERS}'),
    ('protected', rf'(?:preserve|keep|retain|leave)\s+{_PROTECTIONS}(?:\s+(?:unchanged|in\s+place))?'),
    ('all_copper', r'(?:preserve|keep|retain|leave)\s+(?:all\s+)?(?:the\s+)?existing\s+(?:copper|routing|tracks|traces)(?:\s+(?:unchanged|in\s+place))?'),
    ('reconnect', rf'(?:reconnect|route|rebuild)\s+(?:only\s+{_AFFECTED}|{_AFFECTED}(?:\s+only)?)'),
))


def _clauses(text):
    clauses = {}
    while text:
        for role, expression in _CLAUSES:
            match = expression.match(text)
            if match is not None:
                break
        else:
            raise ValueError('Could not read the whole request. Describe the selected parts, an area in mm and routing '
                             'time in whole seconds. Lock flags, copper permissions and electrical limits cannot be changed here.')
        if role in clauses:
            raise ValueError('Give each placement instruction once. Resolve repeated or conflicting clauses, then preview again.')
        clauses[role] = match.groupdict()
        tail = text[match.end():]
        if not tail or tail.strip() in ('.', '!', '?'):
            break
        separator = _JOIN.match(tail)
        if separator is None or not tail[separator.end():]:
            raise ValueError('Finish the placement request before previewing it.')
        text = tail[separator.end():]
    return clauses


def _references(value):
    if (type(value) not in (list, tuple) or len(value) > 16
            or any(type(ref) is not str or _REF.fullmatch(ref) is None for ref in value)
            or len(set(value)) != len(value)):
        raise ValueError('Choose up to sixteen distinct component references on the board.')
    return list(value)


def _bounds(value):
    if (type(value) not in (list, tuple) or len(value) != 4
            or any(type(n) is not int or abs(n) > 2_000_000_000 for n in value)
            or not (value[0] < value[2] and value[1] < value[3])):
        raise ValueError('Use an ordered movement rectangle with exact millimetre coordinates.')
    return list(value)


def _check_count(words, refs):
    words = words.lower().split()
    count = next((_COUNT_WORDS[word] if word in _COUNT_WORDS else int(word)
                  for word in words if word in _COUNT_WORDS or word.isascii() and word.isdecimal()), None)
    singular = any(word in ('part', 'component', 'footprint', 'this') for word in words)
    if (count is not None and count != len(refs)) or (singular and len(refs) != 1):
        raise ValueError(f'The request does not match the {len(refs)} selected parts. Change the selection or wording.')


def _area(area, *, region_nm, outline, explicit_area, previous_area):
    if area is None or re.fullmatch(_VISIBLE, area, re.IGNORECASE):
        if explicit_area:
            return _bounds(region_nm)
        if area is None and previous_area is not None:
            return previous_area
        raise ValueError('Draw or enter a movement area first, give rectangle coordinates in mm, or name the board outline.')
    if re.fullmatch(_OUTLINE, area, re.IGNORECASE):
        return outline
    if re.fullmatch(_EARLIER, area, re.IGNORECASE):
        if previous_area is None:
            raise ValueError('Preview a placement request before referring to the previous area.')
        return previous_area
    match = re.fullmatch(_EXACT, area, re.IGNORECASE)
    try:
        bounds = [nm(number.strip(), 1_000_000) for key in ('start', 'end')
                  for number in match[key].strip('()').split(',')]
    except ValueError as exc:
        raise ValueError('Enter millimetre coordinates within ±2000 mm at whole-nanometre precision.') from exc
    return _bounds(bounds)


def parse(text, *, selected_refs, region_nm, outline_nm, explicit_area, rebuild_copper, previous=None):
    """Interpret placement and follow-ups using only visible controls and passive prior values.

    The caller binds any previous values to the current source and controls.
    All output is proposal input for the shared checks and carries no permission.
    """
    try:
        plain_text = (type(text) is str and len(text.encode('utf-8')) <= 4096 and text.strip()
                      and all(char.isprintable() or char in '\t\r\n' for char in text))
    except UnicodeError:
        plain_text = False
    if not plain_text:
        raise ValueError('Enter a plain placement request of at most 4096 UTF-8 bytes.')
    if type(explicit_area) is not bool or type(rebuild_copper) is not bool:
        raise ValueError('Review the current area and existing copper controls before previewing.')

    clauses = _clauses(text.replace('\r\n', '\n').replace('\r', '\n').strip())
    refs = _references(selected_refs)
    if not refs:
        raise ValueError('Select the parts you want to move on the board first.')
    outline = _bounds(outline_nm)
    previous_area = None
    seconds = None
    if previous is not None:
        if type(previous) is not dict or set(previous) != {'selected_refs', 'region_nm', 'route_seconds'}:
            raise ValueError('Preview a placement request again before revising it.')
        if set(_references(previous['selected_refs'])) != set(refs):
            raise ValueError('The selected parts changed. Preview a new placement request.')
        previous_area = _bounds(previous['region_nm'])
        seconds = previous['route_seconds']
        if seconds is not None and (type(seconds) is not int or not 5 <= seconds <= 900):
            raise ValueError('Review the previous routing time before revising it.')

    if 'all_copper' in clauses and ('reconnect' in clauses or rebuild_copper):
        raise ValueError('Keeping all existing copper conflicts with rebuilding affected nets. Review the copper controls.')
    if 'reconnect' in clauses and not rebuild_copper:
        raise ValueError('Reconnecting affected nets requires choosing Rebuild affected unlocked nets in the copper controls first.')

    move = clauses.get('move')
    area = (move or {}).get('area')
    if move is not None:
        _check_count(move['parts'], refs)
    elif previous_area is None:
        raise ValueError('Preview a placement request before giving a follow-up about its area or routing time.')
    if not (clauses.keys() & {'move', 'time', 'area'}):
        raise ValueError('Describe a placement or give the setting to revise.')
    if 'area' in clauses:
        if area is not None:
            raise ValueError('Give one movement area, then preview again.')
        area = clauses['area']['area']
    if 'hold_area' in clauses:
        if area is not None:
            raise ValueError('Choose whether to keep the previous area or use a different area.')
        area = 'the previous area'

    bounds = (previous_area if move is None and area is None else
              _area(area, region_nm=region_nm, outline=outline, explicit_area=explicit_area, previous_area=previous_area))
    if not (outline[0] <= bounds[0] < bounds[2] <= outline[2] and outline[1] <= bounds[1] < bounds[3] <= outline[3]):
        raise ValueError('Keep the movement area inside the board outline.')
    if 'time' in clauses:
        seconds = int(next(value for value in clauses['time'].values() if value is not None))
        if not 5 <= seconds <= 900:
            raise ValueError('Use a whole-number routing time from 5 to 900 seconds.')
    return {'selected_refs': refs, 'region_nm': bounds, 'route_seconds': seconds}
