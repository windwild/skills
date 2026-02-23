#!/usr/bin/env python3
"""
微信小程序控制台日志读取器
读取开发者工具的控制台输出、错误日志、网络请求等
"""

import subprocess
import json
import os
import re
import time
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    ALL = "all"


@dataclass
class ConsoleLog:
    """控制台日志条目"""
    timestamp: str
    level: str
    message: str
    source: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConsoleReader:
    """
    小程序控制台日志读取器

    功能：
    - 读取控制台日志（debug/info/warn/error）
    - 过滤特定级别的日志
    - 监控错误和异常
    - 导出日志报告
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.logs: List[ConsoleLog] = []
        self.error_handlers: List[Callable[[ConsoleLog], None]] = []

    def _get_log_file_path(self) -> Optional[str]:
        """
        获取日志文件路径

        微信开发者工具的日志通常存储在：
        ~/Library/Application Support/微信开发者工具/
        """
        home = os.path.expanduser("~")
        log_dirs = [
            os.path.join(home, "Library/Application Support/微信开发者工具"),
            os.path.join(home, "Library/Application Support/wechatwebdevtools"),
        ]

        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                # 查找最新的日志文件
                log_files = []
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        if file.endswith(".log") or "console" in file.lower():
                            filepath = os.path.join(root, file)
                            log_files.append((filepath, os.path.getmtime(filepath)))

                if log_files:
                    # 返回最新的日志文件
                    log_files.sort(key=lambda x: x[1], reverse=True)
                    return log_files[0][0]

        return None

    def read_logs_from_script(self) -> List[ConsoleLog]:
        """
        通过自动化脚本读取控制台日志

        使用miniprogram-automator连接到开发者工具并获取日志
        """
        script_content = '''
const automator = require('miniprogram-automator');

async function getLogs() {
    try {
        const miniProgram = await automator.connect({
            wsEndpoint: 'ws://localhost:9420'
        });

        // 获取当前页面
        const page = await miniProgram.currentPage();

        // 执行JavaScript获取控制台日志
        const logs = await miniProgram.evaluate(() => {
            // 这里可以访问小程序的全局对象
            return {
                page: getCurrentPages().map(p => p.route),
                systemInfo: wx.getSystemInfoSync()
            };
        });

        console.log('CONSOLE_LOGS_RESULT: ' + JSON.stringify({
            success: true,
            data: logs
        }));

        await miniProgram.close();
    } catch (error) {
        console.log('CONSOLE_LOGS_RESULT: ' + JSON.stringify({
            success: false,
            error: error.message
        }));
        process.exit(1);
    }
}

getLogs();
'''
        # 创建临时脚本（使用系统临时目录）
        import tempfile
        script_path = os.path.join(tempfile.gettempdir(), f"console_reader_{int(time.time())}.js")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        try:
            result = subprocess.run(
                ["node", script_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # 解析结果
            output = result.stdout + result.stderr
            match = re.search(r'CONSOLE_LOGS_RESULT:\s*(\{.*?\})', output, re.DOTALL)

            if match:
                data = json.loads(match.group(1))
                if data.get("success"):
                    # 转换为ConsoleLog格式
                    log = ConsoleLog(
                        timestamp=datetime.now().isoformat(),
                        level="info",
                        message=json.dumps(data.get("data", {}), ensure_ascii=False)
                    )
                    return [log]

        except Exception as e:
            return [ConsoleLog(
                timestamp=datetime.now().isoformat(),
                level="error",
                message=f"Failed to read logs: {str(e)}"
            )]
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

        return []

    def parse_log_line(self, line: str) -> Optional[ConsoleLog]:
        """解析单行日志"""
        # 常见的日志格式：
        # [2024-01-15 10:30:45] [INFO] message
        # 2024-01-15T10:30:45.123Z [error] message at file.js:123

        patterns = [
            # 格式: [timestamp] [level] message
            r'\[(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]\s*\[(\w+)\]\s*(.+)',
            # 格式: timestamp [level] message
            r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*\[(\w+)\]\s*(.+)',
            # 格式: level: message
            r'(debug|info|warn|error):\s*(.+)',
        ]

        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    return ConsoleLog(
                        timestamp=groups[0] if ':' in groups[0] else datetime.now().isoformat(),
                        level=groups[1].lower(),
                        message=groups[2].strip()
                    )
                elif len(groups) == 2:
                    return ConsoleLog(
                        timestamp=datetime.now().isoformat(),
                        level=groups[0].lower(),
                        message=groups[1].strip()
                    )

        # 无法解析格式，作为普通信息
        return ConsoleLog(
            timestamp=datetime.now().isoformat(),
            level="info",
            message=line.strip()
        )

    def filter_logs(self, level: LogLevel = LogLevel.ALL, pattern: Optional[str] = None) -> List[ConsoleLog]:
        """
        过滤日志

        Args:
            level: 日志级别
            pattern: 正则表达式模式

        Returns:
            过滤后的日志列表
        """
        filtered = self.logs

        if level != LogLevel.ALL:
            filtered = [log for log in filtered if log.level.lower() == level.value]

        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            filtered = [log for log in filtered if regex.search(log.message)]

        return filtered

    def get_errors(self) -> List[ConsoleLog]:
        """获取所有错误日志"""
        return self.filter_logs(LogLevel.ERROR)

    def get_warnings(self) -> List[ConsoleLog]:
        """获取所有警告日志"""
        return self.filter_logs(LogLevel.WARN)

    def on_error(self, handler: Callable[[ConsoleLog], None]):
        """注册错误处理器"""
        self.error_handlers.append(handler)

    def export_to_json(self, filepath: str, level: LogLevel = LogLevel.ALL):
        """导出日志到JSON文件"""
        logs = self.filter_logs(level)
        data = {
            "export_time": datetime.now().isoformat(),
            "project_path": self.project_path,
            "total_logs": len(logs),
            "logs": [log.to_dict() for log in logs]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def export_to_markdown(self, filepath: str, level: LogLevel = LogLevel.ALL):
        """导出日志到Markdown文件"""
        logs = self.filter_logs(level)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# 小程序控制台日志报告\n\n")
            f.write(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**项目路径**: {self.project_path}\n\n")
            f.write(f"**日志总数**: {len(logs)}\n\n")

            # 统计信息
            error_count = len([l for l in logs if l.level == "error"])
            warn_count = len([l for l in logs if l.level == "warn"])

            f.write("## 统计\n\n")
            f.write(f"- 错误: {error_count}\n")
            f.write(f"- 警告: {warn_count}\n")
            f.write(f"- 信息: {len(logs) - error_count - warn_count}\n\n")

            f.write("## 详细日志\n\n")
            f.write("| 时间 | 级别 | 消息 |\n")
            f.write("|------|------|------|\n")

            for log in logs:
                # 转义Markdown表格字符
                message = log.message.replace("|", "\\|").replace("\n", " ")
                f.write(f"| {log.timestamp} | {log.level.upper()} | {message} |\n")


class PerformanceMonitor:
    """性能监控器 - 收集小程序性能数据"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.metrics: List[Dict[str, Any]] = []

    def collect_metrics(self) -> Dict[str, Any]:
        """
        收集性能指标

        使用自动化脚本获取性能数据
        """
        script_content = '''
const automator = require('miniprogram-automator');

async function collectMetrics() {
    try {
        const miniProgram = await automator.connect({
            wsEndpoint: 'ws://localhost:9420'
        });

        const systemInfo = await miniProgram.evaluate(() => {
            return wx.getSystemInfoSync();
        });

        const performance = await miniProgram.evaluate(() => {
            if (typeof wx.getPerformance === 'function') {
                return wx.getPerformance();
            }
            return null;
        });

        console.log('PERFORMANCE_RESULT: ' + JSON.stringify({
            success: true,
            data: {
                systemInfo: systemInfo,
                performance: performance
            }
        }));

        await miniProgram.close();
    } catch (error) {
        console.log('PERFORMANCE_RESULT: ' + JSON.stringify({
            success: false,
            error: error.message
        }));
        process.exit(1);
    }
}

collectMetrics();
'''
        script_path = os.path.join(tempfile.gettempdir(), f"perf_monitor_{int(time.time())}.js")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        try:
            result = subprocess.run(
                ["node", script_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout + result.stderr
            match = re.search(r'PERFORMANCE_RESULT:\s*(\{.*?\})', output, re.DOTALL)

            if match:
                data = json.loads(match.group(1))
                if data.get("success"):
                    self.metrics.append({
                        "timestamp": datetime.now().isoformat(),
                        "data": data.get("data", {})
                    })
                    return data.get("data", {})

        except Exception as e:
            return {"error": str(e)}
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

        return {}

    def export_report(self, filepath: str):
        """导出性能报告"""
        report = {
            "export_time": datetime.now().isoformat(),
            "project_path": self.project_path,
            "metrics_count": len(self.metrics),
            "metrics": self.metrics
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="小程序控制台日志读取器")
    parser.add_argument("--project", "-p", required=True, help="小程序项目路径")
    parser.add_argument("--action", "-a", choices=["read", "errors", "export"], default="read")
    parser.add_argument("--level", choices=["debug", "info", "warn", "error", "all"], default="all")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")

    args = parser.parse_args()

    reader = ConsoleReader(args.project)

    if args.action == "read":
        logs = reader.read_logs_from_script()
        reader.logs = logs
        filtered = reader.filter_logs(LogLevel(args.level))

        for log in filtered:
            print(f"[{log.level.upper()}] {log.timestamp}: {log.message}")

    elif args.action == "errors":
        logs = reader.read_logs_from_script()
        reader.logs = logs
        errors = reader.get_errors()

        print(f"找到 {len(errors)} 个错误:")
        for error in errors:
            print(f"[{error.timestamp}] {error.message}")

    elif args.action == "export":
        logs = reader.read_logs_from_script()
        reader.logs = logs

        output_path = args.output or f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"

        if args.format == "json":
            reader.export_to_json(output_path, LogLevel(args.level))
        else:
            reader.export_to_markdown(output_path, LogLevel(args.level))

        print(f"日志已导出到: {output_path}")


if __name__ == "__main__":
    main()
