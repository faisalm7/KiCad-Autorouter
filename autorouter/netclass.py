"""Narrow native-resolved DSN netclass fidelity checks.

No pattern evaluator, source mutation, solver, or native execution occurs here.
The caller enforces supported board geometry and original-rule scope, binds the
native map to its immutable source, and validates imported geometry and DRC.
A mapping pass alone is never routing acceptance or proof of pin identities.
"""
from decimal import Decimal, InvalidOperation
import copy
import hashlib
import json
from pathlib import Path
import re


_DIMENSIONS = (
    ("width_nm", "track_width", "min_track_width"),
    ("clearance_nm", "clearance", "min_clearance"),
    ("via_diameter_nm", "via_diameter", "min_via_diameter"),
    ("via_drill_nm", "via_drill", "min_through_hole_diameter"),
)
PARENT_POLICY = 'native-parent-dimensions-v1'

# Prospective4Cu only: current2Cu validation/receipt branches remain unchanged.
FOUR_COPPER_NAMES = ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')
FOUR_COPPER_IDS = (0, 4, 6, 2)


def four_copper_source_layers(tree):
    """Exact modern4Cu ordinary signal declaration; no routing admission alone."""
    from . import sexpr as sx
    from .layer_policy import NONCOPPER
    if sx.one(tree, 'version') != ['version', '20260206']:
        raise ValueError('four-copper class transport requires20260206 source')
    table = sx.one(tree, 'layers')
    if table is None: raise ValueError('four-copper source layer table required')
    copper = []; names = set(); ids = set(); displays = set()
    canonical_names = {name.casefold() for name in (*FOUR_COPPER_NAMES, *NONCOPPER.values())}
    for row in table[1:]:
        if (type(row) is not list or len(row) not in (3, 4) or any(type(x) is not str for x in row)
                or not row[0].isdigit() or str(int(row[0])) != row[0]):
            raise ValueError('unqualified four-copper layer declaration')
        name = sx.unquote(row[1])
        if row[0] in ids or name in names: raise ValueError('duplicate source layer identity')
        ids.add(row[0]); names.add(name)
        if name.endswith('.Cu') or row[2] in {'signal','power','mixed','jumper'}:
            if row[2] != 'signal' or len(row) != 3:
                raise ValueError('four-copper signal layers without display aliases required')
            copper.append((int(row[0]), name))
        elif NONCOPPER.get(row[0]) != name or row[2] != 'user':
            raise ValueError('foreign or aliased source layer identity')
        elif len(row) == 4:
            # Display metadata never substitutes for physical IDs or canonical
            # names. Keep its original atom and all source geometry untouched.
            atom = row[3]
            if len(atom) > 514 or re.fullmatch(r'"(?:[^"\\]|\\["\\])*"', atom) is None:
                raise ValueError('bounded quoted noncopper display name required')
            display = sx.unquote(atom)
            try: size = len(display.encode('utf-8'))
            except UnicodeError: raise ValueError('invalid noncopper display name encoding') from None
            if (not 0 < size <= 256 or display != display.strip()
                    or any(ord(char) < 32 or ord(char) == 127 for char in display)):
                raise ValueError('invalid noncopper display name')
            folded = display.casefold()
            if (folded in canonical_names and display != name) or folded in displays:
                raise ValueError('colliding noncopper display name')
            displays.add(folded)
    expected = list(zip(FOUR_COPPER_IDS, FOUR_COPPER_NAMES))
    if copper != expected or table[1:5] != [[str(i), '"'+name+'"', 'signal'] for i,name in expected]:
        raise ValueError('four-copper source physical order/identity differs')
    stackup = sx.one(sx.one(tree,'setup',[]),'stackup')
    if stackup is not None:
        observed=[]
        for layer in sx.children(stackup,'layer'):
            if len(layer)<2 or type(layer[1]) is not str: raise ValueError('malformed source stackup layer')
            name=sx.unquote(layer[1]);kind=sx.one(layer,'type')
            if name.endswith('.Cu') or kind in (['type','copper'],['type','"copper"']):
                if kind not in (['type','copper'],['type','"copper"']): raise ValueError('four-copper stackup type differs')
                observed.append(name)
        if observed != list(FOUR_COPPER_NAMES): raise ValueError('four-copper stackup order differs')
    for route in sx.children(tree,'segment')+sx.children(tree,'arc'):
        layer=sx.one(route,'layer')
        if layer is None or len(layer)!=2 or sx.unquote(layer[1]) not in FOUR_COPPER_NAMES:
            raise ValueError('foreign four-copper route layer')
    for via in sx.children(tree,'via'):
        if (any(kind in via for kind in ('blind','buried','micro'))
                or sx.one(via,'layers')!=['layers','"F.Cu"','"B.Cu"']
                or sx.one(via,'padstack') is not None
                or sx.one(via,'remove_unused_layers') not in (None,['remove_unused_layers','no'])):
            raise ValueError('four-copper class scope requires uniform full through-vias')
    return list(FOUR_COPPER_NAMES)


