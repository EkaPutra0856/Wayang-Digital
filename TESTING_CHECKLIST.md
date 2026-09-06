# Testing Checklist — Wayang Interaktif 2D

Tanggal pengujian: 6 September 2026. Hasil otomatis tidak menggantikan pengamatan
webcam, speaker, arah tangan fisik, dan kenyamanan animasi oleh operator.

## Hasil otomatis

- [x] Update kostum — 9 PNG SPORT ditemukan/dipreload tanpa rename; manifest total 60 aset.
- [x] Suite terbaru: 26 tes lulus, termasuk 7 tes kostum dan 2 tes UI/run-loop tambahan.

- [x] PASS — 5 tes tambahan fade independen, lock X-only, balancing tertunda,
  curtain hold/pause/anti-spam, dan coverage/render curtain; total suite kini 17 tes.

- [x] PASS — syntax seluruh modul aplikasi melalui `py_compile`.
- [x] PASS — import seluruh modul aplikasi.
- [x] PASS — `python -m pip check`: tidak ada dependensi rusak.
- [x] PASS — seluruh 60 aset wajib ada; 50 PNG berhasil didekode dengan alpha sprite.
- [x] PASS — startup `main.py --headless --no-camera --no-voice --mute --frames 5` dan cleanup.
- [x] PASS — validasi aset dijalankan dari direktori kerja lain.
- [x] PASS — MediaPipe memuat model dan memproses frame sintetis.
- [x] PASS — 10 tes state/render/audio melalui `test_wayang.py`.
- [x] PASS — 2 tes integrasi seluruh MP3/MP4 asli melalui `test_media.py`.
- [x] PASS — decode kelima sound sampai selesai, duplicate diabaikan, replay diizinkan.
- [x] PASS — kelima video + PCM internal, pause, selesai, replay, skip, dan satu player.
- [x] PASS — penelusuran source tidak menemukan referensi aktif folder aset lama.
- [x] PASS — inspeksi gambar render offscreen: alpha, rasio, HUD, help, dan latar.
- [x] PASS — `python main.py --windowed --no-voice --frames 90`: window berjalan,
  `[CAMERA] Opened`, 90 frame selesai, cleanup exit code 0, audio underruns 0.
- [x] PASS — `python -m compileall -q .`.

Pengujian media di atas menyalurkan PCM ke buffer pengujian, bukan memastikan
suara terdengar dari speaker. Webcam sintetis bukan pengujian gesture manusia.

## 01 — Startup di perangkat lokal

- [ ] `python main.py` membuka window dan berhenti dengan Q.
- [x] Capture webcam nyata berjalan pada smoke test 90 frame tanpa error baca kamera.
- [ ] Speaker dan mikrofon default bekerja.
- [ ] Background muncul dan nama aplikasi benar.
- [x] Tidak membaca aset dari folder deprecated.

## 02 — Hand tracking

- [ ] Tangan terdeteksi pada pencahayaan pertunjukan.
- [ ] Tangan kanan fisik mengontrol Nando sesuai mapping mirror existing.
- [ ] Tangan kiri fisik mengontrol Ibu.
- [ ] Gerakan dan perubahan pose tidak berkedip berlebihan.
- [ ] Tangan hilang membuat karakter terkait fade-out; kembali terdeteksi → fade-in.
- [x] Data Right/Left memilih pose karakter yang sesuai (otomatis).

## 03 — Bank 1

- [x] Keyboard/state 1–5 → pose 1–5 kedua karakter.
- [ ] Ulangi dengan 1, 2, 3, 4, 5 jari fisik setelah menekan G.
- [ ] HUD menampilkan bank dan nomor pose yang benar.

## 04 — Bank 2

- [x] 1, 2, 3 → pose 6, 7, 8 kedua karakter.
- [x] Slot 4 dan 5 tidak crash dan mempertahankan pose valid terakhir.
- [x] Menahan tombol toggle tidak menghasilkan edge tambahan (tes input state).
- [ ] Tahan TAB satu detik di window: hanya sekali berpindah.
- [ ] Ulangi slot kosong dengan gesture fisik.

## 05 — Background

- [ ] [ / ] berpindah dan wrap-around.
- [ ] F1, F2, F3, F4, F5 memilih background sesuai tabel manual.
- [x] Render menjaga aspect ratio dengan cover/crop.
- [ ] Transisi terlihat halus pada layar/proyektor.
- [ ] Voice taman/rumah/sekolah/kelas/koridor mengubah latar dengan benar.
- [ ] Voice tidak memicu ulang dari audio narasi/video.

## 06 — Sound (ulangi Z, X, C, V, B)

