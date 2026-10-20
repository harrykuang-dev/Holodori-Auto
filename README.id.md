# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Program Windows yang menggabungkan **High & Low**, **Memancing**, **Lompat Tali**, dan **Memasak** dari *hololive Dreams* dalam satu jendela. Keempat fitur berbagi pengaturan bahasa serta pintasan mulai dan berhenti, dengan tetap mempertahankan logika permainan, kontrol, statistik, dan diagnostik masing-masing. Navigasi dan pengaturan bersama memakai gaya Fluent yang sama serta menggunakan gambar dan warna tema asli setiap fitur.

| Fitur | Program asal |
| --- | --- |
| High & Low | [Hololive-Dreams-High-low-Auto-Personal](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal) |
| Memancing | [Hololive-Dreams-Fishing-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto) |
| Lompat Tali | [Hololive-Dreams-Jump-Rope-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto) |
| Memasak | [Hololie-Dreams-Collect-Cooking-Auto](https://github.com/harrykuang-dev/Hololie-Dreams-Collect-Cooking-Auto) |

## Unduh

Unduh ketiga volume, `Holodori-Auto-v1.0.0-windows.7z.001`, `.002`, dan `.003`, dari [v1.0.0](https://github.com/harrykuang-dev/Holodori-Auto/releases/tag/v1.0.0) dan simpan dalam folder yang sama. Gunakan 7-Zip untuk mengekstrak hanya `.7z.001`; volume lainnya akan dibaca otomatis untuk memulihkan folder `Holodori-Auto` secara lengkap. Jalankan `Holodori-Auto.exe` di dalamnya dan simpan seluruh isi folder bersama. Python dan CUDA Toolkit tidak perlu dipasang secara terpisah.

CUDA bersifat opsional. Memasak otomatis menggunakan GPU NVIDIA CUDA yang tersedia, atau menggunakan CPU, termasuk pada komputer dengan grafis AMD. Akselerasi model dengan GPU AMD belum didukung; kecepatan pengenalan memasak di CPU bergantung pada prosesor. High & Low, Memancing, dan Lompat Tali tidak memerlukan CUDA.

## Penggunaan

1. Buka game dan masuk ke minigame yang ingin digunakan.
2. Jalankan Holodori-Auto dan pilih fitur yang sesuai melalui navigasi.
3. Atur bahasa serta pintasan mulai dan berhenti bersama, lalu gunakan kontrol fitur yang dipilih. Untuk Memasak, pilih **Muat model** sebelum **Mulai**.
4. Hentikan proses sebelum berpindah fitur. Program menunggu fitur saat ini selesai ditutup, lalu membuka fitur pilihan dalam jendela yang sama.

Hanya fitur yang dipilih yang berjalan. Pilihan bahasa dan pintasan bersama berlaku untuk fitur aktif dan tetap digunakan saat berpindah fitur. Baris pengaturan yang berulang pada setiap halaman disembunyikan. Saat memasukkan pintasan baru, pemantauan pintasan fitur aktif dijeda hingga pengisian selesai.

Preferensi bersama disimpan di `%LOCALAPPDATA%\HolodoriAuto\settings.json`. Saat pertama kali dijalankan, program mengutamakan pengaturan bahasa dan pintasan High & Low yang sudah ada. Jika belum ada pengaturan, nilai bawaannya adalah bahasa Tionghoa Tradisional, **F8** untuk mulai, dan **INSERT** untuk berhenti. Statistik, catatan permainan, dan opsi khusus setiap fitur tetap menggunakan lokasi data program asal.

Memerlukan Windows 10/11 x64 dan klien game versi Windows. Biarkan game terlihat selama proses berjalan dan ikuti persyaratan resolusi, penangkapan layar, serta jendela aktif dari fitur yang dipilih. Petunjuk lengkap mengenai kontrol dan perilaku setiap fitur tersedia dalam README repositori asal yang ditautkan di atas.

## Menjalankan dari kode sumber

Gunakan Windows x64 dan Python 3.13. Klon repositori beserta submodulnya; ZIP kode sumber dari GitHub tidak menyertakan isi submodul.

```powershell
git clone --recurse-submodules https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-build.txt
python tools/fetch_models.py
python main.py
```

Dependensi mencakup runtime CUDA 12.8. Fitur Memasak secara otomatis memakai GPU NVIDIA yang tersedia, atau CPU jika GPU tidak tersedia, sesuai perilaku program asal.

Perintah pemasangan model mengunduh `models.zip` dari rilis Memasak yang sesuai, memeriksa ukuran berkas dan SHA-256 yang telah ditetapkan, lalu memverifikasi setiap model sebelum pemasangan. Hanya model yang belum ada yang dipasang; berkas yang sudah ada dipertahankan. Jika isi model yang sudah ada berbeda, pindahkan berkas tersebut ke lokasi cadangan sebelum mencoba lagi. Model tetap harus dimuat secara manual melalui antarmuka Memasak.

Untuk memakai arsip yang sudah diunduh dari rilis Memasak, jalankan `python tools/fetch_models.py --archive C:\path\models.zip`. Untuk memverifikasi model yang terpasang tanpa koneksi jaringan, jalankan `python tools/fetch_models.py --check`.

## Membangun program

Setelah dependensi dan model Memasak terpasang, jalankan:

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

Pertahankan seluruh isi folder portabel yang dihasilkan saat menjalankan atau mendistribusikan program. Hasil build mencakup dependensi, sumber daya asli, dan model Memasak.

## Mengikuti pembaruan setiap fitur

Keempat repositori asal tetap dipelihara sebagai submodul Git yang terpisah. `upstream-lock.json` mencatat commit dan versi yang digunakan untuk setiap fitur dalam program gabungan. Memperbarui satu fitur tidak memerlukan penyalinan atau penggabungan algoritma permainannya ke Holodori-Auto.

```powershell
python tools/sync_upstreams.py --check
python tools/sync_upstreams.py --module fishing
git add upstream/fishing upstream-lock.json
python tools/sync_upstreams.py --verify
python -m unittest discover -s tests -v
```

Hilangkan `--module fishing` untuk memperbarui keempat fitur sekaligus. Tinjau perubahan dependensi, manifes model, dan antarmuka integrasi sebelum menggabungkannya. Setelah Memasak diperbarui, jalankan kembali perintah pemasangan model.

GitHub Actions memeriksa pembaruan repositori asal setiap hari dan saat dijalankan secara manual, membuat Pull Request pembaruan, serta menjalankan pemeriksaan integrasi. Pembaruan digabungkan secara manual setelah ditinjau. Lihat [arsitektur dan pemeliharaan](docs/ARCHITECTURE.md) untuk antarmuka integrasi dan susunan build.

## Hak dan lisensi

Kode sumber, gambar, berkas lisensi, dan pemberitahuan pihak ketiga dari program asal tetap disertakan pada masing-masing fitur di `upstream/`. Lihat repositori asal untuk ketentuan dan atribusinya. Nama game dan gambar merupakan milik pemegang hak masing-masing.
