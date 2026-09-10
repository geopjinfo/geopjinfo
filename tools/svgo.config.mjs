// Safe for GitHub-rendered <img> SVGs.
//
// NOTE: svgo 3 has no `active: false`. Naming a plugin in this list ENABLES
// it, so listing `removeDimensions` here (as an earlier version of this file
// did) stripped width/height off the <svg> root - the opposite of the intent.
// Plugins that are not part of preset-default are simply left out.
export default {
  multipass: true,
  floatPrecision: 2,
  plugins: [
    {
      name: 'preset-default',
      params: {
        overrides: {
          removeViewBox: false,   // keep it: <img> scaling depends on it
          removeTitle: false,     // <title> is the accessible name
          removeDesc: false,
          cleanupIds: { minify: true },
          convertPathData: { floatPrecision: 2, transformPrecision: 3 },
          mergePaths: { force: false },
        },
      },
    },
  ],
};
