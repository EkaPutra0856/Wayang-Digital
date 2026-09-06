# Manual Penggunaan — Wayang Interaktif 2D Nando & Ibu

## 1. Persyaratan dan instalasi

- Windows 10/11, webcam, speaker, dan mikrofon untuk kontrol suara.
- Lingkungan proyek yang diuji: Python 3.14.2. Versi paket terpasang dicatat di `requirements.txt`.
- FFmpeg **dan** ffprobe di PATH. Pada komputer ini ditemukan di `C:\ffmpeg\bin`.
- Internet diperlukan hanya untuk pengenalan suara Google dalam bahasa Indonesia.

```powershell
python -m pip install -r requirements.txt
ffmpeg -version
ffprobe -version
python main.py
```

Semua media sumber hanya dibaca dari `FIX ASSET`, relatif terhadap lokasi source;
program dapat dijalankan dari direktori kerja lain. File `hand_landmarker.task`
di root tetap diperlukan sebagai model MediaPipe, bukan aset visual/cerita.
Aset asli tidak diubah, dipindah, atau diganti namanya.

Pada startup pertama, audio MP3 dan audio internal MP4 didekode sekali ke
`.media_cache/` (sekitar 167 MiB untuk media saat ini). Cache PCM dipetakan ke memori,
sehingga penekanan tombol tidak menjalankan FFmpeg atau mendekode MP3 lagi.
Cache bukan aset sumber tambahan, diabaikan Git, dan otomatis dibuat ulang jika
file sumber berubah. Tunggu pesan `[READY]` sebelum menggunakan tombol.

## 2. Cara menjalankan dan pilihan pengujian

```powershell
python main.py
python main.py --windowed
python main.py --no-camera --no-voice
python main.py --camera 1 --mic 2
python main.py --validate-assets
python main.py --headless --no-camera --no-voice --mute --frames 90
```

`--no-camera` tetap menampilkan kedua karakter untuk tes keyboard.
`--no-voice` mematikan pengenalan suara. `--mute` adalah mode uji eksplisit tanpa
speaker; waktu PCM tetap berjalan. `--headless` tidak membuka window dan wajib
memakai `--frames N`. `--frames N` juga dapat dipakai pada window biasa untuk
smoke test yang keluar otomatis. Jika webcam gagal dibuka, keyboard tetap dapat
digunakan dan console menampilkan `[CAMERA ERROR]`.

## 3. Keyboard final

Klik window **Wayang Digital** agar memiliki fokus. Tombol toggle menggunakan
transisi fisik lepas → tekan; menahan tombol tidak mengulang toggle.
Keyboard diabaikan ketika window lain memiliki fokus.

| Tombol | Fungsi |
|---|---|
| TAB | Ganti bank 1 ↔ 2 untuk kedua karakter |
| 1–5 | Pose manual sesuai bank, untuk kedua karakter |
| G | Kembali ke pose gesture; posisi tangan tetap aktif saat tes pose manual |
| [ / ] | Background sebelumnya / berikutnya, wrap-around |
| F1–F5 | Langsung background 1–5 |
| Z / X / C / V / B | Sound 1 / 2 / 3 / 4 / 5 |
| M | Stop sound eksternal |
| 6 / 7 / 8 / 9 / 0 | Video 1 / 2 / 3 / 4 / 5 |
| ESC | Skip video; jika tidak ada video, keluar seperti perilaku lama |
| R | Toggle run mode |
| Panah kiri / kanan (tahan) | Bergerak dan animasi lari saat run mode aktif |
| K | Mulai sequence sepak bola |
| T | Toggle mode tidur |
| H | Toggle pelukan; tidak memulai sound otomatis |
| P | Curtain: tutup, tahan 0,5 detik, buka ke kiri/kanan sambil fade-out |
| L | Lock scale dan posisi vertikal; tangan hanya menggeser kiri/kanan |
| S | Seimbangkan ukuran kedua karakter, lalu lock scale otomatis |
| Y | Switch SCHOOL/SPORT Nando dan aktifkan kostum MANUAL |
| J | Kembali ke kostum AUTO, langsung mengikuti background aktif |
| SPACE | Pause/resume animasi, audio, video, dan posisi karakter |
| F | Toggle fullscreen |
| W | Toggle preview webcam |
| D | Toggle kotak deteksi tangan |
| U | Show/hide seluruh panel UI (status dan panduan); preview webcam tetap melalui W |
| F12 atau ? (tombol /) | Toggle bantuan |
| Q | Keluar, termasuk saat video |

