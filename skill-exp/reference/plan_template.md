# Solution Plan Template / 方案模板（数据侧 · 模型侧 · 训练侧）

Every `content/exp/<id>/plans/P*.md` **must** follow this skeleton.  
Order: **先证据与结论，再给可执行调整**；三侧都要写——若本方案某侧无动作，写 `N/A — 本方案不涉及` 并说明原因。

配套代码：`reference/plan_template.py` → `render_full_plan_md`。

---

## Skeleton（复制即用）

```markdown
# <plan_id> — <一句话假设>

## 0. 诊断摘要
- symptom: `<overfitting|long_tail|…>`
- special_question: …
- evidence: （数字 / 路径，禁止空口）
- figures: `content/exp/<id>/figures/…`（用 `/draw` 产出）
- source: `tricks:…` / boards / …

## 1. 数据侧（Data）
### 1.1 现象
- 观察到什么（分布、缺失、噪声、难子集占比…）

### 1.2 可视化（必填若涉及分布/不均衡/曲线）
- chart: bar / multi_bar / violin / heatmap / …
- command or path: `/draw …` → `figures/xxx.png`
- 读图结论: …

### 1.3 结论
- 用 1–3 句说清「所以数据上必须改什么」

### 1.4 调整方案（可执行）
| 步骤 | 操作 | 对象/比例/规则 | 预期 |
|------|------|----------------|------|
| D1 | | | |
| D2 | | | |

### 1.5 Mini-verify（数据）— **验证本方案，看目标子集**
- **验证对象**: 本方案的数据/标签动作（不是全量训练）
- **target_subset / probe**: 来自 badcase 簇，例如 `handwritten_pinyin`（须与 special_question 对齐）
- **协议**: 子集上 before → 应用方案 → after；主指标 = `target_score.metric`
- **明显收益**: 子集 Δ ≥ `max(0.25×expected_gain, min_clear_gain)`（默认 min_clear_gain=0.01）
- **护栏**: 可选测 `{metric}_global`；跌幅不得超过 `global_max_drop`（默认 0.02）
- **失败**: revise 方案后再测；禁止「子集无收益却开全量训」

示例：方案「Qwen 清洗 OCR 标签」→ probe=`handwritten_pinyin` → 清洗前后子集 F1 须明显↑。

## 2. 模型侧（Model）
### 2.1 是否需要选型
- yes/no + 角色: `clean_closed` / `clean_open` / `train_base` / `distill_*`

### 2.2 榜单与短名单（需要时）
- boards + date: …
- 对比表（≥3 候选）:

| candidate | open/closed | size | key scores | VRAM/cost | decision |
|-----------|-------------|------|------------|-----------|----------|
| | | | | | |

### 2.3 家族下钻（若已定家族如 Qwen）
- ≥3 开源变体对比 → primary / backup
- 结论: …

### 2.4 Mini-verify（模型）
- 验证对象: 选定教师/基座在本方案中的用法（如 Qwen 作 `clean_open`）
- target_subset: 与数据侧同一难子集（或声明不同子集的理由）
- 小切片可用性 + **子集主指标明显收益**（标准同 §1.5）
- 失败则换 primary/backup，不得直接全量

## 3. 训练侧（Train）
### 3.1 现象 / 动机
- 与数据·模型结论如何衔接（如不均衡 → 加权 loss）

### 3.2 训练配方调整
| 步骤 | 项 | 原值 → 新值 | 理由 |
|------|----|-------------|------|
| T1 | loss / sampler / lr / epoch / … | | |

### 3.3 监控与出图
- 曲线: train_loss / val_* → `/draw line` → `figures/…`
- early-stop / 异常信号: …

### 3.4 Mini-verify（训练）
- 验证对象: 本方案的训练配方 diff（短训），不是最终长训
- 短训步数 + **target_subset** 指标 before/after
- 成功标准: 同 §1.5「明显收益」+ 曲线无爆炸/NaN
- 通过后再 `/exp_training` 全量

## 4. 预期收益与风险
- expected_gain vs `target_score`: …
- cost / risk: …
- 回滚条件: …

## 5. 执行顺序（推荐）
1. 数据侧 D* → mini-verify
2. 模型侧锁定（若需要）→ mini-verify
3. 训练侧 T* → mini-verify → 全量 `/exp_training`
```

---

## 填写规则

| 侧 | 必须回答 | 典型产出 |
|----|----------|----------|
| **数据侧** | 现象→图→结论→**比例/增删改规则** | 重采样表、清洗规则、难例扩增清单 |
| **模型侧** | 是否换模；换则榜单+对比表 | primary/backup 模型 id |
| **训练侧** | loss/采样/LR/正则/时长等可执行变更 | 超参 diff + 监控图路径 |

