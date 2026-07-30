#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paper_Rec skill-wxmp — multi-account AppID/Secret store (local JSON)."""

import json
import os
from typing import Dict, Optional


def _default_config_path() -> str:
    env = os.environ.get("WXMP_ACCOUNTS_JSON")
    if env:
        return env
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "wxmp_accounts.json")


class WeChatConfigManager:
    """微信公众号配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径；默认 scripts/wxmp/wxmp_accounts.json 或 WXMP_ACCOUNTS_JSON
        """
        self.config_file = config_file or _default_config_path()
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"accounts": {}}

    def _save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def add_account(self, name: str, app_id: str, app_secret: str,
                   description: str = "", modelscope_api_key: Optional[str] = None):
        """
        添加公众号配置

        Args:
            name: 公众号名称/标识符
            app_id: 微信公众号 AppID
            app_secret: 微信公众号 AppSecret
            description: 公众号描述
            modelscope_api_key: ModelScope API Key（可选）
        """
        if name in self.config["accounts"]:
            raise ValueError(f"公众号 '{name}' 已存在，请使用不同的名称或先删除")

        self.config["accounts"][name] = {
            "app_id": app_id,
            "app_secret": app_secret,
            "description": description,
            "modelscope_api_key": modelscope_api_key
        }
        self._save_config()
        print(f"OK: 公众号 '{name}' 配置已添加")

    def get_account(self, name: str) -> Optional[Dict]:
        """
        获取公众号配置

        Args:
            name: 公众号名称/标识符

        Returns:
            公众号配置字典，不存在返回 None
        """
        return self.config["accounts"].get(name)

    def list_accounts(self) -> Dict:
        """
        列出所有公众号配置

        Returns:
            所有公众号配置
        """
        return self.config["accounts"]

    def delete_account(self, name: str):
        """
        删除公众号配置

        Args:
            name: 公众号名称/标识符
        """
        if name not in self.config["accounts"]:
            raise ValueError(f"公众号 '{name}' 不存在")

        del self.config["accounts"][name]
        self._save_config()
        print(f"OK: 公众号 '{name}' 配置已删除")

    def update_account(self, name: str, **kwargs):
        """
        更新公众号配置

        Args:
            name: 公众号名称/标识符
            **kwargs: 要更新的字段（app_id, app_secret, description, modelscope_api_key）
        """
        if name not in self.config["accounts"]:
            raise ValueError(f"公众号 '{name}' 不存在")

        for key, value in kwargs.items():
            if value is not None:
                self.config["accounts"][name][key] = value

        self._save_config()
        print(f"OK: 公众号 '{name}' 配置已更新")

    def get_default_account(self) -> Optional[str]:
        """
        获取默认公众号名称

        Returns:
            默认公众号名称，未设置返回 None
        """
        return self.config.get("default_account")

    def set_default_account(self, name: str):
        """
        设置默认公众号

        Args:
            name: 公众号名称/标识符
        """
        if name not in self.config["accounts"]:
            raise ValueError(f"公众号 '{name}' 不存在")

        self.config["default_account"] = name
        self._save_config()
        print(f"OK: 默认公众号已设置为 '{name}'")


def create_config_file_example():
    """创建示例配置文件"""
    example_config = {
        "default_account": "account1",
        "accounts": {
            "account1": {
                "app_id": "your_app_id_1",
                "app_secret": "your_app_secret_1",
                "description": "示例公众号1",
                "modelscope_api_key": "ms-your-api-key-1"
            },
            "account2": {
                "app_id": "your_app_id_2",
                "app_secret": "your_app_secret_2",
                "description": "示例公众号2",
                "modelscope_api_key": None
            }
        }
    }

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wxmp_accounts_example.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(example_config, f, indent=2, ensure_ascii=False)

    print(f"OK: 示例配置文件已创建: {out}")


if __name__ == "__main__":
    import sys

    manager = WeChatConfigManager()

    if len(sys.argv) < 2:
        print("用法:")
        print("  添加账号: python config_manager.py add <名称> <AppID> <AppSecret> [描述] [ModelScope_API_Key]")
        print("  列出账号: python config_manager.py list")
        print("  删除账号: python config_manager.py delete <名称>")
        print("  设置默认: python config_manager.py set_default <名称>")
        print("  创建示例: python config_manager.py create_example")
        print("\n示例:")
        print("  python config_manager.py add myaccount wx1234567890abcdef my-secret '我的公众号'")
        print("  python config_manager.py list")
        print("  python config_manager.py set_default myaccount")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "add":
            if len(sys.argv) < 5:
                print("添加账号需要: 名称 AppID AppSecret [描述] [ModelScope_API_Key]")
                sys.exit(1)

            name = sys.argv[2]
            app_id = sys.argv[3]
            app_secret = sys.argv[4]
            description = sys.argv[5] if len(sys.argv) > 5 else ""
            modelscope_api_key = sys.argv[6] if len(sys.argv) > 6 else None

            manager.add_account(name, app_id, app_secret, description, modelscope_api_key)

        elif command == "list":
            accounts = manager.list_accounts()
            default = manager.get_default_account()

            print("\n" + "=" * 60)
            print("微信公众号账号列表")
            print("=" * 60)

            if not accounts:
                print("\n暂无公众号配置")
                print("\n添加公众号: python config_manager.py add <名称> <AppID> <AppSecret>")
            else:
                for name, config in accounts.items():
                    is_default = " (默认)" if name == default else ""
                    print(f"\n  {name}{is_default}")
                    print(f"   描述: {config.get('description', 'N/A')}")
                    print(f"   AppID: {config['app_id']}")
                    print(f"   AppSecret: {config['app_secret'][:10]}...")
                    ms_key = config.get('modelscope_api_key')
                    if ms_key:
                        print(f"   ModelScope Key: {ms_key[:20]}...")
                    else:
                        print(f"   ModelScope Key: 未设置（将使用环境变量）")

            print("\n" + "=" * 60)

        elif command == "delete":
            if len(sys.argv) < 3:
                print("删除账号需要: 名称")
                sys.exit(1)

            name = sys.argv[2]
            manager.delete_account(name)

        elif command == "set_default":
            if len(sys.argv) < 3:
                print("设置默认需要: 名称")
                sys.exit(1)

            name = sys.argv[2]
            manager.set_default_account(name)

        elif command == "create_example":
            create_config_file_example()

        else:
            print(f"未知命令: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: 错误: {e}")
        sys.exit(1)
