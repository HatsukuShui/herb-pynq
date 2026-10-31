"""Generate tables, scientific figures and an honest model-comparison report."""
from pathlib import Path
import json,os
ROOT=Path(__file__).resolve().parents[1]
_cache=ROOT/'build/native/matplotlib_cache'
_cache.mkdir(parents=True,exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR',str(_cache))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]; REPORT=ROOT/'report'
NAMES={'traditional':'传统模型联合选型','lda':'LDA','svm':'RBF SVM','extra_trees':'ExtraTrees 树模型',
       'flat_neural':'普通轻量 MLP','dual_neural':'MOS＋SGP 双支路网络','late_fusion':'决策层融合',
       'mos_only':'MOS 单独','sgp4_only':'SGP5–8 单独','sgp8_only':'SGP1–8 单独',
       'early_fusion':'MOS＋SGP5–8 特征拼接','early_all14':'MOS＋SGP1–8 特征拼接'}

def percentage(v):return f'{100*v:.2f}%'

def main():
    s=json.loads((REPORT/'comparison.json').read_text(encoding='utf-8'))
    q=json.loads((REPORT/'quantization.json').read_text(encoding='utf-8'));protocol=json.loads((ROOT/'data/protocol.json').read_text(encoding='utf-8'))
    selections=json.loads((REPORT/'nested_selections.json').read_text(encoding='utf-8'))
    groups=['lda','svm','extra_trees','flat_neural','dual_neural']
    fusion=['mos_only','sgp4_only','sgp8_only','early_fusion','early_all14','late_fusion','dual_neural']
    def table(keys):
        lines=['| 方法 | 按日期嵌套验证 | Macro-F1 | 已选配置跨日期探索 | 文件分组探索 | 反序诊断（10 段） |',
               '| --- | ---: | ---: | ---: | ---: | ---: |']
        for key in keys:
            d=s[key];lines.append('| '+NAMES[key]+' | '+percentage(d['nested']['accuracy'])+' | '+f"{d['nested']['macro_f1']:.4f}"+' | '+percentage(d['fixed_selected_date_exploratory']['accuracy'])+' | '+percentage(d['grouped_file_exploratory']['accuracy'])+' | '+f"{d['reverse_diagnostic']['correct']}/10"+' |')
        return '\n'.join(lines)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11,4.7),layout='constrained'); labels=['LDA','RBF SVM','ExtraTrees','Small MLP','Dual-branch']
    for ax,metric,title,color in zip(axes,['nested','grouped_file_exploratory'],['Primary: nested leave-date-out','Secondary: grouped files (post-selection)'],['#186b8c','#8696a5']):
        values=[100*s[g][metric]['accuracy'] for g in groups]; bars=ax.barh(labels,values,color=color,height=.6);ax.invert_yaxis();ax.set_xlim(0,105);ax.set_xlabel('Accuracy (%)');ax.set_title(title,fontsize=11)
        ax.bar_label(bars,fmt='%.2f',padding=4);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    fig.suptitle('Herb combinations | 400 events, 3 collection dates',fontsize=13)
    fig.savefig(REPORT/'figures/model_comparison.png',dpi=180);plt.close(fig)
    labels=['MOS only','SGP5-8 only','SGP1-8 only','Early MOS + SGP5-8','Early all 14 channels','Late rank fusion','Dual-branch MOS + SGP5-8']
    fig,ax=plt.subplots(figsize=(9.5,5.2),layout='constrained');bars=ax.barh(labels,[100*s[g]['nested']['accuracy'] for g in fusion],color=['#8a9ba8']*5+['#42a5a1','#186b8c'])
    ax.invert_yaxis();ax.set_xlim(0,72);ax.set_xlabel('Nested leave-date-out accuracy (%)');ax.bar_label(bars,fmt='%.2f',padding=5);ax.set_title('Sensor fusion ablation | model choice inside each training fold');ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    fig.savefig(REPORT/'figures/fusion_ablation.png',dpi=180);plt.close(fig)
    matrix=np.asarray(s['dual_neural']['confusion']);fig,ax=plt.subplots(figsize=(7,6),layout='constrained');im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=40)
    for i in range(10):
        for j in range(10):ax.text(j,i,str(matrix[i,j]),ha='center',va='center',color='white' if matrix[i,j]>23 else '#17212b',fontsize=9)
    ax.set_xticks(np.arange(10),np.arange(1,11));ax.set_yticks(np.arange(10),np.arange(1,11));ax.set_xlabel('Predicted class ID');ax.set_ylabel('True class ID');ax.set_title('Dual-branch: nested date validation (239 / 400)');fig.colorbar(im,ax=ax,label='Event count')
    fig.savefig(REPORT/'figures/dual_confusion.png',dpi=180);plt.close(fig)
    # Per-class statistics use out-of-fold predictions only.
    pred=pd.read_csv(REPORT/'predictions.csv');perclass=[]
    for class_id in range(1,11):
        true=pred.class_id.to_numpy()==class_id;chosen=pred.dual_neural_nested.to_numpy()==class_id;tp=np.sum(true&chosen)
        perclass.append(dict(class_id=class_id,total=int(true.sum()),correct=int(tp),recall=float(tp/true.sum()),precision=float(tp/chosen.sum()) if chosen.any() else 0.))
    pd.DataFrame(perclass).to_csv(REPORT/'per_class_dual.csv',index=False,encoding='utf-8-sig')
    date_lines=['| 留出日期 | 双支路内层选定配置 | 正确 / 总数 | 准确率 |','| --- | --- | ---: | ---: |']
    for row in selections['dual_neural']:
        m=row['test'];date_lines.append(f"| {row['held_date']} | {row['selected']} | {m['correct']}/{m['total']} | {percentage(m['accuracy'])} |")
    quant_lines=['| 格式 | 权重与偏置字节数 | tanh 表字节数 | 400 段外层预测保持一致 | 定点外层准确率 | C++ 整数向量一致 |',
                 '| --- | ---: | ---: | ---: | ---: | ---: |']
    for key in ['q32','q16']:
        r=q['formats'][key];quant_lines.append(f"| {key} | {r['weight_bias_bytes']} | {r['tanh_lut_bytes']} | {r['outer400_class_agreement']}/400 | {percentage(r['nested_outer_quantized']['accuracy'])} | {r['host_cpp_integer_vectors_matched']}/414 |")
    text=f'''# 水盛熙：数据、模型对比与量化实验报告

实验日期：2026-10-12。模型均在本项目数据上重新训练；没有载入此前遗留模型或外部预训练权重。传统算法使用标准库实现，新增双支路网络的前向、损失和梯度在 `src/fusion_model.py` 中显式编写，优化器使用 SciPy L-BFGS。

## 结论

按同一套日期隔离的嵌套验证，ExtraTrees 为 **{percentage(s['extra_trees']['nested']['accuracy'])}**，普通轻量网络为 **{percentage(s['flat_neural']['nested']['accuracy'])}**，双支路网络为 **{percentage(s['dual_neural']['nested']['accuracy'])}**。相差几个样本且只有三个日期，不能据此声称某一类方法普遍更好。普通轻量网络是本轮神经网络候选中按选型规则得到的方案；双支路模型作为 MOS＋SGP 融合与硬件联调候选，已提供完整定点实现，其识别效果仍按实测结果报告。

双支路模型文件分组探索达到 **{percentage(s['dual_neural']['grouped_file_exploratory']['accuracy'])}**，该划分允许同一天的数据出现在训练与验证两侧，且配置已由历史数据选出。不能把它当作“任意日期单独放入一种组合”的真实识别率。反序诊断仅 10 段，双支路正确 {s['dual_neural']['reverse_diagnostic']['correct']} 段，仍暴露顺序和实验条件影响。

## 1. 数据整理

原始压缩包 SHA-256：`{protocol['raw_sha256']}`。

55 个顶层 CSV 内容各不相同；内层压缩包的 44 个 CSV 全部与顶层文件重复，没有作为额外样本使用。40 份正常完整记录产生 400 个事件，每类 40 个；1 份反序记录产生 10 个诊断事件。11 份盖帽记录按用户要求排除；3 份标签不明的局部测试记录排除。

普通记录按峰次对应类别 1→10，反序记录按 10→1。标签编号只用于监督标签，不作为模型特征。日期、文件名、峰序号、绝对时间也不作为模型输入。

每段取响应起点前 -8～-3 秒的局部中位数作为参考，起点后 0～35 秒每 0.5 秒计算一个局部中位数，共 71 点。MOS 用 log(读数/参考)，SGP 用 (读数−参考)/参考。每通道提取最大值、最小值、均值、标准差、早期均值、晚期均值、晚期减早期、中段均值、上升斜率、后段斜率。融合网络输入为 MOS1–6 的 60 个统计量，加 SGP5–8 的 40 个统计量。

当前起点由离线检测产生；局部参考值未被确认是洁净空气。不能将这套离线分段直接视为已经完成在线触发识别。完整清单见 `data/file_inventory.csv`、`data/events.csv` 和 `data/protocol.json`。

## 2. 评估协议

- 共 51 个固定候选：7 种共同特征表示 × 6 种常规模型配置，另加 6 个双支路配置和 3 个决策融合权重。
- 外层留出一个完整采集日期，内层只在余下两个日期间选特征和参数；按内层各日期平均准确率、汇总准确率、ID 顺序选型。
- 每次 StandardScaler 只拟合当前训练折。记录及保守批次组不跨训练/验证两侧，400 个正常事件各作为外层验证一次。
- 单独列出 LDA、SVM、ExtraTrees、轻量网络，各自只在本方法允许的候选中选型。传统模型联合选型另列，避免把“选型流程成绩”误当某个固定算法成绩。
- 反序数据不参与拟合或参数选择；它已在本次对话早期被分析，属于诊断集，不称为全新盲测集。
- 最终部署模型用全部 400 个正常事件重训。嵌套分数评估的是选型流程，各外层折可能使用不同配置；并不意味着最后固定权重已在独立数据上取得同一分数。
- 数据和特征已经被本项目反复探索。嵌套验证控制本轮参数选择的偏差，但不能替代独立新日期、随机投放顺序的数据。

## 3. 传统机器学习与轻量网络

{table(groups)}

![模型对比](figures/model_comparison.png)

传统模型联合选型的外层成绩为 {percentage(s['traditional']['nested']['accuracy'])}。它在每个外层折中依据内层成绩在 LDA/SVM/树模型之间做选择；内层选择不稳定，因而可以低于只限定某一算法的流程。不能将此数值写成“所有传统机器学习都只有 49.5%”。联合轻量网络选型为 {percentage(s['all_light_neural']['nested']['accuracy'])}。

`report/candidate_comparison.csv` 保存全部候选的跨日期探索结果；其中同一特征名可以横向比较算法，但该表用于选择，不能作为独立测试榜单。`report/nested_selections.json` 保存每个外层折的选择依据，`report/predictions.csv` 保存逐事件预测。

## 4. MOS＋SGP 融合消融

{table(fusion)}

![融合消融](figures/fusion_ablation.png)

对当前统计特征，双支路为 59.75%，高于 MOS＋SGP5–8 直接拼接的 53.00%，比 SGP5–8 单独的 57.50% 高 2.25 个百分点；但普通网络选择其他 SGP 特征表示时达到 60.75%。因此暂不能证明融合必然优于所有单传感器方案。SGP1–8 和 14 通道全部输入的对照没有更好，更多通道不自动带来更高识别率。

这里的“多模态”限定为 MOS 与 SGP 两类气体传感器的融合；没有图像分支，也没有训练过图像与气味融合模型。

## 5. 双支路各日期与混淆情况

{chr(10).join(date_lines)}

![双支路混淆矩阵](figures/dual_confusion.png)

类别 1～10 的中文映射见 `data/labels.csv`，逐类查全率、精确率见 `report/per_class_dual.csv`。类别本身平衡，但三天样本量不同，因此同时保存按日期分数和合并分数。

## 6. 量化与导出

最终双支路配置 `{q['selected']['id']}`：MOS 60→16、SGP 40→16，拼接后 32→10，共 **1,962 个权重和偏置**。两支路使用 tanh，输出是 10 个 logit，取最大者对应组合。

{chr(10).join(quant_lines)}

上述字节数是数组载荷，不是 Vivado BRAM/DSP 占用；此外 PS 的均值/标准差共占 1,600 字节。q16 使用 16 位输入/权重/隐藏激活、64 位累加、32 位输出；q32 使用 32 位输入/权重/隐藏激活、64 位累加。两者都含 1,025 项 tanh 查表与插值。

每个外层验证折都对其自身训练得到的网络和标准化参数进行量化，再在留出的日期上比对。两种格式均保留 400/400 个预测类别，外层准确率变化为 0 个百分点。最终模型在 410 段已有事件上也保持类别一致；其中 400 段是训练数据，不能解释为新识别准确率。

C++ 还核对了全部 410 段原始事件的特征提取、浮点输出及整数输出，并额外使用全零、最大、最小和交替边界输入，共 414 组整数测试。默认先用 q32 作精度基准，q16 供资源优化对比。具体误差、整数范围证明和逐折结果见 `report/quantization.json`。

## 7. 验证边界与下一步

已完成 Python 实验、参数导出、普通 g++ 编译的 C++ 仿真及命令行推理验证。没有运行 AMD HLS C Simulation、RTL 联合仿真、Vivado 综合/实现，没有生成可用板级 bitstream，也没有板端性能或传感器实时联调数据。

推荐李明溪先用随包向量核对 PL 整数输出，再接 PS 特征提取，最后接实时采集。35 秒响应观察窗口与网络计算耗时是两个指标；即使网络加速，也不能把采集等待时间当作已消除。

为了改善跨日期可靠性，建议首轮补采 3 个新日期 × 10 类 × 每类 5 次，共 150 次独立放入实验；顺序随机且保存真实单次标签，记录配比、质量、批次、温湿度、加热设置、清洁流程和设备参数。冻结现有模型后评估这批数据，再决定是否扩充训练。此为采集建议，尚未执行。

## 方法与工具依据

- [scikit-learn 数据泄漏与预处理说明](https://scikit-learn.org/stable/common_pitfalls.html)：支持仅在训练折拟合预处理参数的做法。
- [AMD HLS](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vitis/vitis-hls.html)：C/RTL 联合仿真与 IP 导出用于后续硬件验证；本机普通 C++ 测试不代替该步骤。
- 赛道范围及 PS＋PL 允许性依据用户上传 AMD 选题指南第 3.3 节。本报告的识别率、参数量及量化结果均来自随包实际实验文件，不来自这些外部文档。
'''
    (REPORT/'algorithm_report.md').write_text(text,encoding='utf-8')
    # A blank prospective log; it is not fabricated experimental data.
    columns=['sample_id','date','session_id','sequence_index','class_id','mass_a_g','mass_b_g','herb_batch_a','herb_batch_b','distance_mm','temperature_c','humidity_pct','heater_setting','baseline_start','placement_time','response_onset','removal_time','cleaning_method','raw_file','operator','notes']
    pd.DataFrame(columns=columns).to_csv(ROOT/'data/new_collection_template.csv',index=False,encoding='utf-8-sig')
    print('Report and three figures generated from saved experiment evidence.')

if __name__=='__main__':main()
