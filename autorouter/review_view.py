"""Native copper plots for disposable review projects; never routing acceptance."""
from html import escape
from pathlib import Path
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as element_tree
from . import config as c, floor_route as f, pipeline as p, placement_clearance as pc, sexpr as sx
from . import local_settings as ls


KICAD_DOCTYPE = re.compile(rb'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\s+"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')


def display_svg(raw):
    """Remove only KiCad's observed standard declaration, without DTD loading."""
    without_declaration = re.sub(rb'\A(?:\xef\xbb\xbf)?<\?xml\s+[^?]*\?>', b'', raw, count=1)
    if b'<?' in without_declaration:
        raise p.Rejected('SVG processing instructions are unsupported')
    if b'<!ENTITY' in raw.upper():
        raise p.Rejected('external SVG declarations are unsupported')
    clean, count = KICAD_DOCTYPE.subn(b'', raw)
    if count > 1 or b'<!DOCTYPE' in clean.upper():
        raise p.Rejected('external SVG declarations are unsupported')
    return clean


def svg_bytes(path):
    raw = pc.read_bytes(path, 8 * 1024 * 1024)
    # Native plots are displayed as images, not inserted into the HTML DOM.
    # Reject active content or linked resources even if a plot is replaced.
    root = element_tree.fromstring(display_svg(raw))
    if root.tag != '{http://www.w3.org/2000/svg}svg':
        raise p.Rejected('native plot is not SVG')
    for node in root.iter():
        if node.tag.split('}')[-1] in {'script', 'foreignObject', 'image', 'use', 'style', 'animate', 'animateMotion', 'animateTransform', 'set', 'discard'}:
            raise p.Rejected('active or linked SVG content is unsupported')
        for key, value in node.attrib.items():
            if key.split('}')[-1].lower().startswith('on') or 'href' in key.lower() or 'url(' in value.lower():
                raise p.Rejected('linked SVG attribute is unsupported')
    return raw


def write_bound(path, raw):
    expected = hashlib.sha256(raw).hexdigest()
    path.write_bytes(raw)
    if p.sha(path) != expected:
        raise p.Rejected('preview output differs from intended bytes')
    return expected


def check_experimental_preview(destination, preview, native_toolchain=None, experimental_schematic_parity=False, *, comparison_context=None):
    """Replay existing SVG process/PRL proofs using only caller-selected tools."""
    if native_toolchain is None and comparison_context is None:
        _preview_request(destination,preview)
        return
    return _check_preview(destination,preview,native_toolchain,experimental_schematic_parity,
                          comparison_context=comparison_context)


def check_native_preview(destination, preview):
    """Replay normal SVG proofs against the current pinned native plotter.

    This supplies no routing or delivery authority. The caller must have
    checked its exact original receipt and complete review material first.
    """
    return _check_preview(destination,preview)


def _preview_request(destination, preview, native_toolchain=None, experimental_schematic_parity=False, *, comparison_context=None):
    from . import handoff as h
    h.application_kwargs(native_toolchain, experimental_schematic_parity, comparison_context)
    h.check_delivery_context(preview, native_toolchain, experimental_schematic_parity, comparison_context=comparison_context)
    from . import comparison as cmp
    cmp.delivery_path(Path(destination).absolute(),comparison_context,'review')
    if comparison_context is None and type(preview.get('html')) is str and cmp.marked(Path(preview['html']).parent):
        raise p.Rejected('comparison preview origin requires its caller context')


