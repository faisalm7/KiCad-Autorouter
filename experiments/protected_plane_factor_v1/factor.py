"""Pure plane factor retaining captured Default floors and all other DSN data."""
import copy
import hashlib
from autorouter import adapter, default_targets, native_edge, sexpr as sx

POLICY = 'protected-default-plane-retention-factor-v1'


def plane_projection(tree):
    projected = copy.deepcopy(tree)
    structure = sx.one(projected, 'structure')
    if structure is None:
        raise ValueError('original DSN structure required')
    structure[:] = [row for row in structure if not (isinstance(row,list) and row and row[0]=='plane')]
    return projected


def transform(native_raw, native_map, project_raw, task_raw, *, export_source,
              captured_default, captured_derivation, obstacles, edge_context,
              captured_both_before_edge, captured_both, captured_both_edge):
    """Reproduce the old lawful both cell before creating exactly one new cell.

    No product scope is inferred from adapter='graphics'. Caller must bind and
    replay the complete captured original run and independently validate the
    new native candidate under unchanged original rules and Default targets.
    """
    guided, derivation = default_targets.transform(native_raw,native_map,project_raw,task_raw,source=export_source)
    if guided != captured_default or derivation != captured_derivation:
        raise ValueError('captured original Default-target transform differs')
    both, both_adapter = adapter.adapt_bytes(guided,'both',obstacles)
    old_final, old_edge = native_edge.correct(both,edge_context)
    if (both != captured_both_before_edge or old_final != captured_both or old_edge != captured_both_edge):
        raise ValueError('captured both/edge transport differs')
    graphics, graphics_adapter = adapter.adapt_bytes(guided,'graphics',obstacles)
    final, edge = native_edge.correct(graphics,edge_context)
    old_tree, new_tree = (adapter._parse_dsn(raw.decode()) for raw in (old_final,final))
    original_planes = sx.children(sx.one(adapter._parse_dsn(guided.decode()),'structure'),'plane')
    if (not original_planes or sx.children(sx.one(old_tree,'structure'),'plane')
            or sx.children(sx.one(new_tree,'structure'),'plane') != original_planes
            or plane_projection(new_tree) != old_tree
            or both_adapter['graphics_keepouts_added'] != graphics_adapter['graphics_keepouts_added']):
        raise ValueError('factor must differ only by complete original plane declarations')
    digest=lambda raw:hashlib.sha256(raw).hexdigest()
    return final, dict(schema=1,policy=POLICY,adapter='graphics',product_scope_admitted=False,
        default_target_derivation=derivation,adapter_transformations=graphics_adapter,
        native_edge_correction=edge,edge_adapter_input_sha256=digest(graphics),
        factor_plane_count=len(original_planes),factor_planes_sha256=digest(sx.dump(original_planes).encode()),
        captured_both_sha256=digest(captured_both),new_task_dsn_sha256=digest(final),
        exact_nonplane_AST_unchanged=True,reran_old_both=False)
