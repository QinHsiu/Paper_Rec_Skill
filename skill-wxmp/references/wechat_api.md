# WeChat API · 本 skill 用到的接口

权威文档以微信公众平台为准；此处只列 **skill-wxmp 实际调用** 的端点，便于排障。

| 步骤 | Method | Path | 用途 |
|------|--------|------|------|
| Token | GET | `/cgi-bin/token` | `grant_type=client_credential` + AppID/Secret |
| 永久图片 | POST | `/cgi-bin/material/add_material?type=image` | 封面 → `media_id` |
| 新建草稿 | POST | `/cgi-bin/draft/add` | `articles[]`（title/content/thumb_media_id…） |
| 提交发布 | POST | `/cgi-bin/freepublish/submit` | body: `{ "media_id" }`（可选） |

官方说明：

- [获取 access_token](https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html)
- [新增草稿](https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add.html)
- [发布草稿](https://developers.weixin.qq.com/doc/subscription/api/public/api_freepublish_submit.html)

### 实务约束（Paper_Rec）

- Token 缓存约 7200s；配置 IP 白名单
- `title` ≤32 字；`digest` ≤120 字
- `content` 为 HTML；外链图片会被过滤 → 先走素材上传
- 图文封面需永久素材 `thumb_media_id`，比例约 2.35:1（见 [`covers.md`](covers.md)）
