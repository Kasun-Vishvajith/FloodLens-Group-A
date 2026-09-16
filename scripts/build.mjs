import { build } from 'esbuild';
import { cp, mkdir, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = fileURLToPath(new URL('../', import.meta.url));
const out = path.join(root, 'dist');
await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
await cp(path.join(root, 'public'), out, { recursive: true });
await cp(path.join(root, 'src/index.html'), path.join(out, 'index.html'));
await build({ entryPoints: [path.join(root, 'src/main.js')], bundle: true, format: 'esm', minify: true,
  outfile: path.join(out, 'assets/app.js'), define: { 'process.env.NODE_ENV': '"production"' }, legalComments: 'linked' });
// Unbundled controller entry supports meaningful DOM integration tests.
await build({ entryPoints: [path.join(root, 'src/app.js')], bundle: true, format: 'esm', minify: false,
  outfile: path.join(root, 'node_modules/.cache/floodlens-test.mjs'), define: { 'process.env.NODE_ENV': '"production"' } });
console.log('Built deployable website in dist/');
