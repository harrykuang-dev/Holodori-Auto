# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

Holodori-Auto는 *hololive Dreams*용 Windows 자동화 프로그램입니다. **하이&로**, **물고기 낚시**, **줄넘기**, **모아 쿠킹**, **둥실둥실 파이트**를 지원합니다.
언어 설정과 시작 및 정지 단축키는 다섯 가지 기능에서 공통으로 사용됩니다.

## 다운로드 및 사용

Windows 10 또는 11(x64)과 Windows용 게임 클라이언트를 사용하세요. **게임 창은 16:9 비율만 지원합니다.** 게임 창이 화면에 보이도록 유지하세요.

1. [릴리스](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest)에서 `Holodori-Auto-v1.3.1-windows.7z`를 다운로드하고 7-Zip으로 압축을 푼 뒤, 해당 폴더에서 `Holodori-Auto.exe`를 실행합니다.
2. *hololive Dreams*에서 미니게임에 들어간 뒤 Holodori-Auto에서 해당 기능을 선택합니다. **시작**을 클릭하거나 공통 시작 단축키를 누릅니다. 기능을 전환하기 전에 **중지**를 클릭하세요.

표준 패키지에는 DirectML이 포함되어 있습니다. **줄넘기**에는 DirectML 또는 TensorRT를 지원하는 GPU가 필요하며, **모아 쿠킹**은 CPU로도 실행할 수 있습니다. 호환되는 NVIDIA GPU에서 TensorRT를 사용하려면 릴리스에서 `Holodori-Auto-v1.3.1-tensorrt.7z`를 다운로드합니다. 프로그램을 종료하고 `accelerators/tensorrt/`가 `Holodori-Auto.exe` 옆에 오도록 압축을 푼 뒤 다시 실행하세요. TensorRT를 처음 사용하면 해당 GPU용 엔진을 만들어 이후 실행에서 재사용합니다.

## 소스 코드에서 실행 및 빌드

Windows x64와 Python 3.13을 사용합니다. 모델 다운로드 명령은 지정된 **모아 쿠킹** 모델을 검증한 뒤 설치합니다.

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

같은 체크아웃에서 다음 명령을 실행해 DirectML 포터블 패키지를 빌드하고 검증합니다. 빌드마다 새 출력 폴더를 지정하세요.

```powershell
& $python tools/build_release.py --output dist/Holodori-Auto
& $python tools/verify_bundle.py dist/Holodori-Auto/Holodori-Auto.exe --report work/packaged-contents.json
```

## 개발 및 유지보수

다섯 기능의 소스는 `components/`에 있습니다. 공통 창, 언어, 단축키는 `holodori/`에서 관리하며 각 기능은 별도 프로세스에서 실행됩니다. GitHub Actions는 소스와 Windows 포터블 빌드를 검증합니다.

[기술 문서](document/README.md) · [빌드 및 검증](document/ARCHITECTURE.md) · [유지보수 절차](document/UPDATING.md) · [게임 용어](document/GAME-TERMS.md)

## 고지 및 라이선스

Holodori-Auto는 독립 프로젝트입니다. 게임 이름, 스크린샷, 아트워크의 권리는 각 권리자에게 있습니다.

Holodori-Auto의 자체 코드와 문서에는 [MIT 라이선스](LICENSE)가 적용됩니다. **줄넘기** 구현과 YOLO 파생 모델 가중치에는 [AGPL-3.0-only](components/jump_rope/LICENSE)가 계속 적용됩니다. 제3자 자료에는 각각의 조건이 적용됩니다. [라이선스 및 대응 소스](LICENSES.md)와 [제3자 고지](THIRD_PARTY_NOTICES.md)를 참고하세요.