Fallback sound `Z X C V B` dan video `6 7 8 9 0` dipilih sebagai mapping aktual.
Kombinasi Ctrl/Shift tidak diperlukan. Gunakan angka di baris atas keyboard.

**Perubahan konflik lama:** sebelumnya `1` = tas, `2` = buku, `0` = reset efek.
Ketiganya sekarang mengikuti mapping pose/video yang diminta. Efek PNG tas dan
buku terpisah tidak dipertahankan karena sumbernya di luar `FIX ASSET` dan tidak
ada pengganti objek tas/buku terpisah di manifest baru. Visual Nando membawa tas
tersedia melalui `R`; adegan ibu mengantar buku melalui `9`, dengan sound `V`.
`effect_animator.py` sekarang merender efek bola, tidur, lari, dan pelukan.

## 4. Hand tracking

- Mapping existing dipertahankan: **Right → Nando**, **Left → Ibu**, termasuk
  pembalikan label existing untuk kamera mirror.
- Tampilkan telapak dan 1–5 jari ke webcam. Hindari tangan terbalik ke bawah.
- Posisi dan tinggi wayang mengikuti bounding box tangan dengan smoothing.
- Jumlah jari harus stabil sekitar 120 ms sebelum mengubah pose.
- Saat tangan kanan hilang, Nando fade-out selama 0,35 detik; saat tangan kiri
  hilang, Ibu fade-out sendiri. Jika kedua tangan hilang, kedua wayang menghilang.
  Saat tangan kembali, wayang fade-in selama 0,35 detik. Pose terakhir tetap
  disimpan. Mengepal tetap dihitung sebagai tangan terdeteksi, bukan tangan hilang.
- Saat startup dengan kamera, karakter tersembunyi sampai tangan terdeteksi.
  `--no-camera` adalah pengecualian eksplisit untuk preview keyboard: kedua
  karakter tetap terlihat. Pose manual 1–5 pada mode kamera tetap mengikuti fade.
- Setelah tes angka keyboard, tekan `G` untuk mengaktifkan pose gesture lagi.
- `W` menampilkan kamera mini; `D` menampilkan kotak pada panggung.

## 5. Animation bank

Tabel berikut adalah mapping **SCHOOL** dan Ibu. Startup BG1 memakai **SPORT**;
lihat bagian Kostum Nando untuk mapping SPORT 1–9. Ibu tetap memiliki 8 pose.

| Bank | Jari/tombol | Nando | Ibu |
|---|---|---|---|
| 1 | 1 | 37.png | 58.png |
| 1 | 2 | 38.png | 59.png |
| 1 | 3 | 39.png | 60.png |
| 1 | 4 | 40.png | 61.png |
| 1 | 5 | 41.png | 62.png |
| 2 | 1 (pose 6) | 42.png | 63.png |
| 2 | 2 (pose 7) | 43.png | 64.png |
| 2 | 3 (pose 8) | 44.png | 65.png |
| 2 | 4–5 (slot 9–10) | Pertahankan pose valid terakhir | Pertahankan pose valid terakhir |

`TAB` mengganti bank global. Bank dan pose normal terakhir ditampilkan dalam HUD.
Saat mode khusus aktif, indikator RUN/SLEEP/BALL/ENDING menjelaskan override visual.

## 6. Background dan voice

| Nomor | File di Asset/BG | Isi gambar hasil inspeksi | Kata suara |
|---|---|---|---|
| 1 | 1 akhir.png | Taman/lapangan bola | taman |
| 2 | 2 akhir.png | Ruang makan rumah | rumah, makan |
| 3 | 3 akhir.png | Gerbang sekolah | sekolah, al azhar, alazhar, pekalongan |
| 4 | 4 akhir.png | Ruang kelas | kelas |
| 5 | 5 akhir.png | Koridor sekolah | koridor |

