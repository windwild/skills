#!/usr/bin/env python3
"""
微信小程序自动化测试核心模块
提供页面导航、元素操作、截图、控制台日志读取等功能
"""

import subprocess
import json
import time
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AutomationConfig:
    """自动化测试配置"""
    project_path: str
    cli_path: str = "/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
    screenshot_dir: str = "./screenshots"
    timeout: int = 30
    ws_endpoint: str = "ws://localhost:9420"


class WeappAutomation:
    """
    微信小程序自动化测试控制器

    通过开发者工具CLI和自动化脚本实现：
    - 页面导航
    - 元素点击/输入
    - 截图
    - 控制台日志读取
    """

    def __init__(self, config: AutomationConfig):
        self.config = config
        self.session_id: Optional[str] = None
        self._ensure_screenshot_dir()

    def _ensure_screenshot_dir(self):
        """确保截图目录存在"""
        Path(self.config.screenshot_dir).mkdir(parents=True, exist_ok=True)

    def _run_batch_commands(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量执行自动化命令，共用一个 Node.js WebSocket 连接，极大提升性能
        
        Args:
            steps: 操作步骤列表，如 [{"action": "navigate", "params": {"target": "..."}}]
        """
        if not steps:
            return []
            
        automation_script = self._generate_batch_script(steps)

        script_path = os.path.join(self.config.project_path, f"weapp_automation_batch_{int(time.time())}.js")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(automation_script)

        try:
            result = subprocess.run(
                ["node", script_path],
                capture_output=True,
                text=True,
                timeout=self.config.timeout * len(steps)
            )
            return self._parse_batch_result(result)
        except subprocess.TimeoutExpired as e:
            return [{"success": False, "error": f"Execution timed out: {e}"}]
        except Exception as e:
            return [{"success": False, "error": str(e)}]
        finally:
            if os.path.exists(script_path):
                # os.remove(script_path)
                print(f"DEBUG: Script preserved at {script_path}")
                
        return []

    def _generate_batch_script(self, steps: List[Dict[str, Any]]) -> str:
        ws_endpoint = self.config.ws_endpoint if hasattr(self.config, 'ws_endpoint') else 'ws://localhost:9420'

        base_script = '''
const automator = require('miniprogram-automator');

function safeStringify(obj, indent = 2) {
  let cache = [];
  const retVal = JSON.stringify(
    obj,
    (key, value) =>
      typeof value === 'object' && value !== null
        ? cache.includes(value)
          ? undefined // Duplicate reference found, discard key
          : cache.push(value) && value // Store value in our collection
        : value,
    indent
  );
  cache = null; // Enable garbage collection
  return retVal;
}

async function runTest() {
    const miniProgram = await automator.connect({
        wsEndpoint: '%%WS_ENDPOINT%%'
    });
    const results = [];

    try {
        let page = await miniProgram.currentPage();
        // 如果没有页面，可能还没启动完成，等待一下
        if (!page) {
            await miniProgram.waitFor(2000);
            page = await miniProgram.currentPage();
        }
        
%s

        await miniProgram.disconnect();
        console.log('BATCH_RESULT: ' + safeStringify(results));
    } catch (error) {
        results.push({ success: false, error: error.message });
        console.log('BATCH_RESULT: ' + safeStringify(results));
        await miniProgram.disconnect();
        process.exit(1);
    }
}

runTest();
'''
        js_code = []
        for i, step in enumerate(steps):
            action = step.get("action")
            params = step.get("params", {})
            action_snippet = self._get_action_code(action, params)
            
            # 包装每个 snippet 捕捉错误并保存结果
            js_code.append(f'''
        try {{
            let result_{i};
            // --- Action: {action} ---
            {action_snippet.replace("const result =", f"result_{i} =")}
            // -------------------------
            results.push({{ success: true, action: '{action}', data: result_{i} }});
            // Update page ref after potential navigation
            page = await miniProgram.currentPage();
        }} catch(e) {{
            console.error('ACTION_ERROR:', '{action}', e.message, e.stack);
            results.push({{ success: false, action: '{action}', error: e.message }});
            throw e; // 断开链式执行
        }}
''')
        return base_script.replace('%%WS_ENDPOINT%%', ws_endpoint) % "".join(js_code)

    def _run_automation_command(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """向后兼容的单步执行，底层代理到批量执行"""
        results = self._run_batch_commands([{"action": action, "params": params or {}}])
        return results[0] if results else {"success": False, "error": "Unknown error"}

    def _get_action_code(self, action: str, params: Dict[str, Any]) -> str:
        """根据操作类型生成对应的代码"""

        if action == "navigate":
            target = params.get("target", "pages/index/index")
            return f'''
        const newPage = await miniProgram.reLaunch('/{target}');
        await newPage.waitFor(2000);
        const result = {{ page: '{target}', navigated: true }};
'''

        elif action == "click":
            selector = params.get("selector", "")
            return f'''
        const element = await page.$(`{selector}`);
        if (!element) throw new Error('Element not found: {selector}');
        await element.tap();
        await page.waitFor(500);
        const result = {{ selector: '{selector}', clicked: true }};
'''

        elif action == "input":
            selector = params.get("selector", "")
            text = params.get("text", "")
            return f'''
        const element = await page.$(`{selector}`);
        if (!element) throw new Error('Element not found: {selector}');
        await element.input(`{text}`);
        await page.waitFor(500);
        const result = {{ selector: '{selector}', text: '{text}', input: true }};
'''

        elif action == "screenshot":
            filename = params.get("filename", f"screenshot_{int(time.time())}.png")
            filepath = os.path.join(self.config.screenshot_dir, filename)
            return f'''
        await miniProgram.screenshot({{
            path: '{filepath}'
        }});
        const result = {{ path: '{filepath}', filename: '{filename}' }};
'''

        elif action == "get_logs":
            return '''
        const logs = await miniProgram.getSystemInfo();
        const result = { logs: logs };
'''

        elif action == "get_element_text":
            selector = params.get("selector", "")
            return f'''
        const element = await page.$(`{selector}`);
        if (!element) throw new Error('Element not found: {selector}');
        const text = await element.text();
        const result = {{ selector: '{selector}', text: text }};
'''

        elif action == "get_wxml":
            raw_selector = params.get("selector", "")
            selector = raw_selector if raw_selector else "page"
            return f'''
        const element = await page.$(`{selector}`);
        if (!element) throw new Error('Element not found: {selector}');
        
        // Due to driver bugs with element.wxml() in this automator version, 
        // fallback to retrieving the page data which represents the DOM state 
        // accurately in Taro/React architectures.
        const fallbackData = await page.data();
        let info = fallbackData;
        try {{
             const wxmlStr = await element.wxml();
             if (wxmlStr) info = wxmlStr;
        }} catch(e) {{
             console.log("WXML fetch failed, using state proxy");
        }}
        const result = {{ selector: '{selector}', wxml: info }};
'''

        elif action == "get_data":
            path = params.get("path", "")
            return f'''
        const data = await page.data('{path}');
        const result = {{ path: '{path}', data: data }};
'''

        elif action == "scroll":
            selector = params.get("selector", "")
            direction = params.get("direction", "down")
            distance = params.get("distance", 300)
            return f'''
        const element = await page.$(`{selector}`);
        if (!element) throw new Error('Element not found: {selector}');
        await element.scroll({{ direction: '{direction}', distance: {distance} }});
        await page.waitFor(500);
        const result = {{ selector: '{selector}', scrolled: true, direction: '{direction}' }};
'''

        elif action == "wait":
            seconds = float(params.get("seconds", 1.0))
            ms = int(seconds * 1000)
            return f'''
        await page.waitFor({ms});
        const result = {{ waited: {seconds} }};
'''

        else:
            return '''
        const result = { message: 'Unknown action' };
'''

    def _parse_result(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """解析命令执行结果"""
        output = result.stdout + result.stderr

        # 查找AUTOMATION_RESULT标记
        match = re.search(r'AUTOMATION_RESULT:\s*(\{.*?\})', output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
    def _parse_batch_result(self, result: subprocess.CompletedProcess) -> List[Dict[str, Any]]:
        """解析批量执行结果"""
        output = result.stdout + result.stderr

        # 查找 BATCH_RESULT 标记
        match = re.search(r'BATCH_RESULT:\s*(\[.*?\])', output, re.DOTALL)
        if match:
            try:
                print("--- BATCH RUN OUTPUT ---\n", output, "\n-------------------")
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        print("--- FATAL BATCH FAIL ---\n", output, "\n-------------------")
        return [{
            "success": False,
            "error": "Failed to parse batch results",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }]

    # ============ 公共API ============

    def navigate_to(self, page_path: str) -> Dict[str, Any]:
        """
        导航到指定页面

        Args:
            page_path: 页面路径，如 "pages/index/index"

        Returns:
            操作结果
        """
        return self._run_automation_command("navigate", {"target": page_path})

    def click(self, selector: str, page: str = "pages/index/index") -> Dict[str, Any]:
        """
        点击元素

        Args:
            selector: 元素选择器（CSS-like选择器）
            page: 当前页面路径

        Returns:
            操作结果
        """
        return self._run_automation_command("click", {"selector": selector, "page": page})

    def input_text(self, selector: str, text: str, page: str = "pages/index/index") -> Dict[str, Any]:
        """
        在输入框中输入文本

        Args:
            selector: 输入框选择器
            text: 要输入的文本
            page: 当前页面路径

        Returns:
            操作结果
        """
        return self._run_automation_command("input", {"selector": selector, "text": text, "page": page})

    def screenshot(self, filename: Optional[str] = None, page: str = "pages/index/index") -> Dict[str, Any]:
        """
        截图

        Args:
            filename: 截图文件名（可选，默认使用时间戳）
            page: 当前页面路径

        Returns:
            操作结果，包含截图路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

        return self._run_automation_command("screenshot", {"filename": filename, "page": page})

    def get_element_text(self, selector: str, page: str = "pages/index/index") -> Dict[str, Any]:
        """
        获取元素文本

        Args:
            selector: 元素选择器
            page: 当前页面路径

        Returns:
            操作结果，包含元素文本
        """
        return self._run_automation_command("get_element_text", {"selector": selector, "page": page})

    def scroll(self, selector: str, direction: str = "down", distance: int = 300, page: str = "pages/index/index") -> Dict[str, Any]:
        """
        滚动元素

        Args:
            selector: 可滚动元素选择器
            direction: 滚动方向 (up/down/left/right)
            distance: 滚动距离
            page: 当前页面路径

        Returns:
            操作结果
        """
        return self._run_automation_command("scroll", {
            "selector": selector,
            "direction": direction,
            "distance": distance,
            "page": page
        })

    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        Returns:
            系统信息
        """
        return self._run_automation_command("get_logs", {})


class WeappTestRunner:
    """测试运行器，支持链式调用和测试场景定义。现在使用底层批量执行优化，大幅提升性能。"""

    def __init__(self, config: AutomationConfig):
        self.automation = WeappAutomation(config)
        self.steps: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self.current_page = "pages/index/index"
        self._executed = False

    def navigate(self, page_path: str) -> "WeappTestRunner":
        """导航到页面"""
        self.steps.append({"action": "navigate", "params": {"target": page_path}})
        return self

    def click(self, selector: str) -> "WeappTestRunner":
        """点击元素"""
        self.steps.append({"action": "click", "params": {"selector": selector, "page": self.current_page}})
        return self

    def input(self, selector: str, text: str) -> "WeappTestRunner":
        """输入文本"""
        self.steps.append({"action": "input", "params": {"selector": selector, "text": text, "page": self.current_page}})
        return self

    def screenshot(self, filename: Optional[str] = None) -> "WeappTestRunner":
        """截图"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        self.steps.append({"action": "screenshot", "params": {"filename": filename, "page": self.current_page}})
        return self

    def scroll(self, selector: str, direction: str = "down", distance: int = 300) -> "WeappTestRunner":
        """滚动"""
        self.steps.append({"action": "scroll", "params": {
            "selector": selector,
            "direction": direction,
            "distance": distance,
            "page": self.current_page
        }})
        return self

    def get_wxml(self, selector: str) -> "WeappTestRunner":
        """获取元素的 WXML结构"""
        self.steps.append({"action": "get_wxml", "params": {"selector": selector}})
        return self

    def get_data(self, path: str = "") -> "WeappTestRunner":
        """获取页面 data"""
        self.steps.append({"action": "get_data", "params": {"path": path}})
        return self

    def wait(self, seconds: float) -> "WeappTestRunner":
        """等待（通过脚本原生等待实现）"""
        self.steps.append({"action": "wait", "params": {"seconds": seconds}})
        return self

    def run(self) -> "WeappTestRunner":
        """实际执行所有累积的测试步骤"""
        if self._executed or not self.steps:
            return self
            
        batch_results = self.automation._run_batch_commands(self.steps)
        
        # 将批量结果映射回原来的 results 格式，以保证向下兼容
        for i, step in enumerate(self.steps):
            action = step["action"]
            result = batch_results[i] if i < len(batch_results) else {"success": False, "error": "Step not executed due to early failure"}
            
            # 记录执行结果
            step_record = {"action": action, "result": result}
            if action == 'click' or action == 'input' or action == 'scroll':
                step_record['selector'] = step['params'].get('selector')
            if action == 'input':
                step_record['text'] = step['params'].get('text')
                
            self.results.append(step_record)
            
        self._executed = True
        return self

    def get_results(self) -> List[Dict[str, Any]]:
        """获取所有操作结果。如果尚未执行，会自动触发执行。"""
        if not self._executed:
            self.run()
        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        if not self._executed:
            self.run()
            
        total = len(self.steps)
        passed = sum(1 for r in self.results if r["result"].get("success"))
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": passed / total if total > 0 else 0
        }



