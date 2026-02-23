---
name: weapp-automation
description: 微信小程序自动化测试工具集，支持启动微信开发者工具、页面导航、元素操作、截图、控制台日志读取等功能。用于功能测试、UI回归测试、性能监控等场景。当用户需要自动化测试小程序、控制微信开发者工具、读取小程序控制台日志或进行UI截图对比时触发此skill。
---

# 微信小程序自动化测试

## 概述

本skill提供完整的微信小程序自动化测试能力，包括：

1. **启动控制** - 启动/关闭微信开发者工具
2. **页面自动化** - 📝 文本长链输入
- 📸 全自动截图验证
- 🧩 读取 WXML 节点结构
- 📦 读取页面 Data 数据
- 🚀 支持批量脚本打包执行（毫秒级高并发操作）
3. **日志监控** - 读取控制台日志、错误捕获、性能监控
4. **测试场景** - 冒烟测试、UI回归测试、用户旅程测试

## 前置条件

### 1. 安装依赖

```bash
npm install -g miniprogram-automator
```

或使用 npx（无需全局安装）：

```bash
npx miniprogram-automator --help
```

### Fetch DOM / Data Attributes
You can now read the data and internal rendering tree to assert if classes/data are correctly attached before taking a screenshot.

```python
runner.navigate("pages/index/index")
runner.get_wxml(".hero-title") # Extract WXML DOM structure to ensure class rendering is correct
runner.get_data("diseaseInfo") # Read page's internal `data.diseaseInfo`
result = runner.run().get_results()

# For CLI:
# python scripts/weapp_automation.py -p /path/to/project -a get_wxml -s ".hero-title"
# python scripts/weapp_automation.py -p /path/to/project -a get_data --path "diseaseInfo"
```

## Quick Start (For Developers)

### 2. 配置开发者工具

1. 打开微信开发者工具
2. 设置 -> 安全设置 -> 开启"服务端口"
3. 确保项目已导入开发者工具

### 3. 确认CLI路径

根据操作系统选择正确的CLI路径：

**macOS（默认）：**
```
/Applications/wechatwebdevtools.app/Contents/MacOS/cli
```

**Windows：**
```
C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat
```

**自定义配置：**
如果开发者工具使用非默认端口（9420），可在配置中指定：
```python
config = AutomationConfig(
    project_path="/path/to/miniprogram",
    ws_endpoint="ws://localhost:9420"  # 自定义WebSocket端口
)
```

## 快速开始

### 基本使用流程

```python
from weapp_launcher import WeappLauncher
from weapp_automation import AutomationConfig, WeappTestRunner

# 1. 启动开发者工具
launcher = WeappLauncher()
launcher.open_project("/path/to/miniprogram")

# 2. 创建测试配置
config = AutomationConfig(
    project_path="/path/to/miniprogram",
    cli_path="/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
)

# 3. 执行测试
runner = WeappTestRunner(config)
result = (runner
    .navigate("pages/index/index")
    .screenshot("home.png")
    .click(".button")
    .screenshot("after_click.png")
    .get_results())

# 4. 查看结果
print(runner.get_summary())
```

## 核心功能

### 1. 启动器 (weapp_launcher.py)

控制微信开发者工具的启动和关闭。

```python
from weapp_launcher import WeappLauncher

launcher = WeappLauncher()

# 打开项目
launcher.open_project("/path/to/miniprogram")

# 关闭项目
launcher.close_project("/path/to/miniprogram")

# 退出开发者工具
launcher.quit_wechatdevtools()
```

### 2. 自动化操作 (weapp_automation.py)

执行页面自动化操作。

```python
from weapp_automation import AutomationConfig, WeappAutomation

config = AutomationConfig(project_path="/path/to/miniprogram")
auto = WeappAutomation(config)

# 导航
auto.navigate_to("pages/detail/detail")

# 点击元素
auto.click(".submit-button")

# 输入文本
auto.input_text("input[name='search']", "关键词")

# 截图
auto.screenshot("result.png")

# 滚动
auto.scroll(".scroll-view", "down", 500)

# 获取元素文本
result = auto.get_element_text(".title")
print(result["data"]["text"])
```

### 3. 高性能链式测试运行器 (Batch Executor)

使用流畅的链式 API 编写测试流程。引擎底层会自动将所有 actions 打包为单独的一个 Node.js 脚本，并复用同一个 WebSocket 进行批量处理，极大提升了测试渲染速度与连接稳定性。

```python
from weapp_automation import WeappTestRunner

runner = WeappTestRunner(config)

# 所有的操作会被收集，直到调用 get_results() 或 run() 时才真正连通 DevTools 一次性执行
result = (runner
    .navigate("pages/index/index")
    .wait(2)
    .screenshot("home.png")
    .click(".category-item")
    .wait(1)
    .screenshot("category.png")
    .scroll(".product-list", "down", 800)
    .screenshot("scrolled.png")
    .get_results())

summary = runner.get_summary()
print(f"通过: {summary['passed']}/{summary['total']}")
```

