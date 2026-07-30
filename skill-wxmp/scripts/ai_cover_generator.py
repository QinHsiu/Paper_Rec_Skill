#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paper_Rec skill-wxmp — optional ModelScope cover generation."""

import requests
import time
import json
import re
import os
from PIL import Image
from io import BytesIO
from typing import Optional


def get_modelscope_api_key() -> str:
    """
    获取 ModelScope API Key
    
    优先级：
    1. 环境变量 MODELSCOPE_API_KEY
    2. 环境变量 MODELScope_API_KEY (兼容大小写)
    3. 默认值（用于测试，不建议在生产环境使用）
    
    Returns:
        API Key 字符串
        
    Raises:
        ValueError: 如果没有找到有效的 API Key
    """
    # 尝试从环境变量获取
    api_key = (
        os.getenv('MODELSCOPE_API_KEY') or 
        os.getenv('modelscope_api_key') or
        os.getenv('MODELSCOPE_API_KEY')
    )
    
    if not api_key:
        raise ValueError(
            "未找到 ModelScope API Key！\n"
            "请设置环境变量 MODELSCOPE_API_KEY：\n"
            "  方式1: export MODELSCOPE_API_KEY='your-api-key'\n"
            "  方式2: 在运行时传递 API_KEY 参数\n"
            "  方式3: 创建 .env 文件并添加: MODELSCOPE_API_KEY=your-api-key\n"
            "\n"
            "获取 API Key: https://www.modelscope.cn/my/myaccesstoken"
        )
    
    return api_key


class AICoverGenerator:
    """AI 配图生成器"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化配图生成器

        Args:
            api_key: ModelScope API Key，如果不提供则从环境变量获取
        
        Raises:
            ValueError: 如果没有提供 API Key 且环境变量中也未找到
        """
        self.api_key = api_key or get_modelscope_api_key()
        self.base_url = 'https://api-inference.modelscope.cn/'
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def extract_keywords(self, title: str, content: str, max_length: int = 50) -> str:
        """
        从文章标题和内容中提取关键词，生成配图提示词

        Args:
            title: 文章标题
            content: 文章内容
            max_length: 提示词最大长度

        Returns:
            生成的配图提示词
        """
        # 从标题中提取关键信息
        title_keywords = self._extract_title_keywords(title)

        # 从内容中提取关键词
        content_keywords = self._extract_content_keywords(content)

        # 组合关键词
        prompt = self._build_prompt(title_keywords, content_keywords)

        # 限制长度
        if len(prompt) > max_length:
            prompt = prompt[:max_length]

        return prompt

    def _extract_title_keywords(self, title: str) -> str:
        """从标题提取关键词"""
        # 移除标点符号
        title_clean = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', title)

        # 提取关键名词（简化版本，实际可以使用 NLP）
        keywords = title_clean.strip()

        return keywords if keywords else "business article"

    def _extract_content_keywords(self, content: str) -> list:
        """从内容中提取关键词"""
        # 取前500字符进行分析
        sample = content[:500]

        # 寻找常见主题关键词
        keywords = []
        themes = [
            '贸易', '战争', '经济', '陶瓷', '出口', '进口',
            '科技', '教育', '健康', '环境', '交通',
            '金融', '投资', '市场', '企业', '产品'
        ]

        for theme in themes:
            if theme in content:
                keywords.append(theme)
                if len(keywords) >= 2:
                    break

        return keywords

    def _build_prompt(self, title_keywords: str, content_keywords: list) -> str:
        """构建配图提示词"""
        # 根据关键词构建摄影写实风格的配图提示词
        base_styles = [
            "Photorealistic style, professional photography",
            "Cinematic photography, high detail",
            "Realistic photo, natural lighting"
        ]

        style = base_styles[0]

        if content_keywords:
            # 将中文关键词转换为英文提示词
            keywords_en = []
            for kw in content_keywords[:2]:
                # 简单映射
                mapping = {
                    '贸易': 'international trade',
                    '战争': 'war conflict',
                    '经济': 'economy',
                    '陶瓷': 'ceramics',
                    '出口': 'export business',
                    '进口': 'import trade',
                    '科技': 'technology',
                    '教育': 'education',
                    '健康': 'healthcare',
                    '环境': 'environment',
                    '交通': 'transportation',
                    '金融': 'finance',
                    '投资': 'investment',
                    '市场': 'market',
                    '企业': 'company',
                    '产品': 'product'
                }
                keywords_en.append(mapping.get(kw, kw))

            if keywords_en:
                theme = f"featuring {' and '.join(keywords_en)}"
            else:
                theme = f"featuring {title_keywords}"
        else:
            theme = f"featuring {title_keywords}"

        prompt = f"{style}, {theme}, 4K quality, sharp focus, professional photography, cinematic lighting"

        return prompt

    def _resize_to_wechat_cover(self, image: Image.Image) -> Image.Image:
        """
        调整图片尺寸为微信封面标准尺寸 900 × 383 像素

        Args:
            image: PIL Image 对象

        Returns:
            调整后的 PIL Image 对象
        """
        wechat_cover_width = 900
        wechat_cover_height = 383

        # 获取原始尺寸
        original_width, original_height = image.size

        print(f"原始尺寸: {original_width} × {original_height} 像素")

        # 如果已经是标准尺寸，直接返回
        if original_width == wechat_cover_width and original_height == wechat_cover_height:
            print("图片已是微信封面标准尺寸，无需调整")
            return image

        # 使用智能裁剪（保持中心区域）
        # 计算裁剪区域
        target_ratio = wechat_cover_width / wechat_cover_height
        original_ratio = original_width / original_height

        if original_ratio > target_ratio:
            # 原图更宽，需要裁剪左右
            new_height = original_height
            new_width = int(new_height * target_ratio)
            left = (original_width - new_width) // 2
            top = 0
            right = left + new_width
            bottom = original_height
        else:
            # 原图更高，需要裁剪上下
            new_width = original_width
            new_height = int(new_width / target_ratio)
            left = 0
            top = (original_height - new_height) // 2
            right = original_width
            bottom = top + new_height

        # 裁剪并调整大小
        cropped = image.crop((left, top, right, bottom))
        resized = cropped.resize((wechat_cover_width, wechat_cover_height), Image.Resampling.LANCZOS)

        print(f"已调整为微信封面标准尺寸: {wechat_cover_width} × {wechat_cover_height} 像素")

        return resized

    def generate_cover(self, title: str, content: str, output_path: str) -> Optional[str]:
        """
        根据文章内容生成配图

        Args:
            title: 文章标题
            content: 文章内容
            output_path: 输出图片路径

        Returns:
            生成的配图 URL，失败返回 None
        """
        try:
            # 提取提示词
            prompt = self.extract_keywords(title, content)
            print(f"生成配图提示词: {prompt}")

            # 提交生成任务
            response = requests.post(
                f"{self.base_url}v1/images/generations",
                headers={**self.headers, "X-ModelScope-Async-Mode": "true"},
                data=json.dumps({
                    "model": "Tongyi-MAI/Z-Image-Turbo",
                    "prompt": prompt
                }, ensure_ascii=False).encode('utf-8')
            )

            response.raise_for_status()
            task_id = response.json()["task_id"]
            print(f"配图生成任务已提交，任务ID: {task_id}")

            # 轮询等待生成完成
            max_attempts = 30  # 最多等待150秒
            for attempt in range(max_attempts):
                result = requests.get(
                    f"{self.base_url}v1/tasks/{task_id}",
                    headers={**self.headers, "X-ModelScope-Task-Type": "image_generation"},
                )
                result.raise_for_status()
                data = result.json()

                if data["task_status"] == "SUCCEED":
                    image_url = data["output_images"][0]
                    print(f"配图生成成功: {image_url}")

                    # 下载图片
                    image_response = requests.get(image_url)
                    image_response.raise_for_status()

                    # 打开图片
                    image = Image.open(BytesIO(image_response.content))

                    # 调整为微信封面标准尺寸
                    image = self._resize_to_wechat_cover(image)

                    # 保存图片
                    image.save(output_path, quality=95)
                    print(f"配图已保存到: {output_path}")

                    return output_path

                elif data["task_status"] == "FAILED":
                    print("配图生成失败")
                    return None

                print(f"等待配图生成中... ({attempt + 1}/{max_attempts})")
                time.sleep(5)

            print("配图生成超时")
            return None

        except Exception as e:
            print(f"生成配图时出错: {e}")
            return None


