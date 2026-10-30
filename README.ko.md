# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

*hololive Dreams*의 **하이&로**, **낚시**, **줄넘기**, **요리**를 하나의 창에서 실행하는 Windows 프로그램입니다. 네 기능은 언어와 시작·중지 단축키를 공유하며, 각 기능의 기존 게임 로직, 조작 화면, 통계, 진단 기능을 유지합니다. 탐색 영역과 공통 설정에는 같은 Fluent 스타일을 사용하고, 각 기능의 기존 이미지와 테마 색상을 적용합니다.

| 기능 | 원본 프로그램 |
| --- | --- |
| 하이&로 | [Hololive-Dreams-High-low-Auto-Personal](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal) |
| 낚시 | [Hololive-Dreams-Fishing-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto) |
| 줄넘기 | [Hololive-Dreams-Jump-Rope-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto) |
| 요리 | [Hololive-Dreams-Collect-Cooking-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Collect-Cooking-Auto) |

**1.1.2**에는 하이&로 **1.1.2**, 낚시 **1.1.2**, 줄넘기 **1.3.2**, 요리 **1.1.1**이 포함됩니다. 왼쪽 아래 버전을 클릭하면 각 프로그램의 버전과 저장소 링크를 볼 수 있습니다. 처음 열 때는 선택한 단독 프로그램의 기본 창 크기를 화면 DPI에 맞춰 사용합니다. 크기를 조절하거나 최대화한 후 기능을 전환해도 현재 창 크기와 상태가 유지됩니다.

## 다운로드

[Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest)에서 `Holodori-Auto-v1.1.2-windows.7z`를 다운로드하고 7-Zip으로 압축을 푼 뒤 `Holodori-Auto.exe`를 실행하세요. 전체 폴더를 함께 보관하세요. Python이나 CUDA Toolkit을 별도로 설치할 필요는 없습니다.

줄넘기와 요리는 한 패키지의 TensorRT 10.13, CUDA 런타임, DirectML을 공유합니다. 호환 NVIDIA GPU는 TensorRT를, 그 외 지원 GPU는 DirectML을 사용합니다. 줄넘기는 호환 GPU가 필요하며 요리는 CPU로도 전환할 수 있습니다. 모델과 장치별 엔진 캐시는 기능마다 별도로 유지됩니다.

> **첫 사용 안내:** 호환되는 NVIDIA RTX 20 시리즈 이상 GPU에서는 줄넘기나 요리를 처음 사용할 때 해당 GPU용 TensorRT 엔진을 컴파일합니다. 예상 시간은 **1~2분**이며 하드웨어와 시스템 부하에 따라 달라집니다. 완료될 때까지 기다려 주세요. 엔진은 이후 사용을 위해 캐시됩니다.

## 사용 방법

1. 게임을 실행하고 사용할 미니게임 화면으로 이동합니다.
2. Holodori-Auto를 실행하고 탐색 영역에서 해당 기능을 선택합니다.
3. 공통 언어와 시작·중지 단축키를 설정한 뒤 선택한 기능을 조작합니다. 요리는 **시작**을 누르면 선택한 모델을 자동으로 불러오고 준비가 끝나면 시작합니다. 로딩 중에는 **중지**로 취소할 수 있습니다.
4. 기능을 전환하기 전에 실행을 중지합니다. 현재 기능이 완전히 종료된 후 같은 창에서 선택한 기능을 엽니다.

선택한 기능 하나만 실행됩니다. 공통 언어와 단축키 설정은 현재 기능에 적용되며 기능을 전환해도 유지됩니다. 각 화면에서 중복되는 설정 행은 숨겨집니다. 새 단축키를 입력하는 동안 현재 기능의 단축키 감지를 일시 중지하고, 입력이 끝나면 다시 시작합니다.

