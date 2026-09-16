import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';

const root=dirname(fileURLToPath(import.meta.url));
await build({entryPoints:[resolve(root,'frontend/react-ui.jsx')],bundle:true,format:'esm',minify:true,outfile:resolve(root,'dist/react-ui.js'),define:{'process.env.NODE_ENV':'"production"'},legalComments:'linked'});
console.log('React dashboard bundle built. Static output: dist/');
