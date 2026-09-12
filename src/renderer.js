import { CURTAIN, clamp } from './state.js';
export class Renderer {
  constructor(canvas,assets) {this.canvas=canvas;this.ctx=canvas.getContext('2d',{alpha:false});this.assets=assets;this.images={};this.oldScene=null;this.scene=0;this.changedAt=0;}
  async load(progress=()=>{}) {
    const entries=Object.entries(this.assets).filter(([,url])=>url.endsWith('.webp'));
    let complete=0;
    await Promise.all(entries.map(async([id,url])=>{
      const img=new Image();img.src=url;
      try{await img.decode();}catch{throw new Error('Aset '+id+' gagal dimuat. Muat ulang halaman.');}
      this.images[id]=img;progress(++complete/entries.length);
    }));
  }
  fit(image,cover=true,alpha=1) {
    const ctx=this.ctx,w=this.canvas.width,h=this.canvas.height;
    const iw=image.videoWidth||image.width,ih=image.videoHeight||image.height;
    if(!iw||!ih)return;
    const scale=(cover?Math.max:Math.min)(w/iw,h/ih);
    ctx.save();ctx.globalAlpha=alpha;ctx.drawImage(image,(w-iw*scale)/2,(h-ih*scale)/2,iw*scale,ih*scale);ctx.restore();
  }
  sprite(id,x,y,height,alpha=1,flip=false,angle=0) {
    const image=this.images[id];if(!image||alpha<=0)return;
    const ctx=this.ctx,w=height*image.width/image.height;
    ctx.save();ctx.globalAlpha=alpha;ctx.translate(x,y);if(flip)ctx.scale(-1,1);
    if(angle){ctx.rotate(angle*Math.PI/180);ctx.drawImage(image,-w/2,-height/2,w,height);}
    else ctx.drawImage(image,-w/2,-height,w,height);
    ctx.restore();
  }
  draw(state,video) {
    const ctx=this.ctx,w=1280,h=720;
    if(this.canvas.width!==w){this.canvas.width=w;this.canvas.height=h;}
    ctx.fillStyle='#121b17';ctx.fillRect(0,0,w,h);
    if(this.scene!==state.scene){this.oldScene=this.scene;this.scene=state.scene;this.changedAt=state.clock;}
    const blend=clamp((state.clock-this.changedAt)/.4,0,1);
    if(this.oldScene!==null&&blend<1)this.fit(this.images['bg'+this.oldScene]);
    this.fit(this.images['bg'+state.scene],true,this.oldScene!==null?blend:1);
    if(state.videoPlaying&&video.readyState>=2)this.fit(video,false);
    else if(state.hugAlpha>0) {
      const img=this.images.hug;const size=Math.min(h*.8,w*.8*img.height/img.width);
      this.sprite('hug',w/2,h*.94,size*(.94+.06*state.hugAlpha),state.hugAlpha);
    } else {
      for(const label of ['Left','Right']) {
        const c=state.characters[label],special=label==='Right'&&(state.run||state.kick>=0);
        const breath=state.sleep?1+Math.sin(state.clock*2)*.015:c.manual&&!special?1+Math.sin(state.clock*1.745+(label==='Right'?1.4:0))*.012:1;
        this.sprite(state.sprite(label),c.x*w,c.y*h-(label==='Right'?state.jumpHeight:0)+(state.sleep?Math.sin(state.clock*2)*2:0),c.height*h*breath*(label==='Left'?1.5:1),c.alpha,label==='Right'&&state.nandoFlipped());
      }
      if(state.ball){const b=state.ball;this.sprite('ball5',b.x,b.y,h*.12,1,false,b.angle||.001);}
    }
    if(!state.videoPlaying)this.props(state);
    if(state.showBoxes&&!state.videoPlaying)for(const hand of state.hands) {
      const [x1,y1,x2,y2]=hand.box;
      ctx.strokeStyle='#21e5a0';ctx.lineWidth=2;ctx.strokeRect(x1*w,y1*h,(x2-x1)*w,(y2-y1)*h);
      ctx.fillStyle='#123a2b';ctx.fillRect(x1*w,y1*h-26,160,26);
      ctx.fillStyle='#fff';ctx.font='16px sans-serif';ctx.fillText((hand.label==='Right'?'Nando':'Ibu')+' · '+hand.count+' jari',x1*w+6,y1*h-7);
    }
  }
  props(state) {
    const bag=this.images.bag,book=this.images.book;
    if(!bag||!book)return;
    const width=1280*.4,height=width*bag.height/bag.width,x=640,y=720*.55;
    const draw=(id,cx,cy,w,h,angle,alpha)=>{
      if(w<=0||h<=0||alpha<=0)return;
      const ctx=this.ctx;ctx.save();ctx.globalAlpha=alpha;ctx.translate(cx,cy);ctx.rotate(-angle*Math.PI/180);
      ctx.drawImage(this.images[id],-w/2,-h/2,w,h);ctx.restore();
    };
    const b=state.props.book;
    if(b.phase!=='hidden') {
      const enter=b.phase==='enter',p=enter?Math.sin(Math.min(1,b.time/.6)*Math.PI/2):1;
      const scale=enter?.3+.7*p:1+.05*Math.sin(b.time*3.5),bw=width*.55*scale;
      draw('book',x+width*.42*p,y-height*.38*p+(enter?0:Math.sin(b.time*3)*8),bw,bw*book.height/book.width,enter?15*(1-p):15*Math.sin(b.time*2.5),b.alpha);
    }
    const a=state.props.bag;
    if(a.phase!=='hidden') {
      const p=Math.min(1,a.time/.5),pop=1+2.70158*(p-1)**3+1.70158*(p-1)**2;
      draw('bag',x,y,width*(a.phase==='enter'?pop:1+.04*Math.sin(a.time*3)),height*(a.phase==='enter'?pop:1-.04*Math.sin(a.time*3)),0,a.alpha);
    }
  }
  cameraPreview(video,hands=[]) {
    if(video.readyState<2)return;
    const ctx=this.ctx,width=300,height=225,x=this.canvas.width-width-24,y=24;
    const connections=[[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],
      [5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],
      [13,17],[0,17],[17,18],[18,19],[19,20]];
    ctx.save();
    ctx.fillStyle='#122c22';ctx.fillRect(x-3,y-3,width+6,height+6);
    // Mirror only the camera image. Worker landmarks already use mirrored coordinates.
    ctx.save();ctx.translate(x+width,y);ctx.scale(-1,1);
    ctx.drawImage(video,0,0,width,height);ctx.restore();
    ctx.save();ctx.beginPath();ctx.rect(x,y,width,height);ctx.clip();
    for(const hand of hands) {
      const points=hand.landmarks;
      if(!points||points.length!==21)continue;
      const color=hand.label==='Right'?'#ffdf69':'#56f3d0';
      ctx.lineWidth=2.5;ctx.strokeStyle=color;ctx.beginPath();
      for(const [a,b] of connections) {
        ctx.moveTo(x+points[a].x*width,y+points[a].y*height);
        ctx.lineTo(x+points[b].x*width,y+points[b].y*height);
      }
      ctx.stroke();
      for(const point of points) {
        ctx.beginPath();ctx.arc(x+point.x*width,y+point.y*height,3.5,0,Math.PI*2);
        ctx.fillStyle=color;ctx.fill();ctx.lineWidth=1;ctx.strokeStyle='#14261c';ctx.stroke();
      }
      // Anchor the number above the tracked hand, in the same mirrored coordinates.
      const left=Math.min(...points.map(p=>p.x)),right=Math.max(...points.map(p=>p.x));
      const top=Math.min(...points.map(p=>p.y));
      const labelX=clamp(x+(left+right)*width/2,x+18,x+width-18);
      const labelY=clamp(y+top*height-22,y+18,y+height-18);
      ctx.fillStyle='#122c22e6';ctx.beginPath();ctx.arc(labelX,labelY,16,0,Math.PI*2);ctx.fill();
      ctx.font='bold 23px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=color;
      ctx.fillText(String(hand.count),labelX,labelY);
    }
    ctx.restore();ctx.restore();
  }

