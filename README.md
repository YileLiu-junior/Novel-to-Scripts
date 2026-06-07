# XEngineer

> 🎬 改编室 — AI 小说转 YAML 剧本工作台

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B.svg)](https://streamlit.io/)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek%20V4-536DFE.svg)](https://api.deepseek.com)

XEngineer 将小说改编过程分解为**可检查、可追溯、可版本化的步骤**，最终输出一份**结构化 YAML 剧本**，完整保留从原著到剧本的引用链条。
产品介绍 & demo演示视频 ：https://www.bilibili.com/video/BV1WuEh6VE8o/
---

## 目录

- [核心设计理念](#核心设计理念)
- [输入与输出](#输入与输出)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [API 概览](#api-概览)
- [架构总览](#架构总览)
- [生成流水线](#生成流水线)
- [当前开发状态](#当前开发状态)
- [路线图](#路线图)
- [非目标](#非目标)

---

## 核心设计理念

```
传统做法:  小说 → [一个黑盒 Prompt] → 不可验证的文本剧本

XEngineer: 小说 → 3 个可审查的 AI 步骤 → 结构化 YAML → 确定性验证 → 审计报告
                   ↑ 每步保存产物  ↑ 可追溯来源  ↑ 检测引用断裂
```

| 原则 | 说明 |
|------|------|
| **产物优先于文本** | 每一步 AI 调用都保存独立 artifact |
| **结构优先于模型** | Schema 和验证器在 LLM 集成之前就位 |
| **可追溯性** | 每句对白可以回溯到原始章节和段落 |
| **归一化 + 校验管道** | 代码负责结构（ID 生成、引用检查、格式校验），AI 负责内容 |
| **格式中立** | 内部用 JSON/Pydantic，对外用 YAML |

---

## 输入与输出

### 输入

最少 **3 章小说原文**（纯文本），通过 API 或前端上传。

示例文件见 `Input_Exampls/` 目录（《傲慢与偏见》《三生三世十里桃花》《潜伏》）。

### 输出

生成一份**可视化文学剧本**，前端预览页即可阅读。同时支持**下载 TXT**、**一键复制全文**。

```markdown
# E2E-Pipeline-0607-1626
> 傲慢与偏见 前3章 改编测试

**原著**: 《傲慢与偏见》序言、第六十一章、第二章

## 1. 班纳特家-书房 INT 日

△班纳特先生坐在书桌前，手捧一本书，神态悠然。门突然被推开，
班纳特太太快步走进来，脸上带着掩不住的兴奋。

**班纳特太太**：（喘着气，挥动手帕）亲爱的，你听说了吗？
尼日斐花园终于租出去了！

△班纳特先生缓缓抬起眼皮，合上书本，露出一个略带讽刺的微笑。

**班纳特先生**：（慢悠悠地）没听说。是谁告诉你的？

**班纳特太太**：（急促地）朗太太刚说的！租给了一位从英格兰北部
来的阔少爷，彬格莱先生！听说他每年有四五千镑的收入呢！

**班纳特先生**：（翻了一页书，头也不抬）这跟她们有什么关系？
你是想嫁女儿还是租房子？

**班纳特太太**：（提高声调）你怎么如此麻木！这可是千载难逢的机会！

## 2. 麦里屯-舞厅 INT 夜

△舞厅里乐声悠扬，彬格莱先生走向简·班纳特，弯腰邀请。

**彬格莱先生**：（微笑）班纳特小姐，能请你跳下一支舞吗？

△不远处，达西先生独自站着，目光扫过舞池，面无表情。

**达西先生**：（冷淡地）我不喜欢和生人跳舞，
况且这个镇上的姑娘们没有一个配得上做我的舞伴。

△这话被旁边的伊丽莎白隐约听到，她转身看了达西一眼，眉头微皱。

**达西先生**：那边那位伊丽莎白·班纳特小姐，长得还算可以，
但不够漂亮，不值得我献殷勤。

△伊丽莎白听到了这句话，脸一红，随即转过身去，挺直背脊。
```

> **YAML 是中间格式** — 内部用 JSON/Pydantic 保证结构完整（引用链、潜台词、审计报告等），前端展示的是渲染后的 Markdown 文学剧本。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Python 3.11+ · FastAPI 0.111+ |
| **数据建模** | Pydantic v2（纯领域模型，零基础设施依赖） |
| **ASGI 服务器** | uvicorn 0.30+ |
| **持久化** | 本地文件存储（JSON artifact，原子写入，`data/` 目录） |
| **前端框架** | Streamlit 1.x |
| **AI 集成** | DeepSeek V4（抽象 Provider 模式，可替换） |
| **结构化验证** | jsonschema 4+（JSON Schema Draft 2020-12） |
| **序列化** | JSON（内部唯一真实来源）· YAML（对外导出） |

---

## 项目结构

```
XEngineer/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── api/                 #   REST 路由 + DTO（10 组端点）
│   │   ├── services/            #   业务编排层（GenerationOrchestrator 核心）
│   │   ├── ai/                  #   LLM 集成
│   │   │   ├── providers/       #     AiProvider 抽象 + DeepSeek 实现
│   │   │   ├── skills/          #     SkillWrapper 封装（4 个技能）
│   │   │   └── prompts/         #     Markdown 提示模板
│   │   ├── validators/          #   确定性验证（不调 LLM）
│   │   │   ├── schema_validator.py       # JSON Schema 结构校验
│   │   │   ├── reference_validator.py    # 引用完整性检查
│   │   │   ├── audit_validator.py        # 连续性审计
│   │   │   ├── chapter_validator.py      # 章节就绪预检
│   │   │   └── screenplay_normalizer.py  # LLM 输出归一化（校验前清洗）
│   │   ├── exporters/           #   YAML / JSON Schema / 文学剧本导出
│   │   ├── domain/              #   纯 Pydantic 领域模型（10 个模块）
│   │   ├── repositories/        #   数据访问层（JSON 文件读写）
│   │   ├── db/                  #   数据库 DDL（预留，当前未使用）
│   │   └── workers/             #   后台异步任务封装
│   ├── tests/                   #   测试（E2E / pipeline / API smoke / validator）
│   └── pyproject.toml
├── frontend/                    # Streamlit 前端
│   ├── app.py                   #   入口 & 页面路由
│   ├── api_client.py            #   后端 HTTP 调用统一封装
│   ├── views/                   #   各页面视图（7 Tab）
│   │   ├── home.py              #     项目列表页
│   │   ├── editor.py            #     编辑页布局 + 侧边栏导航
│   │   ├── original.py          #     原文管理 + 生成流程
│   │   ├── characters.py        #     人物管理
│   │   ├── scenes.py            #     场景管理
│   │   ├── plots.py             #     事件管理
│   │   ├── screenplay_preview.py#     文学剧本预览
│   │   ├── export.py            #     YAML 预览 + 下载
│   │   └── audit_report.py      #     审查报告
│   ├── utils/                   #   状态管理 / 本地存储 / 导出
│   └── run.bat                  #   Windows 一键启动脚本
├── fixtures/                    # Demo 数据（JSON + YAML）
├── schemas/                     # JSON Schema 定义（Draft 2020-12）
├── Input_Exampls/               # 示例输入文件（小说原文 TXT）
├── docs/                        # API 合约 · Schema 说明 · Demo 清单
└── scripts/                     # 冒烟测试 & 校验脚本
```

---

## 快速开始

### 环境要求

- **Python** 3.11+
- **DeepSeek API Key**（从 [platform.deepseek.com](https://platform.deepseek.com) 获取）

### 1. 配置环境变量

```bash
# 必需
set DEEPSEEK_API_KEY=your-api-key

# 可选
set XENGINEER_AI_PROVIDER=deepseek        # 默认值
set XENGINEER_DEEPSEEK_MODEL=deepseek-v4-flash  # 默认模型
set XENGINEER_DATA_ROOT=./data            # 数据存储路径
```

### 2. 安装依赖

```bash
# 后端依赖
cd backend
pip install -e .

# 前端依赖
cd ../frontend
pip install streamlit PyYAML
```

### 3. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：
- API 文档（Swagger UI）: http://127.0.0.1:8000/docs
- 健康检查: http://127.0.0.1:8000/api/health

### 4. 启动前端

```bash
cd frontend
streamlit run app.py
```

### 5. 运行冒烟测试

```bash
# 验证 fixture 数据文件
python scripts/validate_fixtures.py
```

---

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/projects` | 创建项目 |
| `GET` | `/api/projects/{id}` | 获取项目详情 |
| `PUT` | `/api/projects/{id}/chapters` | 上传 / 替换章节（最少 3 章） |
| `GET` | `/api/projects/{id}/chapters` | 列出章节 |
| `POST` | `/api/projects/{id}/chapters/auto-split` | AI 自动拆章 |
| `POST` | `/api/projects/{id}/generate/story-bible` | 生成故事圣经 |
| `POST` | `/api/projects/{id}/generate/adaptation-plan` | 生成改编计划 |
| `POST` | `/api/projects/{id}/generate/screenplay` | **生成完整剧本**（后台异步） |
| `GET` | `/api/projects/{id}/artifacts` | 列出所有产物 |
| `GET` | `/api/projects/{id}/artifacts/{type}` | 按类型获取产物 |
| `GET` | `/api/projects/{id}/frontend-data` | 获取前端专用数据 |
| `GET` | `/api/projects/{id}/screenplay/rendered` | 获取文学剧本渲染（Markdown / 纯文本） |
| `GET` | `/api/projects/{id}/screenplay/rendered/download` | 下载文学剧本渲染 |
| `POST` | `/api/projects/{id}/yaml/validate` | 验证 YAML 内容 |
| `GET` | `/api/projects/{id}/yaml/download` | 下载 YAML 剧本 |
| `GET` | `/api/projects/{id}/schema/download` | 下载 JSON Schema |
| `GET` | `/api/jobs/{job_id}` | 查询任务进度（job = 任务排队号） |

---

## 架构总览

### 后端分层架构（5 层）

```
HTTP Request
    │
    ▼
┌─ API 层 ───────────────────────────────────────┐
│  router · 10 组路由（health / projects /        │
│  chapters / generation / artifacts /            │
│  frontend_data / yaml / screenplay_render /     │
│  schema / jobs）                                 │
│  请求/响应通过 Pydantic DTO 序列化                │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌─ Service 层 ────────────────────────────────────┐
│  GenerationOrchestrator (核心编排器)              │
│  ChapterService · ChapterIntakeService           │
│  ChapterSplitter · ValidationService             │
│  YamlService · ArtifactService · JobService      │
│  LlmTraceService · SchemaService                 │
│  ScreenplayRenderService                         │
└──┬──────────────┬──────────────┬────────────────┘
   │              │              │
   ▼              ▼              ▼
┌─ AI 层 ─┐ ┌─ Validators ─┐ ┌─ Exporters ──────┐
│Providers │ │ Schema        │ │ YAML ↔ JSON      │
│Skills    │ │ Reference     │ │ Schema 导出       │
│Prompts   │ │ Audit         │ │ 文学剧本渲染      │
│          │ │ Chapter       │ │ (Markdown/TXT)   │
│          │ │ Normalizer    │ └──────────────────┘
└──────────┘ └───────────────┘
   │              │              │
   └──────────────┴──────────────┘
                     │
                     ▼
┌─ Repository / 持久化层 ──────────────────────────┐
│  Project · Chapter · Artifact · Job · LlmRun     │
│  全部通过 file_store 做 JSON 原子写入              │
│                                                   │
│  data/projects/{id}/                              │
│  ├── project.json         项目元数据               │
│  ├── chapters/index.json  章节索引                │
│  ├── artifacts/index.json 产物索引 + JSON/YAML    │
│  └── jobs/index.json      任务排队号状态          │
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
├── views/home.py              项目列表页
│   ├── 卡片网格 · 新建表单 · 删除确认（两步确认）
│   └── 创建时同步后端 project
└── views/editor.py            项目编辑页
    ├── 侧边栏导航 (7 Tab)
    ├── original.py             原文管理（上传/拆章 + AI 生成流程）
    ├── characters.py           人物管理（卡片 + 增删）
    ├── scenes.py               场景管理（卡片 + 增删）
    ├── plots.py                事件管理（卡片 + 编辑表单）
    ├── screenplay_preview.py   文学剧本预览（scene heading + content_blocks）
    ├── export.py               YAML 预览 + 下载 + 文学剧本下载
    └── audit_report.py         审查报告

前端状态管理:
├── utils/state.py              Streamlit session_state 统一管理
├── utils/storage.py            本地 JSON 持久化（自动迁移旧数据）
└── api_client.py               后端 HTTP 调用唯一入口（封装所有 API path）
```

---

## 生成流水线

```
用户上传章节
    │
    ▼
ChapterService + ChapterSplitter
  段落拆分 + 生成稳定 ID (chapter_###, p_###)
  就绪预检：至少 3 章 + 无空文本
    │
    ▼
╔══════════════════════════════════════════════╗
║  阶段 1: NovelReader                         ║
║  提取 → 角色候选 · 事件 · 伏笔 · 源引用        ║
║  产物: novel_analysis                        ║
╚══════════════════╤═══════════════════════════╝
                   │
                   ▼
╔══════════════════════════════════════════════╗
║  阶段 2: StoryOntology                       ║
║  构建 → 角色关系图 · 知情状态 · 连续性锚点       ║
║        · 冲突池 · 影视化约束                   ║
║        · 改编计划（adaptation_plan 一并产出）   ║
║  产物: story_bible + adaptation_plan         ║
╚══════════════════╤═══════════════════════════╝
                   │
                   ▼
╔══════════════════════════════════════════════╗
║  阶段 3: ScreenplayWriter                    ║
║  编写 → 场景 · 动作 · 对白 · 潜台词             ║
║        · scene_heading · content_blocks      ║
║  产物: screenplay_json                       ║
╚══════════════════╤═══════════════════════════╝
                   │
                   ▼
          Normalization Layer
     归一化 LLM 输出 → 补全缺失字段 → 删除非法 null
     → 统一 ID 格式（char_NNN / event_NNN / foreshadow_NNN）
     → 角色自动注册（LLM 引用但未定义的中文角色名）
     → 场景角色引用修复（对白角色自动补入出场列表）
                   │
                   ▼
          ValidationService
     SchemaValidator   → 结构合法性
     ReferenceValidator → 引用完整性
     AuditValidator    → 连续性审计报告
                   │
                   ▼
          YAML Export + 产物保存
     screenplay_yaml · audit_report
     screenplay_rendered (Markdown / 纯文本)
```

生成耗时较长（多轮 AI 调用），采用**异步任务排队**模式：

```
1. 提交生成请求  →  立即返回 job_id（任务排队号）
2. 后台依次执行  →  novel_reader → story_ontology → screenplay_writer
3. 前端轮询进度  →  GET /api/jobs/{job_id}  查看当前做到哪一步了
4. 完成后取产物  →  GET /api/projects/{id}/artifacts/{type}
```

---

## 当前开发状态

### ✅ 已完成（V0 + V1 + V2.1）

- **完整的后端分层架构**：API → Service → AI/Validator/Exporter → Repository（JSON 文件存储）
- **10 个领域模型模块**：纯 Pydantic，Screenplay 聚合根
- **10 组 REST API 端点**：项目 CRUD、章节管理（含 AI 拆章）、生成（3 个入口）、产物、前端数据、文学剧本渲染、YAML、Schema、Job 查询
- **6 个 AI Skill 封装**：NovelReader、StoryOntology、ScreenplayWriter、ChapterBoundaryReader、ContinuityAuditor、DialogueDoctor
- **5 个确定性验证器 + 归一化层**：章节就绪检查、Schema 验证、引用完整性、审计报告、LLM 输出归一化
- **DeepSeek V4 真实集成**：Provider 抽象模式，可替换为其他 LLM
- **异步任务排队系统**：提交生成 → 拿到排队号（job_id）→ 轮询进度 → 完成取产物
- **YAML 双向转换 + 文学剧本渲染**：Pydantic ↔ YAML，支持 Markdown/纯文本导出
- **Streamlit 前端**：项目管理、原文编辑、人物/场景/事件管理、文学剧本预览、审查报告、YAML 导出
- **完整测试覆盖**：E2E 流水线测试、API 冒烟测试、Validator 单元测试、Normalizer 测试
- **Demo 数据**：基于福尔摩斯《血字的研究》的完整示例剧本

### ⏳ 待实现

- **对白医生（DialogueDoctor）** — 潜台词优化（Skill 已定义，待集成入流水线）
- **连续性审计增强** — 因果图 + 伏笔追踪闭环
- **前端 AI 提交触发** — 编辑后重新生成
- **传统剧本格式渲染** — 从 YAML 生成更丰富的中文剧本排版

---

## 路线图

| 版本 | 目标 | 状态 |
|------|------|------|
| **V0** | 3 章输入 → FakeProvider 生成 → YAML 导出 → Schema 验证 | ✅ Done |
| **V1** | adaptation_config + adaptation_plan + 每步 artifact + Job 状态查询 | ✅ Done |
| **V2.1** | DeepSeek 真实集成 + 文件持久化 + 前端后端联通 | ✅ Done |
| **V3** | 因果图增强 + 伏笔追踪闭环 + DialogueDoctor 集成 | 📋 Planned |
| **V4** | 审查闭环 + 人工反馈修正 + 迭代优化 | 📋 Planned |

---

## 非目标

当前阶段 **不引入**：

- Redis / Celery / 外部消息队列
- PostgreSQL JSONB 或图数据库
- RDF / OWL 本体系统
- Final Draft (.fdx) 或 Fountain 格式导出
- 多人协作编辑
- 故事板 / 视频提示词 / 图片生成

> 后续版本会通过 **扩展现有字段和服务** 来增加功能，而非替换现有流水线。

---

## 文档索引

| 文档 | 路径 |
|------|------|
| API 合约 | `docs/api/api-contract.md` |
| Schema 设计说明 | `schemas/screenplay-schema-design.md` |
| Schema 详解 | `docs/schema/screenplay-schema-explained.md` |
| Demo 演示清单 | `docs/demo/demo-checklist.md` |
| Fixtures 说明 | `fixtures/README.md` |
| 示例输入文件 | `Input_Exampls/` |
| 后端 README | `backend/README.md` |

---

<p align="center">
  <sub>Built with ❤️ · v2.1 · June 2026</sub>
</p>
