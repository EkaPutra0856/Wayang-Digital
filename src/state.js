export const SCENES = [
  {name:'Taman', subtitle:'Awal cerita', key:'6', soundKey:'Z'},
  {name:'Rumah', subtitle:'Waktu bersama', key:'7', soundKey:'X'},
  {name:'Sekolah', subtitle:'Berangkat sekolah', key:'0', soundKey:'C'},
  {name:'Kelas', subtitle:'Buku dari Ibu', key:'8', soundKey:'V'},
  {name:'Koridor', subtitle:'Pelukan penutup', key:'9', soundKey:'B'},
  {name:'Ruang Tamu', subtitle:'Rumah keluarga', key:null, soundKey:null},
];
export const TRANSITION_BACKGROUNDS = [0,1,5,4,4];
export const CURTAIN = { closing:0.35, closed:1, opening:0.65 };
export const SCALE_FACTORS = [1, 1.25, 1.5];
const KICK = [0.25,0.35,0.35,0.16,1.6,0.3];
const NANDO_SPAWN_LEFT=.07;
const NANDO_RUN_RIGHT=.86;
export const clamp = (v,min,max)=>Math.max(min,Math.min(max,v));
const character = x=>({x,y:.88,height:.46,pose:1,alpha:1,manual:true,visible:true,candidate:0,candidateTime:0});
export class ShowState {
  constructor({curtainClosed=false}={}) {
    this.scene=0; this.banks={Right:1,Left:1}; this.costume='sport'; this.costumeMode='auto';
    this.characters={Right:character(.70),Left:character(.26)};
    this.lastPose={sport:1,school:1};
    this.paused=false; this.clock=0; this.run=false; this.sleep=false; this.hug=false;
    this.jumpHeight=0;this.jumpVelocity=0;
    this.props={bag:{phase:'hidden',time:0,alpha:0},book:{phase:'hidden',time:0,alpha:0}};
    this.hugAlpha=0; this.facing=1; this.kick=-1; this.kickTimer=0; this.ball=null; this.ballMode=false;
    this.verticalLocked=true; this.scaleLevel=0; this.curtainPhase='idle'; this.curtainTimer=0;
    this.curtainManual=curtainClosed;
    if(curtainClosed)this.curtainPhase='closed';
    this.videoPlaying=false; this.gesture=false; this.showBoxes=false; this.hands=[]; this.nandoSpawnLock=false;
  }
  setScene(index) {
    if (!Number.isInteger(index)||index<0||index>=SCENES.length) return;
    this.jumpHeight=0;this.jumpVelocity=0;
    if(index!==this.scene){this.ballMode=false;this.ball=null;}
    if(index!==0&&this.kick>=0){this.kick=-1;this.kickTimer=0;this.ball=null;}
    this.scene=index;
    this.run=index===2;
    this.nandoSpawnLock=index===2;
    if(index===2) this.characters.Right.x=NANDO_SPAWN_LEFT;
    if(this.costumeMode==='auto') this.setCostume(index<2?'sport':'school','auto');
  }
  setCostume(costume,mode='manual') {
    if(!['sport','school'].includes(costume)) return;
    const char=this.characters.Right;
    this.lastPose[this.costume]=char.pose;
    this.costume=costume; this.costumeMode=mode;
    if(char.pose>this.limit('Right')) char.pose=this.lastPose[costume]||1;
  }
  toggleBank(label) {
    if(!Object.hasOwn(this.banks,label))return;
    this.banks[label]=3-this.banks[label];
    this.characters[label].candidateTime=0;
  }
  limit(label) { return label==='Left'?8:this.costume==='sport'?10:8; }
  pose(finger,label,manual=true) {
    if(finger<1||finger>5) return false;
    const pose=(this.banks[label]-1)*5+finger;
    if(pose>this.limit(label)) return false;
    const c=this.characters[label];
    const hide=manual&&c.manual&&c.visible&&c.pose===pose;
    c.pose=pose;
    if(manual) { c.manual=true; c.visible=!hide; }
    if(label==='Right') this.lastPose[this.costume]=pose;
    return true;
  }
  useGesture() {
    this.gesture=true;
    for(const c of Object.values(this.characters)) {c.manual=false;c.visible=false;}
  }
  useKeyboard() {
    this.gesture=false;
    for(const c of Object.values(this.characters)) {c.manual=true;c.visible=true;}
  }
  changeScale(direction) {
    if(this.paused||this.videoPlaying||![-1,1].includes(direction))return;
    this.scaleLevel=clamp(this.scaleLevel+direction,0,SCALE_FACTORS.length-1);
    for(const c of Object.values(this.characters))c.height=.46*SCALE_FACTORS[this.scaleLevel];
  }
  balance() {
    this.verticalLocked=true;this.scaleLevel=0;
    for(const c of Object.values(this.characters)) {c.height=.46;c.y=.88;}
  }
  curtain(restart=false) {
    if(this.paused||(!restart&&this.curtainPhase!=='idle')) return false;
    this.ballMode=false;this.ball=null;
    this.curtainManual=false;
    this.curtainPhase='closing';this.curtainTimer=0;return true;
  }
  toggleCurtain() {
    if(this.paused)return;
    this.curtainManual=true;
    const closing=['closing','closed'].includes(this.curtainPhase);
    const duration=closing?CURTAIN.closing:CURTAIN.opening;
    const moving=['closing','opening'].includes(this.curtainPhase);
    const progress=moving?clamp(this.curtainTimer/duration,0,1):1;
    this.curtainPhase=closing?'opening':'closing';
    this.curtainTimer=(1-progress)*CURTAIN[this.curtainPhase];
  }
  openCurtain() {
    if(this.paused||this.curtainPhase==='idle'||this.curtainPhase==='opening')return;
    this.toggleCurtain();
  }
  startKick() {
    if(this.paused||this.videoPlaying||this.hug||this.kick>=0) return;
    this.kick=0;this.kickTimer=0;
  }
  jump() {
    if(this.paused||this.videoPlaying||this.sleep||this.hug||this.jumpHeight>0||this.jumpVelocity!==0)return;
    this.jumpVelocity=600;
  }
  toggleProp(name) {
    const p=this.props[name];
    if(this.paused||this.videoPlaying||!p)return;
    if(p.phase==='hidden'||p.phase==='fade') {
      Object.assign(p,{phase:'enter',time:0,alpha:1});
      if(name==='book'&&['hidden','fade'].includes(this.props.bag.phase))this.toggleProp('bag');
    } else p.phase='fade';
  }
  dismissProps() {
    for(const p of Object.values(this.props))if(p.phase!=='hidden')p.phase='fade';
  }
  nandoFlipped() {
    if(this.characters.Right.pose===7&&!this.sleep&&!this.run&&this.kick<0&&this.ball)
      return this.ball.x<this.characters.Right.x*1280;
    return (this.run||this.kick>=0)&&this.facing<0;
  }
  startBall() {
    if(this.ballMode){this.ballMode=false;this.ball=null;return;}
    if(this.paused||this.videoPlaying||this.hug)return;
    const n=this.characters.Right;
    this.ballMode=true;
    this.ball={x:n.x*1280,y:n.y*720-260,vx:this.facing*390,vy:-260,angle:0};
  }
  update(dt,hands=[],direction=0) {
    if(this.paused) return;
    dt=Math.max(0,dt);
    if(this.curtainPhase!=='idle') {
      this.curtainTimer+=dt;
      while(this.curtainPhase!=='idle'&&this.curtainTimer>=CURTAIN[this.curtainPhase]) {
        if(this.curtainManual&&this.curtainPhase==='closed'){this.curtainTimer=0;break;}
        this.curtainTimer-=CURTAIN[this.curtainPhase];
        this.curtainPhase={closing:'closed',closed:'opening',opening:'idle'}[this.curtainPhase];
      }
      if(this.curtainPhase==='idle')this.curtainTimer=0;
    }
    if(this.videoPlaying)return;
    dt=Math.min(dt,.1);
    if(this.jumpHeight>0||this.jumpVelocity!==0) {
      this.jumpHeight+=this.jumpVelocity*dt-600*dt*dt;
      this.jumpVelocity-=1200*dt;
      if(this.jumpHeight<=0){this.jumpHeight=0;this.jumpVelocity=0;}
    }
    this.clock+=dt;this.hands=hands;
    for(const [name,p] of Object.entries(this.props)) {
      p.time+=dt;
      if(p.phase==='enter'&&p.time>=(name==='bag'?.5:.6)){p.phase='loop';p.time=0;}
      if(p.phase==='fade'){p.alpha=Math.max(0,p.alpha-dt*1.5);if(!p.alpha)p.phase='hidden';}
    }
    this.hugAlpha=clamp(this.hugAlpha+dt*(this.hug?2:-2),0,1);
    for(const [label,c] of Object.entries(this.characters)) {
      const hand=hands.find(h=>h.label===label);
      const visible=c.manual?c.visible:!!hand;
      c.alpha=clamp(c.alpha+dt/.35*(visible?1:-1),0,1);
      if(!hand){c.candidate=0;c.candidateTime=0;continue;}
      if(!this.sleep&&!this.hug&&!(label==='Right'&&(this.run||this.kick>=0))) {
        const smooth=1-Math.exp(-14*dt);
        c.x+=((hand.box[0]+hand.box[2])/2-c.x)*smooth;
        if(!this.verticalLocked) {
          c.y+=(clamp(hand.box[3]+(label==='Right'?.03:0),.02,.98)-c.y)*smooth;
        }
      }
      if(!c.manual&&!this.sleep&&!(label==='Right'&&this.kick>=0)) {
        if(c.candidate!==hand.count){c.candidate=hand.count;c.candidateTime=0;}
        else c.candidateTime+=dt;
        if(c.candidateTime>=.12)this.pose(hand.count,label,false);
      }
    }
    if(this.nandoSpawnLock) {
      this.characters.Right.x=NANDO_SPAWN_LEFT;
      if(this.curtainPhase==='idle')this.nandoSpawnLock=false;
    }
    if(this.hug||this.hugAlpha>0)return;
    const n=this.characters.Right;
    if(this.kick>=0) {
      this.kickTimer+=dt;
      while(this.kick>=0&&this.kickTimer>=KICK[this.kick]) {
        this.kickTimer-=KICK[this.kick];this.kick++;
        if(this.kick===4&&!this.ballMode)this.ball={x:n.x*1280+this.facing*n.height*720*.28,y:n.y*720-n.height*720*.25,vx:this.facing*550,vy:-420,angle:0};
        if(this.kick>=KICK.length){this.kick=-1;if(!this.ballMode)this.ball=null;}
      }
      if(!this.ballMode&&this.ball) {
        const b=this.ball;b.x+=b.vx*dt;b.y+=b.vy*dt+450*dt*dt;b.vy+=900*dt;b.angle+=this.facing*480*dt;
        if(b.x< -60||b.x>1340||b.y>700)this.ball=null;
      }
    }
    if(this.ballMode&&this.ball) {
      const b=this.ball,radius=42;
      b.x+=b.vx*dt;b.y+=b.vy*dt;b.angle+=b.vx*dt/radius;
      if(b.x<radius){b.x=radius;b.vx=Math.abs(b.vx);}
      if(b.x>1280-radius){b.x=1280-radius;b.vx=-Math.abs(b.vx);}
      if(b.y<radius){b.y=radius;b.vy=Math.abs(b.vy);}
      if(b.y>720-radius){b.y=720-radius;b.vy=-Math.abs(b.vy);}
      for(const c of Object.values(this.characters)) {
        if(c.alpha<=0)continue;
        const centerX=c.x*1280,centerY=c.y*720-c.height*360-(c===n?this.jumpHeight:0);
        const distanceX=b.x-centerX,distanceY=b.y-centerY;
        const distance=Math.hypot(distanceX,distanceY)||1;
        const collisionRadius=radius+c.height*220;
        if(distance<collisionRadius) {
          const normalX=distanceX/distance,normalY=distanceY/distance;
          b.x=centerX+normalX*collisionRadius;b.y=centerY+normalY*collisionRadius;
          const velocityAlongNormal=b.vx*normalX+b.vy*normalY;
          if(velocityAlongNormal<0) {
            b.vx-=2*velocityAlongNormal*normalX;
            b.vy-=2*velocityAlongNormal*normalY;
            b.vx*=1.03;b.vy*=1.03;
          }
        }
      }
    } else if(this.kick<0&&this.run&&!this.sleep&&direction) {
      this.facing=Math.sign(direction);
      const next=n.x+direction*420*dt/1280;
      n.x=next<NANDO_SPAWN_LEFT?NANDO_RUN_RIGHT:next>NANDO_RUN_RIGHT?NANDO_SPAWN_LEFT:next;
    }
  }
  sprite(label) {
    const c=this.characters[label];
    if(label==='Right'&&this.scene===0&&c.pose===7)return 'ball0';
    if(this.sleep)return label==='Right'?this.costume+'3':'ibu6';
    if(label==='Right'&&this.run)return 'run'+(Math.floor(this.clock*10)%5);
    return (label==='Right'?this.costume:'ibu')+c.pose;
  }
}
