#!/usr/bin/env python3
"""Give every <img> in README.md explicit intrinsic width + height.

Without both, the browser cannot reserve the box before the image arrives, so
the README reflows as ~50 badges stream in. GitHub's markdown CSS applies
`img { max-width: 100% }`, so intrinsic attributes still scale down on narrow
screens - they just also pin the aspect ratio up front.

Also marks images inside collapsed <details> as loading="lazy". Position, not
file path, decides this: the curated toolkit badges sit above the fold and
must load eagerly, while the same badge inside the full-toolkit block should
wait until the reader opens it.

Finally, wraps every toolkit badge in a link to that project's official site,
from BADGE_LINKS below. Nine badges appear twice (curated row + full toolkit),
so the map is keyed by filename and applied everywhere. Re-running unwraps and
rewraps, so editing a URL here propagates on the next run.
"""
import re, pathlib, sys

# Toolkit badge -> official project site. Keyed by assets/badges/<key>.svg.
BADGE_LINKS = {
    'android':       'https://developer.android.com',
    'aws':           'https://aws.amazon.com',
    'bitbucket':     'https://bitbucket.org',
    'css':           'https://developer.mozilla.org/en-US/docs/Web/CSS',
    'dart':          'https://dart.dev',
    'docker':        'https://www.docker.com',
    'express':       'https://expressjs.com',
    'fastify':       'https://fastify.dev',
    'firebase':      'https://firebase.google.com',
    'flutter':       'https://flutter.dev',
    'git':           'https://git-scm.com',
    'github':        'https://github.com',
    'grafana':       'https://grafana.com',
    'html5':         'https://developer.mozilla.org/en-US/docs/Web/HTML',
    'java':          'https://dev.java',
    'javascript':    'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
    'jest':          'https://jestjs.io',
    'jwt':           'https://jwt.io',
    'kafka':         'https://kafka.apache.org',
    'kotlin':        'https://kotlinlang.org',
    'kubernetes':    'https://kubernetes.io',
    'loki':          'https://grafana.com/oss/loki/',
    'loopback-4':    'https://loopback.io',
    'mongodb':       'https://www.mongodb.com',
    'mqtt':          'https://mqtt.org',
    'mysql':         'https://www.mysql.com',
    'nextjs':        'https://nextjs.org',
    'nginx':         'https://nginx.org',
    'nodejs':        'https://nodejs.org',
    'oauth-20':      'https://oauth.net/2/',
    'openapi':       'https://www.openapis.org',
    'opencv':        'https://opencv.org',
    'opentelemetry': 'https://opentelemetry.io',
    'pm2':           'https://pm2.keymetrics.io',
    'postgresql':    'https://www.postgresql.org',
    'postman':       'https://www.postman.com',
    'rabbitmq':      'https://www.rabbitmq.com',
    'react':         'https://react.dev',
    'redis':         'https://redis.io',
    'socketio':      'https://socket.io',
    'sql-server':    'https://learn.microsoft.com/en-us/sql/sql-server/',
    'swagger':       'https://swagger.io',
    'tailwind-css':  'https://tailwindcss.com',
    'typescript':    'https://www.typescriptlang.org',
    'vitest':        'https://vitest.dev',
    'vs-code':       'https://code.visualstudio.com',
    'webrtc':        'https://webrtc.org',
}

BADGE_IMG = r'<img\b[^>]*src="assets/badges/([a-z0-9.-]+)\.svg"[^>]*/?>'


def link_badges(src):
    """Wrap each toolkit badge in its official-site link. Idempotent: existing
    wrappers are stripped first so a changed URL actually takes effect."""
    src = re.sub(r'<a href="[^"]*">(' + BADGE_IMG + r')</a>', r'\1', src)
    missing, n = set(), 0

    def wrap(m):
        nonlocal n
        url = BADGE_LINKS.get(m.group(1))
        if not url:
            missing.add(m.group(1)); return m.group(0)
        n += 1
        return f'<a href="{url}">{m.group(0)}</a>'

    src = re.sub(BADGE_IMG, wrap, src)
    if missing:
        print(f"  ! no BADGE_LINKS entry for: {', '.join(sorted(missing))}",
              file=sys.stderr)
    return src, n

def svg_size(p):
    s = pathlib.Path(p).read_text()
    w = re.search(r'\bwidth="([\d.]+)"', s)
    h = re.search(r'\bheight="([\d.]+)"', s)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    vb = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', s)
    return (float(vb.group(1)), float(vb.group(2))) if vb else (None, None)

def main():
    md = pathlib.Path('README.md'); src = md.read_text(); changed = 0

    # character ranges covered by a <details> block
    hidden = []
    for m in re.finditer(r'<details\b', src):
        end = src.find('</details>', m.start())
        hidden.append((m.start(), end if end != -1 else len(src)))

    def is_hidden(pos):
        return any(a <= pos < b for a, b in hidden)

    def fix(m):
        nonlocal changed
        tag = m.group(0)
        srcm = re.search(r'src="([^"]+)"', tag)
        if not srcm or srcm.group(1).startswith('http'):
            return tag
        path = srcm.group(1)
        if not pathlib.Path(path).exists():
            print(f"  ! missing {path}", file=sys.stderr); return tag
        iw, ih = svg_size(path) if path.endswith('.svg') else (None, None)
        if iw is None:
            from PIL import Image
            iw, ih = Image.open(path).size
        want_h = re.search(r'\bheight="([\d.]+)"', tag)
        h = float(want_h.group(1)) if want_h else ih
        w = round(iw * h / ih)
        tag = re.sub(r'\s+width="[^"]*"', '', tag)
        tag = re.sub(r'\s+height="[^"]*"', '', tag)
        tag = tag.replace('<img', f'<img width="{w}" height="{round(h)}"', 1)
        # only images the reader must expand to see are deferred
        if is_hidden(m.start()) and 'loading=' not in tag:
            tag = tag.replace('<img', '<img loading="lazy"', 1)
        changed += 1
        return tag

    out = re.sub(r'<img\b[^>]*/?>', fix, src)
    out, linked = link_badges(out)
    md.write_text(out)
    print(f"README.md: set intrinsic width+height on {changed} images, "
          f"linked {linked} badges")

if __name__ == '__main__':
    main()