def four_copper_native_layers(native):
    rows=native.get('copper_layers')
    expected=[{'id':i,'name':name,'type':'signal','index':index}
              for index,(i,name) in enumerate(zip(FOUR_COPPER_IDS,FOUR_COPPER_NAMES))]
    if (type(rows) is not list or len(rows)!=4
            or any(type(row) is not dict or set(row)!=set(wanted)
                or any(type(row[k]) is not type(value) or row[k]!=value for k,value in wanted.items())
                for row,wanted in zip(rows,expected))):
        raise ValueError('exact four-copper native layer identities required')
    return list(FOUR_COPPER_NAMES)


def _four_via_stack(via_id, stack):
    from . import sexpr as sx
    match=re.fullmatch(r'Via\[0-3\]_([0-9.]+):([0-9.]+)_um',via_id)
    if match is None or stack is None: raise ValueError('four-copper full through-via ID/padstack required')
    try:diameter,drill=(Decimal(value)*1000 for value in match.groups())
    except InvalidOperation: raise ValueError('malformed four-copper via dimensions') from None
    if not diameter.is_finite() or not drill.is_finite() or not 0<drill<diameter:
        raise ValueError('invalid four-copper via diameter/drill')
    _children_only(stack,{'shape','attach'},2)
    if sx.one(stack,'attach')!=['attach','off']: raise ValueError('four-copper via attachment differs')
    shapes=sx.children(stack,'shape');layers=[]
    for shape in shapes:
        circle=sx.one(shape,'circle')
        if len(shape)!=2 or circle is None or len(circle)!=3 or any(type(x) is not str for x in circle):
            raise ValueError('unqualified four-copper via shape')
        layers.append(sx.unquote(circle[1]))
        try:value=Decimal(circle[2])*1000
        except InvalidOperation: raise ValueError('malformed four-copper via shape diameter') from None
        if not value.is_finite() or value!=diameter: raise ValueError('four-copper via ID and copper shape disagree')
    if len(layers)!=4 or len(set(layers))!=4 or set(layers)!=set(FOUR_COPPER_NAMES):
        raise ValueError('four-copper through-via layer coverage differs')




def qualify_parent_project(project):
    """Experimental closed namespace; native KiCad alone resolves patterns.

    This does not enable the production pipeline. Transport controls must
    qualify the new policy before its preflight guard can admit it.
    """
    reject_tuning_intent(project)
    settings = project.get('net_settings')
    if not isinstance(settings, dict) or settings.get('netclass_assignments') not in (None, {}):
        raise ValueError('Explicit or inherited assignments outside parent policy')
    classes = settings.get('classes')
    if not isinstance(classes, list) or not 2 <= len(classes) <= 16:
        raise ValueError('Parent policy requires two through sixteen declared classes')
    names = []
    for cls in classes:
        if not isinstance(cls, dict): raise ValueError('Malformed declared class')
        name = cls.get('name')
        if (not isinstance(name, str) or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}', name) is None
                or name.casefold() in {'default', 'kicad_default'} and name != 'Default'):
            raise ValueError('Unambiguous literal class names required')
        names.append(name)
        priority = cls.get('priority')
        if type(priority) is not int or not 0 <= priority <= 2147483647:
            raise ValueError('Explicit bounded class priorities required')
        for _, key, _ in _DIMENSIONS: _millimetres_to_nm(cls.get(key))
        if cls['via_drill'] >= cls['via_diameter']: raise ValueError('Via drill exceeds copper')
    if 'Default' not in names or len(set(x.casefold() for x in names)) != len(names):
        raise ValueError('Unique Default and casefold-safe namespace required')
    patterns = settings.get('netclass_patterns')
    if not isinstance(patterns, list) or not 1 <= len(patterns) <= 1024:
        raise ValueError('Bounded native pattern definitions required')
    seen = set()
    for item in patterns:
        if not isinstance(item, dict) or set(item) != {'pattern', 'netclass'}:
            raise ValueError('Malformed native pattern definition')
        pattern = item['pattern']
        if (item['netclass'] not in names or item['netclass'] == 'Default' or not isinstance(pattern, str)
                or not pattern or len(pattern.encode('utf8')) > 4096 or any(ord(x) < 32 for x in pattern)
                or pattern in seen):
            raise ValueError('Unknown/default target or ambiguous native pattern definition')
        seen.add(pattern)
    return {'mode': PARENT_POLICY, 'resolution': 'pinned native effective class and explicit parameter parents',
            'source_class_names': names, 'pattern_evaluation_in_python': False}


