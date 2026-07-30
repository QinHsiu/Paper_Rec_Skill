#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paper_Rec skill-wxmp — Markdown to WeChat-compatible HTML."""

import re
from typing import Optional


class WeChatMarkdownFormatter:
    """微信公众号 Markdown 格式化器（美化版）"""

    def __init__(self):
        """初始化格式化器"""
        self.rules = [
            self._normalize_headers,
            self._normalize_lists,
            self._normalize_blockquotes,
            self._normalize_code_blocks,
            self._normalize_emphasis,
            self._normalize_links,
            self._normalize_blank_lines,
            self._trim_trailing_spaces,
        ]

    def format(self, markdown_text: str) -> str:
        """
        格式化 Markdown 文本

        Args:
            markdown_text: 原始 Markdown 文本

        Returns:
            格式化后的 Markdown 文本
        """
        lines = markdown_text.split('\n')

        # 应用所有格式化规则
        for rule in self.rules:
            lines = rule(lines)

        # 移除开头和结尾的空行
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        return '\n'.join(lines)

    def _normalize_headers(self, lines: list) -> list:
        """规范化标题"""
        result = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)

            if header_match:
                level = len(header_match.group(1))
                content = header_match.group(2).strip()

                # 确保标题前有空行（除非是第一行）
                if result and result[-1].strip():
                    result.append('')

                result.append('#' * level + ' ' + content)

                # 一级标题后添加空行
                if level == 1:
                    result.append('')
                elif i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith('#'):
                    result.append('')
            else:
                result.append(line)

        return result

    def _normalize_lists(self, lines: list) -> list:
        """规范化列表"""
        result = []
        in_list = False

        for line in lines:
            stripped = line.strip()
            list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', line)

            if list_match:
                if not in_list and result and result[-1].strip():
                    result.append('')

                # 保留列表类型（无序列表用 -，有序列表用 1.）
                indent = list_match.group(1)
                marker = list_match.group(2)
                content = list_match.group(3)

                # 对于无序列表，统一使用 - 作为符号
                if marker in ['*', '+']:
                    marker = '-'

                result.append(indent + marker + ' ' + content)
                in_list = True
            else:
                # 非列表行
                if in_list and stripped:
                    result.append('')

                result.append(line)
                in_list = False

        return result

    def _normalize_blockquotes(self, lines: list) -> list:
        """规范化引用块"""
        result = []
        in_blockquote = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('>'):
                # 不在引用块中时，前面加空行
                if not in_blockquote and result and result[-1].strip():
                    result.append('')

                content = stripped[1:].strip()
                result.append('> ' + content)
                in_blockquote = True
            else:
                # 非引用行
                if in_blockquote and stripped:
                    result.append('')

                result.append(line)
                in_blockquote = False

        return result

    def _normalize_code_blocks(self, lines: list) -> list:
        """规范化代码块"""
        result = []
        in_code_block = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```'):
                if not in_code_block and result and result[-1].strip():
                    result.append('')
                result.append(line)
                in_code_block = not in_code_block
            else:
                result.append(line)

        return result

    def _normalize_emphasis(self, lines: list) -> list:
        """规范化强调文本"""
        result = []

        for line in lines:
            if '```' not in line:
                line = re.sub(r'\_\_(.+?)\_\_', r'**\1**', line)
                line = re.sub(r'\_(.+?)\_', r'*\1*', line)

            result.append(line)

        return result

    def _normalize_links(self, lines: list) -> list:
        """规范化链接"""
        result = []

        for line in lines:
            line = re.sub(
                r'\[([^\]]+)\]\(([^\)]+)\)',
                lambda m: f'[{m.group(1)}]({self._escape_url(m.group(2))})',
                line
            )
            result.append(line)

        return result

    def _escape_url(self, url: str) -> str:
        """转义 URL"""
        if url.startswith('"') and url.endswith('"'):
            return url
        if url.startswith("'") and url.endswith("'"):
            return url
        if re.search(r'[\s()]', url):
            return f'"{url}"'
        return url

    def _normalize_blank_lines(self, lines: list) -> list:
        """规范化空行"""
        result = []
        blank_count = 0

        for line in lines:
            if not line.strip():
                blank_count += 1
                if blank_count <= 2:
                    result.append('')
            else:
                blank_count = 0
                result.append(line)

        return result

    def _trim_trailing_spaces(self, lines: list) -> list:
        """去除行尾空格"""
        return [line.rstrip() for line in lines]

    def format_to_wechat_html(self, markdown_text: str, custom_css: Optional[str] = None) -> str:
        """
        将 Markdown 转换为适合微信公众号的 HTML 格式（支持自定义 CSS）

        Args:
            markdown_text: Markdown 文本
            custom_css: 自定义 CSS 样式（可选，用于格式化过程中但不添加到输出）

        Returns:
            HTML 格式的文本
        """
        # 先格式化 Markdown
        formatted = self.format(markdown_text)

        # 转换分隔线
        formatted = re.sub(r'^---+$', r'<hr/>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^\*\*\*+$', r'<hr/>', formatted, flags=re.MULTILINE)

        # 转换引用块（先处理，避免被当作段落）
        formatted = re.sub(
            r'^>\s+(.+)$',
            lambda m: f'<blockquote style="display: block; font-size: 0.9em; overflow: auto; overflow-scrolling: touch; border-left: 3px solid rgba(0, 0, 0, 0.4); background: rgba(0, 0, 0, 0.05); padding-top: 10px; padding-bottom: 10px; padding-left: 20px; padding-right: 10px; margin-bottom: 20px; margin-top: 20px; font-style: normal; padding: 10px; position: relative; line-height: 1.8; text-indent: 0; border: none; color: #888;"><span style="display: inline; color: #555555; font-size: 4em; font-family: Arial, serif; line-height: 1em; font-weight: 700;">"</span><p style="font-size: 16px; padding-top: 8px; padding-bottom: 8px; margin: 0px; color: black; line-height: 26px; display: inline;">{re.sub(r"\*\*(.+?)\*\*", r"<strong style=\"font-weight: bold; color: rgb(71, 193, 168);\">\1</strong>", m.group(1))}</p></blockquote>',
            formatted, flags=re.MULTILINE
        )

        # 转换标题
        formatted = re.sub(r'^#\s+(.+)$', r'<h1 style="margin-top: 30px; margin-bottom: 15px; font-weight: bold; font-size: 24px; color: rgb(89,89,89);"><span class="prefix" style="display: none;"></span><span class="content">\1</span><span class="suffix"></span></h1>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^##\s+(.+)$', r'<h2 style="margin-top: 30px; font-weight: bold; font-size: 22px; border-bottom: 2px solid rgb(89,89,89); margin-bottom: 30px; color: rgb(89,89,89);"><span class="prefix" style="display: none;"></span><span class="content" style="font-size: 22px; display: inline-block; border-bottom: 2px solid rgb(89,89,89);">\1</span><span class="suffix"></span></h2>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^###\s+(.+)$', r'<h3 style="margin-top: 30px; font-weight: bold; font-size: 20px; color: rgb(89,89,89);">\1</h3>', formatted, flags=re.MULTILINE)

        # 逐行处理，处理列表和段落
        lines = formatted.split('\n')
        result = []
        in_list = False
        list_type = None  # 'ul' or 'ol'
        list_items = []
        list_index = 1  # 有序列表的序号
        empty_line_count = 0

        for line in lines:
            stripped = line.strip()

            # 跳过空行（但统计数量，用于判断列表是否结束）
            if not stripped:
                empty_line_count += 1
                continue

            # 如果连续超过2个空行，结束当前列表
            if empty_line_count > 2 and in_list:
                if list_type == 'ul':
                    list_html = '<ul style="margin-top: 8px; margin-bottom: 8px; padding-left: 25px; color: black; list-style-type: disc;">' + ''.join(list_items) + '</ul>'
                else:
                    # 使用 ol 标签
                    list_html = '<ol style="margin-top: 8px; margin-bottom: 8px; padding-left: 25px; color: black;">' + ''.join(list_items) + '</ol>'
                result.append(list_html)
                list_items = []
                in_list = False
                list_type = None
                list_index = 1

            empty_line_count = 0

            # 列表项（有序列表）
            if re.match(r'^\d+\.\s+(.+)$', stripped):
                content = re.sub(r'^\d+\.\s+', '', stripped)
                content = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: bold; color: rgb(71, 193, 168);">\1</strong>', content)
                if not in_list:
                    list_type = 'ol'
                    in_list = True
                list_items.append(f'<li><section style="margin-top: 5px; margin-bottom: 5px; line-height: 26px; text-align: left; color: rgb(1,1,1); font-weight: 500;">{content}</section></li>')
                list_index += 1
            # 列表项（无序列表）
            elif re.match(r'^-\s+(.+)$', stripped):
                content = re.sub(r'^-\s+', '', stripped)
                content = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: bold; color: rgb(71, 193, 168);">\1</strong>', content)
                if not in_list:
                    list_type = 'ul'
                    in_list = True
                list_items.append(f'<li><section style="margin-top: 5px; margin-bottom: 5px; line-height: 26px; text-align: left; color: rgb(1,1,1); font-weight: 500;">{content}</section></li>')
            else:
                if in_list:
                    if list_type == 'ul':
                        list_html = '<ul style="margin-top: 8px; margin-bottom: 8px; padding-left: 25px; color: black; list-style-type: disc;">' + ''.join(list_items) + '</ul>'
                    else:
                        # 使用 ol 标签
                        list_html = '<ol style="margin-top: 8px; margin-bottom: 8px; padding-left: 25px; color: black;">' + ''.join(list_items) + '</ol>'
                    result.append(list_html)
                    list_items = []
                    in_list = False
                    list_type = None
                    list_index = 1

                # 标签已处理过（标题、引用块、分隔线）
                if stripped.startswith(('<h1', '<h2', '<h3', '<blockquote', '<hr')):
                    result.append(stripped)
                # 段落
                else:
                    content = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: bold; color: rgb(71, 193, 168);">\1</strong>', stripped)
                    content = re.sub(r'\*(.+?)\*', r'<em style="font-style: italic; color: rgb(71, 193, 168);">\1</em>', content)
                    result.append(f'<p style="font-size: 16px; padding-top: 8px; padding-bottom: 8px; margin: 0; line-height: 26px; color: rgb(89,89,89);">{content}</p>')

        if in_list:
            if list_type == 'ul':
                list_html = '<ul style="margin-top: 8px; margin-bottom: 8px; padding-left: 25px; color: black; list-style-type: disc;">' + ''.join(list_items) + '</ul>'
            else:
                # 使用 ol 标签
                list_html = '<ol style="margin-top: 8px; margin-bottom: 8px; padding-left: 25px; color: black;">' + ''.join(list_items) + '</ol>'
            result.append(list_html)

        html = '\n'.join(result)

        # 转换图片
        html = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', r'<img src="\2" alt="\1"/>', html)

        # 转换 hr 样式
        html = html.replace('<hr/>', '<hr style="height: 1px; margin: 0; margin-top: 10px; margin-bottom: 10px; border: none; border-top: 1px solid black;">')

        # 去除 <br> 和 <br/> 标签
        html = re.sub(r'<br\s*/?>', '', html)

        # 添加外层 section 和样式（不包含自定义 CSS）
        html = f'<section id="nice" data-website="https://markdown.com.cn/editor" style="font-size: 16px; color: black; line-height: 1.6; word-spacing: 0px; letter-spacing: 0px; word-break: break-word; word-wrap: break-word; text-align: justify; font-family: Optima-Regular, Optima, PingFangSC-light, PingFangTC-light, \'PingFang SC\', Cambria, Cochin, Georgia, Times, \'Times New Roman\', serif; margin-top: -10px; padding: 10px;">\n{html}\n</section>'

        return html


