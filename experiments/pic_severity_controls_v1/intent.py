"""Prospective generic source-intent guard, NOT called by production routing."""
from autorouter import sexpr as sx

MACHINING={'backdrill','tertiary_drill','front_post_machining','back_post_machining'}
EDGE_GEOMETRY={'gr_line','gr_arc','gr_rect','gr_poly','gr_circle','fp_line','fp_arc','fp_rect','fp_poly','fp_circle'}
def audit(tree,project):
    reasons=[];profiles=[]
    if not isinstance(tree,list) or not tree or tree[0]!='kicad_pcb':raise ValueError('native board AST required')
    settings=project.get('net_settings')
    if not isinstance(settings,dict) or not isinstance(settings.get('classes'),list) or not settings['classes']:raise ValueError('class schema unsupported')
    names=[]
    for row in settings['classes']:
        if not isinstance(row,dict) or not isinstance(row.get('name'),str) or not row['name'] or not isinstance(row.get('tuning_profile'),str):raise ValueError('class profile schema unsupported')
        names.append(row['name']);profiles.append({'class':row['name'],'profile':row['tuning_profile']})
        if row['tuning_profile']:reasons.append('nonempty class tuning profile')
    if len(set(names))!=len(names) or 'Default' not in names:raise ValueError('ambiguous classes')
    definitions=project.get('tuning_profiles')
    if (not isinstance(definitions,dict) or set(definitions)!={'meta','tuning_profiles_impedance_geometric'}
            or definitions.get('meta')!={'version':0} or not isinstance(definitions.get('tuning_profiles_impedance_geometric'),list)):
        raise ValueError('profile definitions schema unsupported')
    if definitions['tuning_profiles_impedance_geometric']:reasons.append('tuning profile definitions unsupported')
    nodes=0
    def walk(node):
        nonlocal nodes
        if not isinstance(node,list):return
        nodes+=1
        if nodes>100000:raise ValueError('AST population cap')
        if not node or not isinstance(node[0],str):raise ValueError('malformed AST node')
        if node[0] in MACHINING:reasons.append('post-machining/backdrill intent')
        if node[0]=='generated':reasons.append('generated object intent unsupported')
        # Stackup owns many layer descriptors; it is not a board-item layer.
        layers=sx.children(node,'layer') if node[0]!='stackup' else []
        multilayers=sx.children(node,'layers')
        if any('Edge.Cuts'==sx.unquote(value) for group in multilayers for value in group[1:] if isinstance(value,str)):
            reasons.append('Edge.Cuts multilayer item unsupported')
        if len(layers)>1:raise ValueError('ambiguous layer declaration')
        if layers:
            if len(layers[0])!=2:raise ValueError('malformed layer declaration')
            if sx.unquote(layers[0][1])=='Edge.Cuts' and node[0] not in EDGE_GEOMETRY:reasons.append('text/dimension/unknown Edge.Cuts item')
        for child in node[1:]:
            if isinstance(child,list):walk(child)
    walk(tree)
    return {'prospective_guard_only':True,'source_intent_allowed':not reasons,'reasons':sorted(set(reasons)),
            'class_profiles':profiles,'schematic_parity_qualified':False,'production_support_changed':False}