def _parent_class(row, configured):
    """Decode pinned GetName only in the qualified comma-free namespace."""
    encoded = row['class']
    if len(encoded.encode('utf8')) > 4096: raise ValueError('Oversized native class identity')
    parts = encoded.split(',')
    if (not 1 <= len(parts) <= 2 or len(set(parts)) != len(parts) or any(x not in configured for x in parts)
            or len(parts) == 2 and (parts[1] != 'Default' or parts[0] == 'Default')):
        raise ValueError('Unqualified native constituent identity or order')
    return configured[parts[0]]



def _check_parameter_parents(row, cls):
    """Require each effective dimension's explicit same-source scalar parent."""
    parents = row.get('parameter_parents')
    if not isinstance(parents, dict) or set(parents) != {x[0] for x in _DIMENSIONS}:
        raise ValueError('Complete native parameter-parent observation required')
    for native_key, _, _ in _DIMENSIONS:
        parent = parents[native_key]
        if (not isinstance(parent, dict) or set(parent) != {'name', 'value_nm', 'specified', 'priority'}
                or parent['name'] != cls['name'] or parent['specified'] is not True
                or type(parent['priority']) is not int or parent['priority'] != cls['priority']
                or type(parent['value_nm']) is not int or parent['value_nm'] != row[native_key]):
            raise ValueError('Native dimension parent differs from explicit source definition')


def _millimetres_to_nm(raw, *, allow_zero=False):
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ValueError("Finite numeric dimensions required")
    value = Decimal(str(raw)) * 1000000
    if (not value.is_finite() or value < 0 or (value == 0 and not allow_zero)
            or value != value.to_integral_value()):
        raise ValueError("Dimensions must be finite exact nanometres in the permitted range")
    return int(value)


def _named(node, label):
    if len(node) < 2 or not isinstance(node[1], str):
        raise ValueError("Malformed " + label + " identifier")
    from autorouter import sexpr as sx
    return sx.unquote(node[1])


def _children_only(node, allowed, start=1):
    if any(not isinstance(x, list) or not x or x[0] not in allowed for x in node[start:]):
        raise ValueError("Malformed or unqualified " + str(node[0]) + " override")


def reject_tuning_intent(project):
    """Reject profile assignments/definitions independently of class routing scope.

    These are the pinned KiCad project fields, not meander UI preferences.
    Missing older fields and explicitly empty current fields remain inactive.
    No project value is rewritten and no severity semantics are admitted.
    """
    if not isinstance(project, dict):
        raise ValueError("Project JSON object required")
    settings = project.get("net_settings", {})
    if not isinstance(settings, dict):
        raise ValueError("Malformed net settings")
    classes = settings.get("classes", [])
    if not isinstance(classes, list):
        raise ValueError("Malformed netclass list")
    for cls in classes:
        if not isinstance(cls, dict):
            raise ValueError("Malformed netclass")
        if "tuning_profile" in cls:
            profile = cls["tuning_profile"]
            if not isinstance(profile, str):
                raise ValueError("Malformed netclass tuning profile")
            if profile:
                raise ValueError("Netclass tuning profiles not qualified")
    if "tuning_profiles" not in project:
        return
    definitions = project["tuning_profiles"]
    if (not isinstance(definitions, dict)
            or set(definitions) - {"meta", "tuning_profiles_impedance_geometric"}):
        raise ValueError("Unqualified tuning profile definitions schema")
    if "meta" in definitions:
        meta = definitions["meta"]
        if (not isinstance(meta, dict) or set(meta) != {"version"}
                or type(meta["version"]) is not int or meta["version"] != 0):
            raise ValueError("Unqualified tuning profile definitions schema")
    profiles = definitions.get("tuning_profiles_impedance_geometric", [])
    if not isinstance(profiles, list):
        raise ValueError("Malformed tuning profile definitions")
    if profiles:
        raise ValueError("Tuning profile definitions not qualified")


