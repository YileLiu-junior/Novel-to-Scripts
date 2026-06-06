# 前端专用数据持久化改造报告

## 1. 根本原因

之前人物、场景、情节页面直接使用后端生成的 `screenplay_json` 数据进行展示和编辑，存在以下问题：

- `screenplay_json` 是 AI 生成后的结构化产物，数据结构复杂（如场景使用嵌套的 `scene_heading` + `location` 对象），不适合直接作为前端可编辑数据源
- 前端编辑后没有独立的持久化机制，修改只存在于 `session_state` 中，刷新即丢失
- 添加字段和编辑字段不一致（如人物添加用 `role`，编辑用 `narrative_role`）
- 没有独立的前端数据文件，每次进入页面都重新从 `screenplay_json` 读取，覆盖用户修改

## 2. 修改文件列表

### Backend（2 个文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/api/routes_frontend_data.py` | **新增** | 3 个 API 端点：init / get / save |
| `backend/app/api/router.py` | **修改** | 注册 `routes_frontend_data` 路由 |

### Frontend（4 个文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/api_client.py` | **修改** | 新增 3 个方法：`init_frontend_data` / `get_frontend_data` / `save_frontend_data` |
| `frontend/views/characters.py` | **重写** | 数据源改为 frontend_data API，使用扁平字段结构 |
| `frontend/views/scenes.py` | **重写** | 数据源改为 frontend_data API，使用扁平字段结构 |
| `frontend/views/plots.py` | **重写** | 数据源改为 frontend_data API，使用扁平字段结构 |

## 3. 新增数据目录

```
backend/data/projects/{project_id}/frontend_data/
├── characters.json          # 人物列表
├── character_relations.json # 人物关系
├── scenes.json              # 场景列表
├── scene_relations.json      # 场景关系
├── plots.json               # 情节列表（从 events 转换）
├── causal_relations.json     # 因果关系
└── meta.json                # 元信息（project_id, initialized_at, updated_at, version）
```

每个 JSON 文件格式为 `{"items": [...]}`，`meta.json` 为扁平对象。

## 4. 新增接口

### 4.1 初始化

```
POST /api/projects/{project_id}/frontend-data/init
```

请求体：
```json
{"force": false}
```

功能：检查 `frontend_data/` 是否存在；若已存在且 `force=false`，直接返回已有数据；若不存在，从最新 `screenplay_json` 提取并转换为前端专用数据结构后写入。

响应体：
```json
{
  "characters": [],
  "character_relations": [],
  "scenes": [],
  "scene_relations": [],
  "plots": [],
  "causal_relations": [],
  "meta": {}
}
```

### 4.2 获取全部数据

```
GET /api/projects/{project_id}/frontend-data
```

读取 7 个 JSON 文件，返回合并结果。若未初始化则返回 404。

### 4.3 保存全部数据

```
PUT /api/projects/{project_id}/frontend-data
```

请求体：
```json
{
  "characters": [],
  "character_relations": [],
  "scenes": [],
  "scene_relations": [],
  "plots": [],
  "causal_relations": []
}
```

写入对应 JSON 文件，同时更新 `meta.json` 的 `updated_at` 和 `version`。

## 5. 初始化转换逻辑

| frontend_data 文件 | screenplay_json 来源 | 字段映射 |
|---|---|---|
| `characters.json` | `story_bible.characters` | `id`, `name`, `aliases`, `narrative_role`, `voice_profile`, `source_refs`, `description` |
| `character_relations.json` | `story_bible.relationship_edges` | `id`, `from`, `to`, `relation`, `current_state`, `description` |
| `scenes.json` | `scenes` | `id`, `title`, `sequence`, `location`(扁平), `time`, `interior_exterior`, `heading_text`, `characters`, `dramatic_purpose`, `related_events`, `action`, `dialogue`, `source_refs` |
| `scene_relations.json` | `adaptation_plan.scene_plan` | `id`, `from`(scene_id), `to`(空), `relation`("planning"), `description`(purpose) |
| `plots.json` | `events` | `id`, `title`, `description`(summary), `characters`, `source_refs`, `type`, `importance` |
| `causal_relations.json` | `causal_graph.edges` | `id`, `from`, `to`, `relation`, `description`(reason/evidence) |

## 6. 前端页面数据来源

