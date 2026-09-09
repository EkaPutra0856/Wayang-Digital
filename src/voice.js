import { voiceScene } from './gestures.js';
export class VoiceController {
  constructor(onScene,onChange,onError) {
    Object.assign(this,{onScene,onChange,onError});
    this.Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
    this.supported=!!this.Recognition;this.enabled=false;this.listening=false;this.blocked=false;this.restartTimer=null;
  }
  start() {
    if(!this.supported){this.onError('Kontrol suara tidak tersedia pada browser ini. Gunakan tombol latar.');return;}
    this.enabled=true;this.sync();
  }
  sync() {
    clearTimeout(this.restartTimer);
    if(!this.enabled||this.blocked){this.recognition?.abort();this.onChange();return;}
    if(this.listening)return;
    const recognition=new this.Recognition();this.recognition=recognition;
    recognition.lang='id-ID';recognition.continuous=true;recognition.interimResults=false;
    recognition.onstart=()=>{this.listening=true;this.onChange();};
    recognition.onresult=event=>{
      if(!this.enabled||this.blocked)return;
      for(let i=event.resultIndex;i<event.results.length;i++) {
        if(!event.results[i].isFinal)continue;
        const scene=voiceScene(event.results[i][0].transcript);
        if(scene!==null)this.onScene(scene);
      }
    };
    recognition.onerror=event=>{
      if(['not-allowed','service-not-allowed','audio-capture','network'].includes(event.error)){
        this.enabled=false;this.onError('Kontrol suara tidak tersedia: '+event.error+'. Tombol latar tetap dapat dipakai.');
      }
    };
    recognition.onend=()=>{this.listening=false;this.onChange();if(this.enabled&&!this.blocked)this.restartTimer=setTimeout(()=>this.sync(),700);};
    try{this.listening=true;recognition.start();}catch{this.listening=false;this.enabled=false;this.onError('Mikrofon belum dapat dimulai. Coba aktifkan kembali.');}
    this.onChange();
  }
  setBlocked(blocked){if(this.blocked!==blocked){this.blocked=blocked;this.sync();}}
  stop(){this.enabled=false;clearTimeout(this.restartTimer);this.recognition?.abort();this.listening=false;this.onChange();}
}