### 4. 控制台日志 (console_reader.py)

读取和分析小程序控制台日志。

```python
from console_reader import ConsoleReader, LogLevel

reader = ConsoleReader("/path/to/miniprogram")

# 读取日志
logs = reader.read_logs_from_script()

# 获取错误
errors = reader.get_errors()
for error in errors:
    print(f"[ERROR] {error.message}")

# 导出报告
reader.export_to_markdown("logs_report.md")
```

### 5. 性能监控

```python
from console_reader import PerformanceMonitor

monitor = PerformanceMonitor("/path/to/miniprogram")
metrics = monitor.collect_metrics()
monitor.export_report("performance.json")
```

## 测试场景 (test_scenarios.py)

预定义的测试场景模板。

### 冒烟测试

```python
from test_scenarios import TestScenarios

scenarios = TestScenarios("/path/to/miniprogram")
result = scenarios.smoke_test()
```

### 导航流程测试

```python
pages = ["pages/index/index", "pages/category/category", "pages/cart/cart"]
result = scenarios.navigation_flow_test(pages)
```

### 表单提交测试

```python
form_data = {
    "input[name='username']": "testuser",
    "input[name='email']": "test@example.com"
}
result = scenarios.form_submission_test(form_data)
```

### UI回归测试

```python
pages = ["pages/index/index", "pages/profile/profile"]
result = scenarios.ui_regression_test(pages, baseline_dir="./baseline")
```

### 用户旅程测试

```python
steps = [
    {"action": "navigate", "page": "pages/index/index"},
    {"action": "click", "selector": ".product"},
    {"action": "click", "selector": ".add-to-cart"},
    {"action": "navigate", "page": "pages/cart/cart"},
    {"action": "screenshot", "filename": "cart.png"}
]
result = scenarios.user_journey_test(steps)
```

## 命令行使用

### 启动器

```bash
python scripts/weapp_launcher.py --project /path/to/miniprogram --action open
python scripts/weapp_launcher.py --project /path/to/miniprogram --action quit
```

### 自动化操作

```bash
# 导航
python scripts/weapp_automation.py -p /path/to/miniprogram -a navigate --page pages/index/index

# 点击
python scripts/weapp_automation.py -p /path/to/miniprogram -a click -s ".button"

# 输入
python scripts/weapp_automation.py -p /path/to/miniprogram -a input -s "input" -t "hello"

# 截图
python scripts/weapp_automation.py -p /path/to/miniprogram -a screenshot -f test.png

# 滚动
python scripts/weapp_automation.py -p /path/to/miniprogram -a scroll -s ".scroll-view" --direction down --distance 500
```

### 控制台日志

```bash
# 读取日志
python scripts/console_reader.py -p /path/to/miniprogram -a read

# 导出错误报告
python scripts/console_reader.py -p /path/to/miniprogram -a export --format markdown -o report.md
```

### 测试场景

```bash
# 冒烟测试
python scripts/test_scenarios.py -p /path/to/miniprogram -s smoke

# 导航测试
python scripts/test_scenarios.py -p /path/to/miniprogram -s navigation --pages "pages/index/index,pages/about/about"

# UI回归测试
python scripts/test_scenarios.py -p /path/to/miniprogram -s ui --pages "pages/index/index,pages/profile/profile"
```

## 选择器语法

使用类似CSS的选择器定位元素：

| 选择器 | 示例 | 说明 |
|--------|------|------|
| 类选择器 | `.button` | 选择class为button的元素 |
| ID选择器 | `#submit` | 选择id为submit的元素 |
| 标签选择器 | `view` | 选择view组件 |
| 属性选择器 | `[data-id='123']` | 选择data-id属性为123的元素 |
| 后代选择器 | `.list .item` | 选择list内的item |

## 常见问题

### 连接失败

**问题**: `Error: connect ECONNREFUSED`

**解决**:
1. 确认开发者工具已打开
2. 检查"服务端口"是否开启
3. 确认项目已导入开发者工具

### 元素找不到

**问题**: `Element not found`

**解决**:
1. 确认页面已完全加载（使用wait）
2. 检查选择器是否正确
3. 确认元素在当前页面可见

### 截图失败

**问题**: 截图文件为空或不存在

**解决**:
1. 确认screenshot_dir目录存在且有写入权限
2. 检查页面是否已渲染完成

## 参考文档

详细API文档参见 [references/api_reference.md](references/api_reference.md)

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `scripts/weapp_launcher.py` | 启动/关闭开发者工具 |
| `scripts/weapp_automation.py` | 页面自动化操作 |
| `scripts/console_reader.py` | 控制台日志读取 |
| `scripts/test_scenarios.py` | 预定义测试场景 |
