import test from 'node:test';
import assert from 'node:assert/strict';
import { toHands } from '../src/gestures.js';
import { Renderer } from '../src/renderer.js';
const landmarks=()=>{
 const p=Array.from({length:21},()=>({x:.5,y:.5}));
 for(const [i,x,y] of [[0,.5,.9],[2,.6,.76],[3,.7,.66],[4,.8,.6],
   [5,.4,.65],[6,.4,.4],[8,.4,.15],[9,.5,.63],[10,.5,.35],[12,.5,.08],
   [13,.6,.66],[14,.6,.4],[16,.6,.16],[17,.7,.72],[18,.7,.5],[20,.7,.28]])p[i]={x,y};
 return p;
};
test('worker data keeps all landmarks and correct finger count for both mirrored hands',()=>{
 const left=landmarks(),right=left.map(p=>({x:1-p.x,y:p.y}));
 const result=toHands({landmarks:[left,right],handedness:[[{categoryName:'Right',score:1}],[{categoryName:'Left',score:1}]]});
 assert.equal(result.length,2);
 assert.deepEqual(result.map(h=>[h.label,h.count,h.landmarks.length]),[['Left',5,21],['Right',5,21]]);
 assert.deepEqual(result[0].landmarks,left);assert.deepEqual(result[1].landmarks,right);
});
test('preview draws every joint, skeleton connections and counts without double mirroring',()=>{
 const calls=[];
 const ctx=new Proxy({}, {get:(_,method)=>(...args)=>calls.push([method,...args]),set:()=>true});
 const renderer=new Renderer({width:1280,height:720,getContext:()=>ctx},{});
 const points=landmarks();
 renderer.cameraPreview({readyState:2},[{label:'Right',count:0,landmarks:points},{label:'Left',count:5,landmarks:points}]);
 assert.equal(calls.filter(c=>c[0]==='arc'&&c[3]===3.5).length,42);
 assert.equal(calls.filter(c=>c[0]==='lineTo').length,42);
 assert.deepEqual(calls.filter(c=>c[0]==='fillText').map(c=>c[1]),['0','5']);
 const label=calls.find(c=>c[0]==='fillText');
 assert.equal(label[2],956+(.4+.8)/2*300);assert.equal(label[3],42);
 const dot=calls.find(c=>c[0]==='arc');
 assert.equal(dot[1],956+points[0].x*300);assert.equal(dot[2],24+points[0].y*225);
 calls.length=0;renderer.cameraPreview({readyState:2},[]);
 assert.deepEqual(calls.filter(c=>c[0]==='fillText').map(c=>c[1]),[]);
 assert.equal(calls.filter(c=>c[0]==='arc').length,0);
});
