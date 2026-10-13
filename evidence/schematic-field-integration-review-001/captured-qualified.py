def qualified(native):
    """Only derived complete proofs qualify this particular warning family."""
    from . import schematic_fields
    proof=native.get('field_parity')
    return (isinstance(proof,dict) and proof.get('schema')==1 and proof.get('policy')==POLICY
            and schematic_fields.qualified(proof.get('qualification'),
                [row for row in native.get('findings',[]) if isinstance(row,dict) and row.get('type')==TYPE]))
