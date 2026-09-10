#!/usr/bin/env python3
"""Generate the README's visual furniture as dual-theme SVGs.

Design rules this follows, and why:

* Anything GitHub can render natively stays native markdown. `##` already
  gives a bold heading with a hairline rule underneath, in the reader's own
  theme - reproducing that as an image would cost ~6 KB per heading, lose the
  anchor link, and get the theme wrong for some readers.
* Small labels (tag pills) use SVG <text> with a system font stack, the same
  approach the 47 toolkit badges already take. At 11px the typeface is not
  legible as a typeface, so outlining it would be bytes for nothing.
* Display text uses the same system stack. Outlining Figtree to <path> was
  tried and rejected: it renders identically everywhere, but the exploring
  card came to 44 KB and the stat strip 22 KB - two thirds of the entire
  README payload for a typeface nobody can identify at 14px.
* Every asset ships light + dark. The README picks one with <picture> +
  prefers-color-scheme, so a reader downloads only their own variant.

    python3 tools/build-readme-assets.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

OUT = pathlib.Path('assets/ui')
SYS = 'system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif'

# ── tokens ──────────────────────────────────────────────────────────────────
T = {
    'light': dict(
        ink='#1f2328', muted='#59636e', rule='#d1d9e0',
        stripA='#fdeaf4', stripB='#eefbf7', stripLine='#f7d3e5', stripInk='#7d2456',
        cardA='#fdf0f7', cardB='#edf9f6', cardLine='#f6dbe9', cardInk='#7d2456',
        chipBg='#ffffff', chipLine='#f0d6e4', chipInk='#5c2545',
        tag=dict(pink=('#fdeaf4', '#a8266e'), blue=('#eef7ff', '#1f5c9e')),
        tile=dict(pink=('#ffe6f4', '#c91873'), mint=('#dcf6f0', '#0d7a68'),
                  sky=('#e2effd', '#1c5fa6'), lilac=('#ede6ff', '#6335c0'),
                  amber=('#ffefd9', '#a2611b'), rose=('#ffe6e9', '#b53042')),
    ),
    'dark': dict(
        ink='#e6edf3', muted='#8d96a0', rule='#30363d',
        stripA='#2b1a26', stripB='#152522', stripLine='#48293b', stripInk='#f6b6d5',
        cardA='#241726', cardB='#14231f', cardLine='#3b2836', cardInk='#f6b6d5',
        chipBg='#1b1620', chipLine='#3d2b39', chipInk='#f0c4dc',
        tag=dict(pink=('#3a2130', '#f3a4cb'), blue=('#182634', '#79b8f5')),
        tile=dict(pink=('#3a2130', '#f79ecb'), mint=('#16302b', '#5fd8c0'),
                  sky=('#182a3f', '#79b8f5'), lilac=('#271f3f', '#b79bf5'),
                  amber=('#33260f', '#e5ac5c'), rose=('#361c20', '#f2909c')),
    ),
}

# ── icon geometry (stroked, drawn on a 24x24 grid) ──────────────────────────
ICONS = {
    'identity':  'M12 3l8 3v6c0 5.4-8 9.6-8 9.6S4 17.4 4 12V6z M12 8.6v6.4',
    'plane':     'M20.5 12.6 3.6 18.1l-.9-2.3 5.2-3.4L4.4 9l-2 .6-1-2.1 3-1.4 '
                 '12.8 3.4 1.9-1.8a2 2 0 0 1 2.7 2.9z',
    'marine':    'M12 6.5V21 M6.5 9.5h11 M3.4 12.6a8.6 8.6 0 0 0 17.2 0',
    'vision':    'M3 4.5h18v15H3z M7.4 17.2a5 5 0 0 1 9.2 0',
    'track':     'M12 21s7-6.1 7-11a7 7 0 1 0-14 0c0 4.9 7 11 7 11z',
    'sail':      'M12 3.2 18.4 15H5.6z M3 18.4c1.4 1.4 2.6 1.4 4 0s2.6-1.4 4 0 '
                 '2.6 1.4 4 0 2.6-1.4 4 0',
    'contracts': 'M8.5 8 5 12l3.5 4 M15.5 8l3.5 4-3.5 4',
    'security':  'M12 3l7 2.6v6c0 4.8-7 9.4-7 9.4S5 16.4 5 11.6v-6z',
    'observe':   'M4 19V9 M10 19V5 M16 19v-7 M22 19H2',
    'architect': 'M3 3.5h7v7H3z M14 3.5h7v7h-7z M3 13.5h7v7H3z M14 13.5h7v7h-7z',
    'mobile':    'M7 2.5h10v19H7z M11 18.6h2',
    'mentor':    'M2.5 20a6.5 6.5 0 0 1 13 0 M17 5.5a3 3 0 0 1 0 5.4 '
                 'M18.5 20a6 6 0 0 0-3-5.2',
}
CIRCLES = {'vision': (12, 11, 2.6), 'track': (12, 10, 2.6), 'marine': (12, 4.6, 1.9),
           'mentor': (9, 8, 3.2)}


# Narrow / wide glyphs, so a pill fits its label without measuring a font we
# do not control. Deliberately generous - a slightly loose pill reads fine, a
# clipped one does not.
_NARROW, _WIDE = set("iljtfIr!.,;:'|()[] "), set("mwMW@%")


def est_width(text, size, bold=False):
    u = 0.0
    for ch in text:
        u += 0.30 if ch in _NARROW else 0.86 if ch in _WIDE else 0.58
    return u * size * (1.03 if bold else 1.0)


def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def svg(w, h, body, extra=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img"{extra}>{body}</svg>')


def write(name, content):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def icon_body(key, cx, cy, size, colour, sw=1.85):
    """Stroked icon drawn on the 24-grid, scaled and centred on (cx, cy).

    stroke-width stays in grid units so it scales with the icon, which is what
    keeps the weight looking consistent between the 56px card tiles and the
    44px approach tiles.
    """
    s = size / 24
    parts = [f'<path d="{ICONS[key]}" fill="none" stroke="{colour}" '
             f'stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round"/>']
    if key in CIRCLES:
        x, y, r = CIRCLES[key]
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{colour}" '
                     f'stroke-width="{sw:.2f}"/>')
    return (f'<g transform="translate({cx-size/2:.2f} {cy-size/2:.2f}) scale({s:.4f})">'
            f'{"".join(parts)}</g>')


# ── builders ────────────────────────────────────────────────────────────────
def build_tile(name, icon, hue, theme):
    t = T[theme]; bg, fg = t['tile'][hue]
    body = (f'<rect width="56" height="56" rx="16" fill="{bg}"/>'
            + icon_body(icon, 28, 28, 26, fg))
    return svg(56, 56, body, f' aria-label=""')


def build_appr(name, icon, hue, theme):
    t = T[theme]; bg, fg = t['tile'][hue]
    body = (f'<rect width="44" height="44" rx="13" fill="{bg}"/>'
            + icon_body(icon, 22, 22, 21, fg, sw=2))
    return svg(44, 44, body, ' aria-label=""')


def build_tags(labels_hues, theme):
    """A row of pill tags as one image - one request per card instead of two."""
    t = T[theme]; pad, gap, h, fs = 10, 6, 21, 11
    x, parts = 0, []
    for label, hue in labels_hues:
        bg, fg = t['tag'][hue]
        w = round(est_width(label, fs, bold=True)) + pad * 2
        parts.append(f'<rect x="{x}" y="0" width="{w}" height="{h}" rx="{h/2}" fill="{bg}"/>'
                     f'<text x="{x + w/2}" y="{h/2 + fs*0.35:.1f}" text-anchor="middle" '
                     f'font-family="{SYS}" font-size="{fs}" font-weight="600" '
                     f'fill="{fg}">{esc(label)}</text>')
        x += w + gap
    alt = ' - '.join(l for l, _ in labels_hues)
    return svg(x - gap, h, f'<title>{esc(alt)}</title>' + ''.join(parts))


def build_strip(theme):
    """Two fixed columns, so the layout does not depend on font metrics we
    cannot measure on the reader's machine."""
    t = T[theme]
    W, H, r, fs = 880, 52, 12, 15
    cols = [(22, 'calendar', '14+ years', ' building software'),
            (452, 'mentor', '60+ interns / developers', ' mentored')]
    parts = [f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0.4">'
             f'<stop offset="0" stop-color="{t["stripA"]}"/>'
             f'<stop offset="1" stop-color="{t["stripB"]}"/></linearGradient></defs>'
             f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="{r}" '
             f'fill="url(#g)" stroke="{t["stripLine"]}"/>'
             f'<rect x="428" y="13" width="1" height="{H-26}" fill="{t["stripLine"]}"/>']
    for x, icon, bold, rest in cols:
        if icon == 'calendar':
            parts.append(f'<g transform="translate({x} {H/2-9})" fill="none" '
                         f'stroke="{t["stripInk"]}" stroke-width="1.7" stroke-linecap="round">'
                         f'<rect x="1" y="2.5" width="16" height="14" rx="3"/>'
                         f'<path d="M5.5 1v3.5M12.5 1v3.5M1 7.5h16"/></g>')
        else:
            parts.append(f'<g transform="translate({x} {H/2-9}) scale(0.8)" fill="none" '
                         f'stroke="{t["stripInk"]}" stroke-width="2.2" stroke-linecap="round" '
                         f'stroke-linejoin="round"><circle cx="9" cy="8" r="3.2"/>'
                         f'<path d="M2.5 20a6.5 6.5 0 0 1 13 0M17 5.5a3 3 0 0 1 0 5.4'
                         f'M18.5 20a6 6 0 0 0-3-5.2"/></g>')
        parts.append(f'<text x="{x+27}" y="{H/2 + fs*0.36:.1f}" font-family="{SYS}" '
                     f'font-size="{fs}" fill="{t["stripInk"]}">'
                     f'<tspan font-weight="700">{esc(bold)}</tspan>'
                     f'<tspan font-weight="400">{esc(rest)}</tspan></text>')
    alt = '14+ years building software - 60+ interns / developers mentored'
    return svg(W, H, f'<title>{esc(alt)}</title>' + ''.join(parts))


