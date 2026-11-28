# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

Holodori-Auto adalah program otomatisasi Windows untuk *hololive Dreams* yang menggunakan pengenalan visual pada layar game. Program ini mendukung **High & Low**, **Memancing**, **Hoppin' Rope**, **Collect Cooking**, dan **Puka Puka Fight**.
Kelima fitur menggunakan pengaturan bahasa dan pintasan mulai serta berhenti yang sama.

## Unduh dan gunakan

Gunakan Windows 10 atau 11 (x64) dan klien game Windows. **Hanya jendela game dengan rasio 16:9 yang didukung.** Pastikan jendela game tetap terlihat.

1. Unduh `Holodori-Auto-v1.3.2-windows.7z` dari [Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest), ekstrak dengan 7-Zip, lalu jalankan `Holodori-Auto.exe` dari folder hasil ekstraksi.
2. Buka minigame di *hololive Dreams*. Pilih fitur yang sesuai di Holodori-Auto, lalu klik **Mulai** atau tekan pintasan mulai bersama. Klik **Berhenti** sebelum beralih fitur.

Paket standar sudah menyertakan DirectML. **Hoppin' Rope** memerlukan GPU yang mendukung DirectML atau TensorRT. **Collect Cooking** juga dapat menggunakan CPU. Jika GPU NVIDIA Anda kompatibel, unduh komponen opsional [Holodori-Auto-v1.3.1-tensorrt.7z](https://github.com/harrykuang-dev/Holodori-Auto/releases/download/v1.3.1/Holodori-Auto-v1.3.1-tensorrt.7z) dari Releases. Tutup program, ekstrak arsip agar `accelerators/tensorrt/` berada di samping `Holodori-Auto.exe`, lalu jalankan ulang. Saat pertama kali menggunakan TensorRT, program membuat engine untuk GPU tersebut dan menggunakannya kembali pada sesi berikutnya.

## Jalankan dan build dari kode sumber

Gunakan Windows x64 dan Python 3.13. Perintah pengunduhan memverifikasi model **Collect Cooking** dengan versi yang ditentukan sebelum memasangnya.

```powershell
git clone https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
$python = ".\.venv\Scripts\python.exe"
& $python -m pip install -r requirements.txt -r requirements-build.txt
& $python -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
& $python tools/fetch_models.py
& $python main.py
```

Untuk membuat dan memverifikasi paket portabel DirectML, jalankan perintah berikut dari checkout yang sama. Gunakan direktori keluaran baru untuk setiap build.

```powershell
& $python tools/build_release.py --output dist/Holodori-Auto
& $python tools/verify_bundle.py dist/Holodori-Auto/Holodori-Auto.exe --report work/packaged-contents.json
```

## Pengembangan dan pemeliharaan

Kelima fitur dikelola di `components/`. Jendela, bahasa, dan pintasan bersama dikelola di `holodori/`. Setiap fitur berjalan di proses terpisah. GitHub Actions memverifikasi sumber dan paket portabel Windows.

[Dokumentasi teknis](document/README.md) · [Build dan verifikasi](document/ARCHITECTURE.md) · [Alur pemeliharaan](document/UPDATING.md) · [Istilah dalam game](document/GAME-TERMS.md)

## Pemberitahuan dan lisensi

Holodori-Auto adalah proyek independen. Nama game, tangkapan layar, dan karya visual adalah milik pemegang hak masing-masing.

Kode dan dokumentasi asli Holodori-Auto menggunakan [Lisensi MIT](LICENSE). Implementasi **Hoppin' Rope** dan bobot turunannya dari YOLO tetap menggunakan [AGPL-3.0-only](components/jump_rope/LICENSE). Materi pihak ketiga mengikuti ketentuannya masing-masing. Lihat [lisensi dan kode sumber terkait](LICENSES.md) serta [pemberitahuan pihak ketiga](THIRD_PARTY_NOTICES.md).
