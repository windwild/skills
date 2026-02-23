# 微信小程序自动化测试 API 参考

## 目录

1. [启动器 API](#启动器-api)
2. [自动化 API](#自动化-api)
3. [控制台读取 API](#控制台读取-api)
4. [测试场景 API](#测试场景-api)

---

## 启动器 API

### WeappLauncher 类

用于启动和控制微信开发者工具。

#### 初始化

```python
from weapp_launcher import WeappLauncher

launcher = WeappLauncher(cli_path="/Applications/wechatwebdevtools.app/Contents/MacOS/cli")
```

#### 方法

##### open_project(project_path, auto_preview=False)

打开小程序项目。

**参数：**
- `project_path` (str): 小程序项目根目录路径
- `auto_preview` (bool): 是否自动打开预览

**返回：**
```python
{
    "success": True,
    "stdout": "...",
    "stderr": "..."
}
```

##### close_project(project_path)

关闭小程序项目。

##### quit_wechatdevtools()

退出微信开发者工具。

##### auto_test(project_path, test_script_path)

执行自动化测试脚本。

##### is_running()

检查开发者工具是否正在运行。

---

## 自动化 API

### AutomationConfig 配置类

```python
from weapp_automation import AutomationConfig

config = AutomationConfig(
    project_path="/path/to/miniprogram",
    cli_path="/Applications/wechatwebdevtools.app/Contents/MacOS/cli",
    screenshot_dir="./screenshots",
    timeout=30,
    ws_endpoint="ws://localhost:9420"  # 可选：自定义WebSocket端口
)
```

### WeappAutomation 类

核心自动化控制类。

#### navigate_to(page_path)

导航到指定页面。

```python
automation = WeappAutomation(config)
result = automation.navigate_to("pages/index/index")
```

#### click(selector, page="pages/index/index")

点击元素。

```python
result = automation.click(".button-class")
result = automation.click("#submit-btn", "pages/form/form")
```

#### input_text(selector, text, page="pages/index/index")

在输入框中输入文本。

```python
result = automation.input_text("input[name='username']", "testuser")
```

#### screenshot(filename=None, page="pages/index/index")

截图。

```python
result = automation.screenshot("home.png")
# 或自动生成文件名
result = automation.screenshot()
```

#### get_element_text(selector, page="pages/index/index")

获取元素文本。

```python
result = automation.get_element_text(".title")
print(result["data"]["text"])
```

#### scroll(selector, direction="down", distance=300, page="pages/index/index")

滚动元素。

```python
result = automation.scroll(".scroll-view", "down", 500)
```

### WeappTestRunner 类

链式测试运行器。

```python
from weapp_automation import WeappTestRunner

runner = WeappTestRunner(config)

result = (runner
    .navigate("pages/index/index")
    .click(".button")
    .input("input[name='search']", "keyword")
    .screenshot("search_result.png")
    .get_results())

summary = runner.get_summary()
print(f"通过率: {summary['success_rate'] * 100}%")
```

---

## 控制台读取 API

### ConsoleReader 类

读取和分析控制台日志。

```python
from console_reader import ConsoleReader, LogLevel

reader = ConsoleReader("/path/to/project")

# 读取日志
logs = reader.read_logs_from_script()

# 过滤错误
errors = reader.filter_logs(LogLevel.ERROR)

# 导出报告
reader.export_to_markdown("logs_report.md")
```

#### 方法

##### filter_logs(level=LogLevel.ALL, pattern=None)

过滤日志。

```python
# 只获取错误
errors = reader.filter_logs(LogLevel.ERROR)

# 搜索特定内容
logs = reader.filter_logs(pattern="network")
```

##### get_errors()

获取所有错误日志。

##### get_warnings()

获取所有警告日志。

##### export_to_json(filepath, level=LogLevel.ALL)

导出为JSON格式。

##### export_to_markdown(filepath, level=LogLevel.ALL)

导出为Markdown格式。

### PerformanceMonitor 类

性能监控。

```python
from console_reader import PerformanceMonitor

monitor = PerformanceMonitor("/path/to/project")
metrics = monitor.collect_metrics()
monitor.export_report("performance_report.json")
```

---

## 测试场景 API

### TestScenarios 类

预定义测试场景。

```python
from test_scenarios import TestScenarios

scenarios = TestScenarios("/path/to/project")
```

#### smoke_test()

冒烟测试。

```python
result = scenarios.smoke_test()
```

#### navigation_flow_test(pages)

导航流程测试。

```python
result = scenarios.navigation_flow_test([
    "pages/index/index",
    "pages/category/category",
    "pages/detail/detail"
])
```

#### form_submission_test(form_data)

表单提交测试。

```python
result = scenarios.form_submission_test({
    "input[name='username']": "testuser",
    "input[name='password']": "testpass"
})
```

#### ui_regression_test(pages, baseline_dir="./baseline")

UI回归测试。

```python
result = scenarios.ui_regression_test([
    "pages/index/index",
    "pages/profile/profile"
])
```

#### scroll_performance_test(page, scroll_element, scrolls=5)

滚动性能测试。

```python
result = scenarios.scroll_performance_test(
    "pages/list/list",
    ".scroll-view",
    scrolls=10
)
```

#### user_journey_test(steps)

用户旅程测试。

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

---

## 命令行使用

### 启动器

```bash
python weapp_launcher.py --project /path/to/miniprogram --action open
python weapp_launcher.py --project /path/to/miniprogram --action close
python weapp_launcher.py --project /path/to/miniprogram --action quit
```

### 自动化

```bash
# 导航
python weapp_automation.py --project /path/to/miniprogram --action navigate --page pages/index/index

# 点击
python weapp_automation.py --project /path/to/miniprogram --action click --selector ".button"

# 输入
python weapp_automation.py --project /path/to/miniprogram --action input --selector "input" --text "hello"

# 截图
python weapp_automation.py --project /path/to/miniprogram --action screenshot --filename test.png

# 滚动
python weapp_automation.py --project /path/to/miniprogram --action scroll --selector ".scroll-view" --direction down --distance 500
```

### 控制台读取

```bash
# 读取日志
python console_reader.py --project /path/to/miniprogram --action read

# 查看错误
python console_reader.py --project /path/to/miniprogram --action errors

# 导出报告
python console_reader.py --project /path/to/miniprogram --action export --format markdown --output report.md
```

### 测试场景

```bash
# 冒烟测试
python test_scenarios.py --project /path/to/miniprogram --scenario smoke

# 导航测试
python test_scenarios.py --project /path/to/miniprogram --scenario navigation --pages "pages/index/index,pages/about/about"

# UI回归测试
python test_scenarios.py --project /path/to/miniprogram --scenario ui --pages "pages/index/index,pages/profile/profile"
```

---

## 注意事项

1. **依赖安装**：使用前需要安装 `miniprogram-automator`
   ```bash
   npm install miniprogram-automator
   ```

2. **开发者工具设置**：
   - 开启"服务端口"：设置 -> 安全设置 -> 服务端口
   - 确保项目已导入开发者工具

3. **选择器语法**：
   - `.class` - 类选择器
   - `#id` - ID选择器
   - `tag` - 标签选择器
   - `[attr=value]` - 属性选择器

4. **截图目录**：默认保存到 `./screenshots`，可配置
