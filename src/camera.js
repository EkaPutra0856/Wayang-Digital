export class CameraController {
  constructor(video,onChange,onError) {
    Object.assign(this,{video,onChange,onError});
    this.stream=null;this.worker=null;this.starting=false;this.ready=false;this.busy=false;this.hands=[];this.lastFrame=0;this.lastResult=0;this.generation=0;
    this.mirror=document.createElement('canvas');this.mirror.width=640;this.mirror.height=480;
    this.ctx=this.mirror.getContext('2d');
  }
  async start() {
    if(this.starting||this.stream)return;
    const generation=++this.generation;this.starting=true;this.onChange();
    try {
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('Kamera membutuhkan HTTPS atau localhost.');
      const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480},facingMode:'user'},audio:false});
      if(generation!==this.generation){stream.getTracks().forEach(t=>t.stop());return;}
      this.stream=stream;
      stream.getVideoTracks()[0].addEventListener('ended',()=>{if(this.stream){this.stop();this.onError('Kamera terputus. Akses dikunci. Aktifkan kembali kamera untuk masuk.');}});
      this.video.srcObject=stream;await this.video.play();
      if(generation!==this.generation)return;
      this.worker=new Worker(new URL('./hand-worker.js',import.meta.url),{type:'module'});
      await new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>reject(new Error('Model kamera terlalu lama dimuat. Coba aktifkan kembali.')),45000);
        this.cancelInit=()=>{clearTimeout(timer);reject(new Error('Kamera dibatalkan.'));};
        this.worker.onerror=event=>{clearTimeout(timer);if(this.ready){this.stop();this.onError('Deteksi tangan terhenti. Aktifkan kamera kembali.');}else reject(new Error(event.message||'Deteksi tangan tidak tersedia.'));};
        this.worker.onmessage=({data})=>{
          if(data.type==='ready'){clearTimeout(timer);this.ready=true;resolve();}
          if(data.type==='hands'){this.hands=data.hands;this.busy=false;this.lastResult=performance.now();}
          if(data.type==='error'){clearTimeout(timer);if(this.ready){this.stop();this.onError('Deteksi tangan gagal. Aktifkan kamera kembali untuk membuka akses.');}else reject(new Error(data.message));}
        };
        this.worker.postMessage({type:'init',origin:location.origin});
      });
      if(generation!==this.generation)return;
      this.cancelInit=null;this.starting=false;
      this.onChange();
    } catch(error) {
      if(generation!==this.generation)return;
      this.stop();
      const message=error.name==='NotAllowedError'?'Izin kamera belum diberikan. Izinkan kamera melalui ikon di address bar, lalu coba masuk kembali.'
        :error.name==='NotFoundError'?'Kamera tidak ditemukan. Hubungkan kamera untuk membuka akses.'
        :error.name==='NotReadableError'?'Kamera sedang digunakan aplikasi lain. Tutup aplikasi tersebut lalu coba kembali.':error.message;
      this.onError(message);
    }
  }
  async tick(now,enabled) {
    if(this.ready&&!this.stream?.getVideoTracks().some(track=>track.readyState==='live')) {
      this.stop();this.onError('Kamera tidak aktif. Izinkan kamera kembali untuk masuk.');return;
    }
    if(now-this.lastResult>300)this.hands=[];
    if(!enabled||!this.ready||this.busy||now-this.lastFrame<80||this.video.readyState<2)return;
    this.lastFrame=now;this.busy=true;const generation=this.generation;
    try {
      this.ctx.save();this.ctx.translate(640,0);this.ctx.scale(-1,1);this.ctx.drawImage(this.video,0,0,640,480);this.ctx.restore();
      const frame=await createImageBitmap(this.mirror);
      if(generation!==this.generation){frame.close();return;}
      this.worker.postMessage({type:'frame',frame,timestamp:now},[frame]);
    }catch{this.busy=false;}
  }
  stop() {
    this.generation++;this.cancelInit?.();this.cancelInit=null;
    this.worker?.terminate();this.worker=null;
    this.stream?.getTracks().forEach(t=>t.stop());this.stream=null;
    this.video.srcObject=null;this.ready=false;this.starting=false;this.busy=false;this.hands=[];this.onChange();
  }
}
