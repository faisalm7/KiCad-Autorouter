"""Native copper plots for disposable review projects; never routing acceptance."""
from html import escape
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from . import config as c, floor_route as f, pipeline as p, placement_clearance as pc, sexpr as sx


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
    root = ET.fromstring(display_svg(raw))
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


def render(destination, source, candidate, report, remaining, material):
    """Called inside handoff's existing bounded freshness/publication transaction."""
    destination = Path(destination)
    pin = f.read_json(c.ROOT / 'toolchain.lock.json')['tools']['kicad_cli']
    if c.resolve_tool_path(pin['path']) != c.CLI or p.sha(c.CLI) != pin['sha256']:
        raise p.Rejected('pinned KiCad plotter changed')
    tree = sx.read(source)
    layers = [sx.unquote(x[1]) for x in sx.one(tree, 'layers')[1:]
              if isinstance(x, list) and len(x) > 2 and re.fullmatch(r'(F|B|In[0-9]+)\.Cu', sx.unquote(x[1]))]
    if len(layers) not in (2, 4) or len(layers) != len(set(layers)):
        raise p.Rejected('review plots require two or four distinct copper layers')
    job = f.FloorJob(destination / 'plot-work', remaining(), remaining)
    plots = job.out / 'plots'; plots.mkdir()
    native_plots = job.out / 'native-plots'; native_plots.mkdir()
    rows = []; frozen = {}
    def stable():
        material()
        for name, expected in frozen.items():
            if p.sha(destination / name) != expected:
                raise p.Rejected('completed preview stage changed')
    for layer in layers:
        images = []
        for label, board in [('before', source), ('after', candidate)]:
            target = native_plots / (label + '-' + layer + '.svg')
            job.step(label + '-' + layer, [c.CLI, 'pcb', 'export', 'svg', '--mode-single',
                     '--layers', layer + ',Edge.Cuts', '--fit-page-to-board', '--exclude-drawing-sheet',
                     '--output', target, board])
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
    # The receipt schema is checked centrally by handoff; keep absent fields
    # explicit rather than inventing zero findings for another policy.
    details = escape(json.dumps({'saved_native_findings': summary, 'candidate_metrics': metrics,
                                'ignored_checks': native.get('ignored_checks', 'See original receipt')}, indent=2))
    html = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\'; style-src \'unsafe-inline\'">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Routing review</title>'
            '<style>body{font:16px system-ui;margin:2rem;max-width:1400px;color:#17212b;background:#f7f8fa}'
            '.pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem}figure{margin:0;padding:1rem;background:white;border:1px solid #ccd2db}'
            'img{width:100%;height:auto}figcaption{font-weight:600;margin-bottom:1rem}pre{white-space:pre-wrap}'
            '@media(max-width:700px){.pair{grid-template-columns:1fr}}</style>'
            '<h1>Routing review</h1><p>' + escape(candidate.name) + '</p>'
            '<p>These are KiCad plots of the exact original and candidate copper. Saved zone fills are shown; plotting does not refill zones or perform DRC. '
            'The original may already contain reference routes. Compare each layer at the same board extent.</p>'
            '<p>The candidate passed its recorded routing checks. All warnings still require review; this is not electrical or manufacturing approval. '
            'Open the candidate .kicad_pro in KiCad project manager, then Tools → PCB Editor. Run DRC with zone refill and every severity visible. '
            'To reject, close the disposable project and retain the original. To accept for further design work, keep this separate project; never overwrite an open source board. '
            'Any edit requires new validation.</p><details open><summary>Saved validation and candidate metrics</summary><pre>' + details +
            '</pre></details>' + ''.join(rows) + '</html>')
    frozen['preview.html'] = write_bound(destination / 'preview.html', html.encode())
    stable()
    if p.sha(c.CLI) != pin['sha256']:
        raise p.Rejected('KiCad plotter changed during rendering')
    return {'plotter_sha256': pin['sha256'], 'layers': layers, 'steps': job.steps,
            'html': str(destination / 'preview.html'), 'native_validation_performed': False,
            'zone_refill_performed': False, 'rendered_input_routes': len(p.routes(tree)),
            'display_derivation': 'Exact native SVG bytes with only the observed standard SVG1.1 DOCTYPE removed; raw native plots retained separately. No external DTD or entity is loaded.',
            'files': frozen}
