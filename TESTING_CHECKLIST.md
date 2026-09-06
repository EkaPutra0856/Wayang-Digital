# Testing Checklist — Wayang Interaktif 2D

Tanggal pengujian: 6 September 2026. Hasil otomatis tidak menggantikan pengamatan
webcam, speaker, arah tangan fisik, dan kenyamanan animasi oleh operator.

## Hasil otomatis

- [x] PASS — syntax seluruh modul aplikasi melalui `py_compile`.
- [x] PASS — import seluruh modul aplikasi.
- [x] PASS — `python -m pip check`: tidak ada dependensi rusak.
- [x] PASS — seluruh 51 aset wajib ada; 41 PNG berhasil didekode dengan alpha sprite.
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
- [ ] Tangan hilang mempertahankan posisi/pose terakhir.
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
- [x] Release direction menghentikan frame cycle dan mempertahankan posisi.
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

Belum ada klaim verifikasi gesture manusia, pengenalan suara nyata, persepsi
sinkronisasi speaker, atau target 30 FPS di hardware pertunjukan. Lengkapi kotak
manual di atas saat latihan. Catatan runtime tambahan ada di bawah.

Smoke test window/kamera telah dilakukan dengan mikrofon dimatikan (`--no-voice`).
Perangkat output audio berhasil dibuka; tidak ada track yang dipicu melalui tombol
selama smoke test tersebut. Suara yang terdengar dan pengenalan ucapan tetap NOT TESTED.
Peringatan MediaPipe feedback tensors/NORM_RECT muncul tanpa menghentikan program.
