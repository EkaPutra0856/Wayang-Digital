import './style.css';
import assets from './generated/assets.json';
import { ShowState, SCENES, SCALE_FACTORS } from './state.js';
import { Renderer } from './renderer.js';
import { MediaController } from './media.js';
import { CameraController } from './camera.js';
import { VoiceController } from './voice.js';

const paths={
 play:'m9 5 11 7-11 7V5Z', pause:'M8 5v14M16 5v14',camera:'M15 8V5H3v14h12v-3l6 3V5l-6 3Z',
 expand:'M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5',help:'M9 9a3 3 0 1 1 5 2c-2 1-2 2-2 3m0 3h.01',
 arrow:'m9 5 7 7-7 7', curtain:'M3 4h18M4 4v16l6-8-6-8Zm16 0v16l-6-8 6-8Z',
 sound:'M9 18V5l11-2v13M9 8l11-2M9 18a3 3 0 1 1-3-3c2 0 3 1 3 3Zm11-2a3 3 0 1 1-3-3c2 0 3 1 3 3Z',
 hand:'M8 12V5a2 2 0 0 1 4 0v7-9a2 2 0 0 1 4 0v9-6a2 2 0 0 1 4 0v10c0 8-10 8-13 3l-4-6a2 2 0 0 1 3-2l2 1Z',
 mic:'M9 3h6v11H9V3Zm-3 8v3a6 6 0 0 0 12 0v-3m-6 9v3m-3 0h6',
 stop:'M5 5h14v14H5z', eye:'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Zm10-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z',
};
const icon=name=>'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+(name==='help'?'<circle cx="12" cy="12" r="10"/>':'')+'<path d="'+paths[name]+'"/></svg>';
const button=(action,text,key='',extra='')=>'<button type="button" data-action="'+action+'" '+extra+'>'+text+(key?'<kbd>'+key+'</kbd>':'')+'</button>';
document.querySelector('#app').innerHTML=`
  <section id="welcome" class="access-gate" aria-labelledby="access-title"><div class="welcome-card"><span class="welcome-symbol">${icon('camera')}</span><div class="eyebrow">WAYANG DIGITAL</div><h1 id="access-title">Izin kamera diperlukan</h1><p>Izinkan kamera sebelum masuk ke panggung.<br>Akses hanya terbuka selama kamera aktif.</p><button id="start" data-action="start" class="primary" disabled>Menyiapkan aset...</button><div class="load-track"><span id="load-progress"></span></div><small id="load-caption">Memuat gambar panggung</small><p id="access-error" role="alert" hidden></p><small>Gambar kamera diproses di perangkatmu. Mikrofon tidak diminta.</small></div></section>
  <header class="app-header">
    <a class="brand" href="/" aria-label="Wayang Digital beranda"><span class="brand-mark">${icon('curtain')}</span><span>wayang<span class="brand-light">digital</span><small>RUANG CERITA INTERAKTIF</small></span></a>
    <div class="header-right"><span class="school-label">NANDO & IBU <span>•</span> AL AZHAR</span>${button('help',icon('help')+'<span>Panduan</span>','','class="subtle"')}</div>
  </header>
  <main class="workspace">
    <div class="page-heading"><div><div class="eyebrow">STUDIO PERTUNJUKAN</div><h1>Setiap gerak, sebuah cerita.</h1><p>Hidupkan Nando dan Ibu di panggungmu.</p></div><div class="ready-badge"><i></i><span id="ready-label">Menyiapkan aset</span></div></div>
    <div class="studio-layout">
      <div class="main-column">
        <section class="stage-card" aria-label="Panggung pertunjukan">
          <div class="stage-title"><span><i class="live-dot"></i> PANGGUNG <span id="scene-label">01 / TAMAN</span></span><div>${button('pause',icon('pause'),'','class="icon-button" aria-label="Jeda pertunjukan"')}${button('fullscreen',icon('expand'),'','class="icon-button" aria-label="Layar penuh"')}</div></div>
          <div id="stage" class="stage" tabindex="0" aria-label="Panggung wayang, gunakan keyboard atau panel kontrol">
            <canvas id="canvas" width="1280" height="720" aria-label="Animasi Nando dan Ibu"></canvas>
            <div class="stage-badges"><span id="stage-mode">MODE MANUAL</span><span id="paused-badge" hidden>DIJEDA</span></div>

          </div>
          <div class="stage-footer"><div><span class="dot" id="camera-dot"></span><span id="camera-status">Kamera nonaktif</span><span class="footer-divider"></span><span id="pose-status">Nando 1 · Ibu 1</span></div>${button('focus',icon('eye')+'<span>Fokus panggung</span>','U','class="text-button"')}</div>
        </section>
        <section class="scene-section" aria-labelledby="scene-heading">
          <div class="section-heading"><h2 id="scene-heading">Alur cerita <span>5 adegan</span></h2><span class="section-note">Pilih latar, lalu mainkan transisi</span></div>
          <div class="scene-list">${SCENES.map((s,i)=>`<button class="scene-tile" data-action="scene" data-value="${i}" aria-label="Pilih latar ${s.name}"><span class="scene-image"><img src="${assets['bg'+i]}" alt="" /><span class="scene-number">0${i+1}</span><span class="scene-check">✓</span></span><span class="scene-name">${s.name}<kbd>F${i+1}</kbd></span><span class="scene-subtitle">${s.subtitle}</span></button>`).join('')}</div>
        </section>
        <section class="cue-bar"><div class="cue-title"><span class="cue-icon">${icon('play')}</span><div><strong id="cue-title">Transisi · Taman</strong><span id="media-status">Siap dimainkan</span></div></div><div class="cue-actions">${button('video',icon('play')+'<span>Putar transisi</span>','6','class="primary" id="play-video"')}${button('sound',icon('sound')+'<span>Putar lagu</span>','Z','id="play-sound"')}${button('skip',icon('stop'),'','class="icon-button" aria-label="Lewati video" title="Lewati video (Esc)" id="skip-video"')}</div></section>
        <div class="playback-track"><span id="playback-progress"></span></div>
        <div class="stage-tip">${icon('curtain')} Tirai otomatis menutup pada setiap transisi. Tertutup 1 detik, lalu terbuka sebelum video dimulai.</div>
      </div>
      <aside class="controls" aria-label="Kontrol pertunjukan">
        <div class="control-heading"><h2>Ruang kendali</h2><span class="pill">LIVE STUDIO</span></div>
        <section class="control-section"><div class="label-row"><h3>Karakter</h3><span>Set terpisah untuk setiap karakter</span></div>
          <div class="bank-controls">${button('bank','Nando Set 1','O','class="bank-button" id="bank-nando" data-value="Right"')}${button('bank','Ibu Set 1','A','class="bank-button" id="bank-ibu" data-value="Left"')}</div><div class="character-tabs" role="group" aria-label="Pilih karakter"><button data-action="character" data-value="Right" aria-pressed="true"><span class="avatar"><img src="${assets.sport1}" alt="" /></span><span>Nando<small>Tangan kanan</small></span></button><button data-action="character" data-value="Left" aria-pressed="false"><span class="avatar"><img src="${assets.ibu1}" alt="" /></span><span>Ibu<small>Tangan kiri</small></span></button></div>
          <div class="pose-label">POSE KARAKTER <span id="pose-key">N + angka</span></div><div id="pose-buttons" class="pose-buttons"></div>
          <div class="costume-row"><label for="costume">Kostum Nando</label><select id="costume"><option value="auto">Otomatis</option><option value="sport">Olahraga</option><option value="school">Sekolah</option></select></div>
          <div class="mini-actions">${button('salam','Salam')}${button('gesture','Mode jari','G')}${button('manual','Manual')}</div>
        </section>
        <section class="control-section"><div class="label-row"><h3>Animasi</h3><span>Sentuhan kecil, cerita hidup</span></div><div class="animation-grid">${button('run','<span>↝</span> Lari','R')}${button('ball','<span>◉</span> Bola pantul','B')}${button('sleep','<span>☾</span> Tidur','T')}${button('hug','<span>♡</span> Pelukan','H')}</div>
          <div class="movement"><button data-move="-1" aria-label="Gerakkan Nando ke kiri">←</button><span>Tahan untuk bergerak saat lari</span><button data-move="1" aria-label="Gerakkan Nando ke kanan">→</button></div>
          ${button('curtain',icon('curtain')+'Tutup & buka tirai','P','class="wide"')}
          <div class="mini-actions">${button('lock','Kunci tinggi','L')}${button('balance','Ukuran normal','S')}</div>
        </section>
        <section class="control-section scale-section"><div class="label-row"><h3>Ukuran karakter</h3><strong id="scale-label">Normal 100%</strong></div><div class="scale-controls">${button('scale-down','Perkecil','-','id="scale-down"')}${button('scale-up','Perbesar','+','id="scale-up"')}</div><p class="scale-note">100% / 125% / 150%. Ukuran tidak mengikuti jarak tangan.</p></section>
        <section class="control-section input-section"><div class="label-row"><h3>Kontrol interaktif</h3></div>
          <button class="device-button" data-action="camera" id="camera-button"><span class="device-icon">${icon('camera')}</span><span><strong id="camera-button-text">Aktifkan kamera</strong><small>Gerakkan wayang dengan tangan</small></span><span class="switch" id="camera-switch"></span></button>
          <button class="device-button" data-action="voice" id="voice-button"><span class="device-icon">${icon('mic')}</span><span><strong id="voice-button-text">Kontrol suara</strong><small>Ucapkan nama latar</small></span><span class="switch" id="voice-switch"></span></button>
          <div class="mini-actions">${button('preview','Preview kamera','W')}${button('boxes','Kotak tangan','D')}</div>
          <p class="privacy-note">Gambar kamera diproses di perangkatmu. Kontrol suara mengikuti layanan browser.</p>
        </section>
        <section class="volume-section"><label for="volume">${icon('sound')} Volume</label><input id="volume" aria-label="Volume" type="range" min="0" max="100" value="80" /><span id="volume-label">80%</span>${button('stop-sound',icon('stop'),'','class="icon-button" aria-label="Hentikan lagu" title="Hentikan lagu (M)"')}</section>
      </aside>
    </div>
    <footer class="page-footer"><span>WAYANG DIGITAL <span>•</span> Cerita tumbuh bersama.</span><span><kbd>SPACE</kbd> Jeda <kbd>F</kbd> Layar penuh <kbd>?</kbd> Panduan</span></footer>
  </main>
  <button id="exit-focus" class="exit-focus" data-action="focus" hidden>Tampilkan kontrol <kbd>U</kbd></button>
  <div id="toast" class="toast" role="status" aria-live="polite" hidden></div>
  <dialog id="help"><div class="dialog-heading"><div class="eyebrow">PANDUAN PANGGUNG</div><button data-action="close-help" aria-label="Tutup panduan">×</button></div><h2>Siap menjadi dalang?</h2><p>Pilih adegan dan tekan <strong>Putar transisi</strong>. Gunakan pose dan animasi untuk melanjutkan ceritanya.</p>
  <div class="help-grid">
    <section><h3>Karakter & gerakan</h3><p><kbd>N</kbd> + <kbd>1–5</kbd> Nando · <kbd>I</kbd> + <kbd>1–5</kbd> Ibu<br><kbd>O</kbd> set Nando / <kbd>A</kbd> set Ibu (1 / 2) · ulang pose untuk sembunyikan<br><kbd>G</kbd> mode jari · <kbd>Y</kbd> ganti kostum · <kbd>J</kbd> otomatis<br><kbd>R</kbd> lari · <kbd>← →</kbd> bergerak · <kbd>B</kbd> bola pantul<br><kbd>T</kbd> tidur · <kbd>H</kbd> pelukan · <kbd>+</kbd> / <kbd>-</kbd> ukuran 100/125/150% (kedua karakter)<br><kbd>L</kbd> kunci tinggi · <kbd>S</kbd> ukuran normal</p><p><strong>Salam:</strong> SPORT, Bank 2, N+5. Tombol Salam langsung menyiapkannya.</p></section>
    <section><h3>Latar & media</h3><p><kbd>F1–F5</kbd> pilih latar · <kbd>[ ]</kbd> sebelumnya / berikutnya<br><kbd>6 7 0 8 9</kbd> transisi adegan 1–5 + latar + lagu<br><kbd>Z X C V B</kbd> lagu 1–5 · <kbd>M</kbd> hentikan lagu<br><kbd>P</kbd> tirai · <kbd>SPACE</kbd> jeda semua<br><kbd>ESC</kbd> lewati video / keluar fullscreen<br><kbd>F</kbd> fullscreen · <kbd>U</kbd> fokus panggung · <kbd>Q</kbd> akhiri sesi</p><p>Tirai menutup 0,35 detik, tertutup penuh 1 detik, lalu membuka 0,65 detik. Video dimulai setelah tirai terbuka.</p></section>
    <section><h3>Kamera & suara</h3><p>Izin kamera wajib sebelum masuk. Jika kamera mati atau izin dicabut, akses terkunci kembali. Tangan kanan mengontrol Nando; kiri mengontrol Ibu. Tampilkan telapak dengan 1–5 jari. Titik dan garis pelacak serta jumlah jari ditampilkan di preview kamera. Tanpa tangan, karakter memudar. Jarak tangan tidak mengubah ukuran karakter.</p><p><kbd>W</kbd> preview kamera · <kbd>D</kbd> kotak tangan. Kamera dan mikrofon membutuhkan HTTPS atau localhost. Suara: “taman”, “rumah”, “sekolah”, “kelas”, “koridor”.</p></section>
    <section><h3>Tips pertunjukan</h3><p>Gunakan Chrome atau Edge desktop untuk kontrol lengkap. Semua adegan dan pose juga bisa dipilih dengan tombol layar. Mode suara bergantung dukungan browser dan koneksi internet.</p><p>Tekan <strong>Fokus panggung</strong> atau <strong>Layar penuh</strong> untuk pertunjukan. Saat tab ditinggalkan, pertunjukan otomatis dijeda. Aktifkan Lanjut saat kembali.</p></section>
  </div><button data-action="close-help" class="primary">Mengerti, kembali ke panggung</button></dialog>
  <video id="cutscene" playsinline muted preload="metadata" class="media-element"></video><audio id="soundtrack" preload="none"></audio><video id="webcam" playsinline muted class="media-element"></video>
`;

