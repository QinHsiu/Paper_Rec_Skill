#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper_Rec skill-wxmp — WeChat draft publisher (token, draft CRUD, publish).

Official API: https://developers.weixin.qq.com/doc/subscription/api/draftbox/
"""

import json
import requests
import os
from typing import Dict, List, Optional, Any
from markdown_formatter import WeChatMarkdownFormatter
from upload_material import WeChatMaterialUploader
from ai_cover_generator import AICoverGenerator, get_modelscope_api_key


def _scripts_dir() -> str:
    """skill-wxmp/scripts/ (this file's folder)."""
    return os.path.dirname(os.path.abspath(__file__))


def _skill_root() -> str:
    """skill-wxmp package root."""
    return os.path.abspath(os.path.join(_scripts_dir(), ".."))


def resolve_accounts_config_path() -> str:
    """
    Resolve wxmp_accounts.json path.

    Priority:
      1. env WXMP_ACCOUNTS_JSON
      2. cwd/wxmp_accounts.json
      3. skill-wxmp/scripts/wxmp_accounts.json
    """
    env_path = os.environ.get("WXMP_ACCOUNTS_JSON")
    if env_path and os.path.exists(env_path):
        return env_path
    cwd_path = os.path.join(os.getcwd(), "wxmp_accounts.json")
    if os.path.exists(cwd_path):
        return cwd_path
    skill_path = os.path.join(_scripts_dir(), "wxmp_accounts.json")
    return skill_path


def load_account_config(account_name: Optional[str] = None) -> Dict:
    """
    从配置文件加载公众号配置

    Args:
        account_name: 公众号名称，如果为 None 则使用默认公众号

    Returns:
        包含 app_id, app_secret, modelscope_api_key 的字典

    Raises:
        ValueError: 如果配置文件不存在或公众号不存在
    """
    config_file = resolve_accounts_config_path()
    if not os.path.exists(config_file):
        example = os.path.join(_scripts_dir(), "wxmp_accounts_example.json")
        raise ValueError(
            f"配置文件不存在: {config_file}\n"
            f"请先创建配置文件：\n"
            f"  方式1: python skill-wxmp/scripts/config_manager.py add <名称> <AppID> <AppSecret>\n"
            f"  方式2: 复制 {example} → wxmp_accounts.json 并填写\n"
            f"  或设置环境变量 WXMP_ACCOUNTS_JSON=/path/to/wxmp_accounts.json"
        )

    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 如果未指定公众号名称，使用默认公众号
    if account_name is None:
        account_name = config.get("default_account")
        if not account_name:
            raise ValueError(
                "未指定公众号名称，且配置文件中也没有设置默认公众号\n"
                "请：\n"
                "  1. 使用 config_manager.py set_default <名称> 设置默认公众号\n"
                "  2. 或在运行时指定公众号名称"
            )

    accounts = config.get("accounts", {})
    if account_name not in accounts:
        available = ", ".join(accounts.keys())
        raise ValueError(
            f"公众号 '{account_name}' 不存在\n"
            f"可用的公众号: {available}"
        )

    return accounts[account_name]


def decode_unicode_string(s: str) -> str:
    """
    将 Unicode 转义的字符串转换为中文
    只处理真正的 Unicode 转义序列，不影响已经是中文的字符串

    Args:
        s: 可能包含 Unicode 转义的字符串，如 "\\u5fae\\u4fe1\\u516c\\u4f17\\u53f7"

    Returns:
        转换后的中文字符串
    """
    # 检查字符串是否包含 Unicode 转义序列
    if '\\u' not in s:
        return s

    # 检查是否是字面的 Unicode 转义（只包含 ASCII 和 \u）
    # 如果字符串中包含非 ASCII 字符（已经是中文），则不需要解码
    try:
        # 尝试编码为 ASCII，如果成功说明全是 ASCII 字符（可能有 \u 转义）
        s.encode('ascii')
        # 只包含 ASCII，可能包含 Unicode 转义，需要解码
    except UnicodeEncodeError:
        # 包含非 ASCII 字符（已经是中文），不需要解码
        return s

    # 处理双反斜杠的情况（如 "\\\\u5fae"）
    if '\\\\u' in s:
        s = s.replace('\\\\u', '\\u')

    # 解码 Unicode 转义序列
    try:
        decoded = s.encode('utf-8').decode('unicode-escape')
        return decoded
    except (UnicodeDecodeError, UnicodeEncodeError):
        # 如果解码失败，直接返回原字符串
        return s


class WeChatDraftPublisher:
    """微信公众号草稿发布器"""

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None,
                 ai_api_key: Optional[str] = None, account_name: Optional[str] = None):
        """
        初始化草稿发布器

        支持两种初始化方式：
        1. 直接传递 app_id 和 app_secret
        2. 通过 account_name 从配置文件加载

        Args:
            app_id: 微信公众号 AppID（可选）
            app_secret: 微信公众号 AppSecret（可选）
            ai_api_key: ModelScope API Key（可选，用于自动生成配图）
                     如果不提供，将从环境变量 MODELSCOPE_API_KEY 获取
            account_name: 公众号名称（可选），如果提供则从配置文件加载
        """
        # 如果提供了 account_name，从配置文件加载
        if account_name:
            config = load_account_config(account_name)
            self.app_id = config['app_id']
            self.app_secret = config['app_secret']
            # 如果配置中有 modelscope_api_key，使用配置的；否则使用参数或环境变量
            config_ai_key = config.get('modelscope_api_key')
            if config_ai_key:
                self.ai_api_key = config_ai_key
            else:
                self.ai_api_key = ai_api_key
        else:
            # 直接使用提供的参数
            if not app_id or not app_secret:
                raise ValueError(
                    "必须提供 app_id 和 app_secret，或提供 account_name 从配置文件加载"
                )
            self.app_id = app_id
            self.app_secret = app_secret
            self.ai_api_key = ai_api_key

        self.access_token = None
        self.api_base = "https://api.weixin.qq.com/cgi-bin"
        self.material_uploader = WeChatMaterialUploader(self.app_id, self.app_secret)

        # 初始化 AI 配图生成器
        if self.ai_api_key:
            self.cover_generator = AICoverGenerator(self.ai_api_key)
        else:
            # 尝试从环境变量获取
            try:
                self.cover_generator = AICoverGenerator()
            except ValueError:
                # 环境变量中也没有 API Key，不使用自动配图功能
                self.cover_generator = None

    def get_access_token(self) -> str:
        """
        获取 access_token

        Returns:
            access_token 字符串
        """
        url = f"{self.api_base}/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        response = requests.get(url, params=params)
        result = response.json()

        if "access_token" not in result:
            raise Exception(f"获取 access_token 失败: {result}")

        self.access_token = result["access_token"]
        return self.access_token

    def _use_default_cover(self) -> str:
        """
        使用默认封面图片

        Returns:
            默认封面的 media_id

        Raises:
            ValueError: 如果默认图片不存在或上传失败
        """
        default_cover_paths = [
            os.path.join(_skill_root(), "assets", "default_cover.jpg"),
            os.path.join(os.getcwd(), "assets", "default_cover.jpg"),
            "assets/default_cover.jpg",
        ]

        # 查找默认封面图片
        default_cover = None
        for path in default_cover_paths:
            if os.path.exists(path):
                default_cover = path
                break

        if not default_cover:
            raise ValueError(
                "未找到默认封面图片。\n"
                "请放置于 skill-wxmp/assets/default_cover.jpg，"
                "或提供 thumb_media_id / 配置 MODELSCOPE_API_KEY 自动配图。"
            )

        print(f"使用默认封面图片: {default_cover}")

        # 上传默认封面到素材库
        try:
            upload_result = self.material_uploader.upload_image(default_cover)
            media_id = upload_result.get('media_id')
            print(f"默认封面图片上传成功，media_id: {media_id}")
            return media_id
        except Exception as e:
            raise ValueError(f"上传默认封面失败: {e}")

    def add_draft(self, articles: List[Dict], format_markdown: bool = False,
                  auto_generate_cover: bool = False) -> Dict:
        """
        新建草稿

        Args:
            articles: 文章列表，每篇文章包含:
                - title: 文章标题（必填）
                - content: 文章内容，支持 HTML 标签或 Markdown（必填）
                - thumb_media_id: 封面图片的 media_id（可选，未提供时可自动生成）
                - author: 作者
                - digest: 摘要
                - show_cover_pic: 是否显示封面，0为不显示，1为显示
                - need_open_comment: 是否打开评论，0不打开，1打开
                - only_fans_can_comment: 是否只有粉丝可以评论，0所有人可评论，1粉丝可评论
                - content_type: 内容类型，'html' 或 'markdown'（默认 'html'）
            format_markdown: 是否格式化 Markdown 内容（仅当 content_type 为 'markdown' 时有效）
            auto_generate_cover: 是否自动生成封面图片（需要提供 ai_api_key）

        Returns:
            创建结果，包含 media_id
        """
        if not self.access_token:
            self.get_access_token()

        url = f"{self.api_base}/draft/add?access_token={self.access_token}"

        # Markdown 格式化器
        formatter = WeChatMarkdownFormatter()

        # 解码所有字符串中的 Unicode 转义
        processed_articles = []
        for article in articles:
            processed_article = {}
            content_type = article.get('content_type', 'html').lower()

            # 自动生成封面图片
            thumb_media_id = article.get('thumb_media_id')

            if not thumb_media_id and auto_generate_cover:
                # 尝试使用 AI 生成封面
                if self.cover_generator:
                    print("正在自动生成封面图片...")
                    title = article.get('title', '')
                    content = article.get('content', '')

                    if title and content:
                        # 生成临时图片路径
                        temp_cover_path = f"temp_cover_{hash(title)}.jpg"

                        # 生成配图
                        cover_result = self.cover_generator.generate_cover(
                            title, content, temp_cover_path
                        )

                        if cover_result:
                            try:
                                # 上传配图到微信素材库
                                print("正在上传封面图片到微信素材库...")
                                upload_result = self.material_uploader.upload_image(cover_result)
                                thumb_media_id = upload_result.get('media_id')
                                print(f"封面图片上传成功，media_id: {thumb_media_id}")

                                # 删除临时图片
                                os.remove(cover_result)
                            except Exception as e:
                                print(f"上传封面图片失败: {e}")
                                if os.path.exists(cover_result):
                                    os.remove(cover_result)
                        else:
                            print("封面图片生成失败")
                else:
                    # 未配置 AI，使用默认图片
                    print("未配置 ModelScope API Key，使用默认封面图片...")
                    thumb_media_id = self._use_default_cover()

            # 检查是否有封面图片
            if not thumb_media_id:
                raise ValueError("必须提供 thumb_media_id 或启用自动生成封面（auto_generate_cover=True）")

            for key, value in article.items():
                if isinstance(value, str):
                    # 解码 Unicode 转义为中文字符
                    decoded_value = decode_unicode_string(value)

                    # 处理 Markdown 格式化
                    if key == 'content' and content_type == 'markdown':
                        if format_markdown:
                            # 格式化 Markdown 并转换为 HTML
                            decoded_value = formatter.format_to_wechat_html(decoded_value)
                        else:
                            # 仅转换 Markdown 为 HTML，不格式化
                            decoded_value = formatter.format_to_wechat_html(decoded_value)

                    processed_article[key] = decoded_value
                else:
                    processed_article[key] = value

            # 确保使用生成的或提供的 thumb_media_id
            processed_article['thumb_media_id'] = thumb_media_id

            # 移除 content_type 字段（不需要发送到微信）
            if 'content_type' in processed_article:
                del processed_article['content_type']

            processed_articles.append(processed_article)

        data = {
            "articles": processed_articles
        }

        # 发送请求时使用 ensure_ascii=False 保持中文字符
        response = requests.post(url, data=json.dumps(data, ensure_ascii=False),
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
        result = response.json()

        # 微信 API 成功时可能没有 errcode 字段，或有 errcode: 0
        if result.get("errcode", 0) != 0:
            raise Exception(f"新建草稿失败: {result}")

        # 检查是否返回了必需的字段
        if "media_id" not in result:
            raise Exception(f"新建草稿返回数据异常: {result}")

        return result

    def update_draft(self, media_id: str, index: int = 0, article: Optional[Dict] = None,
                     articles: Optional[List[Dict]] = None) -> Dict:
        """
        更新草稿

        Args:
            media_id: 草稿的 media_id
            index: 要更新的文章在图文消息中的位置（从0开始），多图文消息时有效
            article: 要更新的文章内容
            articles: 完整的图文消息列表（与 article 二选一）

        Returns:
            更新结果
        """
        if not self.access_token:
            self.get_access_token()

        url = f"{self.api_base}/draft/update?access_token={self.access_token}"

        data = {
            "media_id": media_id,
            "index": index
        }

        if article:
            data["article"] = article
        elif articles:
            data["articles"] = articles

        # 发送请求时使用 ensure_ascii=False 保持中文字符
        response = requests.post(url, data=json.dumps(data, ensure_ascii=False),
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
        result = response.json()

        # 微信 API 成功时可能没有 errcode 字段，或有 errcode: 0
        if result.get("errcode", 0) != 0:
            raise Exception(f"更新草稿失败: {result}")

        return result

    def publish_draft(self, media_id: str) -> Dict:
        """
        发布草稿

        Args:
            media_id: 草稿的 media_id

        Returns:
            发布结果，包含 publish_id
        """
        if not self.access_token:
            self.get_access_token()

        url = f"{self.api_base}/freepublish/submit?access_token={self.access_token}"

        data = {
            "media_id": media_id
        }

        # 发送请求时使用 ensure_ascii=False 保持中文字符
        response = requests.post(url, data=json.dumps(data, ensure_ascii=False),
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
        result = response.json()

        # 微信 API 成功时可能没有 errcode 字段，或有 errcode: 0
        if result.get("errcode", 0) != 0:
            raise Exception(f"发布草稿失败: {result}")

        # 检查是否返回了必需的字段
        if "publish_id" not in result:
            raise Exception(f"发布草稿返回数据异常: {result}")

        return result

    def get_publish_status(self, publish_id: str) -> Dict:
        """
        查询发布状态

        Args:
            publish_id: 发布任务 ID

        Returns:
            发布状态信息
        """
        if not self.access_token:
            self.get_access_token()

        url = f"{self.api_base}/freepublish/get?access_token={self.access_token}"

        data = {
            "publish_id": publish_id
        }

        # 发送请求时使用 ensure_ascii=False 保持中文字符
        response = requests.post(url, data=json.dumps(data, ensure_ascii=False),
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
        result = response.json()

        if result.get("errcode") != 0:
            raise Exception(f"查询发布状态失败: {result}")

        return result

    def delete_draft(self, media_id: str) -> Dict:
        """
        删除草稿

        Args:
            media_id: 草稿的 media_id

        Returns:
            删除结果
        """
        if not self.access_token:
            self.get_access_token()

        url = f"{self.api_base}/draft/delete?access_token={self.access_token}"

        data = {
            "media_id": media_id
        }

        # 发送请求时使用 ensure_ascii=False 保持中文字符
        response = requests.post(url, data=json.dumps(data, ensure_ascii=False),
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
        result = response.json()

        # 微信 API 成功时可能没有 errcode 字段，或有 errcode: 0
        if result.get("errcode", 0) != 0:
            raise Exception(f"删除草稿失败: {result}")

        return result


if __name__ == "__main__":
    # 示例用法
    import sys
    import os

    if len(sys.argv) < 3:
        print("用法: python publish_draft.py <APPID> <APPSECRET> <操作> [参数...]")
        print("操作:")
        print("  create <thumb_media_id> <标题> <内容文件>")
        print("  publish <media_id>")
        print("  status <publish_id>")
        print("  delete <media_id>")
        sys.exit(1)

    app_id = sys.argv[1]
    app_secret = sys.argv[2]
    operation = sys.argv[3]

    publisher = WeChatDraftPublisher(app_id, app_secret)

    try:
        if operation == "create":
            if len(sys.argv) < 6:
                print("创建草稿需要: thumb_media_id 标题 内容文件")
                sys.exit(1)

            thumb_media_id = sys.argv[4]
            title = sys.argv[5]
            content_file = sys.argv[6]

            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read()

            article = {
                "title": title,
                "content": content,
                "thumb_media_id": thumb_media_id,
                "show_cover_pic": 1,
                "need_open_comment": 1,
                "only_fans_can_comment": 0
            }

            result = publisher.add_draft([article])
            print(f"草稿创建成功! media_id: {result['media_id']}")

        elif operation == "publish":
            if len(sys.argv) < 5:
                print("发布草稿需要: media_id")
                sys.exit(1)

            media_id = sys.argv[4]
            result = publisher.publish_draft(media_id)
            print(f"草稿发布成功! publish_id: {result['publish_id']}")

        elif operation == "status":
            if len(sys.argv) < 5:
                print("查询状态需要: publish_id")
                sys.exit(1)

            publish_id = sys.argv[4]
            result = publisher.get_publish_status(publish_id)
            print(f"发布状态: {json.dumps(result, indent=2, ensure_ascii=False)}")

        elif operation == "delete":
            if len(sys.argv) < 5:
                print("删除草稿需要: media_id")
                sys.exit(1)

            media_id = sys.argv[4]
            result = publisher.delete_draft(media_id)
            print("草稿删除成功!")

        else:
            print(f"未知操作: {operation}")
            sys.exit(1)

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