def _check_preview(destination, preview, native_toolchain=None, experimental_schematic_parity=False, *, comparison_context=None):
    from . import handoff as h, comparison as cmp
    _preview_request(destination,preview,native_toolchain,experimental_schematic_parity,
                     comparison_context=comparison_context)
    plotter=native_toolchain.cli if native_toolchain is not None else c.CLI
    if native_toolchain is not None:plotter_sha=native_toolchain.cli_sha256
    elif comparison_context is not None:plotter_sha=comparison_context.tools['files'][str(plotter)]
    else:
        pin=p.selected_tool_pins()['kicad_cli']
        if (c.resolve_tool_path(pin['path'])!=plotter or p.sha(plotter)!=pin['sha256']
                or plotter.stat().st_size!=pin['bytes']):
            raise p.Rejected('normal preview requires the current pinned plotter')
        plotter_sha=pin['sha256']
    destination = h.real_path(destination)
    before = pc.inventory(destination / 'before')
    boards = ([comparison_context.source.name] if comparison_context is not None else
        [name for name in before if Path(name).suffix == '.kicad_pcb'])
    if comparison_context is not None and before!=comparison_context.source_hashes:raise p.Rejected('comparison preview original source differs')
    if len(boards) != 1 or Path(boards[0]).name != boards[0]:
        raise p.Rejected('experimental preview needs one exact original PCB')
    board = boards[0]; tree = sx.read(destination / 'before' / board)
    layers = [sx.unquote(x[1]) for x in sx.one(tree, 'layers')[1:]
              if isinstance(x, list) and len(x) > 2 and re.fullmatch(r'(F|B|In[0-9]+)\.Cu', sx.unquote(x[1]))]
    if (len(layers) not in (2, 4) or len(set(layers)) != len(layers)
            or preview.get('layers') != layers or preview.get('plotter') != str(plotter)
            or preview.get('plotter_sha256') != plotter_sha):
        raise p.Rejected('experimental preview layers or caller plotter differ')
    root = destination / 'plot-work'; pairs = []; names = []; required = {'preview.html'}
    for layer in layers:
        for label in ('before', 'after'):
            name = label + '-' + layer; names.append(name)
            source = destination / ('before' if label == 'before' else 'project') / board
            work = root / (name + '-input'); target = root / 'native-plots' / (name + '.svg')
            required.update(str(path.relative_to(destination)) for path in (root / (name + '-input-binding.json'),
                root / (name + '-process.json'), root / (name + '.log'), target, root / 'plots' / (name + '.svg')))
            binding = f.read_json(root / (name + '-input-binding.json'))
            if (binding.get('source') != str(source) or binding.get('input') != str(work / board)
                    or binding.get('saved') is not False or binding.get('local_settings_policy') != ls.JOB_POLICY
                    or binding.get('before') != pc.inventory(source.parent)
                    or binding.get('after') != pc.inventory(work)
                    or preview.get('input_trees', {}).get(str(work.relative_to(destination))) != binding['after']):
                raise p.Rejected('experimental preview input binding changed')
            required.update(str((work / key).relative_to(destination)) for key in binding['after'])
            p.check_drc_project(binding['before'], binding['after'], board)
            argv = [*f.SANDBOX, str(plotter), 'pcb', 'export', 'svg', '--mode-single',
                    '--layers', layer + ',Edge.Cuts', '--fit-page-to-board', '--exclude-drawing-sheet',
                    '--output', str(target), str(work / board)]
            process = f.process_check(root, preview, name, argv)
            if (process.get('local_settings_policy') != ls.JOB_POLICY
                    or process.get('log') != str(root / (name + '.log'))
                    or process.get('log_truncated') is not False
                    or len(pc.read_bytes(root / (name + '.log'), 512 * 1024)) != process.get('log_bytes')):
                raise p.Rejected('experimental preview process/log binding changed')
            ls.check_event(root, binding, process)
            pairs.append((binding, process))
    if ([step.get('name') for step in preview.get('steps', [])] != names
            or set(preview.get('input_trees', {})) != {str((root / (name + '-input')).relative_to(destination)) for name in names}):
        raise p.Rejected('experimental preview stage census differs')
    if (set(preview.get('files', {})) != required or preview.get('html') != str(destination / 'preview.html')
            or preview.get('native_validation_performed') is not False or preview.get('zone_refill_performed') is not False):
        raise p.Rejected('experimental preview proof file census differs')
    p.experimental_native_version(native_toolchain)
    if comparison_context is not None:cmp.require_context(comparison_context)
    elif native_toolchain is None and p.sha(plotter)!=plotter_sha:
        raise p.Rejected('normal preview plotter changed during readback')
    # Flags and link counts are not byte hashes. Recheck after the last tool read.
    for binding, process in pairs:
        ls.check_event(root, binding, process)
    return [(root, binding, process) for binding, process in pairs]