- [x] Seluruh sumber MP3 didekode dan PCM berisi audio.
- [x] Sound sama saat aktif tidak menduplikasi atau mengulang cursor.
- [x] Track berbeda menggantikan track lama.
- [x] Setelah selesai dapat diputar ulang; stop mengosongkan kanal.
- [x] Pause menghasilkan silence tanpa memajukan cursor; resume melanjutkan.
- [ ] Kelima sound terdengar benar lewat speaker lokal.
- [ ] M menghentikan suara yang terdengar.

## 07 — Video (ulangi 6, 7, 8, 9, 0)

- [x] Kelima video terbuka dan selesai kembali ke panggung dalam tes backend.
- [x] Kelima MP4 memiliki stream audio internal dan PCM berhasil didekode.
- [x] Video sama/berbeda saat player aktif diabaikan.
- [x] Hanya satu player dan satu kanal audio; BGM digantikan video.
- [x] Frame dan audio freeze saat pause; skip membersihkan player/audio.
- [x] Letterbox menjaga rasio frame.
- [ ] Video lancar dan audio internal terdengar sinkron di perangkat lokal.
- [ ] ESC di window melewati video tanpa menutup program.
- [ ] Fade akhir video kembali ke wayang tampak halus.

## 08 — Run mode

- [x] Gerakan memakai delta time, posisi setara pada 30 dan 60 FPS.
- [x] Kiri/kanan mengubah facing dan membatasi posisi.
- [x] Release direction mempertahankan posisi; frame tetap looping selama R aktif.
- [x] Tiga putaran beruntun melewati frame 4 → 0 tanpa menghentikan timer.
- [ ] R memperlihatkan RUN ON/OFF.
- [ ] Menahan panah kiri/kanan menjalankan cycle 45–49 dengan arah benar.
- [ ] R OFF mengembalikan kendali posisi ke tangan.

## 09 — Football

- [x] Semua enam tahap dilalui; seluruh PNG pose Ball dipakai.
- [x] Bola independen aktif setelah contact, bergerak dan berputar dua arah.
- [x] Gravitasi dan reset mengakhiri objek tunggal.
- [x] K aktif diabaikan dan sesudah selesai bisa dimainkan ulang.
- [ ] Perpindahan dari bola pada pose ke bola terpisah terlihat wajar.
- [ ] Arah, kecepatan, dan lintasan sesuai kebutuhan panggung.

## 10 — Sleep

- [x] Renderer menggunakan Nando 39.png dan Ibu 63.png yang telah diinspeksi.
- [x] Mode tidur dapat dirender offscreen tanpa error.
- [ ] T ON/OFF terlihat benar; gesture tidak mengubah pose istirahat.
- [ ] Skala 0,985–1,015 dan bob ±2 piksel tampak seperti napas lembut.
- [ ] Operator menerima pose berdiri bermata tertutup sebagai pendekatan tidur.

## 11 — Pelukan

- [x] Pelukan dapat dirender offscreen tanpa error.
- [ ] H fade/scale-in halus dan karakter individual tersembunyi.
- [ ] H lagi kembali normal setelah fade-out.
- [ ] H tidak otomatis memulai ulang sound ending.

## 12 — Prioritas dan pause

- [x] Video menolak trigger sound, bola, tidur, lari, dan pelukan.
- [x] Pause membekukan seluruh state animasi pada tes regresi.
- [x] Pelukan/video membekukan timer football di bawahnya.
- [ ] Uji RUN + K, SLEEP + gesture, HUG + gesture, VIDEO + sound/football.
- [ ] SPACE pada masing-masing mode freeze/resume dan webcam tetap berjalan.
- [ ] F fullscreen/windowed tetap menerima keyboard.
- [ ] W, U, D, F12 bekerja; Alt+Tab tidak memicu mode tanpa sengaja.

## 13 — Stress test lokal

- [ ] Tekan berbagai tombol 30–60 detik tanpa crash/freeze.
- [ ] Tidak ada audio menumpuk, video kedua, atau jumlah bola bertambah.
- [ ] Webcam tidak hilang dan memori cache tidak bertambah tanpa batas.
- [ ] Tutup window saat video aktif: capture dan kanal audio dibersihkan.

## Batas pengujian

### Kostum Nando: hasil otomatis dan uji operator

- [x] Compileall, pip check, validasi aset dan startup headless 10 frame lulus.
- [x] Smoke GUI tanpa kamera/voice 90 frame: exit 0, tanpa audio underrun.
- [x] Smoke GUI dengan webcam, tanpa voice, 90 frame: kamera terbuka dan exit 0.
  Gesture manusia dan mikrofon tidak diverifikasi pada smoke ini.

