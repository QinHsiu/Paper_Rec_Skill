# Plot_Draw（中文）

`/draw` 专用画图 Skill：输入**数据路径 + 文字描述**，可指定图类型；未指定时由 `lib.select_chart` 自动选择。

**实现全部在 [`lib/`](lib/)**，不依赖仓库外的 `plot_demo` / `../` 接入。

```bash
cd skill-draw
pip install -r requirements.txt
python -m lib.cli --data <json|csv> --desc "..." --out <stem>
```

详见 [SKILL.md](SKILL.md) · [chart-catalog.md](chart-catalog.md)。
