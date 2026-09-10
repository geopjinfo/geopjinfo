/**
 * Render README.md the way GitHub does and save the four preview images.
 *
 * marked + github-markdown-css in Chromium. Not a screenshot of the live
 * profile - GitHub can change its sanitiser, CSS, image proxy and spacing -
 * but close enough to catch layout breakage before pushing.
 *
 * Chromium's prefers-color-scheme emulation also exercises the <picture>
 * sources, so the dark-theme asset swap is genuinely verified here.
 *
 *   npm i playwright marked github-markdown-css
 *   node tools/render-previews.mjs
 */
import { chromium } from 'playwright';
import { marked } from 'marked';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = process.cwd();
const cssDir = path.dirname(fileURLToPath(import.meta.resolve('github-markdown-css/github-markdown.css')));
const css = (t) => fs.readFileSync(path.join(cssDir, `github-markdown-${t}.css`), 'utf8');

const body = marked.parse(fs.readFileSync('README.md', 'utf8'), { mangle: false, headerIds: false });

const page = (theme) => `<!doctype html><html data-theme="${theme}"><head><meta charset="utf-8">
<style>${css(theme)}
html,body{margin:0;background:${theme === 'dark' ? '#0d1117' : '#ffffff'}}
.markdown-body{box-sizing:border-box;max-width:980px;margin:0 auto;padding:32px 24px}
@media(max-width:500px){.markdown-body{padding:16px 12px}}
</style></head><body><article class="markdown-body">${body}</article></body></html>`;

const shots = [
  ['light',  1280, 'previews/light.webp'],
  ['dark',   1280, 'previews/dark.webp'],
  ['light',   390, 'previews/mobile-light.webp'],
  ['dark',    390, 'previews/mobile-dark.webp'],
];

// Chromium comes from `npx playwright install chromium`. Override with
// CHROMIUM_PATH if you need a specific binary - never hardcode one here, it
// ends up in the public history and breaks every other machine.
const browser = await chromium.launch(
  process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const tmpHtml = path.join(os.tmpdir(), '_readme_preview.html');
for (const [theme, width, out] of shots) {
  const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: theme });
  const p = await ctx.newPage();
  fs.writeFileSync(tmpHtml, page(theme));
  await p.goto(pathToFileURL(tmpHtml).href);
  // resolve relative asset paths against the repo
  await p.evaluate((base) => {
    document.querySelectorAll('img[src^="assets/"]').forEach(i => i.src = base + '/' + i.getAttribute('src'));
    document.querySelectorAll('source[srcset^="assets/"]').forEach(s => s.srcset = base + '/' + s.getAttribute('srcset'));
  }, pathToFileURL(root).href);
  await p.waitForTimeout(1500);
  const scrollW = await p.evaluate(() => document.documentElement.scrollWidth);
  if (scrollW > width) console.warn(`  ! ${out}: horizontal overflow (${scrollW} > ${width})`);
  await p.screenshot({ path: out.replace('.webp', '.png'), fullPage: true });
  const dims = await p.evaluate(() => [document.documentElement.scrollWidth, document.body.scrollHeight]);
  console.log(`  ${out.padEnd(30)} ${dims[0]}x${dims[1]}`);
  await ctx.close();
}
await browser.close();
