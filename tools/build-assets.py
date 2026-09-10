#!/usr/bin/env python3
"""Build every derived raster asset from the original banner artwork.

  hero.webp              banner with the corrected role lines + rounded corners
  footer.webp            the waterfront strip with the "{ Stay Playful }" script
                         composited onto it, overlapping the artwork

Both come off one in-memory image, so each is encoded exactly once.
Input is the untouched original artwork; it is not kept in the repo, so
pass it explicitly:

    python3 tools/build-assets.py path/to/hero-original.webp

The artwork as committed before this change is `git show 066de44:assets/hero.webp`.
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np, pathlib, sys, os
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from webp_util import save_best

# Figtree (OFL 1.1) is the banner face. It is not vendored - point FIGTREE_TTF
# at a copy, or drop one in tools/fonts/:
#   curl -Lo tools/fonts/Figtree.ttf \
#     'https://raw.githubusercontent.com/google/fonts/main/ofl/figtree/Figtree%5Bwght%5D.ttf'
FONT = pathlib.Path(os.environ.get(
    'FIGTREE_TTF', pathlib.Path(__file__).parent / 'fonts' / 'Figtree.ttf'))
SS   = 4      # text supersampling
RAD  = 36     # banner corner radius, native px (~14px at GitHub render width)
# Quality floors by role: text-bearing brand art is held tight; dense
# decorative art rendered small tolerates more, and holding it to the same
# floor makes the file BIGGER than the source for no visible gain.
FLOOR_BRAND = 0.9945   # banner, signature - carry type
FLOOR_DECOR = 0.9850   # footer - illustration, rendered ~75px tall

BAND, BX   = (343, 484), (60, 1035)          # rows/cols to repaint
ANCH_T, ANCH_B = (331, 343), (484, 496)      # clean gradient rows above / below

# Footer geometry, all in native artwork px.
SIG_BOX = (1700, 82, 2048, 258)              # the "{ Stay Playful }" script
SKY_BOX = (1180, 505, 2062, 745)             # waterfront, capped at 2x footer size
SIG_AT  = (267, 48)                          # script origin inside SKY_BOX: centred,
                                             # with the text landing on the waterline
                                             # (max contrast) and the swoosh clear of
                                             # the bottom rounded corner

LINES = [
    dict(old="Senior Backend Engineer",  new="Senior Application Engineer",
         size=81, wght=700, color=(205, 57, 132), ink_left=83, ink_top=343),
    dict(old="Senior Application Engineer @ AICenter", new="Backend Lead @ AICenter, UAE",
         size=47, wght=400, color=(79, 91, 123), ink_left=84, ink_top=439),
]

def font(size, wght):
    if not FONT.exists():
        sys.exit(f"Figtree not found at {FONT}\n"
                 f"Set FIGTREE_TTF or see the note at the top of this file.")
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_axes([wght]); return f

def ink_offset(text, size, wght):
    f = font(size * SS, wght); pad, bl = 400, 600
    img = Image.new('L', (6000, 1200), 0)
    ImageDraw.Draw(img).text((pad, bl), text, font=f, fill=255, anchor='ls')
    ys, xs = np.nonzero(np.asarray(img) > 40)
    return (xs.min() - pad) / SS, (ys.min() - bl) / SS

def rounded(im, radius):
    W, H = im.size
    m = Image.new('L', (W * 2, H * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W * 2 - 1, H * 2 - 1], radius=radius * 2, fill=255)
    out = im.convert('RGBA'); out.putalpha(m.resize((W, H), Image.LANCZOS)); return out

def key_to_alpha(rgb, boost=1.0):
    """Ink-on-white -> transparent-backed ink."""
    a = np.asarray(rgb).astype(np.float64) / 255.0
    al = np.clip((1.0 - a.min(axis=2) - 0.03) / 0.97, 0, 1) * boost
    al = np.clip(al, 0, 1); m = al > 0.004
    col = np.zeros_like(a)
    for c in range(3):
        col[..., c] = np.where(m, np.clip((a[..., c] - (1 - al)) / np.maximum(al, 1e-6), 0, 1), 0)
    return Image.fromarray(np.dstack([col * 255, al * 255]).astype(np.uint8), 'RGBA')

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'assets/hero.webp'
    im = Image.open(src).convert('RGB')
    W, H = im.size
    a = np.asarray(im).astype(np.float64)

    top = a[ANCH_T[0]:ANCH_T[1], BX[0]:BX[1]].mean(axis=0)
    bot = a[ANCH_B[0]:ANCH_B[1], BX[0]:BX[1]].mean(axis=0)
    n = BAND[1] - BAND[0]
    t = np.linspace(0, 1, n + 2)[1:-1][:, None, None]
    a[BAND[0]:BAND[1], BX[0]:BX[1]] = top[None] * (1 - t) + bot[None] * t
    a[BAND[0]:BAND[1], BX[0]:BX[1]] += np.random.default_rng(7).normal(0, 1.35, (n, BX[1] - BX[0], 3))
    base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    for L in LINES:
        _,  dy = ink_offset(L['old'], L['size'], L['wght'])
        dx, _  = ink_offset(L['new'], L['size'], L['wght'])
        ax, ay = L['ink_left'] - dx, L['ink_top'] - dy
        layer = Image.new('L', (W * SS, 700 * SS), 0)
        ImageDraw.Draw(layer).text((ax * SS, (ay - 300) * SS), L['new'],
                                   font=font(L['size'] * SS, L['wght']), fill=255, anchor='ls')
        full = Image.new('L', (W, H), 0); full.paste(layer.resize((W, 700), Image.LANCZOS), (0, 300))
        base.paste(Image.new('RGB', (W, H), L['color']), (0, 0), full)

    print("encoding (single lossy pass each):")
    save_best(rounded(base, RAD), 'assets/hero.webp', FLOOR_BRAND, 'hero.webp')
    # GitHub strips style/class from README HTML, so two <img> tags can never
    # overlap. The overlap has to exist inside a single asset - composite the
    # script onto the waterfront here, while both are still uncompressed.
    sky = base.crop(SKY_BOX).convert('RGBA')
    sky.alpha_composite(key_to_alpha(base.crop(SIG_BOX)), SIG_AT)
    sky = sky.resize((760, round(760 * sky.height / sky.width)), Image.LANCZOS)
    # The script is type, but it survives the decorative floor: measured per
    # region, the script scores ABOVE the illustration at every quality - the
    # dense artwork is what limits SSIM, not the lettering. Holding this to
    # FLOOR_BRAND is unreachable and falls back to q95 / 45.7 KB, bigger than
    # the two separate assets it replaces.
    save_best(rounded(sky, 20), 'assets/footer.webp', FLOOR_DECOR, 'footer.webp')

if __name__ == '__main__':
    main()
