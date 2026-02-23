# WeApp Automation

微信小程序自动化测试工具集，支持启动微信开发者工具、页面导航、元素操作、截图对比、控制台日志读取等功能。

## ✨ 特性

- 🚀 **启动控制** - 启动/关闭微信开发者工具，开启自动化测试端口
- 📝 **页面自动化** - 支持点击、输入、滚动、截图等操作
- 🔍 **元素检查** - 读取 WXML 节点结构、获取页面 Data 数据
- 📸 **自动截图** - 全自动截图验证，支持批量操作
- 📊 **日志监控** - 读取控制台日志、错误捕获、性能监控
- 🧪 **测试场景** - 冒烟测试、UI 回归测试、用户旅程测试
- ⚡ **高性能** - 批量脚本打包执行，毫秒级高并发操作

## 📋 前置条件

### 1. 安装微信开发者工具

下载并安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)

### 2. 开启服务端口

1. 打开微信开发者工具
2. 设置 -> 安全设置 -> 开启"服务端口"

### 3. 安装 Python 依赖

```bash
pip install miniprogram-automator
```

或使用 npx（无需全局安装）：

```bash
npx miniprogram-automator --help
```

## 🚀 快速开始

### 启动开发者工具

```bash
python scripts/weapp_launcher.py --project /path/to/miniprogram --action open
```

### 运行自动化测试

```python
from scripts.weapp_automation import AutomationConfig, WeappTestRunner

# 创建配置
config = AutomationConfig(
    project_path="/path/to/miniprogram",
    cli_path="/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
)

# 创建测试运行器
runner = WeappTestRunner(config)

# 链式调用执行测试
result = (runner
    .navigate("pages/index/index")
    .wait(2)
    .screenshot("home.png")
    .click(".category-item")
    .wait(1)
    .screenshot("category.png")
    .get_results())

print(runner.get_summary())
```

### 命令行使用

```bash
# 导航到指定页面
python scripts/weapp_automation.py -p /path/to/miniprogram -a navigate --page pages/index/index

# 点击元素
python scripts/weapp_automation.py -p /path/to/miniprogram -a click -s ".button"

# 输入文本
python scripts/weapp_automation.py -p /path/to/miniprogram -a input -s "input" -t "hello"

# 截图
python scripts/weapp_automation.py -p /path/to/miniprogram -a screenshot -f test.png

# 获取 WXML 结构
python scripts/weapp_automation.py -p /path/to/miniprogram -a get_wxml -s ".hero-title"

# 获取页面 Data
python scripts/weapp_automation.py -p /path/to/miniprogram -a get_data --path "diseaseInfo"
```

## 📦 模块说明

| 模块 | 文件 | 功能 |
|------|------|------|
| 启动器 | `weapp_launcher.py` | 控制微信开发者工具的启动和关闭 |
| 自动化核心 | `weapp_automation.py` | 页面导航、元素操作、截图、批量执行 |
| 日志读取 | `console_reader.py` | 读取控制台日志、错误分析、性能监控 |
| 测试场景 | `test_scenarios.py` | 冒烟测试、回归测试、用户旅程测试 |

## 🎯 测试场景

### 冒烟测试

```bash
python scripts/test_scenarios.py -p /path/to/miniprogram -s smoke
```

### UI 回归测试

```bash
python scripts/test_scenarios.py -p /path/to/miniprogram -s ui --pages "pages/index/index,pages/profile/profile"
```

### 用户旅程测试

```python
from scripts.test_scenarios import TestScenarios

scenarios = TestScenarios("/path/to/miniprogram")

steps = [
    {"action": "navigate", "page": "pages/index/index"},
    {"action": "click", "selector": ".product"},
    {"action": "click", "selector": ".add-to-cart"},
    {"action": "navigate", "page": "pages/cart/cart"},
    {"action": "screenshot", "filename": "cart.png"}
]

result = scenarios.user_journey_test(steps)
```

## 🔧 配置选项

### AutomationConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `project_path` | str | 必填 | 小程序项目根目录路径 |
| `cli_path` | str | macOS 默认路径 | 微信开发者工具 CLI 路径 |
| `screenshot_dir` | str | `./screenshots` | 截图保存目录 |
| `timeout` | int | 30 | 操作超时时间（秒） |
| `ws_endpoint` | str | `ws://localhost:9420` | WebSocket 端点 |

### CLI 路径配置

**macOS（默认）：**
```
/Applications/wechatwebdevtools.app/Contents/MacOS/cli
```

**Windows：**
```
C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat
```

## 🎨 选择器语法

使用类似 CSS 的选择器定位元素：

| 选择器 | 示例 | 说明 |
|--------|------|------|
| 类选择器 | `.button` | 选择 class 为 button 的元素 |
| ID 选择器 | `#submit` | 选择 id 为 submit 的元素 |
| 标签选择器 | `view` | 选择 view 组件 |
| 属性选择器 | `[data-id='123']` | 选择 data-id 属性为 123 的元素 |
| 后代选择器 | `.list .item` | 选择 list 内的 item |

## 📊 日志监控

```bash
# 读取控制台日志
python scripts/console_reader.py -p /path/to/miniprogram -a read

# 导出错误报告
python scripts/console_reader.py -p /path/to/miniprogram -a export --format markdown -o report.md
```

```python
from scripts.console_reader import ConsoleReader, LogLevel

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

## ⚠️ 常见问题

### 连接失败

**问题**: `Error: connect ECONNREFUSED`

**解决**:
1. 确认开发者工具已打开
2. 检查"服务端口"是否开启
3. 确认项目已导入开发者工具

### 元素找不到

**问题**: `Element not found`

**解决**:
1. 确认页面已完全加载（使用 wait）
2. 检查选择器是否正确
3. 确认元素在当前页面可见

### 截图失败

**问题**: 截图文件为空或不存在

**解决**:
1. 确认 screenshot_dir 目录存在且有写入权限
2. 检查页面是否已渲染完成

## 📄 许可证

[MIT](../LICENSE)