def generate_cover_from_file(article_file: str, output_path: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    从文章文件生成配图

    Args:
        article_file: 文章文件路径（支持 .md 和 .txt）
        output_path: 输出图片路径
        api_key: ModelScope API Key，如果不提供则从环境变量获取

    Returns:
        生成的配图路径，失败返回 None
    """
    # 读取文章内容
    with open(article_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取标题（第一行 # 开头）
    title = "文章标题"
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            title = re.sub(r'^#+\s+', '', line)
            break

    # 生成配图
    generator = AICoverGenerator(api_key)
    return generator.generate_cover(title, content, output_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python ai_cover_generator.py <文章文件> <输出图片路径> [API_KEY]")
        print("\n参数说明:")
        print("  文章文件      : Markdown 或文本文件路径")
        print("  输出图片路径  : 生成的配图保存路径")
        print("  API_KEY (可选): ModelScope API Key")
        print("\nAPI Key 获取方式（按优先级）:")
        print("  1. 命令行参数传递: python ai_cover_generator.py article.md cover.jpg YOUR_API_KEY")
        print("  2. 环境变量: export MODELSCOPE_API_KEY='your-api-key'")
        print("  3. .env 文件: 创建 .env 文件并添加 MODELSCOPE_API_KEY=your-api-key")
        print("\n获取 API Key: https://www.modelscope.cn/my/myaccesstoken")
        print("\n示例:")
        print("  python ai_cover_generator.py article.md cover.jpg")
        print("  python ai_cover_generator.py article.md cover.jpg your-api-key")
        sys.exit(1)

    article_file = sys.argv[1]
    output_path = sys.argv[2]

    # 使用命令行提供的 API Key，如果没有则从环境变量获取
    api_key = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        # 生成配图
        result = generate_cover_from_file(article_file, output_path, api_key)

        if result:
            print(f"\nOK: 配图生成成功: {result}")
        else:
            print("\nERROR: 配图生成失败")
            sys.exit(1)
    except ValueError as e:
        print(f"\nERROR: 配置错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: 生成配图时出错: {e}")
        sys.exit(1)
