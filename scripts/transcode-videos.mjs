// Optional authoring step. The resulting files are committed; Vercel does not need FFmpeg.
import { mkdir } from 'node:fs/promises';
import { resolve,join } from 'node:path';
import { spawnSync } from 'node:child_process';
const root=resolve(import.meta.dirname,'..');
const output=join(root,'web-assets/video');
await mkdir(output,{recursive:true});
for(const [i,name] of ['vid1','vid2','scene 3','3 nganter buku','4 ending'].entries()) {
 const result=spawnSync('ffmpeg',['-hide_banner','-loglevel','error','-nostdin','-y',
   '-i',join(root,'FIX ASSET/Asset/Vid',name+'.mp4'),
   '-map','0:v:0','-an','-vf','scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2',
   '-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p',
   '-profile:v','high','-level:v','4.0','-movflags','+faststart',join(output,'video'+i+'.mp4')],
   {stdio:'inherit',windowsHide:true});
 if(result.error)throw result.error;
 if(result.status!==0)throw new Error('Cannot transcode '+name);
 console.log('Web video ready:',name);
}
