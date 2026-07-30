# Cover images · 封面

微信图文封面常用 **900 × 383**（约 2.35:1），JPG/PNG，建议 <2MB。

## 本 skill 行为

`upload_material.py` / `image_processor.py` 会在上传前尝试中心裁剪到 900×383。

| 来源 | 何时 |
|------|------|
| `--thumb-media-id` | 已有永久素材 |
| ModelScope | 设置了 `MODELSCOPE_API_KEY` 且 `--auto-cover` |
| `assets/default_cover.jpg` | 无 AI key 时的降级封面 |

## 错误码 53402（封面裁剪失败）

含义：服务端裁剪参数/尺寸不合规。处理：

```powershell
python skill-wxmp/scripts/image_processor.py input.jpg cover.jpg
python skill-wxmp/scripts/upload_material.py <AppID> <AppSecret> image cover.jpg
```

或换一张接近 2.35:1 的图再 `--auto-cover`。
