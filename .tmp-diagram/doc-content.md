# XEngineer 代码架构全景图

> AI 小说转 YAML 剧本工作台 · v0.25 · 单体仓库 (Monorepo)

---

## 一、项目概述

XEngineer 是一个**AI小说转YAML剧本工作台**。核心设计理念：不直接让LLM一次性写出剧本，而是将改编过程分解为**可检查、可追溯、可版本化**的步骤，输出**结构化YAML**，保持从原著到剧本的完整链条。

产品定位为"改编室"（Adaptation Studio）—— AI 做辅助拆解，人类编剧做核心判断。

---

## 二、技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | Python 3.11+ / FastAPI 0.111+ |
| 数据建模 | Pydantic v2（纯领域模型，零基础设施依赖） |
| 数据库 | SQLite（通过 sqlite3 标准库） |
| ASGI 服务器 | uvicorn 0.30+ |
| 前端框架 | Streamlit（Python 原生 Web 框架） |
| AI 集成 | 抽象 Provider 模式（FakeProvider 离线开发 + OpenAIProvider 生产） |
| 数据验证 | jsonschema 4+ (Draft 2020-12) |
| 序列化格式 | JSON（内部唯一真实来源）/ YAML（对外导出） |
| 运行环境 | Windows 11, Conda Python 环境 |

---

## 三、顶层目录结构

```
XEngineer/
├── backend/          # FastAPI + Pydantic v2 后端
│   ├── app/
│   │   ├── api/          # REST 路由 + DTO
│   │   ├── services/     # 业务编排层
│   │   ├── ai/           # LLM Provider + Skill
│   │   ├── validators/   # 确定性规则验证
│   │   ├── exporters/    # YAML/JSON 导出
│   │   ├── repositories/ # 数据访问（内存 Stub）
│   │   ├── domain/       # 纯 Pydantic 领域模型
│   │   ├── db/           # SQLite DDL
│   │   └── workers/      # 后台异步任务
│   └── pyproject.toml
├── frontend/         # Streamlit 前端界面
│   ├── app.py
│   ├── views/        # 各页面视图
│   └── utils/        # 状态管理/存储/导出
├── docs/             # 架构计划 + API合约 + 规范文档
├── fixtures/         # 测试/演示数据（JSON + YAML）
├── schemas/          # JSON Schema 定义
├── scripts/          # 验证和冒烟测试脚本
├── research/         # 基准案例和改编研究
└── Pre-research/     # 竞品调研和可行性分析
```

---

## 四、后端分层架构（6 层 + 跨层领域模型）

### 架构总览

```
HTTP Request → API 层 → Service 层 → AI / Validators / Exporters
                                       ↓
                              Repository 层 → Database 层
                              
              ← 贯穿全部: Domain Models (纯 Pydantic) →
```

### 各层详情

**1. API 层 (app/api/)**
- 根路由 + 8 组 REST 端点
- 请求/响应 DTO（Pydantic 模型，与领域模型分离）

**2. Service 层 (app/services/)**
- `GenerationOrchestrator` — 4 阶段 LLM 流水线核心编排器
- `ChapterService` — 章节规范化、段落拆分
- `ValidationService` — 组合 3 个验证器（Schema + Reference + Audit）
- `YamlService` — YAML 序列化/反序列化 + 导出前验证
- `ArtifactService` — 产物元数据管理
- `JobService` — 异步任务状态机
- `LlmTraceService` — LLM 调用追踪记录

**3. AI 层 (app/ai/)**
- **Providers**（策略模式）：`AiProvider` 抽象基类 → `FakeProvider`（离线） / `OpenAIProvider`（生产）
- **Skills**（模板方法模式）：`SkillWrapper` 基类 → NovelReader / StoryOntology / AdaptationPlanner / ScreenplayWriter
- **Prompts**：独立的 Markdown 提示模板文件

**4. Validators 层 (app/validators/)**
- 确定性规则检查，**不调用 LLM**
- ChapterValidator → 生成就绪预检
- SchemaValidator → JSON Schema 结构化验证
- ReferenceValidator → 交叉引用完整性（章节/角色/事件/场景）
- AuditValidator → 汇总为统一 AuditReport

**5. Exporters 层 (app/exporters/)**
- YamlExporter → 剧本 dict ↔ YAML 字符串
- SchemaExporter → 读取 screenplay.schema.json

**6. Repository + DB 层**
- 5 个 Repository（Project / Chapter / Artifact / Job / LlmRun），当前为内存 Stub
- SQLite DDL 已定义（session.py + tables.py）

**贯穿层：Domain Models (app/domain/)**
- 纯 Pydantic BaseModel，**零基础设施依赖**
- 10 个模块：common / project / source / story_bible / adaptation / screenplay（聚合根） / audit / artifacts / jobs / llm_runs
- Screenplay 作为聚合根，封装从源素材到改编计划、故事圣经、场景、对白、审计报告的全部生命周期

---

## 五、4 阶段 LLM 生成流水线