def qualify_project(project):
    """Admit Default alone, or one active-literal/Native-proven unused class.

    This is an eligibility whitelist, not a general netclass resolver. Native
    KiCad remains the source of the per-net effective class map.
    """
    reject_tuning_intent(project)
    settings = project.get("net_settings")
    if not isinstance(settings, dict):
        raise ValueError("Original net settings required")
    if settings.get("netclass_assignments") not in (None, {}):
        raise ValueError("Explicit or inherited netclass assignments not qualified")
    classes = settings.get("classes")
    if not isinstance(classes, list) or len(classes) not in (1, 2):
        raise ValueError("Only one or two fully specified netclasses qualified")
    patterns = settings.get("netclass_patterns")
    if patterns is None:
        patterns = []
    if not isinstance(patterns, list):
        raise ValueError("Malformed netclass pattern list")
    unused_second = len(classes) == 2 and not patterns
    names = []
    for cls in classes:
        if not isinstance(cls, dict) or not isinstance(cls.get("name"), str):
            raise ValueError("Malformed netclass")
        name = cls["name"]
        pattern = r"[A-Za-z0-9_]{1,64}" if unused_second else r"[A-Za-z_][A-Za-z0-9_]*"
        if (not re.fullmatch(pattern, name) or name == "kicad_default"
                or unused_second and name.casefold() in {"default", "kicad_default"} and name != "Default"):
            raise ValueError("Netclass identifier outside narrow scope")
        names.append(name)
        for _, key, _ in _DIMENSIONS:
            _millimetres_to_nm(cls.get(key))
        if cls["via_drill"] >= cls["via_diameter"]:
            raise ValueError("Via drill must be smaller than copper diameter")
        if any(cls.get(key) for key in ("tuning_profile", "tuning_profiles")):
            raise ValueError("Netclass tuning profiles not qualified")
    if len(set(names)) != len(names) or "Default" not in names:
        raise ValueError("Unique Default class required")
    if unused_second and len({name.casefold() for name in names}) != len(names):
        raise ValueError("Unique unused class namespace required")
    if len(classes) == 1:
        if patterns:
            raise ValueError("Patterns require the explicit second class")
        return {"mode": "single_default", "literal_assignments": {}}
    if unused_second:
        # Eligibility alone cannot prove inactivity. audit_native below requires
        # every actual Native net to remain Default, including padless nets.
        return {"mode": "literal_two_class", "literal_assignments": {}}
    nondefault = next(name for name in names if name != "Default")
    if not isinstance(patterns, list) or not 1 <= len(patterns) <= 1024:
        raise ValueError("A bounded list of literal assignments is required")
    assignments = {}
    for item in patterns:
        if not isinstance(item, dict) or set(item) != {"netclass", "pattern"}:
            raise ValueError("Malformed literal netclass assignment")
        if (item["netclass"] != nondefault or not isinstance(item["pattern"], str)
                or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", item["pattern"]) is None
                or item["pattern"] in assignments):
            raise ValueError("Only unique literal identifier assignments qualified")
        assignments[item["pattern"]] = nondefault
    return {"mode": "literal_two_class", "literal_assignments": assignments}


