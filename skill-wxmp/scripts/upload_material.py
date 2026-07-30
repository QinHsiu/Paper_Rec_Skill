#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paper_Rec skill-wxmp — upload permanent image material (+ cover resize)."""

import requests
from typing import Dict, Optional
from PIL import Image
import io
import os


class WeChatMaterialUploader:
    """微信公众号素材上传器"""

    def __init__(self, app_id: str, app_secret: str):
        """
        初始化素材上传器

        Args:
            app_id: 微信公众号 AppID
            app_secret: 微信公众号 AppSecret
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.api_base = "https://api.weixin.qq.com/cgi-bin"

    def _resize_to_cover(self, image_path: str) -> io.BytesIO:
        """
        调整图片为封面尺寸（900 × 383 像素）

        Args:
            image_path: 图片文件路径

        Returns:
            调整后的图片数据
        """
        img = Image.open(image_path)

        # 目标尺寸
        target_width = 900
        target_height = 383

        # 检查图片尺寸
        width, height = img.size

        print(f"原始图片尺寸: {width} × {height}")

        # 如果已经是目标尺寸，直接返回
        if width == target_width and height == target_height:
            print("图片尺寸符合要求，无需调整")
            with open(image_path, 'rb') as f:
                return io.BytesIO(f.read())

        # 调整图片尺寸为 900 × 383（裁剪模式）
        # 计算缩放比例
        scale = max(target_width / width, target_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)

        # 缩放图片
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 居中裁剪
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        img = img.crop((left, top, right, bottom))

        # 保存为 BytesIO
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)

        print(f"调整后图片尺寸: {target_width} × {target_height}")

        return img_byte_arr

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

    def upload_image(self, file_path: str, resize: bool = True) -> Dict:
        """
        上传图片素材

        Args:
            file_path: 图片文件路径（支持 jpg, png 等格式）
            resize: 是否自动调整图片为封面尺寸（900 × 383），默认 True

        Returns:
            上传结果，包含 media_id 和 url
        """
        if not self.access_token:
            self.get_access_token()

        url = f"{self.api_base}/material/add_material?access_token={self.access_token}&type=thumb"

        # 检查文件大小（限制 2MB）
        file_size = os.path.getsize(file_path)
        if file_size > 2 * 1024 * 1024:
            raise Exception(f"图片大小超过限制（{file_size / 1024 / 1024:.2f}MB），最大 2MB")

        # 自动调整图片尺寸
        if resize:
            print("正在调整图片尺寸为封面格式（900 × 383）...")
            image_data = self._resize_to_cover(file_path)
            files = {'media': ('cover.jpg', image_data, 'image/jpeg')}
        else:
            with open(file_path, 'rb') as f:
                files = {'media': f}

        response = requests.post(url, files=files)
        result = response.json()

        # 微信 API 成功时可能没有 errcode 字段，或有 errcode: 0
        if result.get("errcode", 0) != 0:
            raise Exception(f"上传图片失败: {result}")

        # 检查是否返回了必需的字段
        if "media_id" not in result or "url" not in result:
            raise Exception(f"上传图片返回数据异常: {result}")

        print(f"图片上传成功！")
        print(f"media_id: {result['media_id']}")
        print(f"url: {result['url']}")

        return result

    def upload_temp_image(self, file_path: str) -> Dict:
        """
        上传临时图片素材（有效期3天）

        Args:
            file_path: 图片文件路径

        Returns:
            上传结果，包含 media_id 和 url
        """
        if not self.access_token:
            self.get_access_token()

        url = f"{self.api_base}/media/upload?access_token={self.access_token}&type=image"

        with open(file_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(url, files=files)

        result = response.json()

        if result.get("errcode") != 0:
            raise Exception(f"上传临时图片失败: {result}")

        return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("用法: python upload_material.py <APPID> <APPSECRET> <image|temp> <图片路径>")
        sys.exit(1)

    app_id = sys.argv[1]
    app_secret = sys.argv[2]
    upload_type = sys.argv[3]
    file_path = sys.argv[4]

    uploader = WeChatMaterialUploader(app_id, app_secret)

    try:
        if upload_type == "image":
            result = uploader.upload_image(file_path)
            print(f"图片上传成功!")
            print(f"media_id: {result['media_id']}")
            print(f"url: {result['url']}")
        elif upload_type == "temp":
            result = uploader.upload_temp_image(file_path)
            print(f"临时图片上传成功!")
            print(f"media_id: {result['media_id']}")
            print(f"url: {result['url']}")
        else:
            print(f"未知类型: {upload_type}")
            sys.exit(1)

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
