# Wayang Digital — Web

Aplikasi panggung interaktif Nando & Ibu, siap di-deploy ke Vercel. Seluruh animasi, audio/video, dan deteksi tangan berjalan di browser. Tidak membutuhkan server Python, database, API key, atau environment variable.

## Deploy ke Vercel

1. Upload/push isi proyek ini ke repository Git, **termasuk folder `FIX ASSET`, `web-assets`, dan file `hand_landmarker.task`**. Pastikan dua aset baru `salam.png` dan `scene 3.mp4` ikut terunggah.
2. Pada Vercel, pilih **Add New → Project**, lalu import repository tersebut.
3. Gunakan **Root Directory: `./`** (root proyek ini) dan **Framework Preset: Vite**.
4. Klik **Deploy**. Pengaturan berikut sudah ada di `vercel.json`:
   - Install: `npm ci`
   - Build: `npm run build`
   - Output: `dist`
   - Node.js: **22.x** atau versi lebih baru yang didukung Vercel (minimum 22.12).
5. Buka URL HTTPS yang diberikan Vercel, tekan **Izinkan kamera & masuk**, lalu izinkan kamera pada browser. Panggung hanya terbuka setelah kamera siap. Penolakan izin, kamera tidak tersedia, atau kegagalan deteksi membuat akses tetap terkunci.

Tidak perlu memasang Python, FFmpeg, atau mengunggah `node_modules` ke Vercel. Deploy belum dipublikasikan oleh agen; langkah import/deploy ada di tangan pemilik proyek.

Alternatif dari terminal setelah login Vercel: `npx vercel --prod`.

## Menjalankan lokal

```sh
npm ci
npm run dev
```

Buka alamat localhost yang muncul. Untuk menguji build produksi:

```sh
npm run build
npm run preview
```

Jangan membuka `index.html` langsung dari filesystem. Kamera memerlukan HTTPS atau `localhost`; alamat HTTP LAN biasa tidak mendukung izin kamera.

## Pengoperasian

Semua kontrol tersedia di layar setelah izin kamera diberikan, termasuk pada ponsel. Chrome/Edge desktop direkomendasikan untuk pertunjukan dengan keyboard, webcam, dan suara.

| Tombol | Aksi |
| --- | --- |
| N + 1–5 / I + 1–5 | Pose Nando / Ibu; ulang kombinasi untuk sembunyikan |
| A | Ganti set animasi Nando 1 / 2 (independen) |
| E | Ganti set animasi Ibu 1 / 2 (independen) |
| G | Pose dari jumlah jari |
| Y / J | Ganti kostum manual / otomatis sesuai latar |
| F1–F5 / [ / ] | Pilih / mundur / maju latar |
| 6 / 7 / 0 / 8 / 9 | Video transisi + latar + lagu adegan 1 / 2 / 3 / 4 / 5 |
| Z / X / C / V / B | Lagu adegan 1–5 |
| M | Hentikan lagu, di luar video |
| R / panah kiri-kanan | Mode lari / gerakkan Nando |
| K / T / H | Bola / tidur / pelukan |
| P | Tirai: tutup 0,35 dtk → tahan 2,5 dtk → buka 0,65 dtk |
| + / - | Naik / turun ukuran kedua karakter: 100%, 125%, 150% |
| L / S | Kunci posisi vertikal / kembalikan ukuran normal 100% |
| Space | Jeda/lanjut animasi, video, audio |
| W / D | Preview kamera / kotak deteksi |
| F / U | Fullscreen / fokus panggung |
| Esc | Lewati video atau keluar fullscreen |
| ? / F12 | Panduan; ? lebih aman jika F12 dipakai browser |
| Q | Akhiri sesi, hentikan media dan kamera |

Set Nando dan Ibu disimpan terpisah; tombol A tidak mengubah set Ibu, tombol E tidak mengubah set Nando. Tab hanya untuk navigasi browser.

Klik panggung agar shortcut keyboard aktif. Pada input, dropdown, dan dialog, navigasi keyboard normal tetap bekerja. Menahan tombol toggle tidak mengulang aksi.

**Salam:** tombol Salam langsung memilih SPORT Bank 2 pose 10. Bisa juga SPORT → Bank 2 → N+5, atau 5 jari tangan kanan dalam mode jari.

**Tirai otomatis:** setiap video berhasil mulai, siklus tirai dimulai ulang. Video dan lagu tetap berjalan di belakang tirai. Pemicu video ganda diabaikan. Lagu adegan berlanjut setelah video selesai/dilewati.