Background menggunakan cover/crop dengan aspect ratio tetap dan transisi 0,4 detik.
Voice hanya mengganti background; video dipanggil terpisah agar urutan cerita tetap
di tangan operator. Kata berulang untuk background yang sama tidak memulai ulang
transisi. Voice sementara diabaikan ketika sound/video berjalan atau pause, untuk
mencegah audio pertunjukan memicu background. Gunakan keyboard saat narasi aktif.

## 7. Sound

| Tombol | File di Asset/Sound |
|---|---|
| Z | 1 opening.mp3 |
| X | 2 makan.mp3 |
| C | 3 brangkat sekolah.mp3 |
| V | 4 ibu nganter buku.mp3 |
| B | 5 pelukan ending.mp3 |

Hanya satu kanal audio aktif. Sound yang sama saat bermain/paused diabaikan.
Sound berbeda menggantikan sound lama. Setelah selesai boleh diputar ulang;
lepaskan tombol, lalu tekan lagi. `M` menghentikan BGM. Tidak ada sleep penunggu
audio di main loop. Kegagalan perangkat audio dilaporkan jelas saat startup;
gunakan `--mute` hanya jika memang ingin pengujian tanpa suara.

## 8. Video dengan audio internal

| Tombol | File di Asset/Vid |
|---|---|
| 6 | vid1.mp4 |
| 7 | vid2.mp4 |
| 8 | Create_a_cinematic_second_.mp4 |
| 9 | 3 nganter buku.mp4 |
| 0 | 4 ending.mp4 |

Urutan mengikuti mapping eksplisit instruksi. Kelima file terdeteksi memiliki
audio internal. OpenCV mendekode frame; PCM hasil ekstraksi FFmpeg dimainkan
melalui `sounddevice` yang sama dengan BGM. Waktu audio, dikurangi latensi output,
menjadi acuan frame video. Video mempertahankan aspect ratio dengan letterbox.

Video menghentikan BGM, mengambil prioritas, dan menolak semua pemicu sound,
video kedua, dan mode karakter selama berlangsung. BGM lama tidak dimulai ulang.
`SPACE` pause/resume gambar dan audio, `ESC` skip. Pada akhir video, frame terakhir
memudar ke panggung selama 0,45 detik. Webcam tetap dibaca selama video tetapi
preview disembunyikan. `F`, `U`, bantuan, pause, skip, dan keluar tetap tersedia.

## 9. Lari

Tekan `R`, lalu tahan panah kiri/kanan. Nando memakai frame 45–49 pada 10 FPS,
bergerak 420 piksel canvas per detik. Selama R aktif, frame 45–49 selalu looping
pada 10 FPS, termasuk ketika panah dilepas. Panah dilepas → hanya posisi berhenti;
Nando tetap berlari di tempat. Timer berputar kontinu tanpa jeda khusus antar-cycle.
Ke kiri menggunakan flip horizontal; gambar asli menghadap kanan.
Posisi dibatasi dengan lebar maksimum sprite lari. Tangan tidak mengambil alih
posisi Nando selama mode ini aktif. `R` lagi mengembalikan kendali posisi ke tangan.
Konstanta `RUN_SPEED` dan `RUN_FPS` ada di `animation_controller.py`.

## 10. Sepak bola

`K` memulai enam tahap: persiapan tanpa bola → angkat bola → persiapan tendang →
kontak → bola lepas → gerakan lanjutan. Kelima PNG pose dipakai, lalu `ball.png`
menjadi satu objek terpisah yang bergerak, mendapat gravitasi, dan berputar.
Arah mengikuti arah terakhir Nando. `K` selama sequence diabaikan. Bola direset
saat keluar layar, mencapai bawah panggung, atau sequence selesai. Dapat diulang.

## 11. Tidur