const $=selector=>document.querySelector(selector);
let state=new ShowState(),started=false,loaded=false,selected='Right',showPreview=true,focusMode=false,toastTimer,poseSignature='',pointerDirection=0;
const held=new Set(),canvas=$('#canvas'),stage=$('#stage'),video=$('#cutscene'),audio=$('#soundtrack');
const renderer=new Renderer(canvas,assets);
function toast(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,7000);}
const media=new MediaController(video,audio,assets,()=>{state.videoPlaying=media.active;sync();},toast,()=>{if(!state.paused)state.curtain(true);});
const camera=new CameraController($('#webcam'),()=>{
  if(!camera.ready&&started)lockAccess();
  if(camera.ready&&!state.gesture)state.useGesture();
  sync();
},message=>{$('#access-error').textContent=message;$('#access-error').hidden=false;toast(message);});
const voice=new VoiceController(index=>{if(started&&!state.paused&&!media.active&&!media.loading&&media.sound===null){state.setScene(index);sync();}},sync,toast);
audio.volume=.8;

function renderPoses() {
  const signature=[selected,state.banks[selected],state.costume,state.scene].join();
  if(poseSignature!==signature) {
    poseSignature=signature;
    $('#pose-buttons').innerHTML=Array.from({length:5},(_,i)=>{
      const pose=(state.banks[selected]-1)*5+i+1,valid=pose<=state.limit(selected);
      const id=selected==='Right'&&state.scene===0&&pose===7?'ball0':(selected==='Right'?state.costume:'ibu')+pose;
      const label='Pose '+pose;
      return '<button data-action="pose" data-value="'+(i+1)+'" '+(!valid?'disabled':'')+' aria-label="'+(valid?label:'Slot kosong')+'" title="'+(valid?label:'Slot kosong')+'">'+(valid?'<img src="'+assets[id]+'" alt="" />':'<span>—</span>')+'<small>'+pose+'</small></button>';
    }).join('');
  }
  for(const b of $('#pose-buttons').children)b.setAttribute('aria-pressed',String(state.characters[selected].pose===(state.banks[selected]-1)*5+Number(b.dataset.value)&&state.characters[selected].visible));
  $('#pose-key').textContent=selected==='Right'?'N + angka':'I + angka';
}
function lockAccess() {
  started=false;state.paused=true;held.clear();pointerDirection=0;
  media.dispose();voice.stop();focusMode=false;setFocus();
  $('#help').close();$('#welcome').hidden=false;
  if(document.fullscreenElement)document.exitFullscreen().catch(()=>{});
  sync();$('#start').focus();
}
function sync() {
  document.body.classList.toggle('access-locked',!started);
  $('.workspace').inert=!started;$('.app-header').inert=!started;
  $('#start').disabled=!loaded||camera.starting;
  $('#start').textContent=camera.starting?'Menunggu izin dan menyiapkan kamera...':'Izinkan kamera & masuk';

  const scene=SCENES[state.scene];
  $('#scene-label').textContent='0'+(state.scene+1)+' / '+scene.name.toUpperCase();
  $('#cue-title').textContent='Transisi · '+scene.name;
  $('#ready-label').textContent=!loaded?'Menyiapkan aset':!started?'Siap bercerita':state.paused?'Pertunjukan dijeda':'Panggung siap';
  $('#stage-mode').textContent=state.gesture?'MODE JARI':'MODE MANUAL';
  $('#paused-badge').hidden=!state.paused;
  document.querySelectorAll('[data-action="pause"]').forEach(b=>{b.setAttribute('aria-pressed',String(state.paused));b.setAttribute('aria-label',state.paused?'Lanjutkan pertunjukan':'Jeda pertunjukan');});
  $('#pose-status').textContent='Nando '+state.characters.Right.pose+' · Ibu '+state.characters.Left.pose;
  $('#bank-nando').innerHTML='Nando Set '+state.banks.Right+'<kbd>O</kbd>';
  $('#bank-ibu').innerHTML='Ibu Set '+state.banks.Left+'<kbd>A</kbd>';
  $('#costume').value=state.costumeMode==='auto'?'auto':state.costume;
  for(const b of document.querySelectorAll('[data-action="scene"]'))b.setAttribute('aria-pressed',String(Number(b.dataset.value)===state.scene));
  for(const b of document.querySelectorAll('[data-action="character"]'))b.setAttribute('aria-pressed',String(b.dataset.value===selected));
  for(const [action,on] of Object.entries({run:state.run,sleep:state.sleep,hug:state.hug,kick:state.kick>=0,ball:state.ballMode,lock:state.verticalLocked,gesture:state.gesture,manual:!state.gesture,boxes:state.showBoxes,preview:showPreview})){
    document.querySelectorAll('[data-action="'+action+'"]').forEach(b=>b.setAttribute('aria-pressed',String(on)));
  }
  const busy=media.active||media.loading;
  $('#play-video').disabled=busy||state.paused||!started;
  $('#play-video').querySelector('kbd').textContent=scene.key;
  $('#play-video').querySelector('span').textContent=media.loading?'Memuat…':media.active?'Sedang diputar':'Putar transisi';
  $('#play-sound').disabled=busy||state.paused||!started;
  $('#play-sound').querySelector('kbd').textContent=scene.soundKey;
  $('#skip-video').disabled=!busy;
  $('#media-status').textContent=media.loading?'Menyiapkan video & lagu':media.active?'Video '+SCENES[media.scene].name+' sedang diputar':media.sound!==null?'Lagu '+SCENES[media.sound].name+' sedang diputar':'Siap dimainkan';
  $('#camera-button-text').textContent=camera.starting?'Menyiapkan kamera…':camera.ready?'Kamera aktif':'Aktifkan kamera';
  $('#camera-status').textContent=camera.starting?'Memuat deteksi tangan':camera.ready?'Kamera terhubung':'Kamera nonaktif';
  $('#camera-dot').classList.toggle('on',camera.ready);
  $('#camera-switch').classList.toggle('on',camera.ready);$('#camera-button').setAttribute('aria-pressed',String(camera.ready));
  $('#voice-switch').classList.toggle('on',voice.enabled);$('#voice-button').setAttribute('aria-pressed',String(voice.enabled));
  $('#voice-button-text').textContent=!voice.supported?'Suara tidak didukung':voice.enabled?(voice.blocked?'Suara dijeda saat media':'Kontrol suara aktif'):'Kontrol suara';
  $('#scale-label').textContent=['Normal 100%','Besar 125%','Paling besar 150%'][state.scaleLevel];
  $('#scale-down').disabled=state.scaleLevel===0||state.paused||busy;
  $('#scale-up').disabled=state.scaleLevel===SCALE_FACTORS.length-1||state.paused||busy;
  renderPoses();
}

