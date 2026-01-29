# Project Indexer

为大型代码库生成层级化索引，使 AI 助手能够渐进式理解项目结构，而无需超出上下文限制。

## 为什么需要它？

当项目代码量较大时，AI 助手难以一次性理解整个代码库。Project Indexer 通过预构建"认知地图"，让你可以：

- **快速定位** - 初次了解大型项目的结构和架构
- **精准查找** - 定位特定功能的代码位置
- **高效迭代** - 开发时快速找到需要修改的文件
- **突破限制** - 解决项目上下文过大导致 AI 无法一次性理解的问题

## 功能特性

- **多语言支持** - 支持 TypeScript/JavaScript 和 Python
- **增量更新** - 仅重新索引变更文件，节省时间
- **智能忽略** - 自动遵循 `.gitignore` 和 `.indexignore` 规则
- **项目检测** - 自动识别项目类型和技术栈
- **符号提取** - 精确提取类、函数、接口、类型等定义
- **可扩展架构** - 易于添加新语言支持

## 快速开始

### 基本用法

```bash
# 索引当前目录
python project-indexer/scripts/index_project.py

# 索引指定项目
python project-indexer/scripts/index_project.py /path/to/your/project

# 增量更新（仅处理变更文件）
python project-indexer/scripts/index_project.py --update

# 强制完整重建
python project-indexer/scripts/index_project.py --force
```

### 输出结构

运行后会在项目根目录生成 `project-index/` 目录：

```
project-index/
├── INDEX.md              # 总索引（项目概览）
├── .index-meta.json      # 增量更新元数据
└── directories/          # 目录级详细索引
    ├── root.md
    ├── src.md
    └── ...
```

## 支持的语言

| 语言 | 扩展名 | 提取内容 |
|------|--------|----------|
| TypeScript/JavaScript | `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs` | 导出函数、类、接口、类型、常量 |
| Python | `.py`, `.pyi` | 类定义、函数定义（含方法） |

## 项目结构

```
project-index/
├── project-indexer/              # 源代码
│   ├── scripts/
│   │   ├── index_project.py      # 主入口脚本
│   │   ├── parsers/              # 语言解析器
│   │   │   ├── base.py           # 基础解析器抽象类
│   │   │   ├── python_parser.py  # Python 解析器
│   │   │   └── typescript.py     # TypeScript 解析器
│   │   └── utils/                # 工具库
│   │       ├── tree.py           # 目录树生成
│   │       ├── ignore.py         # 忽略规则处理
│   │       └── meta.py           # 增量更新管理
│   ├── references/
│   │   └── supported-languages.md
│   └── SKILL.md                  # 技能文档
├── project-index/                # 生成的索引输出
└── project-indexer.skill         # Claude Code Skill 包
```

## 配置

### 忽略规则

创建 `.indexignore` 文件来自定义忽略规则（语法同 `.gitignore`）：

```gitignore
# 忽略测试文件
**/*.test.ts
**/*.spec.js

# 忽略特定目录
docs/
examples/
```

**默认忽略的目录：**
- `.git`, `node_modules`, `__pycache__`
- `dist`, `build`, `.next`, `.nuxt`
- `venv`, `.venv`, `env`
- 以及所有 `project-index` 输出目录

## 作为 Claude Code Skill 使用

Project Indexer 可作为 Claude Code 的 Skill 使用：

```bash
# 安装 skill
claude install project-indexer.skill

# 在 Claude Code 中使用
/project-indexer
```

## 扩展新语言

实现 `BaseParser` 接口即可添加新语言支持：

```python
from parsers.base import BaseParser, FileSignature, ParserRegistry

@ParserRegistry.register
class MyLanguageParser(BaseParser):
    @property
    def extensions(self) -> list[str]:
        return [".mylang"]

    @property
    def language_name(self) -> str:
        return "MyLanguage"

    def parse(self, file_path: Path) -> FileSignature:
        # 实现解析逻辑
        return FileSignature(exports=[], imports=[])
```

## 技术实现

- **纯 Python 实现** - 无外部依赖
- **基于正则解析** - 快速提取代码符号
- **增量更新机制** - 基于文件 mtime 和大小检测变更
- **上下文限制** - 单文件最大 32000 字符（约 8k tokens）

## License

MIT