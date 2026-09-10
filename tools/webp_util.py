"""Shared WebP encoding helpers.

The rule the whole asset pipeline follows: every image gets exactly ONE lossy
pass, from uncompressed pixels. Re-encoding an already-compressed file
compounds artefacts and, because the degraded file becomes its own reference,
the quality search silently stops finding savings.
"""
from PIL import Image
from scipy.ndimage import uniform_filter
import numpy as np, io

QUALITIES = [95, 92, 88, 85, 82, 79, 76, 73, 70, 67]
_SSIM_MAX_EDGE = 1600          # downsample before SSIM; keeps big screenshots fast


def flatten(im, ground=(255, 255, 255)):
    """Composite over a ground so alpha images compare meaningfully."""
    if im.mode != 'RGBA':
        return im.convert('RGB')
    bg = Image.new('RGB', im.size, ground)
    bg.paste(im, (0, 0), im)
    return bg


def _fit(im):
    e = max(im.size)
    if e <= _SSIM_MAX_EDGE:
        return im
    s = _SSIM_MAX_EDGE / e
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def ssim(a, b):
    a = np.asarray(_fit(a).convert('L'), dtype=np.float64)
    b = np.asarray(_fit(b).convert('L'), dtype=np.float64)
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    m1, m2 = uniform_filter(a, 7), uniform_filter(b, 7)
    s1 = uniform_filter(a * a, 7) - m1 ** 2
    s2 = uniform_filter(b * b, 7) - m2 ** 2
    s12 = uniform_filter(a * b, 7) - m1 * m2
    num = (2 * m1 * m2 + C1) * (2 * s12 + C2)
    den = (m1 ** 2 + m2 ** 2 + C1) * (s1 + s2 + C2)
    return float((num / den).mean())


def encode(im, q):
    buf = io.BytesIO()
    im.save(buf, 'WEBP', quality=q, method=6, exact=False)
    return buf.getvalue()


def save_best(im, path, floor, label=None):
    """Write `im` at the lowest quality whose SSIM against the uncompressed
    original still clears `floor`. Returns (bytes_written, quality, ssim)."""
    ref = flatten(im)
    chosen = None
    for q in QUALITIES:
        data = encode(im, q)
        s = ssim(ref, flatten(Image.open(io.BytesIO(data))))
        if s >= floor:
            chosen = (q, s, data)
        else:
            break
    if chosen is None:
        data = encode(im, QUALITIES[0])
        chosen = (QUALITIES[0], ssim(ref, flatten(Image.open(io.BytesIO(data)))), data)
    q, s, data = chosen
    with open(path, 'wb') as f:
        f.write(data)
    if label:
        print(f"  {label:<28} {len(data)/1024:>7.1f} KB   q={q:<3} SSIM={s:.5f}")
    return len(data), q, s
