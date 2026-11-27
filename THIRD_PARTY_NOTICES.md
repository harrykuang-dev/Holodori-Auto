# Third-party notices / 第三方來源與聲明

## Code, strategies, models, and references / 程式碼、策略、模型及參考資料

| External source / 外部來源 | Use in Holodori-Auto / 用途及授權 |
| --- | --- |
| [mwty-0415/Hololive-Dreams-Auto-High-Low](https://github.com/mwty-0415/Hololive-Dreams-Auto-High-Low) | Source of parts of the High & Low implementation. The upstream repository does not specify a project-wide license. / 比大小功能的部分程式碼來自此倉庫。上游未列出專案整體授權。 |
| [Oreki0504/hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper) | Provides the poker hand evaluator and hold/discard optimizer in `components/high_low/poker_core.py`, the basis of `components/high_low/recognizer.py`, and card recognition templates. Retains Totarou Oriki's [MIT notice](components/high_low/licenses/poker-core-MIT.txt). The card artwork rights remain with the game's rights holders. / 提供撲克牌型評估、留牌與換牌策略、牌面辨識程式和模板。牌面圖像權利由遊戲權利人保有。 |
| [brianhliou/dobutsu-shogi](https://github.com/brianhliou/dobutsu-shogi) | Its [public tablebase](https://dobutsu.brianhliou.com/) supplies exact results for eligible three-row board positions. The upstream repository uses the [MIT License](https://github.com/brianhliou/dobutsu-shogi/blob/main/LICENSE). Holodori-Auto queries the service and implements its own local solver. / 查詢適用的三排棋局精確解，本機求解器由 Holodori-Auto 維護。 |
| [Ultralytics](https://github.com/ultralytics/ultralytics) | YOLO26 is the base for the distributed rope-detection weights. See the [AGPL notice and source](components/jump_rope/NOTICE.md). / 跳繩辨識權重衍生自 YOLO26，適用 AGPL 聲明。 |
| [PyTorch](https://github.com/pytorch/pytorch) and [TorchVision](https://github.com/pytorch/vision) | Used in model training and export. The ResNet18 and ResNet101 click-position classifiers were initialized with TorchVision's ImageNet-1K V1 weights. See [TorchVision's pretrained weight terms](https://docs.pytorch.org/vision/stable/models.html#general-information-on-pre-trained-weights), the [model manifest](components/cooking/models-manifest.json) and the [checkpoint manifest](components/cooking/tools/checkpoints-manifest.json). / 用於模型訓練與匯出。ResNet18 與 ResNet101 點位分類器採用 TorchVision 的 ImageNet-1K V1 預訓練權重初始化，權重條款及檔案清單見上方連結。 |
| [sml2h3/ddddocr](https://github.com/sml2h3/ddddocr) | Provides the packaged OCR implementation and `common_old.onnx` classifier used to read reward amounts. The package retains its [upstream MIT notice](https://github.com/sml2h3/ddddocr/blob/master/LICENSE). / 提供辨識獎勵數字的 OCR 程式及分類模型，發行包保留上游 MIT 授權聲明。 |
| [CyleAR/hololive-toolkit](https://github.com/CyleAR/hololive-toolkit/tree/8089309806b10ce6cc0ae660a46d2217eb815a1e) | Used to validate the extraction of the game sprite that supplies the [fishing reference mask](components/fishing/assets/vision/PROVENANCE.md). / 用於核對釣魚辨識遮罩所用遊戲圖像的擷取方式。 |
| [HolodoriDB](https://github.com/HolodoriDB) | The [in-game terminology reference](document/GAME-TERMS.md) uses its mirrors of the six game localization tables. / 六種語言的遊戲用詞以此處鏡像的遊戲字串表核對。 |

The maintainer's earlier repositories and migration commits are recorded in [source origins](document/SOURCE-ORIGINS.json). Retained MIT notices for previously shared shortcut code are in the [High & Low notices](components/high_low/licenses/) and the [Collect Cooking notices](components/cooking/third-party/).

維護者原有倉庫的整合提交見[來源紀錄](document/SOURCE-ORIGINS.json)。原有專案共用的快捷鍵程式碼保留上方連結所列的 MIT 聲明。

## Packaged dependencies / 隨附相依套件

The standard Windows package contains [ONNX Runtime](https://github.com/microsoft/onnxruntime) with [DirectML](https://github.com/microsoft/DirectML) and Python dependencies declared in [requirements.txt](requirements.txt). It retains the libraries' applicable licenses and notices, including [ONNX Runtime's license](components/cooking/third-party/onnxruntime/LICENSE) and [notices](components/cooking/third-party/onnxruntime/ThirdPartyNotices.txt). [PyDirectInput](https://github.com/learncodebygaming/pydirectinput) retains its MIT license and the BSD-3-Clause notice for code from [PyAutoGUI](https://github.com/asweigart/pyautogui). [PyInstaller](https://github.com/pyinstaller/pyinstaller) is the build tool and its bootloader distribution uses its published license and exception.

標準 Windows 發行包包含 ONNX Runtime、DirectML 與 `requirements.txt` 所列的 Python 相依套件，並保留適用的授權與聲明。PyInstaller 的啟動載入器適用其發布的授權與例外條款。

The optional GPU add-on contains NVIDIA [TensorRT](https://github.com/NVIDIA/TensorRT), its Python bindings and NVIDIA CUDA runtime libraries. Package metadata and license files accompany the distributed libraries. See the retained licenses for the [TensorRT libraries](components/cooking/third-party/tensorrt_cu12_libs/LICENSE.txt), [TensorRT bindings](components/cooking/third-party/tensorrt_cu12_bindings/LICENSE.txt), and [CUDA runtime](components/cooking/third-party/nvidia-cuda-runtime-cu12/License.txt).

選用的 GPU 組件包含 NVIDIA TensorRT、其 Python 繫結與 NVIDIA CUDA 執行庫，並保留上方連結所列的 NVIDIA 授權及套件資訊。
