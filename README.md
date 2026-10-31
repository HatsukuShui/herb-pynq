# 中药气味识别 · Herb PYNQ

基于 **PYNQ-Z2（Zynq-7020，xc7z020clg400-1）** 的中药气味分类工程，包含 STM32 采集板固件、单味药材与 MOS＋SGP 融合算法、HLS/RTL、Vivado 重建脚本和可直接复制到板上的部署文件。

数据处理流程：传感器记录 → ARM 端窗口与特征提取 → 标准化和定点量化 → AXI4-Lite → FPGA 分类核 → 类别及得分。

## 工程结构

| 目录 | 内容 |
| --- | --- |
| `build/deploy/` | 配套 bit/HWH/XSA、板端脚本、演示 Notebook 和回放数据 |
| `build/models/` | 两个已导出的 HLS IP，包含 Verilog/VHDL、权重 ROM、驱动和 IP 元数据 |
| `build/*.tcl`、`board/` | Vivado/Vitis 构建脚本及 PYNQ-Z2 PS7 配置 |
| `src/ps/` | ARM/PYNQ 推理与回放源码 |
| `third_party/algorithm_20261013/` | 与现有位流配套的 C++/HLS 源码、定点参数及测试向量 |
| `algorithm/small_herb/` | 单味药材八分类的特征、训练、推理、模型和量化代码 |
| `algorithm/mixture_fusion/` | MOS＋SGP 十分类、传统模型与轻量网络对照、训练及导出代码 |
| `hardware/firmware/` | STM32F030 采集和控制固件、Keil 工程 |
| `hardware/schematic/` | 嘉立创 EDA 原理图工程 `TO6+SGP.eprj2` |
| `data/` | 原始小/大数据集 ZIP 与采集记录模板 |
| `legacy_reference/` | 早期 SPI、采集、24 维分类及仿真参考代码 |
| `scripts/`、`skill/` | 驱动测试、回放向量导出、Overlay 与整数结果检查 |

## 在 PYNQ-Z2 上运行

工程使用 Vivado/Vitis **2026.1**；归档中的历史板端环境为 **PYNQ 3.1.1**、PL 时钟 **100 MHz**。

把 `build/deploy/` 整个目录复制到板卡，例如 `~/jupyter_notebooks/herb_models/`，在该目录执行：

```sh
sh run_on_pynq.sh                    # 定点向量回放
sh run_raw_on_pynq.sh --examples     # 原始记录示例
sh run_raw_on_pynq.sh --all          # 全量原始事件回放
```

也可使用同目录的 `recognition_demo.ipynb`。原始事件回放需要板端 g++、NumPy 和 PYNQ；Notebook 的表格展示还需要 pandas。首次运行会编译 C++ 特征处理库。

`herb_models.bit` 与 `herb_models.hwh` 必须同名且位于同一目录。`herb_models.xsa` 保持在 `hardware_export/` 子目录，避免 PYNQ 3.1.1 加载元数据时发生冲突。

| FPGA 核 | 输入 | 类别 |
| --- | --- | --- |
| `small_classifier` / `small_lr_q` | 50 维，Q16 逻辑回归 | 单味药材 8 类，编号 0–7 |
| `fusion_classifier` / `fusion_q` | 100 维，MOS＋SGP 双支路 Q32 网络 | 组合 10 类，编号 1–10 |

模型需要配套的通道顺序、特征提取和量化参数；ADC 原码不能直接作为上述特征输入。

## 重建 FPGA 工程

建议把仓库克隆到英文短路径，例如 `C:/fpga/herb-pynq`。在 Vivado 2026.1 命令环境进入仓库根目录，按顺序运行：

```sh
vivado -mode batch -source build/create_model_overlay.tcl
vivado -mode batch -source build/implement_models.tcl
```

第一步使用仓库内已导出的 HLS IP，生成 `build/model_overlay/herb_models.xpr`；第二步实现、检查时序并导出 bit/HWH/XSA。`PROJECT_ROOT` 环境变量若已设置，应指向当前仓库根目录。已有生成目录时脚本会停止，可打开现有 XPR 继续，或在新的克隆副本重建。

修改分类器后需重新运行 HLS：在另一份工作副本中先备份 `build/models/`，使用 Vitis 2026.1 命令环境，分别设置 `MODEL=small_lr` 和 `MODEL=fusion_q32` 后执行：

```sh
vitis-run --mode hls --tcl build/build_models.tcl
```

随后重建 Vivado 并重新验证板端结果。生成 IP 内的文件名大小写及 `.dat` 权重文件必须保留。

## 算法预测与训练

建议使用独立的 Python 3.12 环境，依赖版本随原算法工程保存在 `requirements.txt`：

```sh
python -m pip install -r algorithm/small_herb/requirements.txt
python algorithm/small_herb/predict.py --txt algorithm/small_herb/example_event.txt --start-row 11 --format q16
python algorithm/mixture_fusion/src/predict_event.py --csv algorithm/mixture_fusion/data/example_event.csv --onset-seconds 0 --format q32
```

两种入口都需要已知的响应起点。示例来自既有记录，用于检查接口。

从原始数据重新训练：

```sh
python algorithm/small_herb/train.py --archive data/small_raw.zip
python algorithm/mixture_fusion/src/build_dataset.py --archive data/mixture_raw.zip
python algorithm/mixture_fusion/src/train_compare.py
```

训练会更新算法目录中的模型与结果；建议在工作副本中执行。重新训练的模型不会自动替换已有 FPGA 位流，需要成套重新导出参数、生成 IP 和验证。

## 固件与本地检查

使用 Keil MDK 打开 `hardware/firmware/MDK-ARM/robot.uvprojx`；原理图使用嘉立创 EDA 打开 `hardware/schematic/TO6+SGP.eprj2`。固件包含传感器、SPI ADC、温湿度、加热、泵和通信相关代码。

以下检查无需开发板，也不执行综合：

```sh
python scripts/verify_repository.py
python scripts/test_model_driver.py
python skill/test_skills.py
python skill/overlay_check/check_overlay.py build/deploy/herb_models.bit
```

历史记录中的整数回放为 164＋414 组，原始事件的计算结果与参考一致为 570/570。这些是一致性结果，不能等同于独立测试识别率。当前位流演示的是已记录数据到 FPGA 分类的链路；实时传感器接入、自动起点检测及未知/空气拒识仍需继续联调。`legacy_reference/` 的旧 24 维系统不在当前双模型位流中。

工程保留原有厂商版权和许可信息，PYNQ 配置的许可见 `board/PYNQ_LICENSE`。