async function fullscreen() {
  try{if(document.fullscreenElement)await document.exitFullscreen();else if(stage.requestFullscreen)await stage.requestFullscreen();else{focusMode=!focusMode;setFocus();toast('Browser ini memakai mode fokus untuk panggung.');}}catch{toast('Layar penuh belum tersedia. Gunakan Fokus panggung.');}
}
function setFocus(){document.body.classList.toggle('focus-mode',focusMode);$('#exit-focus').hidden=!focusMode;}
async function dispatch(action,value) {
  if(action==='start'){
    if(!loaded||camera.starting)return;
    $('#access-error').hidden=true;
    await camera.start();
    if(!camera.ready)return;
    started=true;state.paused=false;$('#welcome').hidden=true;stage.focus();sync();return;
  }
  if(!started)return;
  if(action==='help'){if(!$('#help').open)$('#help').showModal();return;}
  if(action==='close-help'){$('#help').close();return;}
  if(action==='focus'){focusMode=!focusMode;setFocus();return;}
  if(action==='fullscreen'){await fullscreen();return;}
  if(action==='pause'){state.paused=!state.paused;await media.pause(state.paused);sync();return;}
  if(action==='skip'){media.stop();sync();return;}
  if(action==='end'){media.dispose();camera.stop();voice.stop();state=new ShowState();started=false;$('#welcome').hidden=false;$('#start').textContent='Izinkan kamera & masuk';focusMode=false;setFocus();if(document.fullscreenElement)await document.exitFullscreen();sync();return;}
  if(action==='preview'){showPreview=!showPreview;sync();return;}
  if(action==='boxes'){state.showBoxes=!state.showBoxes;sync();return;}
  if(action==='camera'){if(camera.stream||camera.starting)camera.stop();else await camera.start();return;}
  if(action==='voice'){if(voice.enabled)voice.stop();else voice.start();return;}
  if(action==='stop-sound'){if(!media.active&&!media.loading)media.stopSound();return;}
  if(action==='character'){selected=value;sync();return;}
  if(state.paused){toast('Lanjutkan pertunjukan untuk mengubah adegan atau animasi.');return;}
  if(action==='curtain'){state.curtain();sync();return;}
  if(action==='video'&&state.curtainPhase!=='idle'){toast('Tunggu tirai selesai bergerak.');return;}
  if(media.active||media.loading){toast('Lewati atau tunggu video selesai untuk mengubah panggung.');return;}
  switch(action) {
    case 'scene':state.setScene(Number(value));break;
    case 'video': {
      state.curtain(true);
      const waitForCurtain=async()=>{
        while(state.curtainPhase!=='idle')await new Promise(resolve=>setTimeout(resolve,16));
      };
      await media.playVideo(value===undefined?state.scene:Number(value),()=>{state.setScene(media.scene);if(state.paused)media.pause(true);},waitForCurtain);
      break;
    }
    case 'sound':await media.playSound(value===undefined?state.scene:Number(value));break;
    case 'bank':state.toggleBank(value);break;
    case 'pose':state.pose(Number(value),selected);break;
    case 'manual-pose':state.pose(value.finger,value.label);break;
    case 'costume':if(value==='auto')state.setCostume(state.scene<2?'sport':'school','auto');else state.setCostume(value);break;
    case 'gesture':state.useGesture();if(!camera.ready)toast('Aktifkan kamera untuk mode jari, atau pilih Manual.');break;
    case 'manual':state.useKeyboard();break;
    case 'salam':state.setCostume('sport');state.banks.Right=2;state.run=false;state.sleep=false;state.hug=false;state.kick=-1;state.ball=null;selected='Right';state.pose(5,'Right');state.characters.Right.visible=true;break;
    case 'run':state.run=!state.run;break;
    case 'sleep':state.sleep=!state.sleep;break;
    case 'hug':state.hug=!state.hug;break;
    case 'kick':state.startKick();break;
    case 'ball':state.startBall();break;
    case 'lock':state.verticalLocked=!state.verticalLocked;break;
    case 'scale-up':state.changeScale(1);break;
    case 'scale-down':state.changeScale(-1);break;
    case 'balance':state.balance();break;
  }
  sync();
}
document.addEventListener('click',e=>{const b=e.target.closest('[data-action]');if(b&&!b.disabled)dispatch(b.dataset.action,b.dataset.value);});
$('#costume').addEventListener('change',e=>dispatch('costume',e.target.value));
$('#volume').addEventListener('input',e=>{audio.volume=Number(e.target.value)/100;$('#volume-label').textContent=e.target.value+'%';});
document.querySelectorAll('[data-move]').forEach(b=>{
  b.addEventListener('pointerdown',e=>{if(!started||state.paused||media.active)return;b.setPointerCapture(e.pointerId);pointerDirection=Number(b.dataset.move);});
  for(const event of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(event,()=>pointerDirection=0);
});
const shortcuts={Equal:'scale-up',NumpadAdd:'scale-up',Minus:'scale-down',NumpadSubtract:'scale-down',KeyR:'run',KeyB:'ball',KeyT:'sleep',KeyH:'hug',KeyP:'curtain',KeyL:'lock',KeyS:'balance',KeyG:'gesture',KeyF:'fullscreen',KeyU:'focus',KeyW:'preview',KeyD:'boxes',KeyM:'stop-sound',KeyQ:'end',Space:'pause'};
window.addEventListener('keydown',e=>{
  if(e.ctrlKey||e.metaKey||e.altKey||e.target.closest('input,select,textarea'))return;
  if($('#help').open)return;
  if(e.code==='Slash'||e.code==='F12'){e.preventDefault();if(!e.repeat)dispatch('help');return;}
  if(!started)return;
  if(e.code==='Space'&&e.target.closest('button'))return;
  held.add(e.code);
  const bankNando=e.code==='KeyO'||e.key.toLowerCase()==='o',bankIbu=e.code==='KeyA'||e.key.toLowerCase()==='a';
  const known=shortcuts[e.code]||bankNando||bankIbu||['Escape','ArrowLeft','ArrowRight','KeyI','KeyN','KeyY','KeyJ','BracketLeft','BracketRight'].includes(e.code)||/^Digit[0-9]$/.test(e.code)||/^F[1-5]$/.test(e.code)||['KeyZ','KeyX','KeyC','KeyV','KeyB'].includes(e.code);
  if(known)e.preventDefault();
  if(e.repeat)return;
  if(shortcuts[e.code])dispatch(shortcuts[e.code]);
  else if(bankNando)dispatch('bank','Right');
  else if(bankIbu)dispatch('bank','Left');
  else if(e.code==='Escape'){if(media.active||media.loading)dispatch('skip');else if(document.fullscreenElement)document.exitFullscreen();else if(focusMode)dispatch('focus');}
  else if(e.code==='KeyY')dispatch('costume',state.costume==='sport'?'school':'sport');
  else if(e.code==='KeyJ')dispatch('costume','auto');
  else if(e.code==='BracketLeft')dispatch('scene',(state.scene+4)%5);
  else if(e.code==='BracketRight')dispatch('scene',(state.scene+1)%5);
  else if(/^F[1-5]$/.test(e.code))dispatch('scene',Number(e.code.slice(1))-1);
  else if(/^Digit[1-5]$/.test(e.code)) {
    for(const [key,label] of [['KeyN','Right'],['KeyI','Left']])if(held.has(key))dispatch('manual-pose',{label,finger:Number(e.code.slice(5))});
  } else {
    const key=e.code.replace('Digit','').replace('Key','');
    const videoScene=SCENES.findIndex(s=>s.key===key),soundScene=SCENES.findIndex(s=>s.soundKey===key);
    if(videoScene>=0)dispatch('video',videoScene);else if(soundScene>=0)dispatch('sound',soundScene);
  }
});
window.addEventListener('keyup',e=>held.delete(e.code));
window.addEventListener('blur',()=>{held.clear();pointerDirection=0;});
document.addEventListener('visibilitychange',()=>{
  held.clear();pointerDirection=0;
  if(document.hidden&&started&&!state.paused){state.paused=true;media.pause(true);sync();}
});
window.addEventListener('pagehide',()=>{media.dispose();camera.stop();voice.stop();});
let previous=performance.now(),lastUI=0;
function frame(now) {
  const dt=Math.max(0,(now-previous)/1000);previous=now;
  if(loaded) {
    if(started) {
      camera.tick(now,!document.hidden);
      media.sync();
      state.update(dt,camera.hands,pointerDirection||(Number(held.has('ArrowRight'))-Number(held.has('ArrowLeft'))));
      voice.setBlocked(!started||state.paused||media.active||media.loading||media.sound!==null||document.hidden);
    }
    renderer.draw(state,video);
    if(showPreview&&camera.ready)renderer.cameraPreview(camera.video,camera.hands);
    renderer.curtain(state);
    stage.dataset.curtain=state.curtainPhase;stage.dataset.paused=String(state.paused);stage.dataset.scene=String(state.scene);stage.dataset.nando=String(state.characters.Right.pose);stage.dataset.costume=state.costume;
    const elapsed=media.active?video.currentTime:audio.currentTime,duration=media.active?video.duration:audio.duration;
    $('#playback-progress').style.width=(Number.isFinite(duration)&&duration>0?Math.min(100,elapsed/duration*100):0)+'%';
    if(now-lastUI>250){sync();lastUI=now;}
  }
  requestAnimationFrame(frame);
}
sync();requestAnimationFrame(frame);
renderer.load(progress=>{$('#load-progress').style.width=progress*100+'%';}).then(()=>{
  loaded=true;$('#start').disabled=false;$('#start').textContent='Izinkan kamera & masuk';$('#load-caption').textContent='Pilih Izinkan pada permintaan kamera dari browser.';sync();
}).catch(error=>{$('#load-caption').textContent=error.message;$('#start').disabled=false;$('#start').textContent='Muat ulang';$('#start').dataset.action='reload';$('#start').onclick=()=>location.reload();toast(error.message);});