`T` memakai **Nando SCHOOL 39.png**, **Nando SPORT 1 (3).png**, dan **Ibu 63.png**, dipilih setelah inspeksi karena
mata tertutup. Tidak ada pose benar-benar tidur; gambar tersebut adalah pendekatan
istirahat, masih dalam posisi berdiri. Tidak ada aset baru yang dibuat.
Skala bernapas berkisar 0,985–1,015 dan gerak vertikal ±2 piksel. Pose gesture dan
posisi tangan tidak mengganti pose/posisi istirahat. `T` lagi kembali normal.

## 12. Pelukan

`H` menampilkan `Asset/Pelukan.png` dengan fade dan scale-in halus, menyembunyikan
karakter individual. `H` lagi memudarkan pelukan dan mengembalikan karakter.
Sound ending dikontrol terpisah dengan `B`.

## 13. Prioritas, pause, fullscreen

Urutan: **video → pelukan → sepak bola Nando → tidur → lari → gesture**.
Mode bawah dipertahankan tetapi tidak mengambil alih visual; timer bola berhenti
saat tertutup pelukan/video. Ibu dapat tetap tidur ketika Nando bermain bola.
`SPACE` membekukan timer, posisi, bola, lari, breathing, transisi, dan audio/video.
Webcam tetap bekerja. Pemicu visual/media baru diabaikan selama pause; bantuan,
preview, fullscreen, stop BGM, dan keluar tetap dapat digunakan.

`F` mengubah fullscreen/windowed. Canvas mempertahankan aspect ratio monitor
dengan resolusi render maksimum 1920×1080. Batas 30 FPS adalah target, tergantung
kecepatan kamera, CPU, dan resolusi. Tidak ada PNG yang dibaca ulang setiap frame;
sprite resize memakai cache LRU terbatas, transparansi dikomposit sebagai BGRA.

## 14. Troubleshooting

- **Tombol tidak merespons:** klik window Wayang Digital, lepaskan tombol lalu
  tekan kembali. Setelah Alt+Tab, tombol yang sudah ditahan sengaja diabaikan.
- **Pose tetap:** periksa MANUAL, pause, RUN/SLEEP/BALL/ENDING dan bank. Tekan `G`
  untuk gesture. Slot 9–10 memang mempertahankan pose sebelumnya.
- **Missing asset:** baca path `[ASSET ERROR]`, pulihkan nama asli dan lokasi file.
  `python main.py --validate-assets` memvalidasi semua file dan decode PNG.
- **FFmpeg tidak ditemukan:** tambahkan folder bin FFmpeg ke PATH, buka terminal
  baru, verifikasi ffmpeg dan ffprobe. Cache dibuat di luar `FIX ASSET`.
- **Audio tidak terdengar:** pastikan bukan `--mute`, cek speaker/default output,
  volume Windows, dan sound tidak paused. Saat video, tombol BGM diabaikan.
- **Kamera gagal:** tutup aplikasi lain yang memakai kamera, cek izin Kamera
  Windows; coba `--camera 1`. Pengujian manual dapat memakai `--no-camera`.
- **Voice gagal:** cek internet, izin mikrofon, device default atau `--mic N`.
  `python tes/tesmic.py` adalah diagnostik lokal; Ctrl+C untuk berhenti.
- **FPS rendah:** tutup aplikasi berat. Hindari pencahayaan gelap yang membuat
  kamera menurunkan FPS. HUD dapat dimatikan dengan `U`, preview dengan `W`.
- **Peringatan MediaPipe feedback tensors:** model berhasil dimuat pada pengujian;
  peringatan upstream dapat muncul di stderr tanpa menghentikan aplikasi.

## 15. Curtain dan kontrol ukuran

`P` memulai curtain merah prosedural tanpa file aset tambahan. Urutannya:
menutup dari kiri/kanan selama 0,35 detik → **tertutup penuh selama 0,5 detik** →
membuka ke sisi kiri/kanan sambil fade-out selama 0,65 detik. Curtain menutup
seluruh layar termasuk HUD/preview, dan dapat dipakai di atas video. Tekan lagi
saat transisi berjalan akan diabaikan. `SPACE` membekukan/melanjutkan curtain.
Background/mode tetap dapat diganti di balik curtain melalui kontrol yang biasa;
curtain tidak mengganti background atau sound secara otomatis.

