"""Project-owned validation/policy snapshot; receives already bounded decoded JSON.

Only file IO was removed from the original parse_report; validation body is exact.
"""
Rejected=ValueError

CRITICAL_CHECKS={'hole_clearance','hole_to_hole','hole_near_hole','starved_thermal','zones_intersect','padstack','items_not_allowed','through_hole_pad_without_hole','unconnected_items','shorting_items','clearance','track_width','via_diameter','annular_width','drill_out_of_range','copper_edge_clearance','invalid_outline','tracks_crossing'}

KNOWN_CHECKS = CRITICAL_CHECKS | set('annular_width clearance connection_width copper_edge_clearance copper_sliver courtyards_overlap creepage diff_pair_gap_out_of_range diff_pair_uncoupled_length_too_long drill_out_of_range duplicate_footprints extra_footprint footprint footprint_filters_mismatch footprint_symbol_mismatch footprint_type_mismatch hole_clearance hole_near_hole hole_to_hole holes_co_located invalid_outline isolated_copper item_on_disabled_layer items_not_allowed length_out_of_range lib_footprint_issues lib_footprint_mismatch malformed_courtyard microvia_drill_out_of_range mirrored_text_on_front_layer missing_courtyard missing_footprint net_conflict nonmirrored_text_on_back_layer npth_inside_courtyard overlapping_pads padstack pth_inside_courtyard shorting_items silk_edge_clearance silk_over_copper silk_overlap skew_out_of_range solder_mask_bridge starved_thermal text_height text_thickness through_hole_pad_without_hole too_many_vias track_angle track_dangling track_segment_length track_width tracks_crossing unconnected_items unresolved_variable via_dangling zones_intersect track_not_centered_on_via tuning_profile_track_geometries'.split())

def parse_data(data, board_name):
    if data.get('$schema')!='https://schemas.kicad.org/drc.v1.json' or data.get('kicad_version')!='10.0.0' or data.get('source')!=board_name:
        raise Rejected('validator report identity/schema/version mismatch')
    for key in ('violations','unconnected_items','schematic_parity','ignored_checks','included_severities'):
        if not isinstance(data.get(key),list): raise Rejected('validator report missing '+key)
    if set(data['included_severities'])!={'error','warning','exclusion'}: raise Rejected('validator omitted severities')
    if any(not isinstance(v,dict) or not isinstance(v.get('key'),str) or v['key'] not in KNOWN_CHECKS for v in data['ignored_checks']): raise Rejected('malformed or unknown ignored check')
    if any(v.get('key') in CRITICAL_CHECKS for v in data['ignored_checks']): raise Rejected('validator disabled required check')
    findings=data['violations']+data['unconnected_items']+data['schematic_parity']
    for v in findings:
        if not isinstance(v,dict) or v.get('severity') not in ('error','warning','exclusion') or not isinstance(v.get('type'),str) or not isinstance(v.get('items'),list):
            raise Rejected('invalid finding schema')
        if 'excluded' in v and type(v['excluded']) is not bool:
            raise Rejected('invalid finding exclusion flag')
    return {'opens':len(data['unconnected_items']), 'blocking':sum(v['severity']=='error' for v in data['violations']+data['schematic_parity']),
            'warnings':sum(v['severity']=='warning' for v in findings), 'exclusions':sum(v['severity']=='exclusion' or v.get('excluded',False) for v in findings),
            'ignored_checks':data['ignored_checks'],'findings':findings}

CRITICAL_FINDINGS = CRITICAL_CHECKS | {'padstack_invalid'}

def native_rejection_reasons(native):
    """Application policy over unchanged native evidence; never a DRC rewrite."""
    if not isinstance(native,dict) or any(type(native.get(k)) is not int or native[k]<0
                                        for k in ('opens','blocking','warnings','exclusions')):
        return ['malformed native summary counts']
    findings=native.get('findings')
    if not isinstance(findings,list): return ['missing native findings']
    ignored=native.get('ignored_checks')
    if not isinstance(ignored,list): return ['missing native ignored-check metadata']
    reasons=[]
    for check in ignored:
        if not isinstance(check,dict) or not isinstance(check.get('key'),str) or check['key'] not in KNOWN_CHECKS:
            return ['malformed or unknown native ignored check']
        if check['key'] in CRITICAL_FINDINGS:
            reasons.append('disabled policy-critical native check: '+check['key'])
    for key in ('opens','blocking','exclusions'):
        if native[key]: reasons.append('native '+key+'='+str(native[key]))
    for finding in findings:
        if (not isinstance(finding,dict) or not isinstance(finding.get('type'),str)
                or not finding['type'] or finding.get('severity') not in ('error','warning','exclusion')
                or not isinstance(finding.get('items'),list) or any(not isinstance(item,dict) for item in finding['items'])
                or ('excluded' in finding and type(finding['excluded']) is not bool)):
            return ['malformed native finding']
        # Error/exclusion checks also fail closed if a caller supplies dishonest
        # counters. check_result separately re-derives every counter from JSON.
        if finding['severity']=='error': reasons.append('native error finding: '+finding['type'])
        if finding['severity']=='exclusion' or finding.get('excluded',False):
            reasons.append('excluded native finding: '+finding['type'])
        if finding['type'] in CRITICAL_FINDINGS:
            reasons.append('policy-critical native finding: '+finding['type']+' ('+finding['severity']+')')
    return sorted(set(reasons))

def native_accepted(native):
    return not native_rejection_reasons(native)
