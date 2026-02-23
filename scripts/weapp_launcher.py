#!/usr/bin/env python3
"""
微信小程序开发者工具启动器
提供启动、关闭、连接开发者工具的功能
"""

import subprocess
import os
import time
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# 微信开发者工具CLI路径（macOS默认路径）
DEFAULT_CLI_PATH = "/Applications/wechatwebdevtools.app/Contents/MacOS/cli"

class WeappLauncher:
    """微信小程序开发者工具启动器"""

    def __init__(self, cli_path: str = DEFAULT_CLI_PATH):
        self.cli_path = cli_path
        self._validate_cli()

    def _validate_cli(self):
        """验证CLI工具是否存在"""
        if not os.path.exists(self.cli_path):
            raise FileNotFoundError(
                f"微信开发者工具CLI未找到: {self.cli_path}\n"
                "请确保已安装微信开发者工具，或手动指定cli路径"
            )

    def _run_command(self, args: list, timeout: int = 30) -> Dict[str, Any]:
        """运行CLI命令"""
        cmd = [self.cli_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timeout",
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": ""
            }

    def open_project(self, project_path: str, auto_preview: bool = False) -> Dict[str, Any]:
        """
        打开小程序项目

        Args:
            project_path: 小程序项目根目录路径
            auto_preview: 是否自动打开预览

        Returns:
            命令执行结果
        """
        if not os.path.exists(project_path):
            return {
                "success": False,
                "error": f"项目路径不存在: {project_path}"
            }

        args = ["-o", project_path]
        if auto_preview:
            args.append("--preview")

        return self._run_command(args)

    def close_project(self, project_path: str) -> Dict[str, Any]:
        """
        关闭小程序项目

        Args:
            project_path: 小程序项目根目录路径

        Returns:
            命令执行结果
        """
        args = ["-c", project_path]
        return self._run_command(args)

    def quit_wechatdevtools(self) -> Dict[str, Any]:
        """退出微信开发者工具"""
        return self._run_command(["-q"])

    def auto_test(self, project_path: str, port: int = 9420) -> Dict[str, Any]:
        """
        开启自动化测试端口

        Args:
            project_path: 小程序项目路径
            port: 自动化测试 WebSocket 端口

        Returns:
            执行结果
        """
        args = [
            "auto",
            "--project", project_path,
            "--auto-port", str(port)
        ]
        return self._run_command(args, timeout=120)

    def is_running(self) -> bool:
        """检查开发者工具是否正在运行"""
        result = subprocess.run(
            ["pgrep", "-f", "wechatwebdevtools"],
            capture_output=True
        )
        return result.returncode == 0


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="微信小程序开发者工具启动器")
    parser.add_argument("--cli-path", default=DEFAULT_CLI_PATH, help="CLI工具路径")
    parser.add_argument("--project", "-p", required=True, help="小程序项目路径")
    parser.add_argument("--action", "-a", choices=["open", "close", "quit", "test"], default="open")
    parser.add_argument("--auto-preview", action="store_true", help="自动打开预览")
    parser.add_argument("--test-script", help="自动化测试脚本路径")

    args = parser.parse_args()

    launcher = WeappLauncher(args.cli_path)

    if args.action == "open":
        result = launcher.open_project(args.project, args.auto_preview)
    elif args.action == "close":
        result = launcher.close_project(args.project)
    elif args.action == "quit":
        result = launcher.quit_wechatdevtools()
    elif args.action == "test":
        result = launcher.auto_test(args.project, 9420)
    else:
        print(f"未知操作: {args.action}")
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