def render(destination, source, candidate, report, remaining, material, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Called inside handoff's existing bounded freshness/publication transaction."""
    destination = Path(destination)
    from . import handoff as h
    ctx = h.delivery_kwargs(native_toolchain, experimental_schematic_parity)
    app=h.application_kwargs(native_toolchain,experimental_schematic_parity,comparison_context)
    from . import comparison as cmp
    cmp.delivery_path(destination,comparison_context,'review')
    if comparison_context is None and any(cmp.marked(Path(path).parent) for path in (source,candidate)):
        raise p.Rejected('comparison render inputs require their caller context')
    if comparison_context is not None and any(h.real_path(path)!=destination/folder/comparison_context.source.name
            for path,folder in ((source,'before'),(candidate,'project'))):
        raise p.Rejected('comparison render inputs differ from exact review copies')
    if comparison_context is not None or cmp.marked(destination,report):
        h.review_policy(report,comparison_context.output if comparison_context is not None else destination,**app)
    if native_toolchain is None:
        pin = p.selected_tool_pins()['kicad_cli']
        plotter = c.CLI
        if (c.resolve_tool_path(pin['path']) != plotter or p.sha(plotter) != pin['sha256']
                or plotter.stat().st_size != pin['bytes']):
            raise p.Rejected('pinned KiCad plotter changed')
    else:
        plotter = native_toolchain.cli
        pin = {'sha256': native_toolchain.cli_sha256}
    tree = sx.read(source)
    layers = [sx.unquote(x[1]) for x in sx.one(tree, 'layers')[1:]
              if isinstance(x, list) and len(x) > 2 and re.fullmatch(r'(F|B|In[0-9]+)\.Cu', sx.unquote(x[1]))]
    if len(layers) not in (2, 4) or len(layers) != len(set(layers)):
        raise p.Rejected('review plots require two or four distinct copper layers')
    job = f.FloorJob(destination / 'plot-work', remaining(), remaining, protect_local_settings=True, **ctx)
    plots = job.out / 'plots'; plots.mkdir()
    native_plots = job.out / 'native-plots'; native_plots.mkdir()
    rows = []; frozen = {}; input_trees = {}
    def stable():
        material()
        for directory, expected in input_trees.items():
            if pc.inventory(directory) != expected:
                raise p.Rejected('completed preview input file set changed')
        for name, expected in frozen.items():
            if p.sha(destination / name) != expected:
                raise p.Rejected('completed preview stage changed')
    for layer in layers:
        images = []
        for label, board in [('before', source), ('after', candidate)]:
            name = label + '-' + layer
            work = job.out / (name + '-input')
            before = pc.inventory(board.parent)
            shutil.copytree(board.parent, work)
            if pc.inventory(work) != before:
                raise p.Rejected('native plot input copy differs')
            target = native_plots / (name + '.svg')
            process = ls.protected_step(job, name, [plotter, 'pcb', 'export', 'svg', '--mode-single',
                     '--layers', layer + ',Edge.Cuts', '--fit-page-to-board', '--exclude-drawing-sheet',
                     '--output', target, work / board.name])
            after = pc.inventory(work)
            p.check_drc_project(before, after, board.name)
            input_trees[work] = after
            for relative, digest in after.items():
                frozen[str((work / relative).relative_to(destination))] = digest
            binding = job.out / (name + '-input-binding.json')
            payload = {'source': str(board), 'input': str(work / board.name), 'before': before, 'after': after,
                       'saved': False, 'local_settings_policy': ls.JOB_POLICY}
            ls.check_event(job.out, payload, process)
            frozen[str(binding.relative_to(destination))] = write_bound(binding, (json.dumps(payload, indent=2) + '\n').encode())
            native_raw = svg_bytes(target)
            frozen[str(target.relative_to(destination))] = hashlib.sha256(native_raw).hexdigest()
            display = plots / target.name
            frozen[str(display.relative_to(destination))] = write_bound(display, display_svg(native_raw))
            for path in (job.out / (label + '-' + layer + '.log'),
                         job.out / (label + '-' + layer + '-process.json')):
                frozen[str(path.relative_to(destination))] = p.sha(path)
            stable()
            images.append('<figure><figcaption>' + ('Original project' if label == 'before' else 'Candidate') +
                          '</figcaption><img alt="' + escape(label + ' ' + layer, quote=True) +
                          '" src="plot-work/plots/' + target.name + '"></figure>')
        rows.append('<section><h2>' + escape(layer) + '</h2><div class="pair">' + ''.join(images) + '</div></section>')
    native = report.get('final_drc', report.get('native', {}))
    metrics = report.get('metrics', {})
    summary = {key: native.get(key) for key in ('opens', 'blocking', 'warnings', 'exclusions')}
    ignored = native.get('ignored_checks')
    length = metrics.get('track_length_mm')
    summary_rows = [('Open connections', summary['opens']), ('Blocking findings', summary['blocking']),
                    ('Warnings', summary['warnings']), ('Exclusions', summary['exclusions']),
                    ('Ignored checks', len(ignored) if isinstance(ignored, list) else None),
                    ('Candidate track length', format(length, '.6f') + ' mm' if type(length) in (int, float) else None),
                    ('Candidate vias', metrics.get('vias'))]
    saved_summary = '<section><h2>Saved routing-check summary</h2><dl class="saved-summary">' + ''.join(
        '<dt>' + escape(label) + '</dt><dd>' + escape(str(value) if value is not None else 'Not recorded') + '</dd>'
        for label, value in summary_rows) + '</dl></section>'
    # The receipt schema is checked centrally by handoff; keep absent fields
    # explicit rather than inventing zero findings for another policy.
    details = escape(json.dumps({'saved_native_findings': summary,
                                'findings': native.get('findings', 'See original receipt'),
                                'candidate_metrics': metrics,
                                'ignored_checks': native.get('ignored_checks', 'See original receipt')}, indent=2))
    html = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\'; style-src \'unsafe-inline\'">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Routing review</title>'
            '<style>body{font:16px system-ui;margin:2rem;max-width:1400px;color:#17212b;background:#f7f8fa}'
            '.pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem}figure{margin:0;padding:1rem;background:white;border:1px solid #ccd2db}'
            'img{width:100%;height:auto}figcaption{font-weight:600;margin-bottom:1rem}pre{white-space:pre-wrap}'
            '.saved-summary{display:grid;grid-template-columns:max-content 1fr;gap:.25rem 1rem}'
            '.saved-summary dt{font-weight:600}.saved-summary dd{margin:0}summary{cursor:pointer}'
            '@media(max-width:700px){.pair{grid-template-columns:1fr}}</style>'
            '<h1>Routing review</h1><p>' + escape(candidate.name) + '</p>'
            '<p>These are KiCad plots of the exact original and candidate copper. Saved zone fills are shown; plotting does not refill zones or perform DRC. '
            'The original may already contain reference routes. Compare each layer at the same board extent.</p>'
            '<p>The candidate passed its recorded routing checks. All warnings still require review; this is not electrical or manufacturing approval. '
            'Open the candidate .kicad_pro in KiCad project manager, then Tools → PCB Editor. Run DRC with zone refill and every severity visible. '
            'To reject, close the disposable project and retain the original. To accept for further design work, keep this separate project; never overwrite an open source board. '
            'Any edit requires new validation.</p>' + saved_summary +
            '<p>Routing-check acceptance is separate from whole-project DRC cleanliness. '
            '<a href="#saved-details">Review all saved findings, warnings, exclusions and ignored checks</a> below the copper plots.</p>' +
            ''.join(rows) + '<details id="saved-details"><summary>All saved findings, ignored checks and candidate metrics (structured details)</summary><pre>' + details +
            '</pre></details></html>')
    frozen['preview.html'] = write_bound(destination / 'preview.html', html.encode())
    stable()
    if p.sha(plotter) != pin['sha256']:
        raise p.Rejected('KiCad plotter changed during rendering')
    result = {'plotter': str(plotter), 'plotter_sha256': pin['sha256'], 'layers': layers, 'steps': job.steps,
            'html': str(destination / 'preview.html'), 'native_validation_performed': False,
            'zone_refill_performed': False, 'rendered_input_routes': len(p.routes(tree)),
            'display_derivation': 'Exact native SVG bytes with only the observed standard SVG1.1 DOCTYPE removed; raw native plots retained separately. No external DTD or entity is loaded.',
            'input_trees': {str(directory.relative_to(destination)): expected for directory, expected in input_trees.items()},
            'files': frozen}

    if native_toolchain is not None or comparison_context is not None:
        result.update(h.delivery_record(**app))
        check_experimental_preview(destination, result, **app)
    return result