def audit_native(native, project, *, parent_policy=False, native_toolchain=None):
    """Check effective native classes against qualified original project settings.

    The caller must independently bind the native process/input/report hashes.
    Returned rows are copies of the validated native rows; this function does
    not infer connectivity, resolve patterns, or establish routing acceptance.
    """
    from . import pipeline as p
    expected_version = p.experimental_native_version(native_toolchain)
    if type(parent_policy) is not bool: raise ValueError('Explicit parent-policy flag required')
    policy = qualify_parent_project(project) if parent_policy else qualify_project(project)
    if (not isinstance(native, dict) or type(native.get("schema")) is not int or native.get("schema") != 1
            or native.get("native_version") != expected_version or native.get("units") != "integer nanometres"):
        raise ValueError("Unexpected native version")
    if 'copper_layers' in native: four_copper_native_layers(native)
    native_rows = native.get("nets")
    if not isinstance(native_rows, list) or not native_rows or len(native_rows) > 10000:
        raise ValueError("Missing or oversized native net inventory")
    codes = set()
    literal_composites = set()
    for row in native_rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"]:
            raise ValueError("Malformed native net record")
        if not isinstance(row.get("class"), str):
            raise ValueError("Malformed native class name")
        for key in ("netcode", "width_nm", "clearance_nm", "via_diameter_nm", "via_drill_nm", "copper_pad_count"):
            if type(row.get(key)) is not int or row[key] < (0 if key == "copper_pad_count" else 1):
                raise ValueError("Native dimensions/counts must be integer nanometres")
        if row["netcode"] in codes:
            raise ValueError("Duplicate native netcode")
        codes.add(row["netcode"])
        # Only these literal names are admitted by the policy; general patterns
        # remain unqualified. Actual DSN mapping still comes from native rows.
        if not parent_policy:
            expected_class = policy["literal_assignments"].get(row["name"], "Default")
            if row["class"] != expected_class:
                if (policy['mode'] == 'literal_two_class' and expected_class != 'Default'
                        and row['class'] == expected_class + ',Default'):
                    literal_composites.add(row['class'])
                else:
                    raise ValueError("Native class resolution differs from admitted literal assignment")
    records = {row["name"]: row for row in native_rows}
    if len(records) != len(native["nets"]):
        raise ValueError("Duplicate native net")
    configured = {item["name"]: item for item in project["net_settings"]["classes"]}
    if literal_composites:
        # Existing literal qualification already fixed every assignment. Reuse
        # the explicit priority/namespace guard without admitting new patterns.
        qualify_parent_project(project)
    try:
        floors = project["board"]["design_settings"]["rules"]
        if not isinstance(floors, dict):
            raise ValueError("Original board rule object required")
        minimums = {key: _millimetres_to_nm(floors[key], allow_zero=True) for _, _, key in _DIMENSIONS}
    except (KeyError, TypeError):
        raise ValueError("Original board dimension floors required") from None
    observed_classes = {row["class"] for row in records.values()}
    # Declared active assignments must exercise native nondefault resolution.
    # Empty assignments are the separately checked unused-definition scope;
    # its per-net expected-class check above permits only actual Default rows.
    if policy["mode"] == "literal_two_class" and policy["literal_assignments"] and observed_classes <= {"Default"}:
        raise ValueError("Native resolution did not exercise a nondefault class")
    if parent_policy and observed_classes <= {'Default'}:
        raise ValueError('Native parent resolution did not exercise a nondefault class')
    for row in records.values():
        require_parents = parent_policy or row['class'] in literal_composites
        cls = _parent_class(row, configured) if require_parents else configured.get(row["class"])
        if cls is None:
            raise ValueError("Composite/implicit native class outside this narrow audit")
        if require_parents:
            _check_parameter_parents(row, cls)
        for native_key, json_key, floor_key in _DIMENSIONS:
            value = Decimal(str(row[native_key]))
            if value != Decimal(str(cls[json_key])) * 1000000:
                raise ValueError("Native resolved class differs from original project value: " + native_key)
            if value < minimums[floor_key]:
                raise ValueError("Class parameter below original board floor: " + native_key)
    return {"passed": True, "policy": policy, "native_nets": len(records),
            "nets": copy.deepcopy(native_rows), "routing_accepted": False}


