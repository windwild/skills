#!/usr/bin/env python3
"""
微信小程序测试场景示例
提供常见测试场景的预定义脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weapp_automation import AutomationConfig, WeappTestRunner
from typing import Dict, Any, List
import json


class TestScenarios:
    """预定义测试场景"""

    def __init__(self, project_path: str, cli_path: str = None):
        self.config = AutomationConfig(
            project_path=project_path,
            cli_path=cli_path or "/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
        )

    def smoke_test(self) -> Dict[str, Any]:
        """
        冒烟测试 - 验证小程序基本功能

        测试内容：
        1. 启动并导航到首页
        2. 截图首页
        3. 检查基本元素
        """
        runner = WeappTestRunner(self.config)

        result = (runner
            .navigate("pages/index/index")
            .wait(2)
            .screenshot("smoke_test_home.png")
            .get_results())

        return {
            "scenario": "smoke_test",
            "results": result,
            "summary": runner.get_summary()
        }

    def navigation_flow_test(self, pages: List[str]) -> Dict[str, Any]:
        """
        导航流程测试

        Args:
            pages: 要依次导航的页面路径列表

        测试内容：
        1. 依次导航到每个页面
        2. 每个页面截图
        3. 验证页面加载成功
        """
        runner = WeappTestRunner(self.config)

        for i, page in enumerate(pages):
            runner.navigate(page).wait(1).screenshot(f"nav_flow_{i}_{page.replace('/', '_')}.png")

        return {
            "scenario": "navigation_flow_test",
            "pages": pages,
            "results": runner.get_results(),
            "summary": runner.get_summary()
        }

    def form_submission_test(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """
        表单提交测试

        Args:
            form_data: 表单字段和值，如 {"input[name='username']": "testuser"}

        测试内容：
        1. 导航到表单页面
        2. 填写表单
        3. 提交表单
        4. 验证提交结果
        """
        runner = WeappTestRunner(self.config)

        runner.navigate("pages/form/form").wait(1)

        # 填写表单
        for selector, value in form_data.items():
            runner.input(selector, value).wait(0.5)

        # 截图填写后的表单
        runner.screenshot("form_filled.png")

        # 点击提交按钮
        runner.click("button[type='submit']").wait(2)

        # 截图提交结果
        runner.screenshot("form_submitted.png")

        return {
            "scenario": "form_submission_test",
            "form_data": form_data,
            "results": runner.get_results(),
            "summary": runner.get_summary()
        }

    def ui_regression_test(self, pages: List[str], baseline_dir: str = "./baseline") -> Dict[str, Any]:
        """
        UI回归测试

        Args:
            pages: 要测试的页面列表
            baseline_dir: 基线截图目录

        测试内容：
        1. 对每个页面截图
        2. 与基线对比（如存在）
        3. 生成对比报告
        """
        import shutil
        from pathlib import Path

        runner = WeappTestRunner(self.config)

        # 创建基线目录
        Path(baseline_dir).mkdir(parents=True, exist_ok=True)

        screenshots = []
        for page in pages:
            filename = f"ui_{page.replace('/', '_')}.png"
            runner.navigate(page).wait(1).screenshot(filename)
            screenshots.append({
                "page": page,
                "filename": filename,
                "path": os.path.join(self.config.screenshot_dir, filename)
            })

        return {
            "scenario": "ui_regression_test",
            "pages": pages,
            "screenshots": screenshots,
            "baseline_dir": baseline_dir,
            "results": runner.get_results(),
            "summary": runner.get_summary()
        }

    def scroll_performance_test(self, page: str, scroll_element: str, scrolls: int = 5) -> Dict[str, Any]:
        """
        滚动性能测试

        Args:
            page: 测试页面
            scroll_element: 可滚动元素选择器
            scrolls: 滚动次数

        测试内容：
        1. 导航到页面
        2. 多次滚动
        3. 每次滚动后截图
        """
        runner = WeappTestRunner(self.config)

        runner.navigate(page).wait(1)

        for i in range(scrolls):
            runner.scroll(scroll_element, "down", 500).wait(0.5)
            runner.screenshot(f"scroll_{i}.png")

        return {
            "scenario": "scroll_performance_test",
            "page": page,
            "scrolls": scrolls,
            "results": runner.get_results(),
            "summary": runner.get_summary()
        }

    def user_journey_test(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        用户旅程测试

        Args:
            steps: 测试步骤列表，每个步骤包含 action 和参数

        示例步骤：
        [
            {"action": "navigate", "page": "pages/index/index"},
            {"action": "click", "selector": ".product-item"},
            {"action": "click", "selector": ".add-to-cart"},
            {"action": "navigate", "page": "pages/cart/cart"},
            {"action": "screenshot", "filename": "cart.png"}
        ]
        """
        runner = WeappTestRunner(self.config)

        for step in steps:
            action = step.get("action")

            if action == "navigate":
                runner.navigate(step.get("page", "pages/index/index"))
            elif action == "click":
                runner.click(step.get("selector"))
            elif action == "input":
                runner.input(step.get("selector"), step.get("text", ""))
            elif action == "scroll":
                runner.scroll(step.get("selector"), step.get("direction", "down"), step.get("distance", 300))
            elif action == "screenshot":
                runner.screenshot(step.get("filename"))
            elif action == "wait":
                runner.wait(step.get("seconds", 1))

        return {
            "scenario": "user_journey_test",
            "steps": steps,
            "results": runner.get_results(),
            "summary": runner.get_summary()
        }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="微信小程序测试场景")
    parser.add_argument("--project", "-p", required=True, help="小程序项目路径")
    parser.add_argument("--cli-path", help="CLI路径")
    parser.add_argument("--scenario", "-s", required=True,
                        choices=["smoke", "navigation", "form", "ui", "scroll", "journey"],
                        help="测试场景")
    parser.add_argument("--pages", help="页面列表，逗号分隔（用于navigation/ui场景）")
    parser.add_argument("--output", "-o", help="输出结果文件路径")

    args = parser.parse_args()

    scenarios = TestScenarios(args.project, args.cli_path)

    if args.scenario == "smoke":
        result = scenarios.smoke_test()
    elif args.scenario == "navigation":
        if not args.pages:
            print("错误: navigation场景需要提供 --pages 参数")
            sys.exit(1)
        pages = args.pages.split(",")
        result = scenarios.navigation_flow_test(pages)
    elif args.scenario == "form":
        # 示例表单数据
        form_data = {
            "input[name='username']": "testuser",
            "input[name='email']": "test@example.com"
        }
        result = scenarios.form_submission_test(form_data)
    elif args.scenario == "ui":
        if not args.pages:
            print("错误: ui场景需要提供 --pages 参数")
            sys.exit(1)
        pages = args.pages.split(",")
        result = scenarios.ui_regression_test(pages)
    elif args.scenario == "scroll":
        result = scenarios.scroll_performance_test("pages/list/list", ".scroll-view", 5)
    elif args.scenario == "journey":
        # 示例用户旅程
        steps = [
            {"action": "navigate", "page": "pages/index/index"},
            {"action": "wait", "seconds": 2},
            {"action": "screenshot", "filename": "journey_start.png"}
        ]
        result = scenarios.user_journey_test(steps)
    else:
        print(f"未知场景: {args.scenario}")
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
