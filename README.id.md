# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Holodori-Auto adalah program Windows untuk mengotomatiskan minigame **High & Low**, **Memancing**, **Lompat Tali**, **Memasak**, dan **Catur Rakit** di *hololive Dreams*. Pilih mode di menu navigasi untuk menggunakan kontrol dan melihat statistiknya. Pengaturan bahasa serta pintasan mulai dan berhenti berlaku untuk semua mode.

## Unduh

Unduh `Holodori-Auto-v1.2.10-windows.7z` dari [Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest), ekstrak dengan 7-Zip, lalu jalankan `Holodori-Auto.exe`. Simpan seluruh isi folder bersama. Python dan CUDA Toolkit tidak perlu dipasang secara terpisah.

Lompat Tali dan Memasak berbagi TensorRT 10.13, pustaka runtime CUDA, dan DirectML dalam satu paket. GPU NVIDIA yang kompatibel otomatis memakai TensorRT; GPU lain yang didukung memakai DirectML. Lompat Tali memerlukan GPU yang kompatibel; Memasak juga dapat beralih ke CPU. Model dan cache engine khusus perangkat tetap terpisah.

> **Tips penggunaan pertama:** Pada GPU NVIDIA RTX seri 20 dan yang lebih baru yang kompatibel, penggunaan pertama Lompat Tali atau Memasak mengompilasi engine TensorRT untuk GPU tersebut. Perkiraan waktunya **1–2 menit**, tergantung perangkat keras dan beban sistem. Tunggu hingga kompilasi selesai; engine disimpan dalam cache untuk penggunaan berikutnya.

## Penggunaan

1. Buka game dan masuk ke minigame yang ingin digunakan.
2. Jalankan Holodori-Auto dan pilih fitur yang sesuai melalui navigasi.
3. Atur bahasa serta pintasan mulai dan berhenti bersama, lalu gunakan kontrol fitur yang dipilih. Pada Memasak, **Mulai** otomatis memuat dan melakukan pemanasan model yang dipilih sebelum mulai; **Berhenti** membatalkan pemuatan.
4. Hentikan proses sebelum berpindah fitur. Program menunggu fitur saat ini selesai ditutup, lalu membuka fitur pilihan dalam jendela yang sama.

Hanya fitur yang dipilih yang berjalan. Pilihan bahasa dan pintasan bersama berlaku untuk fitur aktif dan tetap digunakan saat berpindah fitur. Baris pengaturan yang berulang pada setiap halaman disembunyikan. Saat memasukkan pintasan baru, pemantauan pintasan fitur aktif dijeda hingga pengisian selesai.

Preferensi bersama disimpan di `%LOCALAPPDATA%\HolodoriAuto\settings.json`. Saat pertama kali dijalankan, program mengutamakan pengaturan bahasa dan pintasan High & Low yang sudah ada. Jika belum ada pengaturan, nilai bawaannya adalah bahasa Tionghoa Tradisional, **F8** untuk mulai, dan **INSERT** untuk berhenti. Statistik, catatan permainan, dan opsi khusus setiap fitur tetap menggunakan lokasi data program asal.

Memerlukan Windows 10/11 x64 dan klien game versi Windows. Pastikan layar game tetap terlihat selama program berjalan, lalu ikuti persyaratan resolusi, penangkapan layar, dan jendela aktif untuk mode yang dipilih.

Saat dibuka, ukuran awal jendela mengikuti ukuran bawaan mode yang dipilih dan disesuaikan dengan DPI layar. Setelah jendela diubah ukurannya atau dimaksimalkan, perpindahan mode mempertahankan keadaan jendela saat ini. Klik nomor versi di sudut kiri bawah untuk membuka repositori Holodori-Auto.

### Catur Rakit

Buka layar solo Puka Puka Fight di game, lalu pilih **Catur Rakit** di Holodori-Auto. Batas pertandingan adalah 1–9999 dan menghitung kemenangan yang sudah menyelesaikan layar hasil. Program melanjutkan level Normal dan masuk ke Challenge setelah game membukanya seusai Normal 30.

