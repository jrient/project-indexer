---
name: project-indexer
description: |
  为大型项目生成层级化索引，解决 AI 上下文超限问题。通过预构建"认知地图"，让 AI 可以渐进式地了解项目结构，快速定位需要修改的文件。

  使用场景：
  - 初次了解一个大型项目的结构和架构
  - 需要定位特定功能的代码位置
  - 迭代开发时快速找到需要修改的文件
  - 项目上下文过大导致 AI 无法一次性理解

  触发词：索引项目、生成项目索引、扫描项目结构、project index、analyze codebase structure
---

# Project Indexer

为大型代码库生成层级化索引，让 AI 可以渐进式理解项目而不超出上下文限制。

## Quick Start

### 生成索引

```bash
# 索引当前目录
python scripts/index_project.py

# 索引指定项目
python scripts/index_project.py /path/to/project

# 增量更新（只索引变更文件）
python scripts/index_project.py --update

# 强制完整重建
python scripts/index_project.py --force
```

### 使用索引

索引生成后，在 `project-index/` 目录下：

1. **先读 `INDEX.md`** - 了解项目概览和目录结构
2. **按需读取目录索引** - 根据任务定位到具体目录的 `directories/*.md`
3. **定位具体文件** - 根据索引中的签名信息确定需要修改的文件

## 索引结构

```
project-index/
├── INDEX.md                    # 总索引：项目概览、技术栈、目录树
├── directories/                # 目录级索引
│   ├── root.md                # 根目录文件
│   ├── src.md                 # src/ 目录
│   ├── src_components.md      # src/components/ 目录
│   └── ...
└── .index-meta.json           # 增量更新元数据
```

## 索引内容示例

### 总索引 (INDEX.md)

```markdown
# Project Index: my-project

## Project Information
- **Type**: typescript
- **Tech Stack**: TypeScript, React, Next.js
- **Generated**: 2024-01-27 10:00:00

## Directory Structure
my-project
├── src/
│   ├── components/
│   ├── hooks/
│   └── utils/
├── package.json
└── tsconfig.json

## Directory Index Navigation
- [root](directories/root.md)
- [src](directories/src.md)
- [src_components](directories/src_components.md)
```

### 目录索引

```markdown
# src/utils

## Files

### formatDate.ts
**Path**: `src/utils/formatDate.ts`
**Language**: TypeScript/JavaScript

**Exports**:
- `function formatDate(date, format): string`
- `const DEFAULT_FORMAT: string`

**Dependencies**: `date-fns`
```

## 支持的语言

| 语言 | 扩展名 | 提取内容 |
|------|--------|----------|
| TypeScript/JavaScript | .ts, .tsx, .js, .jsx | 导出的函数、类、接口、类型、常量 |
| Python | .py, .pyi | 类定义、函数定义（含方法） |

## 忽略规则

默认忽略以下目录/文件：
- `.git`, `node_modules`, `__pycache__`
- `dist`, `build`, `coverage`
- `.venv`, `venv`, `env`
- 遵循 `.gitignore` 规则
- 可创建 `.indexignore` 添加额外规则

## 工作流程

### 场景 1：初次了解项目

1. 运行 `python scripts/index_project.py /path/to/project`
2. 阅读 `project-index/INDEX.md` 了解整体结构
3. 根据需要深入阅读具体目录的索引

### 场景 2：定位功能代码

1. 阅读 `INDEX.md` 的目录结构
2. 根据功能猜测可能的目录
3. 阅读对应目录索引，查看文件签名
4. 定位到具体文件后再读取源代码

### 场景 3：增量更新

```bash
# 项目有变更后
python scripts/index_project.py --update
```

只会重新索引修改过的文件，节省时间。
