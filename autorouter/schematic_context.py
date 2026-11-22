"""Read-only saved hierarchy and PCB pad assignments, without approval authority."""
import hashlib

from . import gui, placement_clearance as files, pipeline, schematic_hierarchy as hierarchy


def capture(board, expected):
    """Use the existing exact instance, symbol, unit and pad binding checks."""
    board = gui.saved_project_board(board)
    root = board.with_suffix('.kicad_sch').name
    names = [str(hierarchy._relative(name)) for name in expected if name.endswith('.kicad_sch')]
    if root not in names or not 1 <= len(names) <= hierarchy.MAX_FILES:
        raise ValueError('The saved schematic set is missing or outside the supported size.')

    def read(name):
        raw = files.read_bytes(board.parent / name)
        if hashlib.sha256(raw).hexdigest() != expected.get(name):
            raise ValueError('Saved files changed during schematic inspection.')
        return raw

    schematics = {name: read(name) for name in names}
    closure = hierarchy._closure(schematics, root)
    components, _ = hierarchy._symbols(*closure)
    tree = hierarchy.flat._tree(read(board.name), 'board', 'kicad_pcb')
    nets, _, _ = hierarchy._board(tree, components)
    if gui.source_inventory(board) != expected:
        raise ValueError('Saved files changed during schematic inspection.')
    pins = {reference: {} for reference in components}
    for net, terminals in nets.items():
        for reference, pin in terminals:
            pins[reference][pin] = net
    bindings = {}
    for reference, component in sorted(components.items()):
        units = [component['units'][i] for i in sorted(component['units'])]
        bindings[reference] = dict(
            file=units[0]['file'], sheet=list(component['names']), library=component['lib_id'],
            units=units, pin_nets=pins[reference],
        )
    return dict(
        schema=1, kind='autorouter.saved-schematic-context.v1', source=str(board),
        source_hashes=dict(expected), root=root, sheets=closure[1], components=bindings,
        pcb_nets={net: sorted(terminals) for net, terminals in sorted(nets.items())},
        connectivity_source='saved PCB pad assignments', electrical_validation_performed=False,
    )


def observe(board, expected):
    """Context refusal is informative and independent of placement eligibility."""
    try:
        return capture(board, expected), ''
    except (OSError, TypeError, ValueError, pipeline.Rejected) as exc:
        return None, str(exc).removeprefix('hierarchy parity: ')


def current(context, board):
    source = gui.saved_project_board(board)
    if (str(source) != context['source']
            or gui.source_inventory(source) != context['source_hashes']):
        raise ValueError('Saved project changed. Inspect the project again to refresh schematic context.')


def selection_summary(context, references, *, proposed=False):
    """Show the verified saved facts relevant to the visible selection."""
    if not references:
        return ''
    parts = [context['components'][ref] for ref in references if ref in context['components']]
    if not parts:
        return 'The selected components have no verified schematic link.'
    labels = ', '.join(ref if len(ref) <= 20 else ref[:19] + '…' for ref in references[:3])
    if len(references) > 3:
        labels += f' +{len(references) - 3}'
    sheets = {' / '.join(part['sheet']) or 'Root sheet' for part in parts}
    if len(parts) < len(references):
        linked = f'{len(parts)} of {len(references)} linked'
    elif len(sheets) == 1:
        linked, = sheets
    else:
        linked = f'{len(sheets)} schematic sheets'
    if len(linked) > 46:
        linked = linked[:45] + '…'
    nets = sorted({net for part in parts for net in part['pin_nets'].values()})
    names = ', '.join(net if len(net) <= 24 else net[:23] + '…' for net in nets[:3])
    if len(nets) > 3:
        names += f' +{len(nets) - 3}'
    prefix = 'Suggested' if proposed else 'Selected'
    return f'{prefix} {labels} · {linked}\nSaved PCB nets · ' + (names or 'none assigned')


def describe(context, references):
    """Present linked source facts and bounded peers for the components in view."""
    if context is None:
        raise ValueError('Saved schematic context is unavailable.')
    sheets = context['sheets']
    lines = [
        'Saved schematic · ' + context['root'],
        f"{len(sheets)} sheet instance{'s' if len(sheets) != 1 else ''} · "
        f"{len(context['components'])} linked PCB components",
    ]
    for instance in sheets:
        sheet = ' / '.join(instance['names']) or 'Root sheet'
        lines.append(f"{sheet}  ·  {instance['file']}")
    if not references:
        lines.extend(('', 'Select components on the board or in Settings to see their pins and connections.'))
    for ref in references:
        part = context['components'].get(ref)
        lines.append('')
        if part is None:
            lines.append(f'{ref} has no verified schematic link in this capture.')
            continue
        sheet = ' / '.join(part['sheet']) or 'Root sheet'
        lines.extend((f'{ref}  ·  {sheet}', part['library']))
        for pin, net in sorted(part['pin_nets'].items()):
            peers = [f'{other}.{number}' for other, number in context['pcb_nets'][net]
                     if (other, number) != (ref, pin)]
            others = ', '.join(peers[:5])
            if len(peers) > 5:
                others += f' and {len(peers) - 5} more'
            lines.append(f'Pin {pin}  ·  {net}' + (f'  →  {others}' if others else '  ·  no other pad'))
    lines.extend(('', 'Pin and net data come from saved PCB pad assignments. '
        'Schematic wiring, routed continuity and electrical suitability require separate checks. '
        'Save and re-inspect to include unsaved edits.'))
    return '\n'.join(lines)
