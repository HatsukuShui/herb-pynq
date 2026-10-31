# PYNQ-Z2 双模型整数回放

板卡必须为 PYNQ-Z2（xc7z020clg400-1），使用能正常启动的 PYNQ 系统。

将本目录复制到板卡；必须保持 herb_models.bit 和 herb_models.hwh 同目录、同名。执行：

```bash
sh run_on_pynq.sh
```

2026-10-15 已在用户的 PYNQ-Z2 / PYNQ 3.1.1 上验证：small_lr 164 组、fusion_q32 414 组全部通过，全部得分与类别一致。任一不符会立即报错；超时后重新加载 Overlay 再试。

hardware_export/herb_models.xsa 供 Vitis 硬件平台使用。不要将同名 XSA 放到 bit/HWH 同目录：PYNQ 3.1.1 会因此选错元数据加载路径。run_on_pynq.sh 指定 PYNQ 专用 Python 及 XILINX_XRT=/usr，避免 sudo 丢失环境。manifest.json 用于文件完整性核对。

本包只验证量化特征到分类输出。不是传感器实时识别程序。小模型为单味药材逻辑回归（50维）；大模型为组合药材 MOS+SGP 双支路 Q32 网络（100维）。原始数据必须由各自交付包的 PS 特征提取和标准化函数处理，不能直接传入 ADC 码值或原工程的24维特征。

模型训练材料来自水盛熙 2026-10-13 总交付包。硬件工程在 Vivado/Vitis 2026.1 构建，目标100 MHz。详细报告位于主工程 report/model_integration_status.md。