```
用户上传 Chapters
       ↓
ChapterService 归一化（段落拆分 + 就绪检查）
       ↓
[阶段 1] NovelReader       → 提取角色、事件、伏笔、源引用
       ↓                     产物: novel_analysis
[阶段 2] StoryOntology      → 构建角色关系图、知识状态、因果图
       ↓                     产物: story_bible
[阶段 3] AdaptationPlanner  → 决策保留/合并/删除事件、场景布局
       ↓                     产物: adaptation_plan
[阶段 4] ScreenplayWriter   → 编写场景、动作、对白、潜台词
       ↓                     产物: screenplay_json
Validation                  → Schema + Reference + Audit 三重验证
       ↓
YAML Export + 产物保存      → screenplay_yaml + audit_report
```

异步执行：POST → 202 Accepted + job_id → BackgroundTask → 轮询 GET /api/jobs/{id}

---

## 六、前端架构（Streamlit 单页应用）

```
app.py（入口 + 页面配置）
├── views/home.py              项目列表页
│   ├── 项目卡片网格
│   ├── 新建项目表单
│   └── 删除确认（两步确认）
└── views/editor.py            项目编辑页
    ├── 侧边栏导航（5 个 Tab）
    └── 内容区分发：
        ├── original.py        原文编辑器（TextArea + 文件上传）
        ├── characters.py      人物管理（卡片网格 + 添加/删除）
        ├── scenes.py          场景管理（卡片网格 + 添加）
        ├── acts.py            场次管理（卡片视图 + 编辑表单）
        └── export.py          YAML 预览 + 下载

utils/
├── state.py        会话状态管理（st.session_state 路由）
├── storage.py      项目 JSON 文件 CRUD
└── exporter.py     项目 → YAML 结构化转换

数据存储: data/projects.json（单一 JSON 文件）
```

---

## 七、领域模型详解

| 模块 | 核心模型 | 说明 |
|------|----------|------|
| common | SourceRef, Location, VoiceProfile, ValidationFinding | 共享值类型 |
| project | Project | 项目实体（id, title, logline, format） |
| source | Chapter, Paragraph, ChapterSet | 源素材层级 |
| story_bible | Character, RelationshipEdge, KnowledgeState, Event, CausalGraph, Foreshadowing | 叙事分析输出 |
| adaptation | AdaptationConfig, AdaptationPlan | 改编策略 |
| screenplay | Screenplay（聚合根） | 组合全部分析数据 |
| audit | AuditWarning, AuditReport | 验证结果 |
| artifacts | Artifact（6 种类型） | 工作流产物 |
| jobs | GenerationJob | 异步任务状态机（queued → running → succeeded/failed） |
| llm_runs | LlmRun | LLM 调用可追溯性记录 |

---

## 八、核心设计原则

1. **领域模型为唯一真实来源** — 纯 Pydantic 模型，不依赖 FastAPI/SQLite 等基础设施
2. **AI Provider 策略模式** — FakeProvider ↔ OpenAIProvider 通过相同接口可互换
3. **Skill Wrapper 模式** — 每个技能封装一个 LLM 调用，输入/输出由 Service 层验证和持久化
4. **验证器 ≠ 模型，导出器 ≠ 修复** — 验证器做确定性检查，导出器只做序列化
5. **Fixture 优先，Schema 优先** — 先有数据和 Schema，再写代码和模型
6. **异步 Fire-and-Forget** — BackgroundTask + Job 轮询，前端不阻塞等待

---

## 九、API Endpoints

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/projects | 创建项目 |
| GET | /api/projects/{id} | 获取项目详情 |
| PUT | /api/projects/{id}/chapters | 上传/替换章节 |
| GET | /api/projects/{id}/chapters | 列出章节 |
| POST | /api/projects/{id}/generate/story-bible | 生成故事圣经 |
| POST | /api/projects/{id}/generate/adaptation-plan | 生成改编计划 |
| POST | /api/projects/{id}/generate/screenplay | 生成剧本 |
| GET | /api/projects/{id}/artifacts | 列出产物 |
| GET | /api/projects/{id}/artifacts/{type} | 按类型获取产物 |
| POST | /api/projects/{id}/yaml/validate | 验证 YAML |
| GET | /api/projects/{id}/yaml/download | 下载 YAML |
| GET | /api/projects/{id}/schema/download | 下载 JSON Schema |
| GET | /api/jobs/{job_id} | 查询任务状态 |

---

## 十、当前开发阶段

- **V0+V1 骨架已完成**：所有接口和合约已定义，大多数 Repository 和 AI Provider 使用 Stub/Fake 实现
- **FakeProvider 可运行完整管线**：无需真实 API Key 即可体验完整流程
- **待实现**：OpenAI Provider 真实集成、SQLite 持久化、前端 AI 提交功能、图片生成功能

---

> 分析时间：2026-06-05 · 代码库路径：F:\Program Files\XEngineer（不含 .tmp-novel-to-script-team）

<whiteboard type="blank"></whiteboard>
