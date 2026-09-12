import { readFile,stat,readdir } from 'node:fs/promises';
import { resolve,join } from 'node:path';
import assert from 'node:assert/strict';
const root=resolve(import.meta.dirname,'..'),dist=join(root,'dist');
const assets=JSON.parse(await readFile(join(root,'src/generated/assets.json'),'utf8'));
assert.equal(Object.keys(assets).length,56,'Expected 46 images and 10 media');
for(const url of Object.values(assets)) {
 const file=join(dist,url);
 assert.ok((await stat(file)).size>0,'Missing or empty asset: '+url);
}
for(const url of ['index.html','favicon.svg','models/hand_landmarker.task','vision/vision_wasm_internal.js','vision/vision_wasm_internal.wasm'])assert.ok((await stat(join(dist,url))).size>0);
async function size(dir){let bytes=0;for(const item of await readdir(dir,{withFileTypes:true})){const p=join(dir,item.name);bytes+=item.isDirectory()?await size(p):(await stat(p)).size;}return bytes;}
console.log('Production output verified: '+Object.keys(assets).length+' media assets, local model and WASM; '+((await size(dist))/1048576).toFixed(1)+' MiB total.');
