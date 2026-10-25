# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Program Windows yang menggabungkan **High & Low**, **Memancing**, **Lompat Tali**, dan **Memasak** dari *hololive Dreams* dalam satu jendela. Keempat fitur berbagi pengaturan bahasa serta pintasan mulai dan berhenti, dengan tetap mempertahankan logika permainan, kontrol, statistik, dan diagnostik masing-masing. Navigasi dan pengaturan bersama memakai gaya Fluent yang sama serta menggunakan gambar dan warna tema asli setiap fitur.

| Fitur | Program asal |
| --- | --- |
| High & Low | [Hololive-Dreams-High-low-Auto-Personal](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal) |
| Memancing | [Hololive-Dreams-Fishing-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto) |
| Lompat Tali | [Hololive-Dreams-Jump-Rope-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto) |
| Memasak | [Hololive-Dreams-Collect-Cooking-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Collect-Cooking-Auto) |

**1.1.0** mencakup High & Low **1.1.1**, Memancing **1.1.2**, Lompat Tali **1.3.0**, dan Memasak **1.1.0**. Klik versi di sudut kiri bawah untuk melihat versi dan tautan repositori setiap program. Setiap fitur memakai ukuran jendela bawaan program mandirinya, disesuaikan dengan DPI layar.

## Unduh

Unduh `Holodori-Auto-v1.1.0-windows.7z` dari [Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest), ekstrak dengan 7-Zip, lalu jalankan `Holodori-Auto.exe`. Simpan seluruh isi folder bersama. Python dan CUDA Toolkit tidak perlu dipasang secara terpisah.

Lompat Tali dan Memasak berbagi TensorRT 10.13, pustaka runtime CUDA, dan DirectML dalam satu paket. GPU NVIDIA yang kompatibel otomatis memakai TensorRT; GPU lain yang didukung memakai DirectML. Lompat Tali memerlukan GPU yang kompatibel; Memasak juga dapat beralih ke CPU. Model dan cache engine khusus perangkat tetap terpisah. Pemuatan pertama TensorRT dapat memerlukan waktu lebih lama untuk membangun cache.

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
python -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
python tools/fetch_models.py
python main.py
```

Dependensi mencakup runtime TensorRT 10.13 dan DirectML bersama; PyTorch tidak lagi diperlukan.

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
