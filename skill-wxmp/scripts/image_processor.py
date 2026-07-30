#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paper_Rec skill-wxmp — resize/crop cover to 900x383."""

from PIL import Image
import io
import os


def resize_to_wechat_cover(image_path: str, output_path: str = None) -> str:
    """
    调整图片为微信公众号封面尺寸（900 × 383 像素）

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径（可选，不提供则覆盖原文件）

    Returns:
        输出图片路径
    """
    # 打开图片
    img = Image.open(image_path)

    # 目标尺寸
    target_width = 900
    target_height = 383

    print(f"原始图片尺寸: {img.size[0]} × {img.size[1]}")

    # 如果已经是目标尺寸，直接返回
    if img.size[0] == target_width and img.size[1] == target_height:
        print("图片尺寸符合要求，无需调整")
        return image_path

    # 转换为 RGB 模式（如果是 RGBA）
    if img.mode == 'RGBA':
        # 创建白色背景
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # 调整图片尺寸为 900 × 383（裁剪模式）
    # 计算缩放比例
    scale = max(target_width / img.size[0], target_height / img.size[1])
    new_width = int(img.size[0] * scale)
    new_height = int(img.size[1] * scale)

    # 缩放图片
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 居中裁剪
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    img = img.crop((left, top, right, bottom))

    # 确定输出路径
    if output_path is None:
        output_path = image_path

    # 保存图片
    img.save(output_path, format='JPEG', quality=95)
    print(f"调整后图片尺寸: {target_width} × {target_height}")
    print(f"图片已保存到: {output_path}")

    return output_path


def check_image_specs(image_path: str) -> dict:
    """
    检查图片规格

    Args:
        image_path: 图片路径

    Returns:
        图片信息字典
    """
    img = Image.open(image_path)
    file_size = os.path.getsize(image_path)

    info = {
        'width': img.size[0],
        'height': img.size[1],
        'ratio': img.size[0] / img.size[1],
        'mode': img.mode,
        'format': img.format,
        'size_mb': file_size / 1024 / 1024
    }

    # 检查是否符合要求
    target_ratio = 900 / 383
    tolerance = 0.01

    info['valid_cover'] = (
        abs(info['ratio'] - target_ratio) < tolerance and
        info['size_mb'] <= 2.0
    )

    return info


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python image_processor.py <图片路径> [输出路径]")
        print("示例: python image_processor.py input.jpg")
        print("示例: python image_processor.py input.jpg output.jpg")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # 检查图片
    print("\n=== 检查图片信息 ===")
    info = check_image_specs(input_path)
    print(f"尺寸: {info['width']} × {info['height']}")
    print(f"比例: {info['ratio']:.2f}")
    print(f"格式: {info['format']}")
    print(f"模式: {info['mode']}")
    print(f"大小: {info['size_mb']:.2f} MB")
    print(f"符合封面要求: {'是' if info['valid_cover'] else '否'}")

    # 调整图片
    print("\n=== 调整图片尺寸 ===")
    result = resize_to_wechat_cover(input_path, output_path)
    print(f"\n完成！图片路径: {result}")
