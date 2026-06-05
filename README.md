# XEngineer

> 🎬 改编室 — AI 小说转 YAML 剧本工作台

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B.svg)](https://streamlit.io/)
[![Status](https://img.shields.io/badge/status-V0%2BV1%20skeleton-orange.svg)]()

XEngineer 不直接让 LLM 一次性写出剧本，而是将小说改编过程分解为**可检查、可追溯、可版本化的步骤**，最终输出一份**结构化 YAML 剧本**，完整保留从原著到剧本的引用链条。

---

## 目录

- [核心设计理念](#核心设计理念)
- [输入与输出](#输入与输出)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [API 概览](#api-概览)
- [架构总览](#架构总览)
- [4 阶段生成流水线](#4-阶段生成流水线)
- [当前开发状态](#当前开发状态)
- [路线图](#路线图)
- [非目标](#非目标)
- [文档索引](#文档索引)

---

## 核心设计理念

```
传统做法:  小说 → [一个黑盒 Prompt] → 不可验证的文本剧本

XEngineer: 小说 → 4 个可审查的 AI 步骤 → 结构化 YAML → 确定性验证 → 审计报告
                   ↑ 每步保存产物  ↑ 可追溯来源  ↑ 检测引用断裂
```

| 原则 | 说明 |
|------|------|
| **产物优先于文本** | 每一步 AI 调用都保存独立 artifact |
| **结构优先于模型** | Schema 和验证器在 LLM 集成之前就位 |
| **可追溯性** | 每句对白可以回溯到原始章节和段落 |
| **离线可运行** | FakeProvider 无需 API Key 即可跑通全流程 |
| **格式中立** | 内部用 JSON/Pydantic，对外用 YAML |

---

## 输入与输出

### 输入

最少 **3 章小说原文**（纯文本），通过 API 或前端上传。

### 输出

一份结构化 YAML 剧本文件，包含：

```yaml
schema_version: "1.0"
project:                        # 项目元数据
  title: "血字的研究"
  target_format: "web_series"

source:                         # 源小说章节引用
  chapters:
    - id: chapter_001
      title: "歇洛克·福尔摩斯先生"

adaptation_config:              # 改编策略
  fidelity_level: "high"
  preserve_priorities: ["relationship_arc", "deduction_showcase"]

story_bible:                    # AI 提取的角色档案 + 关系图
  characters:
    - id: char_001
      name: "约翰·华生"
      voice_profile:
        rhythm: "观察细致，叙述克制"

events:                         # 故事事件列表
  - id: event_001
    summary: "华生经斯坦福德介绍见到福尔摩斯"

adaptation_plan:                # 改编决策（保留/合并/删除哪些事件）
  retained_events: ["event_001", "event_002"]
  scene_plan:
    - scene_id: scene_001
      purpose: "建立华生与福尔摩斯的关系入口"

scenes:                         # ★ 真正剧本内容 ★
  - id: scene_001
    title: "贝克街合租"
    location:
      name: "贝克街房间"
      time: "day"
      interior_exterior: "INT"
    action:
      - "华生打量房间，福尔摩斯已经把注意力放在更细微的观察上。"
    dialogue:
      - id: line_001
        character_id: char_001
        line: "如果房租真的能分摊，我愿意试试。"
        subtext: "他需要一个新的开始，但不愿显得太脆弱"
        emotional_state: "controlled_uncertainty"

audit_report:                   # 质量审计
  continuity_warnings: [...]
  unresolved_foreshadowing: [...]
```

> **YAML 是中间格式** — 它包含了传统剧本的全部内容（场景、对白、动作），并额外附加了来源引用、潜台词、角色声音等元数据。理论上可以渲染为传统剧本排版（Final Draft、中文剧本格式等）。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Python 3.11+ · FastAPI 0.111+ |
| **数据建模** | Pydantic v2（纯领域模型，零基础设施依赖） |
| **ASGI 服务器** | uvicorn 0.30+ |
| **数据库** | SQLite（sqlite3 标准库） |
| **前端框架** | Streamlit（Python Web 框架） |
| **AI 集成** | 抽象 Provider 模式 — FakeProvider（离线）⇄ OpenAIProvider（生产） |
| **结构化验证** | jsonschema 4+（JSON Schema Draft 2020-12） |
| **序列化** | JSON（内部唯一真实来源）· YAML（对外导出） |

---

## 项目结构

```
XEngineer/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── api/                 #   REST 路由 + DTO（8 组端点）
│   │   ├── services/            #   业务编排层（Orchestrator 核心）
│   │   ├── ai/                  #   LLM 集成
│   │   │   ├── providers/       #     AiProvider 抽象 + Fake + OpenAI
│   │   │   ├── skills/          #     SkillWrapper 封装（4 个技能）
│   │   │   └── prompts/         #     Markdown 提示模板
│   │   ├── validators/          #   确定性验证（不调 LLM）
│   │   ├── exporters/           #   YAML / JSON Schema 导出
│   │   ├── domain/              #   纯 Pydantic 领域模型（10 个模块）
│   │   ├── repositories/        #   数据访问层（内存 Stub）
│   │   ├── db/                  #   SQLite DDL
│   │   └── workers/             #   后台异步任务封装
│   └── pyproject.toml
├── frontend/                    # Streamlit 前端
│   ├── app.py                   #   入口 & 页面配置
│   ├── views/                   #   各页面视图（home / editor / 5 tab）
│   ├── utils/                   #   状态管理 / 存储 / 导出
│   └── run.bat                  #   Windows 一键启动脚本
├── fixtures/                    # 测试 & 演示数据（JSON + YAML）
├── schemas/                     # JSON Schema 定义（Draft 2020-12）
├── docs/                        # 架构计划 · API 合约 · 规范文档
├── scripts/                     # 验证 & 冒烟测试脚本
├── research/                    # 基准案例（福尔摩斯 / 小妇人 / 傲慢与偏见 等）
└── Pre-research/                # 竞品调研 & 可行性分析
```

---

## 环境要求

- **Python** 3.11+
- **Windows** 11（开发环境）或任何支持 Python 的操作系统
- **可选**：Conda（前端使用 conda 环境 `voicecal`）

### 依赖安装

```bash
# 后端依赖
cd backend
pip install -e .
# 或
pip install fastapi>=0.111 pydantic>=2 PyYAML>=6 jsonschema>=4 "uvicorn[standard]>=0.30"

# 前端依赖
cd ../frontend
pip install streamlit PyYAML
```

---

## 快速开始

### 1. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：
- API 文档（Swagger UI）: http://127.0.0.1:8000/docs
- 健康检查: http://127.0.0.1:8000/api/health

### 2. 启动前端（Windows）

```bash
# 方式 A：一键启动
cd frontend
run.bat

# 方式 B：手动启动
cd frontend
streamlit run app.py
```

> `run.bat` 默认使用 `D:\Tools\Miniconda3\envs\voicecal\python.exe`，如果你的 Python 路径不同，请修改 `run.bat` 中的 `PYTHON_EXE` 变量。

### 3. 运行离线冒烟测试

```bash
# 验证 fixture 数据文件
python scripts/validate_fixtures.py

# 运行冒烟测试（无需 API Key）
python scripts/run_demo_smoke.py
```

冒烟测试流程：
1. 加载 `fixtures/demo_novel_3_chapters.json`（福尔摩斯《血字的研究》3 章）
2. 创建项目 → 保存章节 → 用 FakeProvider 生成剧本 → 校验引用 → 导出 YAML
3. 全过程不需要真实的 LLM API Key

---

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/projects` | 创建项目 |
| `GET` | `/api/projects/{id}` | 获取项目详情 |
| `PUT` | `/api/projects/{id}/chapters` | 上传 / 替换章节（最少 3 章） |
| `GET` | `/api/projects/{id}/chapters` | 列出章节 |
| `POST` | `/api/projects/{id}/generate/story-bible` | 生成故事圣经 |
| `POST` | `/api/projects/{id}/generate/adaptation-plan` | 生成改编计划 |
| `POST` | `/api/projects/{id}/generate/screenplay` | **生成完整剧本**（后台异步） |
| `GET` | `/api/projects/{id}/artifacts` | 列出所有产物 |
| `GET` | `/api/projects/{id}/artifacts/{type}` | 按类型获取产物 |
| `POST` | `/api/projects/{id}/yaml/validate` | 验证 YAML 内容 |
| `GET` | `/api/projects/{id}/yaml/download` | 下载 YAML 剧本 |
| `GET` | `/api/projects/{id}/schema/download` | 下载 JSON Schema |
| `GET` | `/api/jobs/{job_id}` | 查询异步任务状态 |

---

## 架构总览

### 后端分层架构（6 层）

```
HTTP Request
    │
    ▼
┌─ API 层 ───────────────────────────────────────┐
│  router · routes_health · routes_projects ·      │
│  routes_chapters · routes_generation ·           │
│  routes_artifacts · routes_yaml · routes_jobs    │
│  请求/响应通过 Pydantic DTO 序列化                │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌─ Service 层 ────────────────────────────────────┐
│  GenerationOrchestrator (核心编排器)              │
│  ChapterService · ValidationService              │
│  YamlService · ArtifactService · JobService      │
└──┬──────────────┬──────────────┬────────────────┘
   │              │              │
   ▼              ▼              ▼
┌─ AI 层 ─┐ ┌─ Validators ─┐ ┌─ Exporters ─┐
│Providers │ │ Schema        │ │ YAML ↔ JSON │
│Skills    │ │ Reference     │ │ Schema 导出  │
│Prompts   │ │ Audit         │ └─────────────┘
└──────────┘ └───────────────┘
   │              │              │
   └──────────────┴──────────────┘
                     │
                     ▼
┌─ Repository 层 ─────────────────────────────────┐
│  Project · Chapter · Artifact · Job · LlmRun     │
│  当前实现：内存 Stub（合约已定义）                  │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌─ Database 层 ───────────────────────────────────┐
│  SQLite (session.py + tables.py DDL)            │
└─────────────────────────────────────────────────┘

         ← 贯穿全部层 ───────────────────── →
         Domain Models (纯 Pydantic, 零依赖)
         common · source · story_bible · adaptation
         screenplay (聚合根) · audit · artifacts
         jobs · llm_runs
```

### 前端架构（Streamlit 单页应用）

```
app.py (入口)
├── views/home.py           项目列表页
│   ├── 卡片网格 · 新建表单 · 删除确认（两步确认）
└── views/editor.py         项目编辑页
    ├── 侧边栏导航 (5 Tab)
    └── original.py         原文编辑器（TextArea + 文件上传）
        characters.py       人物管理（卡片 + 增删）
        scenes.py           场景管理（卡片 + 增）
        acts.py             场次编排（卡片 + 编辑表单）
        export.py           YAML 预览 + 下载
```

---

## 4 阶段生成流水线

```
用户上传章节
    │
    ▼
ChapterService.normalize_chapters()
  段落拆分 + 生成稳定 ID (chapter_###, p_###)
  就绪预检：至少 3 章 + 无空文本
    │
    ▼
╔══════════════════════════════════════════════╗
║  阶段 1: NovelReader                         ║
║  提取 → 角色 · 事件 · 伏笔 · 源引用            ║
║  产物: novel_analysis                        ║
╚══════════════════╤═══════════════════════════╝
                   │
                   ▼
╔══════════════════════════════════════════════╗
║  阶段 2: StoryOntology                       ║
║  构建 → 角色关系图 · 知识状态 · 因果图          ║
║  产物: story_bible                           ║
╚══════════════════╤═══════════════════════════╝
                   │
                   ▼
╔══════════════════════════════════════════════╗
║  阶段 3: AdaptationPlanner                   ║
║  决策 → 保留/合并/删除事件 · 场景布局            ║
║  产物: adaptation_plan                       ║
╚══════════════════╤═══════════════════════════╝
                   │
                   ▼
╔══════════════════════════════════════════════╗
║  阶段 4: ScreenplayWriter                    ║
║  编写 → 场景 · 动作 · 对白 · 潜台词             ║
║  产物: screenplay_json                       ║
╚══════════════════╤═══════════════════════════╝
                   │
                   ▼
          ValidationService
     SchemaValidator   → 结构合法性
     ReferenceValidator → 引用完整性
     AuditValidator    → 审计报告
                   │
                   ▼
          YAML Export + 产物保存
     screenplay_yaml · audit_report
```

执行模式：**异步 Fire-and-Forget**
```
POST /api/projects/{id}/generate/screenplay
  → 202 Accepted { job_id }
  → BackgroundTasks.run_v1()
  → GET /api/jobs/{job_id} (轮询进度)
  → GET /api/projects/{id}/artifacts/{type} (获取产物)
```

---

## 当前开发状态

### ✅ 已完成（V0+V1 骨架）

- **完整的后端分层架构**：API → Service → AI/Validator/Exporter → Repository → DB
- **10 个领域模型模块**：纯 Pydantic，Screenplay 聚合根
- **8 组 REST API 端点**：项目 CRUD、章节管理、生成、产物、YAML、Schema、Job 查询
- **4 个 AI Skill 封装**：NovelReader、StoryOntology、AdaptationPlanner、ScreenplayWriter
- **4 个确定性验证器**：章节就绪检查、Schema 验证、引用完整性、审计报告
- **FakeProvider 离线流水线**：无需 API Key 即可跑通全流程
- **异步任务系统**：BackgroundTask + Job 状态机 + 轮询
- **YAML 双向转换**：Pydantic ↔ YAML 解析和导出
- **Streamlit 前端**：项目管理、原文编辑、人物/场景/场次管理、YAML 导出
- **冒烟测试**：`scripts/validate_fixtures.py` 和 `scripts/run_demo_smoke.py`
- **Demo 数据**：基于福尔摩斯《血字的研究》的完整示例剧本

### ⏳ 待实现

- **OpenAI Provider 真实集成**（当前 FakeProvider 占位）
- **SQLite 持久化**（当前 Repository 为内存 Stub）
- **前端 AI 提交触发**（"提交"按钮已预留但未连接后端）
- **前端图片生成功能**（"生成形象""生成剧照"为预留按钮）
- **对白医生（DialogueDoctor）** — 潜台词优化
- **连续性审计增强** — 因果图 + 伏笔追踪
- **传统剧本格式渲染** — 从 YAML 生成可阅读的剧本排版

---

## 路线图

| 版本 | 目标 | 状态 |
|------|------|------|
| **V0** | 3 章输入 → FakeProvider 生成 → YAML 导出 → Schema 验证 | ✅ Done |
| **V1** | adaptation_config + adaptation_plan + 每步 artifact + Job 状态查询 | ✅ Done |
| **V2** | 真实 OpenAI Provider + SQLite 持久化 + 前端后端联通 | 📋 Planned |
| **V3** | 因果图 + 伏笔追踪 + 增强故事圣经 | 📋 Planned |
| **V4** | 对白医生 + 潜台词深度 + 角色声音一致性 | 📋 Planned |
| **V5** | 审查闭环 + 人工反馈修正 + 迭代优化 | 📋 Planned |

---

## 非目标

当前阶段 **不引入**：

- Redis / Celery / 外部消息队列
- PostgreSQL JSONB 或图数据库
- RDF / OWL 本体系统
- Final Draft (.fdx) 或 Fountain 格式导出
- 多人协作编辑
- 故事板 / 视频提示词 / 图片生成
- 预算风险评估

> 后续版本会通过 **扩展现有字段和服务** 来增加功能，而非替换 V0+V1 流水线。

---

## 文档索引

| 文档 | 路径 |
|------|------|
| Agent 操作规则 | `AGENTS.md` |
| 产品需求文档 | `Pre-research/AI小说转剧本MVP方案细化.md` |
| 竞品调研 | `Pre-research/竞品调研和痛点分析.md` |
| 可行性分析 | `Pre-research/可行性方案.md` |
| 技术挑战调研 | `Pre-research/ai-novel-to-shootable-screenplay-technical-challenges.md` |
| 目录结构方案 | `docs/plans/2026-06-05-004-project-directory-structure.md` |
| 后端框架决策 | `docs/plans/2026-06-05-005-v1-backend-framework-and-agent-team-decision.md` |
| 后端规范序列 | `docs/plans/2026-06-05-006-v0-v1-backend-spec-and-agent-team-plan.md` |
| API 合约 | `docs/api/api-contract.md` |
| Schema 设计说明 | `schemas/screenplay-schema-design.md` |
| Schema 详解 | `docs/schema/screenplay-schema-explained.md` |
| 演示清单 | `docs/demo/demo-checklist.md` |
| 前端使用指南 | `frontend/使用指南.md` |
| 代码架构飞书文档 | [飞书文档](https://www.feishu.cn/docx/JNngdxyBtoFegixdDPgcjNPgnbf) |
| 代码架构飞书画板 | [飞书画板](https://www.feishu.cn/docx/OXvtdKafkocCSzxzvNQcY2Szn0e) |
| 基准案例 | `research/novel-to-script-cases/README.md` |

---

<p align="center">
  <sub>Built with ❤️ during a 72-hour vibe-coding sprint · v0.25 · June 2026</sub>
</p>