def build_explore(theme):
    t = T[theme]
    W, r = 880, 14
    lead = 'Building depth through study, experiments and practical projects.'
    chips = ['System design', 'LLM foundations', 'RAG & retrieval', 'AI agents']
    fs_lead, fs_chip = 14, 13
    ch, pad, gap = 34, 16, 10
    H = 20 + 16 + 14 + ch + 18
    parts = [f'<defs><linearGradient id="c" x1="0" y1="0" x2="1" y2="0.5">'
             f'<stop offset="0" stop-color="{t["cardA"]}"/>'
             f'<stop offset="1" stop-color="{t["cardB"]}"/></linearGradient></defs>'
             f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="{r}" '
             f'fill="url(#c)" stroke="{t["cardLine"]}"/>'
             f'<text x="22" y="37" font-family="{SYS}" font-size="{fs_lead}" '
             f'font-weight="500" fill="{t["cardInk"]}">{esc(lead)}</text>']
    x, y = 22, H - 18 - ch
    for label in chips:
        w = round(est_width(label, fs_chip, bold=True)) + pad * 2
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{ch}" rx="10" '
                     f'fill="{t["chipBg"]}" stroke="{t["chipLine"]}"/>'
                     f'<text x="{x + w/2}" y="{y + ch/2 + fs_chip*0.35:.1f}" '
                     f'text-anchor="middle" font-family="{SYS}" font-size="{fs_chip}" '
                     f'font-weight="600" fill="{t["chipInk"]}">{esc(label)}</text>')
        x += w + gap
    alt = 'Currently exploring: ' + ', '.join(chips)
    return svg(W, H, f'<title>{esc(alt)}</title>' + ''.join(parts))


