# Profile design notes

One README, rendered in the reader's own GitHub theme.

## What is text and what is an image

GitHub strips `style` and `class` from README HTML, so the card-and-pill look
cannot be CSS - it has to be baked into images. The split is deliberate:

* **Native markdown** carries every heading, all body copy, the card titles and
  descriptions, the toolkit labels and both `<details>` blocks. This text stays
  selectable, searchable and screen-reader friendly, and it takes the reader's
  theme automatically. `##` also gives a bold heading with a hairline rule for
  free, which is the section divider the design wanted anyway.
* **Generated SVGs** carry only the visual furniture: the stat strip, the six
  case-study icon tiles, the tag pill rows, the approach icons and the
  exploring card. `tools/build-readme-assets.py` emits them from one token
  table, so a palette change is one edit and a rebuild.

Every generated asset ships a light and a dark variant, selected with
`<picture>` + `prefers-color-scheme`. A reader downloads only their own
variant. Caveat worth knowing: a reader who forces dark in GitHub's settings
while their OS stays light will get the light variant, because
`prefers-color-scheme` reports the OS preference. This is the technique GitHub
itself documents, and the light assets stay legible either way.

The hero, the signature and the footer waterfront intentionally keep their
light Candy colours in both themes.

## Type

The banner is set in Figtree. Assets use a system font stack instead - an SVG
loaded through `<img>` cannot fetch a webfont, so `font-family: Figtree` would
silently fall back to whatever the reader happens to have. Outlining Figtree to
paths was built and then rejected: it renders identically everywhere, but the
exploring card alone came to 44 KB, which is more than the entire rest of the
README's images put together.

## Performance

* Every image declares intrinsic `width` and `height`, so the browser reserves
  each box before the file arrives and nothing reflows on load.
* `loading="lazy"` on images inside collapsed `<details>` only - the curated
  toolkit badges above the fold load eagerly.
* Raster assets are encoded by `tools/optimize-assets.py`, which searches for
  the lowest WebP quality that still clears an SSIM floor rather than using a
  fixed quality. Floors are set by role: brand art that carries type is held
  tight, decorative art rendered small is not.
* All SVGs are minified with svgo, keeping `viewBox` (scaling depends on it)
  and `<title>` (the accessible name).

## Toolkit

47 self-hosted SVG badges. Nine sit on the surface in three curated rows; the
full set stays in a `<details>` block. No live stats services and no remote
badge requests, so nothing about a visitor is reported to a third party.

## Previews

`previews/*.webp` are the README rendered with marked and github-markdown-css
in Chromium (`node tools/render-previews.mjs`), with Chromium's
`prefers-color-scheme` emulation exercising the `<picture>` sources. They
approximate GitHub rendering and are not screenshots of the published profile -
GitHub can change its sanitiser, CSS, image proxy and spacing.

## Content

Project entries describe professional portfolio work, not public repositories.
Portfolio links point to the verified projects section. Brand palette and
professional content: https://georgepj.me