  curtain(state) {
    if(state.curtainPhase==='idle')return;
    const ctx=this.ctx,w=this.canvas.width,h=this.canvas.height;
    let amount=1,alpha=1;
    const ease=t=>t*t*(3-2*t);
    if(state.curtainPhase==='closing')amount=ease(clamp(state.curtainTimer/CURTAIN.closing,0,1));
    if(state.curtainPhase==='opening'){const p=clamp(state.curtainTimer/CURTAIN.opening,0,1);amount=1-ease(p);alpha=1-p;}
    const size=Math.ceil(w/2*amount);
    ctx.save();ctx.globalAlpha=alpha;
    for(const right of [false,true]) {
      ctx.save();if(right){ctx.translate(w,0);ctx.scale(-1,1);}
      ctx.beginPath();ctx.rect(0,0,size,h);ctx.clip();
      const offset=size-w/2;
      for(let x=0;x<w/2;x+=2) {
        const shade=.65+.25*Math.cos(x*.06)+.1*Math.cos(x*.12);
        ctx.fillStyle='rgb('+Math.round(146*shade)+','+Math.round(34*shade)+','+Math.round(43*shade)+')';ctx.fillRect(x+offset,0,3,h);
      }
      const gradient=ctx.createLinearGradient(0,0,0,h);gradient.addColorStop(0,'#0000');gradient.addColorStop(1,'#0006');ctx.fillStyle=gradient;ctx.fillRect(0,0,size,h);
      ctx.fillStyle='#d0a45e';ctx.fillRect(size-5,0,3,h);ctx.restore();
    }
    ctx.restore();
  }
}