- 可视化优先 `/draw`（`skill-draw/lib`），路径写进方案。  
- 数字须来自分析或榜单快照；未知标 `TBD` 并列出待测项。  
- 多方案时每个 `P*` 各自一份完整三侧模板（可引用同一张分布图）。

---

## 示例：长尾 / 样本不均衡 → 调训练集比例

```markdown
# P2 — [long_tail] 重采样稀有类并配合加权 loss

## 0. 诊断摘要
- symptom: `long_tail`
- special_question: 为何稀有类 F1 远低于头部类？
- evidence: train 类分布 head:tail ≈ 18:1；badcase 中稀有类占 42%
- figures: `content/exp/demo/figures/label_dist.png`（`/draw bar`）
- source: `tricks:long_tail#resample`

## 1. 数据侧（Data）
### 1.1 现象
- 训练集类别严重不均；稀有类在验证 badcase 中过表示。

### 1.2 可视化
- chart: `bar`（各类样本数）+ 可选 `multi_bar`（train vs val 占比）
- path: `figures/label_dist.png`
- 读图结论: 头部 3 类占 80%+，尾部 5 类合计 <8%。

### 1.3 结论
- **必须调整训练集比例**（或等价采样），不能只调模型；否则尾类梯度不足。

### 1.4 调整方案
| 步骤 | 操作 | 对象/比例/规则 | 预期 |
|------|------|----------------|------|
| D1 | 稀有类过采样 | 尾类每类上采样至头部中位数的 40%（或 class-balanced sampler） | 尾类 epoch 内见样次数↑ |
| D2 | 难例挖掘 | 从 badcase 稀有类簇增补 / 合成 ×2 | 覆盖失败模式 |
| D3 | 头部降采样（可选） | 头部每类最多不超过中位数 ×3 | 缓解极端偏斜 |

### 1.5 Mini-verify（数据）
- target_subset: 稀有类 / long-tail 簇（非全量集）
- probe: 固定 2k 子集，按新采样器抽 1 epoch 统计类频 + 子集主指标
- 明显收益: 尾类有效曝光 ≥ 原 3× **且** 子集 F1/召回 Δ 达 `min_clear_gain`；`F1_global` 跌幅 ≤ `global_max_drop`

## 2. 模型侧（Model）
### 2.1 是否需要选型
- 本轮 **否**（沿用当前基座）；若清洗标签再开 `clean_*`
### 2.2–2.4
- N/A — 本方案不涉及换模

## 3. 训练侧（Train）
### 3.1 动机
- 采样之外，用 class-balanced / focal 稳住尾类梯度。

### 3.2 训练配方调整
| 步骤 | 项 | 原值 → 新值 | 理由 |
|------|----|-------------|------|
| T1 | loss | CE → focal(γ=2) 或加权 CE | 对齐 long_tail |
| T2 | sampler | random → class-balanced | 与 D1 一致 |
| T3 | early-stop | 盯 val macro-F1 | 避免只涨 micro |

### 3.3 监控与出图
- `/draw line` → `figures/curves_rebalance.png`（train_loss + val_macro_F1）

### 3.4 Mini-verify（训练）
- 短训 1–2k steps；成功: val 稀有类 F1↑ 且头部 F1 降幅 ≤ ε

## 4. 预期收益与风险
- expected_gain: macro-F1 +0.02～0.05（待 probe）
- risk: 分布偏移；过度上采样噪声
- 回滚: 恢复原 sampler + CE

## 5. 执行顺序
1. D1–D3 → 数据 mini-verify
2. T1–T3 短训 → 训练 mini-verify
3. 通过后全量 `/exp_training`

## 6. Claim 绑定（可选 · AI-Research-SKILLs）
若存在研究主线 / thread claims，补全：

```markdown
## Claims
### C01
- Statement: …
- Falsification: 若子集指标不升 / 全局跌超 ε → 否证
- Proof: [E…] 或本方案 mini-verify 路径

## Experiments
### E01
- Verifies: C01
- Setup / Procedure / Expected: （方向性即可）
```

规则：每个 `C*` 至少有一个 `E*`；每个 `E*` 必须声明 `Verifies`。`/exp_eval` 后做一次绑定检查（未绑定 → 记入 gaps，勿自动改 claim status）。
```

---

## 与其它模块的关系

| 产出 | 模板位置 |
|------|----------|
| 分析报告总览 | `output-template.md` § A（可只列计划摘要表） |
| 单方案正文 | 本文件 / `plans/P*.md` |
| 模型榜单对比 | §2 + `model_leaderboards.md` |
| 出图 | `/draw` → §1.2 / §3.3 |