**Isi ulang energi otomatis** nonaktif secara bawaan. Saat aktif, program dapat mengonfirmasi satu item pemulihan dan melanjutkan. Program memeriksa jendela game 16:9 di latar depan dan sorotan sasaran sah sebelum mengeklik. Posisi standar delapan bidak dapat dikirim sebagai data papan, cadangan, dan giliran ke [basis data Animal Shogi](https://dobutsu.brianhliou.com/).

## Menjalankan dari kode sumber

Gunakan Windows x64 dan Python 3.13. Klon repositori beserta submodulnya; ZIP kode sumber dari GitHub tidak menyertakan isi submodul.

```powershell
git clone --recurse-submodules https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-build.txt
python -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
python tools/fetch_models.py
python main.py
```

Dependensi mencakup runtime TensorRT 10.13 dan DirectML bersama; PyTorch tidak lagi diperlukan.

Perintah pemasangan model mengunduh `models.zip` dari rilis Memasak yang sesuai, memeriksa ukuran berkas dan SHA-256 yang telah ditetapkan, lalu memverifikasi setiap model sebelum pemasangan. Hanya model yang belum ada yang dipasang; berkas yang sudah ada dipertahankan. Jika isi model yang sudah ada berbeda, pindahkan berkas tersebut ke lokasi cadangan sebelum mencoba lagi. Memasak otomatis memuat model yang dipilih saat Mulai ditekan.

Untuk memakai arsip yang sudah diunduh dari rilis Memasak, jalankan `python tools/fetch_models.py --archive C:\path\models.zip`. Untuk memverifikasi model yang terpasang tanpa koneksi jaringan, jalankan `python tools/fetch_models.py --check`.

## Membangun program

Setelah dependensi dan model Memasak terpasang, jalankan:

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

Pertahankan seluruh isi folder portabel yang dihasilkan saat menjalankan atau mendistribusikan program. Hasil build mencakup dependensi, sumber daya asli, dan model Memasak.

## Pengembangan dan pemeliharaan

Kelima fitur dapat dijalankan melalui `main.py`. Navigasi, bahasa, pintasan, dan paket portabel Windows digunakan bersama.

| Fitur | Referensi teknis |
| --- | --- |
| High & Low | [OCR](document/high-low/OCR.md) · [Strategi](document/high-low/STRATEGY.md) |
| Memancing | [Pengenalan dan diagnostik](document/fishing/DEVELOPMENT.md) |
| Lompat Tali | [Perekaman layar, pengaturan waktu, dan model](document/jump-rope/DEVELOPMENT.md) |
| Memasak | [Pengembangan dan diagnostik](document/cooking/DEVELOPMENT.md) · [Inferensi](document/cooking/INFERENCE.md) |
| Catur Rakit | [Pengenalan papan dan pelacakan langkah](document/raft-chess.md) |

[Indeks dokumentasi teknis](document/README.md) memuat [arsitektur dan prosedur validasi](document/ARCHITECTURE.md) serta [pemeliharaan versi kode sumber](document/UPDATING.md). GitHub Actions memeriksa versi sumber, menjalankan pengujian, dan memverifikasi paket portabel.

## Hak dan lisensi

Lompat Tali 1.3.3 dan bobot turunan YOLO memakai **AGPL-3.0-only**; Memancing memakai **MIT**. Pemberitahuan MIT yang ada untuk komponen yang dirujuk High & Low dan Memasak tetap disertakan. Runtime NVIDIA, dependensi lain, dan gambar game mempertahankan ketentuannya masing-masing. Lihat [lisensi dan kode sumber terkait](LICENSES.md). Release menyediakan `Holodori-Auto-v1.2.10-source.zip` dengan sumber keempat submodul pada commit yang ditetapkan; arsip sumber otomatis GitHub tidak menyertakan submodul.