`L` mengunci tinggi dan posisi kaki kedua karakter pada posisi saat tombol ditekan.
Ukuran ekstrem dijepit ke 25–65% tinggi panggung dan posisi kaki ke area yang wajar.
Sesudah itu tangan hanya mengubah X (kiri/kanan): mendekat/menjauh dari webcam
tidak lagi memperbesar/memperkecil wayang, dan gerakan tangan vertikal diabaikan.
`L` lagi melepaskan lock. Pose jari dan fade ketika tangan hilang tetap berjalan.
Animasi napas pada mode tidur tetap memiliki variasi skala kecil yang disengaja.

`S` menyiapkan balancing untuk masing-masing tangan dan otomatis menyalakan lock.
Ketika tangan terkait terdeteksi pada mode kontrol tangan, karakter secara halus
menuju tinggi **46% panggung** dan posisi kaki **88% tinggi panggung**. Tangan yang
belum terdeteksi tetap berstatus PENDING, sehingga dapat diseimbangkan bergantian.
Setelah selesai ukurannya tetap terkunci; mendekat/menjauh tidak mengubahnya.
Kedua karakter disamakan tinggi visualnya tanpa merusak aspect ratio PNG.
Balancing menunggu sampai mode tidur/lari/football yang mengambil alih karakter
dimatikan. `L` membatalkan balancing yang masih tertunda.

HUD menampilkan `SCALE LOCK` dan `BALANCE`. Tombol P/L/S memakai deteksi edge yang
sama seperti toggle lainnya, sehingga menahan tombol tidak memicu berulang.

## 16. Kostum Nando

Hanya Nando memiliki dua kostum: **SCHOOL** (`Nando Fix Animation/37–44.png`)
dan **SPORT** (`FIX ASSET/Nando Olahraga/`). Kesembilan PNG olahraga dipakai
dengan nama asli, dipreload saat startup, dan memakai cache resize yang sama.
Validasi aset kini mencakup **60 file**, termasuk **50 PNG** dan 9 pose SPORT.

### AUTO dan MANUAL

Default startup BG1 adalah `COSTUME: SPORT [AUTO]`.

| Background | Kostum AUTO |
|---|---|
| BG1 — Taman/lapangan | SPORT |
| BG2 — Rumah/ruang makan | SPORT |
| BG3 — Gerbang sekolah | SCHOOL |
| BG4 — Kelas | SCHOOL |
| BG5 — Koridor | SCHOOL |

Aturan berlaku untuk F1–F5, [ / ], voice, dan pemanggilan internal
`AnimationController.set_background(index)` (indeks 0–4). Perubahan background
baru harus melalui fungsi ini, bukan assignment langsung ke `current_bg`.

- `Y`: beralih SCHOOL ↔ SPORT dan menetapkan MANUAL. Ganti BG sesudahnya tidak
  mengubah kostum. Contoh BG4 SCHOOL → Y → SPORT MANUAL → F5 tetap SPORT.
- `J`: kembali AUTO dan langsung menyesuaikan BG aktif. Contoh BG5 SPORT MANUAL
  → J → SCHOOL AUTO.
- Y/J memakai edge-trigger; tidak berulang ketika ditahan. Keduanya diabaikan
  selama pause/video, mengikuti kebijakan kontrol panggung existing.
- Mode kostum MANUAL berbeda dengan pose MANUAL (1–5/G); gesture tetap dapat
  digunakan ketika kostum dipilih secara manual.

### Mapping SPORT

| Bank | Jari / tombol | Pose | File di Nando Olahraga |
|---|---|---|---|
| 1 | 1 | 1 | 1 (1).png |
| 1 | 2 | 2 | 1 (2).png |
| 1 | 3 | 3 | 1 (3).png |
| 1 | 4 | 4 | 1 (4).png |
| 1 | 5 | 5 | 1 (5).png |
| 2 | 1 | 6 | 1 (6).png |
| 2 | 2 | 7 | 1 (7).png |
| 2 | 3 | 8 | 1 (8).png |
| 2 | 4 | 9 | 1 (9).png |
| 2 | 5 | 10 kosong | Pertahankan pose SPORT valid terakhir |

