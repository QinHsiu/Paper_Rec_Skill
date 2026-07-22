# 宣传物料使用说明

以「熟练研二」视角：一套可复述流程 + 实机截图 + 走查视频 + 口播字幕。

## 研究生流程（对外叙事）

```text
检索入库 → 双栏研读挂证据 → 主线 Delta/缺口 → 实验硬闸 → 诚信草稿导出
```

完整口播、分镜、时长见 [`GRAD_DEMO_PLAYBOOK.md`](GRAD_DEMO_PLAYBOOK.md)。

## 已产出文件

| 路径 | 用途 |
|:---|:---|
| `shots/01-home.png` | README / 首屏海报 |
| `shots/02-pages.png` | 论文库 |
| `shots/03-read-dual.png` | **核心差异化**：双栏研读 |
| `shots/04-thread.png` | 研究主线 |
| `shots/05-experiments.png` | 实验看板 |
| `shots/06-ask.png` | 智能研读 |
| `shots/07-endcard.png` | 片尾卡 |
| `shots/00-hero-concept.png` | 概念海报（非实机） |
| `out/paper-rec-grad-demo.mp4` | **含中文旁白**（默认 Xiaoxiao 神经女声，分段韵律） |
| `out/narration.zh.mp3` | 旁白音轨 |
| `add_narration.py` | 重合成：`--engine edge`（免费）或 `--engine openai`（需自备 Key，`tts-1-hd`） |
| `out/paper-rec-grad-demo.webm` | 实机走查（无声，可另叠旁白） |
| `out/paper-rec-grad-demo.gif` | 预览动图 |
| `out/narration.zh.srt` | 中文口播字幕（叠到精修片） |

## 重新采集

```powershell
# Wiki 已在 :5173 / :8787
node docs/promo/capture_promo.mjs
python docs/promo/make_slideshow.py
```

## 发布建议（研究生口吻）

1. **朋友圈 / 推文**：`01-home` + `03-read-dual` + 一句「摘录挂主线，实验过硬闸」
2. **B 站**：用 OBS 按 Playbook 实机重录 90s（光标放大），叠 `narration.zh.srt`，片尾 `07-endcard` 3s
3. **组会安利**：现场点七步，2–3 分钟，不念广告词

### OBS 精修清单（推荐）

- 画布 1920×1080；浏览器仅留 Wiki 窗口
- 光标放大 150%；勿露 API Key / 真实邮箱
- 示例主线：`mm-llm-alignment`
- 旁白：直接念 Playbook「90 秒口播稿」
