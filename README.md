# Skills

个人技能集合仓库，包含各种自动化工具和 Claude Code Skill 定义。

## 📦 Skills 列表

| Skill | 目录 | 描述 |
|-------|------|------|
| **WeApp Automation** | [`weapp-automation/`](weapp-automation/) | 微信小程序自动化测试工具集 |

---

## 🔧 WeApp Automation

微信小程序自动化测试工具集，支持启动微信开发者工具、页面导航、元素操作、截图对比、控制台日志读取等功能。

### 特性

- 🚀 **启动控制** - 启动/关闭微信开发者工具，开启自动化测试端口
- 📝 **页面自动化** - 支持点击、输入、滚动、截图等操作
- 🔍 **元素检查** - 读取 WXML 节点结构、获取页面 Data 数据
- 📸 **自动截图** - 全自动截图验证，支持批量操作
- 📊 **日志监控** - 读取控制台日志、错误捕获、性能监控
- 🧪 **测试场景** - 冒烟测试、UI 回归测试、用户旅程测试
- ⚡ **高性能** - 批量脚本打包执行，毫秒级高并发操作

### 快速开始

```bash
cd weapp-automation

# 启动开发者工具
python scripts/weapp_launcher.py --project /path/to/miniprogram --action open

# 运行自动化测试
python scripts/weapp_automation.py -p /path/to/miniprogram -a screenshot -f test.png
```

更多详情查看 [`weapp-automation/README.md`](weapp-automation/)

---

## 🚀 添加新 Skill

要添加新的 skill，创建一个新的子目录：

```
skills/
├── README.md           # 本文件
├── weapp-automation/   # 现有 skill
└── your-new-skill/     # 新 skill
    ├── SKILL.md
    ├── README.md
    └── ...
```

### Skill 结构规范

每个 skill 目录应包含：

- `SKILL.md` - Claude Code Skill 定义文件（元数据、功能描述、使用示例）
- `README.md` - 用户文档（安装、配置、API 参考）
- 代码文件和配置

---

## 📄 许可证

[MIT](LICENSE)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
