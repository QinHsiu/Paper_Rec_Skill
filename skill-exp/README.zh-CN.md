# Exp_Sandbox（中文说明）

面向通用 Agent 的**自动化实验沙箱**技能：分析数据与 badcase → 生成多套方案 → 小规模验证 → 训练监控 → 评估达标 → 自循环迭代。

可挂载于 Claude Code、Codex、OpenClaw 等平台。实验结束可用 `wiki_bridge sync-exp --thread <id>` 挂到研究主线。

---

## 命令

| 命令 | 说明 |
|------|------|
| `/exp_analysis` | 分析模式 |
| `/exp_analysis train` 或 `/analysis train` | 训练数据分析 |
| `/exp_analysis eval` 或 `/analysis eval` | 测试集 / 评估集分析 |
| `/exp_training` | 启动训练并监控 loss、验证指标与曲线 |
| `/exp_eval` | 验证模式，输出评估指标并对照 `target_score` |
| `/exp_loop` | 自循环：`analysis([plan])_clean_validation_training_evaluation_next-step` |

---

## 运行上下文（尽量在首条消息给出）

- **target_score**：在什么任务、什么测试集、达到什么指标  
- **tool/function**：闭源模型账号、开源模型入口、数据访问、训练服务器接入与资源说明  
- **analysis_tool?**：若无，则用默认统计/可视化（图尺寸分辨率、音频时长采样率、文本长度与标签分布等）  
- **other_source_model**：可补充 Papers With Code、Hugging Face 公开结果、Wiki 论文笔记中的方法  

---

## 核心流程摘要

1. **badcase → 聚类（保多样性）→ 具体问题 → 多方案**  
2. **方案落盘 → 数据/标签清洗（增删改插 / 重标）→ 小规模验证**  
3. **训练：loss + 验证指标 + 多曲线可视化**  
4. **达标或无更优方案 → final 实验记录、方案结果、后续优化建议**

详情见 [SKILL.md](SKILL.md)、参考伪代码 [`reference/`](reference/)、模板 [output-template.md](output-template.md)、示例 [examples.md](examples.md)。

---

## 安装

```bash
mkdir -p .agents/skills/exp-sandbox
cp -r ./* .agents/skills/exp-sandbox/
```

---

## 借鉴说明

思路借鉴 [zjunlp/predict-before-execute](https://github.com/zjunlp/predict-before-execute)（Predict-then-Verify / FOREAGENT）：先对多方案做偏好排序与小规模验证，再投入全量训练，以降低无效执行成本。本技能为独立指令包，不包含该仓库代码。完整说明与引用见 [README.md § Acknowledgement](README.md#acknowledgement--借鉴说明)。