def format_markdown(text: str) -> str:
    """格式化 Markdown 文本（便捷函数）"""
    formatter = WeChatMarkdownFormatter()
    return formatter.format(text)


def markdown_to_html(text: str) -> str:
    """将 Markdown 转换为微信公众号 HTML 格式（便捷函数）"""
    formatter = WeChatMarkdownFormatter()
    return formatter.format_to_wechat_html(text)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        # 使用示例文本测试
        sample = """# 标题1

这是一段文本。

## 标题2

这是另一段文本。

* 列表项1
* 列表项2

> 这是一段引用

**粗体文本** *斜体文本*

[链接](https://example.com)

```
代码块
```
"""

        print("=== 原始 Markdown ===")
        print(sample)

        formatter = WeChatMarkdownFormatter()

        print("\n=== 格式化后的 HTML ===")
        html = formatter.format_to_wechat_html(sample)
        print(html)
    else:
        # 从文件读取
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()

        # 读取自定义 CSS（如果有）
        custom_css = None
        if len(sys.argv) > 3:
            with open(sys.argv[3], 'r', encoding='utf-8') as f:
                custom_css = f.read()

        formatter = WeChatMarkdownFormatter()
        formatted = formatter.format_to_wechat_html(text, custom_css=custom_css)

        # 输出到文件
        output_file = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].replace('.md', '_formatted.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted)

        print(f"OK: 已格式化并保存到: {output_file}")