**Ukuran:** selalu tetap terhadap jarak tangan. Ibu ditampilkan 50% lebih besar dari ukuran sebelumnya pada setiap tingkat skala; ukuran Nando tetap. Normal 100%, langkah pertama 125%, langkah kedua 150%. Tombol + (atau =), - dan tombol numpad + / - mengubah kedua karakter bersama. Menahan tombol tidak mengulang perubahan; ukuran dibatasi pada tiga tingkat. S mengembalikan ke 100%. L hanya mengatur kunci gerak vertikal, tidak pernah mengaktifkan skala dari kamera.

**Kamera:** gambar diproses lokal di Web Worker. Tangan kanan mengontrol Nando, tangan kiri Ibu; pose berganti setelah jumlah jari stabil 120 ms. Tangan hilang memudarkan karakter. Izin kamera dan kamera aktif wajib untuk mengakses aplikasi, termasuk kontrol manual. Jika kamera dimatikan, terputus, atau izin dicabut, panggung terkunci kembali dan semua media berhenti. Tombol masuk bisa dipakai untuk mencoba kembali setelah izin diperbaiki. Preview kamera menampilkan 21 titik dan garis jari per tangan, warna berbeda untuk Nando/Ibu, dan angka 0-5. Angka ditampilkan tepat di atas tangan yang terlacak, mengikuti gerak tangan dan hanya muncul bersama garis pelacak. Tidak ada teks hitungan di bawah preview atau panel; saat tangan hilang, angka ikut hilang. Preview tetap tersedia saat video/pause, dan tetap tertutup saat tirai menutup panggung. W menyembunyikan/menampilkan preview.

**Suara:** memakai SpeechRecognition browser, bahasa Indonesia. Kata: taman, rumah, makan, sekolah, al azhar, kelas, koridor. Browser dapat mengirim suara ke layanan pengenalannya dan memerlukan internet; fitur hanya aktif setelah tombol ditekan. Suara dijeda selama media diputar agar lagu tidak mengganti latar. Tidak semua browser mendukungnya.

Saat tab disembunyikan, pertunjukan dijeda. Tekan lanjut setelah kembali. Izin kamera/mikrofon dari browser tetap harus diberikan pengguna situs; kode web tidak dapat memberikannya otomatis.

## Build dan aset

`scripts/prepare-assets.mjs` memvalidasi sumber dengan membacanya, mengoptimasi 43 PNG menjadi WebP, menyalin 5 MP3 + 5 MP4 H.264, dan menyiapkan model + WASM lokal. Aset asli tetap tersedia untuk versi desktop.

- Sumber: `FIX ASSET/`, `web-assets/video/`, `hand_landmarker.task`
- Hasil sementara: `public/media/`, `public/models/`, `public/vision/`, `src/generated/`
- Build produksi: `dist/`
- Nama media menggunakan hash konten, aman untuk cache panjang.
- Build gagal bila ada aset wajib yang hilang.
- Hanya aset yang masuk manifest web dikirim ke hasil build; cache PCM dan file Python tidak diperlukan.

Dua video asli memakai HEVC yang tidak selalu dapat ditampilkan browser. Semua transisi web sudah disiapkan sebagai **H.264 yuv420p 720p + faststart**, tanpa audio internal karena lagu diputar terpisah. Versi ini ada di `web-assets/video/` dan wajib ikut repository. Untuk mengganti video di masa depan, jalankan `node scripts/transcode-videos.mjs` pada komputer dengan FFmpeg, lalu commit hasilnya. Vercel memakai hasil jadi dan tidak melakukan transcode.

## Pengujian

```sh
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

`npm run check` menjalankan unit tests, build, dan pengujian browser sekaligus (setelah Chromium terpasang). Tes browser menggunakan hasil produksi melalui Vite preview, termasuk video asli, pemetaan tombol, tirai, pause, kegagalan media, izin kamera ditolak dan akses terkunci, kamera terputus, model tangan dengan webcam simulasi, dan layout mobile.

Kamera simulasi menguji inisialisasi model dan pemrosesan frame; akurasi jumlah jari manusia masih bergantung pencahayaan, kamera, posisi tangan, dan perangkat.

## Struktur

- `src/main.js`: panel operator, keyboard, lifecycle browser.
- `src/state.js`: state animasi yang dapat diuji tanpa browser.
- `src/renderer.js`: panggung Canvas 2D.
- `src/media.js`: video dan lagu.
- `src/camera.js`, `src/hand-worker.js`, `src/gestures.js`: deteksi tangan.
- `src/voice.js`: kontrol suara opsional.
- `vercel.json`: konfigurasi deploy.

Versi desktop Python tetap tersedia melalui `python main.py`; panduannya ada di `MANUAL_PENGGUNAAN.md`. Panduan tersebut khusus desktop, sedangkan README ini untuk web.

Referensi implementasi: [Vite pada Vercel](https://vercel.com/docs/frameworks/frontend/vite), [MediaPipe Hand Landmarker Web](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js).
