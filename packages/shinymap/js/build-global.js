#!/usr/bin/env node
/**
 * Build script for the global browser bundle (shinymap.global.js)
 * This creates an IIFE bundle that exposes window.shinymap with all exports
 */

import * as esbuild from 'esbuild';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const outdir = join(__dirname, '../python/src/shinymap/www');

await esbuild.build({
  entryPoints: [join(__dirname, 'src/index.tsx')],
  bundle: true,
  format: 'iife',
  globalName: 'shinymap',
  outfile: join(outdir, 'shinymap.global.js'),
  platform: 'browser',
  target: ['es2020'],
  minify: false,
  sourcemap: false,
  logLevel: 'info',
  footer: {
    js: '// Explicitly assign to window for maximum compatibility\nif (typeof window !== "undefined") window.shinymap = shinymap;\nif (typeof globalThis !== "undefined") globalThis.shinymap = shinymap;'
  },
});

console.log(`✓ Built global bundle to ${outdir}/shinymap.global.js`);