| 页面 | 数据文件 | 关系文件 |
|------|----------|----------|
| 人物管理 | `frontend_data/characters.json` | `frontend_data/character_relations.json` |
| 场景管理 | `frontend_data/scenes.json` | `frontend_data/scene_relations.json` |
| 情节页面 | `frontend_data/plots.json` | `frontend_data/causal_relations.json` |

数据加载流程：
1. 进入页面 → 调用 `api_client.init_frontend_data(backend_pid)`
2. init 接口自动检查是否已初始化，未初始化则从 `screenplay_json` 转换
3. 返回数据缓存到 `st.session_state[_fd_*]`
4. 页面从 `session_state` 读取渲染

## 7. 保存逻辑

```
用户点击保存
  → 前端校验（名称唯一性等）
  → 更新当前模块数据
  → PUT /api/projects/{project_id}/frontend-data
     （同时携带其他模块的 session_state 缓存数据，避免覆盖）
  → 后端写入 frontend_data/*.json
  → 返回保存后的完整数据
  → 更新 session_state 缓存
  → st.rerun() 刷新页面显示
```

关键设计：PUT 接口保存**全部 6 个模块数据**，前端保存时从 `session_state` 获取其他模块的缓存数据一并提交，避免某一模块保存时覆盖其他模块的修改。

## 8. 防覆盖机制

- `init` 接口默认 `force=false`：若 `frontend_data/` 目录和 `meta.json` 已存在，直接返回已有数据，**不重新生成**
- 只有前端显式传 `{"force": true}` 时才覆盖（预留给"重新从生成结果初始化"功能）
- 用户编辑后的数据保存在 `frontend_data/` 下，与 `screenplay_json` 完全独立
- `screenplay_json` 作为 AI 生成结果保持不变，不被前端编辑影响

## 9. 验收结果

### 9.1 初始化 ✅
- `POST /{project_id}/frontend-data/init` 接口已实现
- 首次调用时从 `screenplay_json` 转换并创建 `frontend_data/` 目录及 7 个 JSON 文件
- 后续调用直接返回已有数据

### 9.2 人物保存 ✅
- 编辑表单字段：name, aliases, narrative_role, voice_profile.rhythm, voice_profile.diction, description
- 添加表单字段与编辑表单完全一致
- 保存调用 `PUT /frontend-data`，写入 `characters.json`
- 保存成功后 `st.rerun()` 刷新页面
- 刷新后从 `frontend_data` 重新读取，修改保留
- 人物关系实时从 characters 构建 ID→name 映射

### 9.3 场景保存 ✅
- 使用扁平结构：sequence, location, time, interior_exterior, heading_text
- 编辑/添加表单字段一致
- 保存写入 `scenes.json`
- 场景关系实时从 scenes 构建 ID→title 映射

### 9.4 情节保存 ✅
- 编辑/添加表单字段一致：title, description, characters, type, importance
- 保存写入 `plots.json`
- 因果关系实时从 plots 构建 ID→title 映射

### 9.5 添加 ✅
- 人物自动生成 `char_XXX` ID
- 场景自动生成 `scene_XXX` ID
- 情节自动生成 `event_XXX` ID
- ID 规则：从已有数据中找最大编号 +1，补齐三位

### 9.6 删除 ✅
- 删除前需二次确认
- 删除后调用保存接口写入后端
- 刷新后不再显示

### 9.7 字段一致 ✅
- 三个页面的添加表单和编辑表单字段完全一致
- 卡片预览只显示摘要（人物：姓名+角色+别名前2+描述前50；场景：序号+标题+地点+时间+目的前50；情节：标题+描述前80+角色名称）
- 完整内容在编辑表单中查看

## 10. 后续 TODO

1. **"重新从生成结果初始化"按钮**：在人物/场景/情节页面顶部增加按钮，调用 `init` 接口时传 `force=true`，允许用户重新从 `screenplay_json` 生成 `frontend_data`（需二次确认避免误操作）
2. **frontend_data 反向导出**：将编辑后的 `frontend_data` 反向合并回 `screenplay_json` 或导出为 YAML/文学剧本
3. **分模块保存接口**：当前使用整体保存（PUT 全部 6 个模块），后续可优化为分模块 PUT 以减少数据传输量
4. **场景关系编辑**：当前场景关系和人物关系为只读展示，后续可增加添加/编辑/删除关系功能
5. **因果关系编辑**：同上
