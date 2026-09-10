#!/usr/bin/env python3
"""Optimise the raster assets this repo does not build from source.

`build-assets.py` already encodes the banner and its derivatives in a single
lossy pass. This handles the rendered README previews, which come out of the
Chromium preview pipeline, and reports the whole asset budget.

    python3 tools/optimize-assets.py
"""
from PIL import Image
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from webp_util import save_best

# Screenshots: read at a glance, never zoomed. A looser floor than brand art.
PREVIEWS = {p: 0.9850 for p in
            ['previews/light.webp', 'previews/dark.webp',
             'previews/mobile-light.webp', 'previews/mobile-dark.webp']}


def main():
    print("previews (re-encode):")
    tb = ta = 0
    for rel, floor in PREVIEWS.items():
        p = pathlib.Path(rel)
        # Encode from the PNG render-previews.mjs just wrote: those are
        # uncompressed pixels, so this stays the one lossy pass. Re-reading
        # the .webp would compound artefacts AND, after a README change,
        # silently re-encode the previous render.
        src = p.with_suffix('.png')
        if not src.exists():
            print(f"  {rel:<28} — no {src.name}, run render-previews.mjs —")
            continue
        before = p.stat().st_size if p.exists() else 0
        after, q, s = save_best(Image.open(src), rel, floor, p.name)
        if before and after >= before:            # never regress
            print(f"    (re-encode was larger than the previous render)")
        tb += before; ta += after
    if tb:
        print(f"  {'subtotal':<28} {tb/1024:>7.1f} KB -> {ta/1024:.1f} KB "
              f"({(tb-ta)*100//tb}% smaller)")

    print("\nasset budget:")
    groups = {'banner + footer': sorted(pathlib.Path('assets').glob('*.webp')),
              'project icons':   sorted(pathlib.Path('assets/icons').glob('*.svg')),
              'toolkit badges':  sorted(pathlib.Path('assets/badges').glob('*.svg')),
              'previews':        sorted(pathlib.Path('previews').glob('*.webp'))}
    total = 0
    for name, files in groups.items():
        b = sum(f.stat().st_size for f in files)
        total += b
        print(f"  {name:<20} {len(files):>3} files {b/1024:>8.1f} KB")
    print(f"  {'TOTAL':<20} {'':>9} {total/1024:>8.1f} KB")


if __name__ == '__main__':
    main()
