import test from 'node:test';
import assert from 'node:assert/strict';
import { ShowState, SCENES } from '../src/state.js';
import { voiceScene, toHands } from '../src/gestures.js';

test('Nando jumps once, freezes on pause and lands at original feet position',()=>{
 const s=new ShowState(),y=s.characters.Right.y;s.jump();s.update(.1);
 assert.ok(s.jumpHeight>0);const velocity=s.jumpVelocity;s.jump();assert.equal(s.jumpVelocity,velocity);
 const height=s.jumpHeight;s.paused=true;s.update(.1);assert.equal(s.jumpHeight,height);
 s.paused=false;for(let i=0;i<20;i++)s.update(.1);
 assert.equal(s.jumpHeight,0);assert.equal(s.jumpVelocity,0);assert.equal(s.characters.Right.y,y);
 s.jump();s.update(.1);assert.ok(s.jumpHeight>0);
});
test('only pose 7 follows the ball horizontally',()=>{
 const s=new ShowState();s.characters.Right.pose=7;
 s.ball={x:0};assert.equal(s.nandoFlipped(),true);
 s.ball.x=1280;assert.equal(s.nandoFlipped(),false);
 s.ball.x=0;
 for(const pose of [1,2,3,4,5,6,8,9,10]){s.characters.Right.pose=pose;assert.equal(s.nandoFlipped(),false);}
 s.run=true;s.facing=-1;assert.equal(s.nandoFlipped(),true);
});

test('web starts closed and transition opens only once',()=>{
 const s=new ShowState({curtainClosed:true});s.update(100);
 assert.equal(s.curtainPhase,'closed');s.openCurtain();s.update(.2);
 assert.equal(s.curtainPhase,'opening');
 const timer=s.curtainTimer;s.openCurtain();assert.equal(s.curtainTimer,timer);
 s.update(1);assert.equal(s.curtainPhase,'idle');
 s.openCurtain();s.update(10);assert.equal(s.curtainPhase,'idle');
 s.toggleCurtain();s.update(.35);s.openCurtain();s.update(1);
 assert.equal(s.curtainPhase,'idle');
});

test('manual curtain stays closed until toggled and can close again',()=>{
 const s=new ShowState();s.toggleCurtain();s.update(10);
 assert.equal(s.curtainPhase,'closed');s.update(100);
 assert.equal(s.curtainPhase,'closed');s.toggleCurtain();s.update(1);
 assert.equal(s.curtainPhase,'idle');s.toggleCurtain();s.update(.35);
 assert.equal(s.curtainPhase,'closed');s.curtain(true);s.update(3);
 assert.equal(s.curtainPhase,'idle');
});
test('all five scenes retain keyboard mapping including scene 3',()=>{
 assert.deepEqual(SCENES.map(s=>s.key),['6','7','0','8','9']);
 const s=new ShowState();for(let i=0;i<5;i++){s.setScene(i);assert.equal(s.costume,i<2?'sport':'school');}
 assert.equal(s.characters.Right.x,.07);
 s.characters.Right.x=.7;s.setScene(2);assert.equal(s.characters.Right.x,.07);
 assert.equal(s.run,true);
 s.update(.1,[{label:'Right',box:[.45,.2,.55,.6],count:1}]);assert.equal(s.characters.Right.x,.07);
 s.setCostume('sport');s.setScene(4);assert.equal(s.costume,'sport');assert.equal(s.run,false);
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
test('Taman Pose 7 uses the static no-ball frame',()=>{
 const s=new ShowState();s.banks.Right=2;s.pose(2,'Right');
 assert.equal(s.characters.Right.pose,7);assert.equal(s.sprite('Right'),'ball0');
 s.setScene(1);assert.equal(s.sprite('Right'),'sport7');
});
test('B ball trigger stays active and bounces at borders and characters',()=>{
 const s=new ShowState();s.startBall();assert.equal(s.ballMode,true);assert.ok(s.ball);
 s.ball={x:1250,y:360,vx:500,vy:0,angle:0};s.update(.1);assert.ok(s.ball.vx<0);assert.ok(s.ball.x<=1238);
 s.ball={x:300,y:468,vx:100,vy:0,angle:0};s.update(.1);assert.ok(s.ball.vx<0);assert.ok(s.ball.vy===0);
 for(let i=0;i<100;i++)s.update(.1);assert.ok(s.ball);assert.equal(s.ballMode,true);
});
test('B toggles the persistent ball and scene transitions clear it',()=>{
 const s=new ShowState();s.startBall();assert.equal(s.ballMode,true);assert.ok(s.ball);
 s.startBall();assert.equal(s.ballMode,false);assert.equal(s.ball,null);
 s.startBall();s.setScene(1);assert.equal(s.ballMode,false);assert.equal(s.ball,null);
 s.startBall();s.curtain();assert.equal(s.ballMode,false);assert.equal(s.ball,null);
});
test('B can start the persistent ball during the kick pose',()=>{
 const s=new ShowState();s.startKick();s.startBall();
 assert.equal(s.kick,0);assert.equal(s.ballMode,true);assert.ok(s.ball);
 s.startBall();assert.equal(s.ballMode,false);assert.equal(s.ball,null);
});
test('two right-hand fingers keep Pose 7 normal on every scene',()=>{
 const s=new ShowState();s.banks.Right=2;s.useGesture();
 for(let i=0;i<4;i++)s.update(.05,[{label:'Right',box:[.4,.2,.6,.6],count:2}]);
 assert.equal(s.kick,-1);assert.equal(s.characters.Right.pose,7);
 const other=new ShowState();other.setScene(1);other.banks.Right=2;other.useGesture();
 for(let i=0;i<4;i++)other.update(.05,[{label:'Right',box:[.4,.2,.6,.6],count:2}]);
 assert.equal(other.kick,-1);assert.equal(other.characters.Right.pose,7);
});
test('running wraps from either edge to the opposite side',()=>{
 const s=new ShowState();s.run=true;s.characters.Right.x=.08;
 s.update(.1,[], -1);assert.equal(s.characters.Right.x,.86);
 s.characters.Right.x=.07;s.update(.1,[], 1);assert.ok(s.characters.Right.x>.07);
 s.characters.Right.x=.85;s.update(.1,[],1);assert.equal(s.characters.Right.x,.07);
});
test('voice triggers use full keywords, prioritizing class over school',()=>{
 assert.equal(voiceScene('ayo ke kelas sekolah'),3);assert.equal(voiceScene('taman'),0);
 assert.equal(voiceScene('makanan'),null);assert.equal(voiceScene('koridor sekolah'),4);
 assert.deepEqual(toHands({landmarks:[]}),[]);
});

test('independent banks route manual and gesture poses to each character',()=>{
 const s=new ShowState();s.setScene(1);s.toggleBank('Right');
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