- [x] F1/F2 → SPORT; F3/F4/F5 → SCHOOL; startup SPORT AUTO.
- [x] [ / ] wrap-around dan fungsi background internal mengikuti AUTO.
- [x] Indeks hasil mapping voice diproses lewat set_background yang sama.
- [x] Y dua arah menetapkan MANUAL; ganti BG mempertahankan override.
- [x] J langsung mengikuti BG aktif dan kembali AUTO.
- [x] SPORT Bank1 1–5 dan Bank2 6–9 memilih nama PNG yang benar.
- [x] SPORT slot 10 mempertahankan pose 9, Ibu slot 9/10 tetap pose valid terakhir.
- [x] SCHOOL Bank1/2 tetap 37–44.png; Ibu tetap 58–65.png.
- [x] Angka keyboard, TAB, dan G/gesture sintetis mengikuti kostum.
- [x] SCHOOL pose 7 ↔ SPORT pose 7; SPORT pose 9 → fallback SCHOOL valid.
- [x] Switch saat alpha nol tidak membuat karakter muncul; fade kembali memakai kostum terbaru.
- [x] Lock/balance mempertahankan tinggi, X/Y, kaki dan status balance saat switch.
- [x] Render semua pose SCHOOL/SPORT 1–8 menghasilkan tinggi piksel yang sama.
- [x] Run/football/sleep/hug/video tidak mengganti permanent costume state.
- [x] Sleep lookup SPORT 1 (3).png dan SCHOOL 39.png benar.
- [x] Curtain + auto/manual costume tetap bekerja.
- [ ] Uji tombol fisik Y/J (termasuk ditahan), TAB dan 1–5 pada window.
- [ ] Uji semua 9 pose SPORT dengan jari manusia, termasuk Bank2 jari4/jari5.
- [ ] Ucapkan pergantian latar via mikrofon dan periksa kostum AUTO.
- [ ] Amati fade/lock/balance saat mendekatkan dan menjauhkan tangan secara nyata.
- [ ] Amati pakaian sementara pada run/football lalu kembali ke kostum sebelumnya.

Tes otomatis menggunakan gesture sintetis dan handler keyboard. Pengamatan
operator atas ekspresi/proporsi serta pengenalan ucapan nyata tetap perlu latihan lokal.

### Tambahan: fade, curtain, dan scale

- [x] UI show/hide menyembunyikan panel status dan panduan bersamaan.
- [x] Panduan dirender pada 640x360, 1280x720, 1920x1080 tanpa error.
- [x] F12 mengaktifkan UI saat membuka panduan; U menyembunyikannya kembali.
- [x] Inspeksi render panduan 1280x720: dua kolom rapi dan teks tidak terpotong.
- [ ] Uji kenyamanan loop lari dan UI terbaru pada proyektor/perangkat pertunjukan.

- [x] Tidak ada tangan pada startup → alpha kedua karakter nol.
- [x] Tangan kanan/kiri hilang secara independen → fade 0,35 detik hingga nol.
- [x] Tangan terdeteksi kembali → alpha naik secara bertahap.
- [x] L mempertahankan tinggi/Y saat bounding box berubah ukuran dan posisi vertikal.
- [x] L OFF mengembalikan perubahan ukuran dari gesture.
- [x] S menunggu tangan terkait, menyeimbangkan tinggi ke 46%, lalu mengunci.
- [x] Curtain tertutup penuh 0,5 detik, freeze saat pause, menolak trigger ganda.
- [x] Curtain menutup semua piksel (termasuk lebar ganjil), membuka dari tengah.
- [ ] Coba P/L/S secara fisik, termasuk menahan tombol dan menggunakan saat curtain aktif.
- [ ] Pastikan transisi/fade halus di panggung dengan pencahayaan kamera sebenarnya.
- [ ] Dekatkan/jauhkan tangan setelah L/S: ukuran dan posisi kaki tetap, hanya X berubah.
- [ ] --no-camera tetap dapat menampilkan karakter untuk tes pose keyboard.

Pengujian otomatis fitur tambahan lulus. Interaksi manusia dengan webcam untuk
fitur tambahan belum diverifikasi secara langsung.

Belum ada klaim verifikasi gesture manusia, pengenalan suara nyata, persepsi
sinkronisasi speaker, atau target 30 FPS di hardware pertunjukan. Lengkapi kotak
manual di atas saat latihan. Catatan runtime tambahan ada di bawah.

Smoke test window/kamera telah dilakukan dengan mikrofon dimatikan (`--no-voice`).
Perangkat output audio berhasil dibuka; tidak ada track yang dipicu melalui tombol
selama smoke test tersebut. Suara yang terdengar dan pengenalan ucapan tetap NOT TESTED.
Peringatan MediaPipe feedback tensors/NORM_RECT muncul tanpa menghentikan program.
