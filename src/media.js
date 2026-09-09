export class MediaController {
  constructor(video,audio,assets,onChange,onError,onFinished=()=>{}) {
    Object.assign(this,{video,audio,assets,onChange,onError,onFinished});
    this.active=false;this.loading=false;this.scene=null;this.sound=null;this.generation=0;this.paused=false;this.buffering=false;
    this.video.muted=true;this.video.playsInline=true;this.video.preload='metadata';this.audio.preload='none';
    this.video.addEventListener('ended',()=>this.finish(true));
    this.video.addEventListener('waiting',()=>{if(this.active){this.buffering=true;this.audio.pause();}});
    this.video.addEventListener('playing',()=>{this.buffering=false;if(this.active&&!this.paused&&this.sound!==null)this.audio.play().catch(()=>this.onError('Tekan lanjut untuk mengaktifkan audio kembali.'));});
    this.video.addEventListener('error',()=>{if(this.active||this.loading){this.stop();this.stopSound();this.onError('Video gagal dimuat. Periksa koneksi lalu coba lagi.');}});
    this.audio.addEventListener('ended',()=>{this.sound=null;this.onChange();});
    this.audio.addEventListener('error',()=>{if(this.sound!==null){this.sound=null;this.onError('Audio gagal dimuat. Periksa koneksi lalu coba lagi.');this.onChange();}});
  }
  async playVideo(scene,onStarted,waitUntilStart=async()=>{}) {
    if(this.active||this.loading)return false;
    const generation=++this.generation;
    this.loading=true;this.scene=scene;this.paused=false;this.buffering=false;
    this.video.src=this.assets['video'+scene];
    this.stopSound();this.audio.src=this.assets['audio'+scene];this.sound=scene;
    this.onChange();
    await waitUntilStart();
    if(generation!==this.generation)return false;
    // Both play calls originate from the same user gesture, including on mobile.
    const timeout=setTimeout(()=>{if(generation===this.generation&&this.loading){this.stop();this.stopSound();this.onError('Video terlalu lama dimuat. Periksa koneksi dan coba kembali.');}},25000);
    const results=await Promise.allSettled([this.video.play(),this.audio.play()]);
    clearTimeout(timeout);
    if(generation!==this.generation)return false;
    this.loading=false;
    if(results[0].status==='rejected'||!this.video.videoWidth) {
      this.stop();this.stopSound();this.onError('Video belum dapat diputar. Tekan tombol transisi untuk mencoba lagi.');return false;
    }
    this.active=true;
    if(results[1].status==='rejected'){this.sound=null;this.onError('Audio diblokir browser. Setelah video selesai, tekan Putar lagu.');}
    onStarted();this.onChange();return true;
  }
  async playSound(scene) {
    if(this.active||this.loading||this.sound===scene)return;
    this.audio.pause();this.audio.src=this.assets['audio'+scene];this.sound=scene;
    try {await this.audio.play();}catch{this.sound=null;this.onError('Audio belum dapat diputar. Tekan Putar lagu untuk mencoba lagi.');}
    this.onChange();
  }
  stopSound() {this.audio.pause();this.audio.removeAttribute('src');this.audio.load();this.sound=null;this.onChange();}
  finish(ended=false) {this.active=false;this.loading=false;this.buffering=false;this.scene=null;this.onChange();if(ended)this.onFinished();}
  stop() {this.generation++;this.video.pause();this.video.removeAttribute('src');this.video.load();this.finish();}
  async pause(paused) {
    this.paused=paused;
    if(paused){this.video.pause();this.audio.pause();return;}
    const requests=[];
    if(this.active)requests.push(this.video.play());
    if(this.sound!==null)requests.push(this.audio.play());
    const results=await Promise.allSettled(requests);
    if(results.some(r=>r.status==='rejected'))this.onError('Pemutaran tertahan browser. Coba jeda dan lanjutkan kembali.');
  }
  sync() {
    if(!this.active||this.paused||this.buffering||this.sound===null||this.audio.readyState<2)return;
    // Keep the scene song on the video clock, including after slow network buffering.
    const delta=Math.abs(this.audio.currentTime-this.video.currentTime);
    if(delta>.25&&this.video.currentTime<this.audio.duration)this.audio.currentTime=this.video.currentTime;
  }
  dispose(){this.stop();this.stopSound();}
}