공통 설정은 `%LOCALAPPDATA%\HolodoriAuto\settings.json`에 저장됩니다. 처음 실행할 때 기존 High & Low의 언어와 단축키 설정이 있으면 우선 적용합니다. 기존 설정이 없으면 번체 중국어, 시작 **F8**, 중지 **INSERT**가 기본값입니다. 통계, 게임 기록, 기능별 옵션은 원본 프로그램의 데이터 위치를 계속 사용합니다.

Windows 10/11 x64와 Windows용 게임 클라이언트가 필요합니다. 실행 중에는 게임 화면이 보이도록 유지하고, 선택한 기능의 해상도, 화면 캡처, 전경 실행 요구 사항을 따르세요. 각 기능의 자세한 조작과 동작은 위에 연결된 원본 저장소의 README를 참조하세요.

## 소스에서 실행

Windows x64와 Python 3.13을 사용합니다. 저장소를 복제할 때 서브모듈도 함께 가져와야 합니다. GitHub의 소스 ZIP에는 서브모듈 내용이 포함되지 않습니다.

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

의존성에는 공통 TensorRT 10.13 및 DirectML 런타임이 포함됩니다. PyTorch는 더 이상 필요하지 않습니다.

모델 설치 명령은 요리의 해당 릴리스에서 `models.zip`을 다운로드하고, 고정된 파일 크기와 SHA-256을 대조합니다. 각 모델도 검증한 후 누락된 모델만 설치합니다. 기존 파일은 유지합니다. 기존 모델의 내용이 다르면 해당 파일을 백업 위치로 이동한 후 다시 실행하세요. 요리는 시작을 누르면 선택한 모델을 자동으로 불러옵니다.

요리 릴리스에서 이미 다운로드한 압축 파일을 사용하려면 `python tools/fetch_models.py --archive C:\path\models.zip`을 실행합니다. 설치된 모델을 오프라인으로 검증하려면 `python tools/fetch_models.py --check`를 실행합니다.

## 빌드

의존성과 요리 모델을 설치한 후 실행합니다.

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

실행하거나 배포할 때 생성된 포터블 폴더 전체를 유지하세요. 빌드에는 의존성, 원본 리소스, 요리 모델이 포함됩니다.

## 각 기능의 업데이트 반영

네 원본 저장소는 독립적인 Git 서브모듈로 유지됩니다. `upstream-lock.json`은 통합 버전에서 사용하는 각 기능의 정확한 커밋과 버전을 기록합니다. 기능 하나를 업데이트할 때 게임 알고리즘을 Holodori-Auto로 복사하거나 병합할 필요가 없습니다.

```powershell
python tools/sync_upstreams.py --check
python tools/sync_upstreams.py --module fishing
git add upstream/fishing upstream-lock.json
python tools/sync_upstreams.py --verify
python -m unittest discover -s tests -v
```

`--module fishing`을 생략하면 네 기능을 모두 업데이트합니다. 병합 전에 의존성, 모델 매니페스트, 통합 인터페이스의 변경 사항을 확인하세요. 요리를 업데이트한 경우 모델 설치 명령을 다시 실행합니다.

GitHub Actions는 매일 및 수동 실행 시 원본 저장소의 업데이트를 확인하고, 업데이트 Pull Request를 생성해 통합 검사를 실행합니다. 업데이트는 검토 후 수동으로 병합합니다. 통합 인터페이스와 빌드 구성은 [아키텍처 및 유지보수 문서](docs/ARCHITECTURE.md)를 참조하세요.

## 권리 및 라이선스

줄넘기 1.3.2과 YOLO 파생 가중치는 **AGPL-3.0-only**, 낚시는 **MIT**를 사용합니다. 하이&로와 요리가 참조하는 구성 요소의 기존 MIT 고지는 유지됩니다. NVIDIA 런타임, 기타 의존성 및 게임 이미지에는 각각의 조건이 적용됩니다. [라이선스 및 대응 소스](LICENSES.md)를 참조하세요. Release의 `Holodori-Auto-v1.1.2-source.zip`에는 고정된 네 서브모듈의 소스가 포함됩니다. GitHub가 자동 생성하는 소스 압축 파일에는 서브모듈이 포함되지 않습니다.
