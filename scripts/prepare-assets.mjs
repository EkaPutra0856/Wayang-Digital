import { mkdir, copyFile, readFile, writeFile, readdir, stat, unlink } from 'node:fs/promises';
import { resolve, join, extname } from 'node:path';
import { createHash } from 'node:crypto';
import sharp from 'sharp';

const root = resolve(import.meta.dirname, '..');
const source = join(root, 'FIX ASSET');
const output = join(root, 'public/media');
await mkdir(output, { recursive: true });
await mkdir(join(root, 'src/generated'), { recursive: true });
const manifest = {};
const images = [
  ['bag','../Effect/Tas.png'],
  ['book','../Effect/Buku.png'],
  ...Array.from({length:6}, (_,i)=>['bg'+i, 'Asset/BG/'+(i+1)+' akhir.png', true]),
  ...Array.from({length:8}, (_,i)=>['school'+(i+1), 'Nando Fix Animation/'+(37+i)+'.png']),
  ...Array.from({length:9}, (_,i)=>['sport'+(i+1), 'Nando Olahraga/1 ('+(i+1)+').png']),
  ['sport10','Nando Olahraga/salam.png'],
  ...Array.from({length:8}, (_,i)=>['ibu'+(i+1), 'Ibu/'+(58+i)+'.png']),
  ...Array.from({length:5}, (_,i)=>['run'+i, 'side with bag/'+(45+i)+'.png']),
  ...['1 without ball','1 with ball','2 with ball','3 with ball','3 without ball','ball'].map((n,i)=>['ball'+i,'Ball/'+n+'.png']),
  ['hug','Asset/Pelukan.png'],
];
const media = [
  ...['1 opening','2 makan','3 brangkat sekolah','4 ibu nganter buku','5 pelukan ending'].map((n,i)=>['audio'+i,'Asset/Sound/'+n+'.mp3']),
  ...['vid1','vid2','scene 3','3 nganter buku','4 ending'].map((n,i)=>['video'+i,'Asset/Vid/'+n+'.mp4']),
];
for (const [id, relative, background] of [...images, ...media]) {
  const sourcePath = id.startsWith('video') ? join(root,'web-assets/video',id+'.mp4') : join(source,relative);
  const input = await readFile(sourcePath);
  const hash = createHash('sha256').update(input).update('web-v1').digest('hex').slice(0,12);
  const image = extname(relative) === '.png';
  const filename = id+'-'+hash+(image ? '.webp' : extname(relative));
  const target = join(output, filename);
  let exists = true;
  try { await stat(target); } catch { exists = false; }
  if (!exists) {
    if (image) {
      let pipeline = sharp(input);
      if (!background) pipeline = pipeline.trim({ background: '#00000000', threshold: 0 });
      await pipeline.resize(background ? {width:1920, height:1080, fit:'inside', withoutEnlargement:true}
        : {height:900, width:900, fit:'inside', withoutEnlargement:true}).webp({quality:88, alphaQuality:100}).toFile(target);
    } else await copyFile(sourcePath,target);
  }
  manifest[id] = '/media/'+filename;
}
// Remove only stale generated, hashed media inside this build-owned directory.
const currentNames=new Set(Object.values(manifest).map(url=>url.split('/').pop()));
for(const name of await readdir(output)) {
  if(/^[a-z]+[0-9]*-[a-f0-9]{12}\.(webp|mp4|mp3)$/.test(name)&&!currentNames.has(name))await unlink(join(output,name));
}
await writeFile(join(root,'src/generated/assets.json'),JSON.stringify(manifest,null,2)+'\n');
await mkdir(join(root,'public/models'),{recursive:true});
await copyFile(join(root,'hand_landmarker.task'),join(root,'public/models/hand_landmarker.task'));
const wasmRoot=join(root,'node_modules/@mediapipe/tasks-vision/wasm');
await mkdir(join(root,'public/vision'),{recursive:true});
for (const file of await readdir(wasmRoot)) {
  if (/\.(wasm|js)$/.test(file)) await copyFile(join(wasmRoot,file),join(root,'public/vision',file));
}
console.log('Prepared '+images.length+' images, '+media.length+' media, and local hand tracking runtime.');