def audit_mapping(tree, native, project, *, parent_policy=False, native_toolchain=None):
    """Compare DSN to native-resolved membership; never evaluate pattern strings."""
    from autorouter import sexpr as sx
    from autorouter.adapter import _check_units

    verified = audit_native(native, project, parent_policy=parent_policy, native_toolchain=native_toolchain)
    policy = verified["policy"]
    records = {row["name"]: row for row in verified["nets"]}
    configured = {item["name"]: item for item in project["net_settings"]["classes"]}
    # Only audit_native-verified opaque identities may name a source definition.
    # Preserve Native/DSN strings and membership; never rewrite an export class.
    configured.update({row['class']: _parent_class(row, configured)
        for row in verified['nets'] if parent_policy or row['class'] not in configured})
    _check_units(tree)
    network, library, structure = (sx.one(tree, key) for key in ("network", "library", "structure"))
    if any(node is None for node in (network, library, structure)):
        raise ValueError("DSN is missing required network/library/structure")
    expected = {name for name, row in records.items() if row["copper_pad_count"] > 0}
    exported = [_named(node, "DSN net") for node in sx.children(network, "net")]
    if len(set(exported)) != len(exported) or set(exported) != expected:
        raise ValueError("DSN/native copper-terminal net inventory differs")
    _children_only(network, {"net", "class"})
    for net in sx.children(network, "net"):
        pins = sx.one(net, "pins")
        if pins is None or any(not isinstance(x, str) for x in pins[1:]):
            raise ValueError("Malformed DSN pins")
        if len(pins) - 1 != records[sx.unquote(net[1])]["copper_pad_count"]:
            raise ValueError("DSN/native terminal count differs")
        _children_only(net, {"pins"}, 2)
    layer_nodes = sx.children(structure, "layer")
    layers = {_named(x, "DSN layer") for x in layer_nodes}
    four = 'copper_layers' in native
    if four:
        expected_layers = four_copper_native_layers(native)
        if (len(layer_nodes)!=4 or [_named(x,"DSN layer") for x in layer_nodes]!=expected_layers
                or any(len(row)!=4 or sx.one(row,'type')!=['type','signal']
                       or sx.one(row,'property')!=['property',['index',str(i)]] for i,row in enumerate(layer_nodes))):
            raise ValueError('four-copper DSN physical layer order/index differs')
    elif len(layers) != 2 or len(layer_nodes) != 2:
        raise ValueError("Audit only understands two-layer through-via export")
    stacks = {_named(x, "DSN padstack"): x for x in sx.children(library, "padstack")}
    if len(stacks) != len(sx.children(library, "padstack")):
        raise ValueError("Duplicate DSN padstack identifier")
    declared_vias = sx.one(structure, "via")
    if declared_vias is None:
        raise ValueError("DSN via declaration missing")
    if any(not isinstance(x, str) for x in declared_vias[1:]):
        raise ValueError("Malformed DSN via declaration")
    via_names = [sx.unquote(x) for x in declared_vias[1:]]
    declared_vias = set(via_names)
    if len(declared_vias) != len(via_names):
        raise ValueError("Duplicate DSN via declaration")
    if four:
        for via_name in via_names: _four_via_stack(via_name,stacks.get(via_name))
    membership, classes, class_names = {}, [], set()
    for cls in sx.children(network, "class"):
        name = _named(cls, "DSN class")
        if name in class_names:
            raise ValueError("Duplicate DSN class")
        class_names.add(name)
        members = [sx.unquote(x) for x in cls[2:] if isinstance(x, str)]
        if len(members) != len(set(members)):
            raise ValueError("Duplicate class member")
        if any(not isinstance(x, str) and (not isinstance(x, list) or not x or x[0] not in {"rule", "circuit"}) for x in cls[2:]):
            raise ValueError("Unqualified DSN class override")
        rules, circuit = sx.one(cls, "rule"), sx.one(cls, "circuit")
        if rules is None or circuit is None:
            raise ValueError("Missing or unqualified DSN class rules")
        _children_only(rules, {"width", "clearance"})
        if len(circuit) != 2 or not isinstance(circuit[1], list) or circuit[1][0] != "use_via":
            raise ValueError("Unqualified DSN class circuit override")
        width, clearance = sx.one(rules, "width"), sx.one(rules, "clearance")
        via = sx.one(circuit, "use_via")
        if any(x is None or len(x) != 2 or not isinstance(x[1], str) for x in (width, clearance, via)):
            raise ValueError("Malformed class geometry")
        via_id = sx.unquote(via[1])
        match = re.fullmatch(r"Via\[0-3\]_([0-9.]+):([0-9.]+)_um" if four else r"Via\[0-1\]_([0-9.]+):([0-9.]+)_um", via_id)
        if not match or via_id not in declared_vias or via_id not in stacks:
            raise ValueError("Unknown native through-via ID or padstack")
        try:
            dimensions = {"width_nm": Decimal(width[1]) * 1000,
                          "clearance_nm": Decimal(clearance[1]) * 1000,
                          "via_diameter_nm": Decimal(match[1]) * 1000,
                          "via_drill_nm": Decimal(match[2]) * 1000}
        except InvalidOperation:
            raise ValueError("Malformed exported class dimension") from None
        if any(not value.is_finite() or value <= 0 for value in dimensions.values()):
            raise ValueError("Invalid exported class dimension")
        stack = stacks[via_id]
        _children_only(stack, {"shape", "attach"}, 2)
        if sx.one(stack, "attach") != ["attach", "off"]:
            raise ValueError("Unqualified via attachment semantics")
        project_class = configured.get("Default" if name == "kicad_default" else name)
        if project_class is None:
            raise ValueError("Unknown DSN class definition")
        for native_key, project_key, _ in _DIMENSIONS:
            if dimensions[native_key] != Decimal(str(project_class[project_key])) * 1000000:
                raise ValueError("DSN class differs from original project dimensions: " + name)
        shapes = sx.children(stack, "shape")
        shape_layers = set()
        for shape in shapes:
            circle = sx.one(shape, "circle")
            if (len(shape) != 2 or circle is None or len(circle) != 3
                    or not all(isinstance(x, str) for x in circle)):
                raise ValueError("Unqualified via shape")
            shape_layers.add(sx.unquote(circle[1]))
            try:
                diameter = Decimal(circle[2]) * 1000
            except InvalidOperation:
                raise ValueError("Malformed via copper diameter") from None
            if not diameter.is_finite() or diameter != dimensions["via_diameter_nm"]:
                raise ValueError("Via ID and actual copper shape disagree")
        if len(shapes) != (4 if four else 2) or shape_layers != layers:
            raise ValueError("Through-via layer coverage differs")
        for net in members:
            if net not in records or net in membership:
                raise ValueError("Unknown or multiply assigned DSN class member")
            row = records[net]
            expected_name = "kicad_default" if row["class"] == "Default" else row["class"]
            if name != expected_name or any(value != row[key] for key, value in dimensions.items()):
                raise ValueError("DSN class differs from native mapping for " + net)
            membership[net] = name
        classes.append({"dsn_class": name, "member_count": len(members),
                        "via": via_id, "dimensions_nm": {key: str(value) for key, value in dimensions.items()}})
    expected_classes = {"kicad_default"} | {row["class"] for row in records.values() if row["class"] != "Default"}
    if class_names != expected_classes:
        raise ValueError("DSN/native class definition inventory differs")
    if set(membership) != set(records):
        raise ValueError("Native net missing from explicit DSN classes")
    return {"passed": True, "native_nets": len(records), "exported_terminal_nets": len(expected),
            "policy": policy, "classes": classes, "membership": membership,
            "limitations": ["Via drill is encoded by pinned KiCad via ID.",
                            "Terminal counts do not prove pin identities.",
                            "Imported route geometry and native DRC require separate validation."],
            "routing_accepted": False}

def audit_dsn(path, native, project, *, parent_policy=False, native_toolchain=None):
    """Return a hash-bound, non-mutating mapping audit or fail closed."""
    from autorouter.adapter import _parse_dsn
    from autorouter import sexpr as sx
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > sx.MAX_BYTES:
        raise ValueError("Bounded regular DSN file required")
    raw = path.read_bytes()
    result = audit_mapping(_parse_dsn(raw.decode("utf-8")), native, project, parent_policy=parent_policy, native_toolchain=native_toolchain)
    if path.is_symlink() or path.read_bytes() != raw:
        raise ValueError("DSN changed during mapping audit")
    result["dsn_sha256"] = hashlib.sha256(raw).hexdigest()
    result["native_map_sha256"] = hashlib.sha256(json.dumps(native, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    result["project_json_sha256"] = hashlib.sha256(json.dumps(project, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    result["source_modified"] = False
    return result