Gesture dan tombol angka memakai lookup yang sama. SPORT pose 9 tidak mengubah
Ibu ke slot kosong: Ibu mempertahankan pose terakhirnya. Mapping SCHOOL/Ibu
tetap seperti sebelumnya. Ganti kostum mempertahankan nomor pose logis bila
tersedia. Dari SPORT pose 9 ke SCHOOL, gunakan pose SCHOOL valid terakhir
(default pose 1 bila belum pernah dipilih); tidak menampilkan sprite kosong.

### Kompatibilitas panggung

- **Fade:** Y/J saat tangan hilang hanya mengubah kostum, tidak memunculkan Nando.
  Tangan kembali → fade-in dengan kostum terbaru. Durasi tetap 0,35 detik.
- **Lock/balance:** X, posisi kaki/Y, tinggi visual, alpha, dan status balance
  tidak direset. PNG dipotong margin transparannya hanya di memori lalu dirender
  dengan tinggi visual yang sama; aspect ratio masing-masing kostum dipertahankan.
- **Run:** 45–49 masih memakai baju sekolah dan tas, hasil inspeksi aset.
  Ini override visual sementara bahkan saat state SPORT; R OFF kembali SPORT.
  Belum ada frame sport-run khusus, sehingga perubahan pakaian saat lari terlihat.
- **Football:** pose Ball memakai pakaian olahraga sebagai animasi sementara.
  Selesai K → kembali kostum aktif (SCHOOL maupun SPORT), tanpa mengganti mode.
- **Sleep:** SPORT menggunakan **1 (3).png** karena mata tertutup dan gestur
  santai; belum ada pose tidur berbaring. SCHOOL tetap 39.png, Ibu tetap 63.png.
  Breathing 0,985–1,015 dan bob ±2 piksel tetap berjalan.
- **Hug:** Pelukan.png tetap override tunggal; H OFF kembali kostum aktif.
- **Curtain:** P lalu F4 di AUTO mengganti ke SCHOOL di balik tirai. P lalu Y
  memilih kostum MANUAL tanpa mengubah animasi curtain.
- **Video:** tidak mengubah kostum/BG atau mode AUTO/MANUAL. Setelah selesai
  state panggung sebelumnya kembali. Voice tetap diblokir saat media berbunyi.

## 17. UI dan panduan di layar

Panel status menampilkan latar, bank, pose, kostum AUTO/MANUAL, run, sleep, bola,
lock/balance, pelukan, serta nama audio/video. Tampilan memakai kartu gelap dengan
aksen emas agar terbaca di berbagai latar.

Saat startup, UI tersembunyi secara default. Tekan `U` untuk menampilkannya.
`U` adalah tombol **show/hide seluruh UI**: status maupun panduan disembunyikan.
Tekan U lagi untuk menampilkan kembali. Preview kamera terpisah, dikendalikan W.
`F12` atau `?` membuka/menutup panduan; ketika dibuka, UI otomatis diaktifkan.
Panduan menggantikan panel status dengan enam kelompok dalam dua kolom:
karakter/kostum, latar/media, animasi, tampilan, ukuran/visibilitas, dan cara bermain.
Ukuran panel mengikuti resolusi panggung. Curtain tetap berada di atas semua UI.

## 18. Pengujian dan referensi implementasi

Lihat `TESTING_CHECKLIST.md` untuk hasil aktual dan pemeriksaan manual yang tersisa.

```powershell
python -m compileall -q .
python -m unittest test_wayang test_media -v
python -m pip check
```

Backend mengikuti API [sounddevice OutputStream](https://python-sounddevice.readthedocs.io/en/0.5.3/api/streams.html),
[FFmpeg stream mapping](https://ffmpeg.org/ffmpeg.html), dan
[GetAsyncKeyState Windows](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getasynckeystate).
