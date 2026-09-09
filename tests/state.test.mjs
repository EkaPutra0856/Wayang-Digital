import test from 'node:test';
import assert from 'node:assert/strict';
import { ShowState, SCENES } from '../src/state.js';
import { voiceScene, toHands } from '../src/gestures.js';
test('all five scenes retain keyboard mapping including scene 3',()=>{
 assert.deepEqual(SCENES.map(s=>s.key),['6','7','0','8','9']);
 const s=new ShowState();for(let i=0;i<5;i++){s.setScene(i);assert.equal(s.costume,i<2?'sport':'school');}
 s.setCostume('sport');s.setScene(4);assert.equal(s.costume,'sport');
});
test('salam is selectable in bank 2 and costume fallback stays valid',()=>{
 const s=new ShowState();s.banks={Right:2,Left:2};s.pose(5,'Right');assert.equal(s.sprite('Right'),'sport10');
 assert.equal(s.pose(5,'Left'),false);assert.equal(s.characters.Left.pose,1);
 s.setCostume('school');assert.equal(s.characters.Right.pose,1);
 s.setCostume('sport');s.pose(5,'Right');assert.equal(s.sprite('Right'),'sport10');
});
test('curtain closes, holds 1 second, freezes during pause and opens before video',()=>{
 const s=new ShowState();s.curtain();s.videoPlaying=true;
 s.update(.35);assert.equal(s.curtainPhase,'closed');
 s.update(.99);assert.equal(s.curtainPhase,'closed');
 s.paused=true;s.update(100);assert.equal(s.curtainPhase,'closed');
 s.paused=false;s.update(.03);assert.equal(s.curtainPhase,'opening');
 s.update(.65);assert.equal(s.curtainPhase,'idle');
});
test('duplicate curtain does not restart, new video can explicitly restart',()=>{
 const s=new ShowState();s.curtain();s.update(.2);assert.equal(s.curtain(),false);
 assert.equal(s.curtainTimer,.2);assert.equal(s.curtain(true),true);assert.equal(s.curtainTimer,0);
});
test('gesture debounce and independent fades, manual hidden pose remains hidden',()=>{
 const s=new ShowState();s.useGesture();s.banks={Right:2,Left:2};
 const hands=[{label:'Right',box:[.4,.2,.6,.6],count:5}];
 for(let i=0;i<10;i++)s.update(.05,hands);
 assert.equal(s.characters.Right.pose,10);assert.equal(s.characters.Left.alpha,0);
 s.pose(5,'Right');s.pose(5,'Right');
 for(let i=0;i<10;i++)s.update(.05,hands);
 assert.equal(s.characters.Right.alpha,0);
});
test('pause freezes movement, special animation and ball physics',()=>{
 const s=new ShowState();s.run=true;s.startKick();s.update(.1);
 const before=JSON.stringify(s);s.paused=true;const paused=JSON.stringify(s);s.update(.1,[],1);
 assert.equal(JSON.stringify(s),paused);assert.notEqual(before,paused);
});
test('kick completes and running remains within the stage',()=>{
 const s=new ShowState();s.startKick();let flew=false;
 for(let i=0;i<70;i++){s.update(.05);flew ||= !!s.ball;}
 assert.ok(flew);assert.equal(s.kick,-1);assert.equal(s.ball,null);
 s.run=true;for(let i=0;i<100;i++)s.update(.1,[],1);assert.ok(s.characters.Right.x<=.86);
});
test('voice triggers use full keywords, prioritizing class over school',()=>{
 assert.equal(voiceScene('ayo ke kelas sekolah'),3);assert.equal(voiceScene('taman'),0);
 assert.equal(voiceScene('makanan'),null);assert.equal(voiceScene('koridor sekolah'),4);
 assert.deepEqual(toHands({landmarks:[]}),[]);
});

test('independent banks route manual and gesture poses to each character',()=>{
 const s=new ShowState();s.toggleBank('Right');
 assert.deepEqual(s.banks,{Right:2,Left:1});
 s.pose(3,'Right');s.pose(3,'Left');
 assert.equal(s.characters.Right.pose,8);assert.equal(s.characters.Left.pose,3);
 s.useGesture();
 const hands=['Right','Left'].map(label=>({label,count:2,box:[.2,.2,.4,.6]}));
 for(let i=0;i<6;i++)s.update(.05,hands);
 assert.equal(s.characters.Right.pose,7);assert.equal(s.characters.Left.pose,2);
 s.toggleBank('Left');assert.deepEqual(s.banks,{Right:2,Left:2});
 s.toggleBank('Right');assert.deepEqual(s.banks,{Right:1,Left:2});
 const fresh=new ShowState();assert.deepEqual(fresh.banks,{Right:1,Left:1});
});

test('camera distance never changes character scale, even with vertical movement unlocked',()=>{
 const s=new ShowState();s.useGesture();s.verticalLocked=false;
 for(const expected of [.46,.575,.69]) {
  for(const box of [[.48,.45,.52,.55],[.1,.05,.9,.95]]) {
   for(let i=0;i<20;i++)s.update(.05,['Right','Left'].map(label=>({label,count:1,box})));
   for(const c of Object.values(s.characters))assert.ok(Math.abs(c.height-expected)<1e-10);
  }
  s.changeScale(1);
 }
 assert.equal(s.scaleLevel,2);s.changeScale(1);assert.equal(s.scaleLevel,2);
 s.changeScale(-1);assert.equal(s.scaleLevel,1);
 s.changeScale(-1);s.changeScale(-1);assert.equal(s.scaleLevel,0);
 s.changeScale(1);s.balance();assert.equal(s.scaleLevel,0);
 assert.equal(s.characters.Right.height,.46);assert.equal(s.characters.Left.height,.46);
 s.paused=true;s.changeScale(1);assert.equal(s.scaleLevel,0);
});