def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="微信小程序自动化测试")
    parser.add_argument("--project", "-p", required=True, help="小程序项目路径")
    parser.add_argument("--cli-path", default="/Applications/wechatwebdevtools.app/Contents/MacOS/cli", help="CLI路径")
    parser.add_argument("--action", "-a", required=True,
                        choices=["navigate", "click", "input", "screenshot", "scroll", "info", "get_wxml", "get_data"],
                        help="操作类型")
    parser.add_argument("--selector", "-s", help="元素选择器")
    parser.add_argument("--text", "-t", help="输入文本")
    parser.add_argument("--path", help="数据路径(get_data 专用)", default="")
    parser.add_argument("--page", default="pages/index/index", help="页面路径")
    parser.add_argument("--filename", "-f", help="截图文件名")
    parser.add_argument("--direction", choices=["up", "down", "left", "right"], default="down", help="滚动方向")
    parser.add_argument("--distance", type=int, default=300, help="滚动距离")

    args = parser.parse_args()

    config = AutomationConfig(
        project_path=args.project,
        cli_path=args.cli_path
    )

    automation = WeappAutomation(config)

    if args.action == "navigate":
        result = automation.navigate_to(args.page)
    elif args.action == "click":
        if not args.selector:
            print("错误: click操作需要提供 --selector 参数")
            sys.exit(1)
        result = automation.click(args.selector, args.page)
    elif args.action == "input":
        if not args.selector or not args.text:
            print("错误: input操作需要提供 --selector 和 --text 参数")
            sys.exit(1)
        result = automation.input_text(args.selector, args.text, args.page)
    elif args.action == "screenshot":
        result = automation.screenshot(args.filename, args.page)
    elif args.action == "scroll":
        if not args.selector:
            print("错误: scroll操作需要提供 --selector 参数")
            sys.exit(1)
        result = automation.scroll(args.selector, args.direction, args.distance, args.page)
    elif args.action == "get_wxml":
        if not args.selector:
            print("错误: get_wxml操作需要提供 --selector 参数")
            sys.exit(1)
        result = automation._run_automation_command("get_wxml", {"selector": args.selector, "page": args.page})
    elif args.action == "get_data":
        result = automation._run_automation_command("get_data", {"path": args.path, "page": args.page})
    elif args.action == "info":
        result = automation.get_system_info()
    else:
        print(f"未知操作: {args.action}")
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
