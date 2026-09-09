export const SCENES = [
  {name:'Taman', subtitle:'Awal cerita', key:'6', soundKey:'Z'},
  {name:'Rumah', subtitle:'Waktu bersama', key:'7', soundKey:'X'},
  {name:'Sekolah', subtitle:'Berangkat sekolah', key:'0', soundKey:'C'},
  {name:'Kelas', subtitle:'Buku dari Ibu', key:'8', soundKey:'V'},
  {name:'Koridor', subtitle:'Pelukan penutup', key:'9', soundKey:'B'},
];
export const CURTAIN = { closing:0.35, closed:1, opening:0.65 };
export const SCALE_FACTORS = [1, 1.25, 1.5];
const KICK = [0.25,0.35,0.35,0.16,1.6,0.3];
export const clamp = (v,min,max)=>Math.max(min,Math.min(max,v));
const character = x=>({x,y:.88,height:.46,pose:1,alpha:1,manual:true,visible:true,candidate:0,candidateTime:0});
export class ShowState {
  constructor() {
    this.scene=0; this.banks={Right:1,Left:1}; this.costume='sport'; this.costumeMode='auto';
    this.characters={Right:character(.70),Left:character(.26)};
    this.lastPose={sport:1,school:1};
    this.paused=false; this.clock=0; this.run=false; this.sleep=false; this.hug=false;
    this.hugAlpha=0; this.facing=1; this.kick=-1; this.kickTimer=0; this.ball=null;
    this.verticalLocked=true; this.scaleLevel=0; this.curtainPhase='idle'; this.curtainTimer=0;
    this.videoPlaying=false; this.gesture=false; this.showBoxes=false; this.hands=[];
  }
  setScene(index) {
    if (!Number.isInteger(index)||index<0||index>=SCENES.length) return;
    this.scene=index;
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
    this.curtainPhase='closing';this.curtainTimer=0;return true;
  }
  startKick() {
    if(this.paused||this.videoPlaying||this.hug||this.kick>=0) return;
    this.kick=0;this.kickTimer=0;this.ball=null;
  }
  update(dt,hands=[],direction=0) {
    if(this.paused) return;
    dt=Math.max(0,dt);
    if(this.curtainPhase!=='idle') {
      this.curtainTimer+=dt;
      while(this.curtainPhase!=='idle'&&this.curtainTimer>=CURTAIN[this.curtainPhase]) {
        this.curtainTimer-=CURTAIN[this.curtainPhase];
        this.curtainPhase={closing:'closed',closed:'opening',opening:'idle'}[this.curtainPhase];
      }
      if(this.curtainPhase==='idle')this.curtainTimer=0;
    }
    if(this.videoPlaying)return;
    dt=Math.min(dt,.1);
    this.clock+=dt;this.hands=hands;
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
    if(this.hug||this.hugAlpha>0)return;
    const n=this.characters.Right;
    if(this.kick>=0) {
      this.kickTimer+=dt;
      while(this.kick>=0&&this.kickTimer>=KICK[this.kick]) {
        this.kickTimer-=KICK[this.kick];this.kick++;
        if(this.kick===4)this.ball={x:n.x*1280+this.facing*n.height*720*.28,y:n.y*720-n.height*720*.25,vx:this.facing*550,vy:-420,angle:0};
        if(this.kick>=KICK.length){this.kick=-1;this.ball=null;}
      }
      if(this.ball) {
        const b=this.ball;b.x+=b.vx*dt;b.y+=b.vy*dt+450*dt*dt;b.vy+=900*dt;b.angle+=this.facing*480*dt;
        if(b.x< -60||b.x>1340||b.y>700)this.ball=null;
      }
    } else if(this.run&&!this.sleep&&direction) {
      this.facing=Math.sign(direction);n.x=clamp(n.x+direction*420*dt/1280,.14,.86);
    }
  }
  sprite(label) {
    const c=this.characters[label];
    if(label==='Right'&&this.kick>=0)return 'ball'+[0,1,2,3,4,0][this.kick];
    if(this.sleep)return label==='Right'?this.costume+'3':'ibu6';
    if(label==='Right'&&this.run)return 'run'+(Math.floor(this.clock*10)%5);
    return (label==='Right'?this.costume:'ibu')+c.pose;
  }
}