TILES = [('purelive', 'identity', 'pink'), ('smartpass', 'plane', 'sky'),
         ('classmarine', 'marine', 'amber'), ('faceblade', 'vision', 'lilac'),
         ('smarttrack', 'track', 'mint'), ('bestmarine', 'sail', 'rose')]
APPRS = [('contracts', 'contracts', 'sky'), ('security', 'security', 'pink'),
         ('observability', 'observe', 'mint'), ('architecture', 'architect', 'lilac')]
TAGS = {
    'purelive':    [('Identity', 'pink'), ('Security', 'pink')],
    'smartpass':   [('Airports', 'blue'), ('Realtime', 'blue')],
    'classmarine': [('Accounting', 'pink'), ('Integrations', 'pink')],
    'faceblade':   [('Computer vision', 'pink'), ('Mobile', 'pink')],
    'smarttrack':  [('IoT', 'blue'), ('Realtime', 'blue')],
    'bestmarine':  [('Bookings', 'pink'), ('Payments', 'pink')],
}


def main():
    n = 0
    for theme in ('light', 'dark'):
        for name, icon, hue in TILES:
            write(f'tile-{name}-{theme}.svg', build_tile(name, icon, hue, theme)); n += 1
        for name, icon, hue in APPRS:
            write(f'appr-{name}-{theme}.svg', build_appr(name, icon, hue, theme)); n += 1
        for name, lh in TAGS.items():
            write(f'tags-{name}-{theme}.svg', build_tags(lh, theme)); n += 1
        write(f'appr-mentor-{theme}.svg', build_appr('mentor', 'mentor', 'pink', theme)); n += 1
        write(f'icon-mobile-{theme}.svg', build_appr('mobile', 'mobile', 'sky', theme)); n += 1
        write(f'strip-{theme}.svg', build_strip(theme)); n += 1
        write(f'explore-{theme}.svg', build_explore(theme)); n += 1
    total = sum(p.stat().st_size for p in OUT.glob('*.svg'))
    print(f"wrote {n} SVGs to {OUT}  ({total/1024:.1f} KB total, "
          f"~{total/2048:.1f} KB fetched per reader)")


if __name__ == '__main__':
    main()
