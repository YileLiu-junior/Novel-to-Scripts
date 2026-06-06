# AI 小说转剧本工具 MVP 方案细化

生成日期：2026-06-05  
适用场景：72h vibe coding 项目 / AI 辅助剧本创作工具  
当前策略：保留可控改编、角色声音/潜台词、因果/伏笔守护、轻量故事本体；暂缓预算风险模块。

---

## 1. 一句话定位

**一款面向小说作者的 AI 改编工作台：用轻量故事本体和 YAML Schema，把 3 个章节以上的小说自动转化为可审查、可编辑、可继续打磨的结构化剧本初稿。**

产品不定位为“替代编剧的 AI Writer”，而定位为：

> **尊重原著、懂视听转译、可追溯的导演助理 / 改编助理。**

它要解决的不是“AI 能不能写出一段剧本”，而是：

- AI 改编时为什么会乱改？
- AI 为什么会丢掉伏笔？
- AI 为什么让所有角色说话都像同一个人？
- 作者为什么不信任黑箱生成？
- 生成出来的 YAML 为什么不仅是排版格式，而是可继续打磨的创作资产？

---

## 2. 最终 MVP 取舍

### 2.1 保留范围

本 MVP 保留四个方向，但做收敛后的组合：

1. **可控改编工作台**
   - 支持导入 3 个以上章节。
   - 支持选择目标剧本形态。
   - 支持忠实度控制。
   - 生成结构化 YAML 剧本。

2. **角色声音与潜台词**
   - 为核心角色生成 voice profile。
   - 让对白不只是“解释剧情”，而是包含表层意图、真实意图、潜台词和动作外化。
   - 支持对角色语言风格进行编辑和重新生成。

3. **因果链与伏笔守护**
   - 抽取事件、因果关系、伏笔、兑现点。
   - 每场戏保留 `source_refs`，说明来自原著哪些章节或段落。
   - 检查角色是否知道不该知道的信息，避免连续性错误。

4. **轻量故事本体 Lightweight Story Ontology**
   - 用结构化方式保存人物、关系、秘密、知识状态、事件和伏笔。
   - 不做重型 RDF/OWL 本体系统，不做图数据库。
   - 把 Ontology 作为 YAML Schema 的核心设计思想，并在 UI 中做轻量“故事圣经”面板。

### 2.2 暂缓范围

本轮明确暂缓预算风险模块：

- 不做预算档位。
- 不做外景/夜戏/群演/特效统计。
- 不做低成本替代表达。
- 不做制片可拍性评分。

暂缓原因：

- 预算风险是一套独立规则系统，会显著增加工程和 prompt 复杂度。
- 当前 MVP 的主线已经足够强：可控改编 + 角色声音 + 因果伏笔 + Schema。
- 比赛要求的核心是“3 个章节以上小说自动转换为结构化剧本 YAML，并写 Schema 文档”，预算风险不是必需项。

---

## 3. 方案迭代路线

本项目不要一开始就试图把所有亮点同时做满。更稳的策略是按“合规基础 -> 可控改编 -> 故事本体 -> 潜台词 -> 审查闭环”逐步迭代。每一步都能形成一个可演示版本，后一步建立在前一步之上。

### 3.1 V0：题目合规基础版

目标：

> 先确保满足比赛硬性要求：3 个章节以上小说输入，自动生成结构化 YAML 剧本，并有 Schema 文档。

实现内容：

- 多章节小说输入。
- 至少 3 章校验。
- 基础剧本 YAML 生成。
- YAML 预览与下载。
- 初版 Schema 文档。

YAML 至少包含：

```yaml
project:
source:
characters:
scenes:
```

开发要写：

- 章节输入 UI。
- 章节 ID 管理。
- AI 调用按钮。
- YAML 预览。
- YAML 下载。
- 基础 Schema 校验。

Skill 要写：

- `ScreenplayYamlWriterSkill` 的最小版。
- 要求模型只输出 YAML，不输出解释文本。
- 要求每场包含场景、角色、动作、对白。

Demo 卖点：

> 我们不是只生成一段文本，而是能把 3 个以上章节转成结构化剧本 YAML。

是否必须完成：**必须。**

如果 V0 不稳，后面的亮点都没有意义。

---

### 3.2 V1：可控改编工作台版

目标：

> 让用户能控制“AI 到底怎么改”，避免 AI 过度魔改或机械复印。

实现内容：

- 改编目标选择：短剧 / 网剧 / 电影 / 通用。
- 忠实度选择：低 / 中 / 高。
- 保留重点选择：名场面 / 人物关系 / 原著台词 / 伏笔。
- 生成改编计划 `adaptation_plan`。
- 再根据改编计划生成 YAML 剧本。

新增 YAML：

```yaml
adaptation_config:
  target_format: "web_series"
  fidelity_level: "high"
  preserve_priorities:
    - "relationship_arc"
    - "foreshadowing"

adaptation_plan:
  retained_events: []
  merged_events: []
  protected_elements: []
```

开发要写：

- 改编参数面板。
- 参数进入 AI pipeline。
- 展示“AI 为什么这样改”的改编说明。
- YAML 中写入 `adaptation_config` 和 `adaptation_plan`。

Skill 要写：

- `AdaptationPlannerSkill`。
- 重点限制：
  - 高忠实度时不能删除核心关系和关键伏笔。
  - 每个合并/删减都必须有 reason。
  - 不允许无理由新增主线。

Demo 卖点：

> 作者不是把小说丢给黑箱，而是先设定改编尺度，再让 AI 按策略工作。

是否必须完成：**高优先级。**

这是产品“工作台感”的核心。

---

### 3.3 V2：轻量故事本体版

目标：

> 让 AI 先建立“故事圣经”，再写剧本。这样后续角色声音、因果链、伏笔审查都有结构化底座。

实现内容：

- 生成角色卡。
- 生成人物别名。
- 生成显性目标与隐藏目标。
- 生成秘密。
- 生成人物关系。
- 生成角色已知/未知信息。
- 所有内容带 `source_refs` 或 `evidence_level`。

新增 YAML：

```yaml
story_bible:
  characters: []
  relationship_edges: []
  knowledge_states: []
```

开发要写：

- 故事圣经面板。
- 人物卡展示与编辑。
- 关系列表展示。
- 角色 ID / 关系 ID / secret ID 管理。
- scene 引用角色时做 ID 校验。

Skill 要写：

- `NovelReaderSkill`。
- `StoryOntologySkill`。
- 重点限制：
  - 无原文依据的内容必须标为 `inferred`。
  - 不能把推断当事实。
  - 每个角色要有稳定 ID。
  - 每个关系要有关系类型与证据等级。

Demo 卖点：

> 我们不是直接写剧本，而是先生成故事圣经，让 AI 改编有记忆、有依据、有边界。

是否必须完成：**强烈建议完成。**

这是 Schema 显得高级的关键。

---

### 3.4 V3：因果链与伏笔守护版

目标：

> 解决普通 AI 转剧本最隐蔽的问题：它可能悄悄丢掉原著里的关键因果和伏笔。

实现内容：

- 抽取关键事件。
- 生成事件因果边。
- 识别伏笔 setup。
- 标记 payoff 计划。
- 每场戏引用相关 event 和 foreshadowing。
- 显示未兑现伏笔。

新增 YAML：

```yaml
events: []

causal_graph:
  edges: []

foreshadowing: []
```

开发要写：

- 事件列表。
- 因果关系列表。
- 伏笔/兑现列表。
- 场景详情中展示相关事件和伏笔。
- 未兑现伏笔 warning。
- 引用校验：
  - `setup_event` 是否存在。
  - `payoff_scene` 是否存在。
  - `causal_graph.edges.from/to` 是否存在。

Skill 要写：

- `NovelReaderSkill` 的事件/伏笔抽取部分。
- `ContinuityAuditorSkill` 的伏笔审查部分。
- 重点限制：
  - 时间先后不等于因果。
  - 因果边必须有 explanation。
  - 不确定的伏笔标为 `candidate`。
  - 已埋未兑现要进入 audit_report。

Demo 卖点：

> 每场戏都知道自己从哪里来、承接了什么、埋了什么、将来要兑现什么。

是否必须完成：**建议完成最小版。**

V3 是技术故事最强的一层，但 UI 可以很轻。

---

### 3.5 V4：角色声音与潜台词版

目标：

> 解决 AI 剧本最容易被创作者嫌弃的问题：对白太直白、角色声音千人一面。

实现内容：

- 为角色生成 `voice_profile`。
- 每句台词生成：
  - surface intent。
  - subtext。
  - emotional state。
  - action hint。
- 提供台词重写方向：
  - 更克制。
  - 更锋利。
  - 更生活化。
  - 更有距离感。

新增 YAML：

```yaml
dialogue:
  - character_id: char_001
    line: ""
    surface_intent: ""
    subtext: ""
    emotional_state: ""
    action_hint: ""
```

开发要写：

- 台词详情面板。
- 潜台词展示。
- 角色 voice profile 展示。
- 单场或单句重写按钮。

Skill 要写：

- `DialogueDoctorSkill`。
- 重点限制：
  - 不把潜台词直接说出口。
  - 不写抽象心理，要写可表演动作。
  - 不同角色要有不同句式、节奏和回避方式。
  - 重写时不能破坏 scene 的因果和伏笔。

Demo 卖点：

> AI 不只是把小说心理描写改成对白，而是把心理活动转译成动作、沉默、潜台词和可表演空间。

是否必须完成：**推荐完成一个高质量小范围版本。**

可以只对 1-2 场关键戏做得很漂亮，不必覆盖全剧。

---

### 3.6 V5：审查闭环与打磨版

目标：

> 让产品从“生成器”变成“改编工作台”：生成后还能审查、修复、导出。

实现内容：

- 连续性审查。
- 未兑现伏笔审查。
- 缺失 source_refs 审查。
- 台词过度解释审查。
- Schema 校验失败提示。
- 可选 YAML 修复。

新增 YAML：

```yaml
audit_report:
  continuity_warnings: []
  unresolved_foreshadowing: []
  dialogue_warnings: []
  schema_warnings: []
```

开发要写：

- 审查面板。
- warning 列表。
- 点击 warning 定位到 scene。
- Schema 校验错误展示。
- 可选“一键修复结构错误”。

Skill 要写：

- `ContinuityAuditorSkill`。
- 可选 `YamlRepairSkill`。
- 重点限制：
  - 审查 skill 不大规模重写。
  - 每条 warning 必须指向具体 ID。
  - 不确定问题标为 `needs_human_review`。

Demo 卖点：

> AI 不只负责生成，还会把可能出错的改编判断暴露给作者。

是否必须完成：**时间允许时完成。**

如果时间紧，至少做 Schema 校验和未兑现伏笔 warning。

---

### 3.7 推荐实现顺序

实际开发顺序建议：

```text
V0 题目合规基础版
  -> V1 可控改编工作台版
  -> V2 轻量故事本体版
  -> V3 因果链与伏笔守护版
  -> V4 角色声音与潜台词版
  -> V5 审查闭环与打磨版
```

如果时间不够，最低可交付组合是：

```text
V0 + V1 + V2 的最小版
```

这已经能讲清：

- 多章节输入。
- 可控改编。
- 结构化故事圣经。
- YAML Schema 设计深度。

如果时间中等，推荐交付组合是：

```text
V0 + V1 + V2 + V3
```

这是技术故事最强的版本。

如果时间充裕，完整比赛版是：

```text
V0 + V1 + V2 + V3 + V4 + V5 的轻量版
```

这是最像成熟产品的版本。

---

## 4. 产品故事走向

### 4.1 普通 AI 转剧本的问题

普通 AI 小说转剧本工具通常是：

```text
小说文本 -> Prompt -> 剧本文本
```

这条路线有几个明显问题：

- 作者不知道 AI 为什么删掉某个情节。
- 原著中的小伏笔容易在摘要阶段被吞掉。
- 人物目标、秘密、关系状态无法被稳定追踪。
- 台词容易把潜台词说穿。
- 生成结果虽然像剧本，但不可审查、不可追溯、不可长期编辑。

### 4.2 本产品的主张

本产品采用：

```text
小说文本
  -> 原著资产解析
  -> 轻量故事本体
  -> 改编策略规划
  -> 结构化剧本 YAML
  -> 连续性/伏笔/潜台词审查
```

核心故事：

> 我们不是让 AI 直接胡写剧本，而是先把原著拆成可检查的故事资产，再用 YAML Schema 保存“原著到剧本”的改编推理过程。

这让作者拿到的不只是“文本”，而是一份可以继续协作、修订、校验和导出的剧本工程文件。

---

## 5. 核心用户流程

### 5.1 首屏：导入小说

用户粘贴或上传至少 3 个章节。

建议交互：

- 左侧：章节列表与原文。
- 中间：AI 解析进度。
- 右侧：生成出的故事资产摘要。

基础校验：

- 少于 3 个章节时提示不满足题目要求。
- 每章允许设置标题。
- 用户可以手动调整章节分隔。

### 5.2 第二步：生成故事本体

AI 从小说中抽取：

- 人物。
- 别名。
- 角色目标。
- 秘密。
- 人物关系。
- 已知/未知信息。
- 关键事件。
- 伏笔候选。
- 重要物件。
- 原文引用。

UI 上可以叫“故事圣经”或“人物关系档案”，不要在主界面里直接叫 Ontology，以免显得过学术。

### 5.3 第三步：选择改编策略

用户选择：

- 目标格式：短剧 / 网剧 / 电影剧本 / 通用剧本。
- 忠实度：低、中、高。
- 重点保留：名场面、人物关系、原著台词、悬念伏笔。
- 台词风格：克制、强冲突、生活流、类型片化。

72h MVP 中，目标格式可以只影响生成提示和 YAML 字段，不需要做复杂排版。

### 5.4 第四步：生成 YAML 剧本

生成内容包括：

- 项目信息。
- 原著来源。
- 故事本体。
- 改编策略。
- 事件与因果关系。
- 伏笔与兑现点。
- 场景列表。
- 每场动作、对白、潜台词、来源引用。
- 审查报告。

### 5.5 第五步：审查与编辑

用户可以查看：

- 哪些场景对应哪些原文。
- 哪些伏笔已埋但未兑现。
- 哪些角色说话风格过于接近。
- 哪些角色知道了不该知道的信息。
- 哪些场景缺少戏剧目的。

MVP 中审查可以是列表式，不必做复杂图谱。

### 5.6 第六步：导出

支持：

- 复制 YAML。
- 下载 `.yaml` 文件。
- 下载或查看 YAML Schema 说明文档。

---

## 6. 功能模块细化

### 6.1 模块 A：多章节输入与原文管理

### 目标

满足题目中“3 个章节以上小说文本”的硬性要求，并为后续 `source_refs` 提供稳定来源。

### MVP 功能

- 支持粘贴多章节文本。
- 支持手动添加章节。
- 每个章节拥有稳定 ID：

```yaml
source:
  chapters:
    - id: chapter_001
      title: "第一章 雨夜"
      order: 1
```

- 支持章节字数统计。
- 支持分段编号，用于后续引用。

### 开发重点

- 文本输入 UI。
- 章节数组管理。
- 自动生成 `chapter_001`、`chapter_002` 这类 ID。
- 分段与 paragraph index。

### Skill 重点

不需要让 skill 负责章节管理。skill 只消费已经结构化的章节输入。

---

### 6.2 模块 B：轻量故事本体 Story Ontology

### 目标

把原著中的人物、关系、秘密、事件和知识状态变成可引用、可校验、可编辑的结构化数据。

### 为什么要做

小说转剧本最大的风险不是格式错误，而是：

- 人物动机被简化。
- 关系变化被跳过。
- 伏笔被摘要吞掉。
- 角色突然知道了不该知道的信息。
- 后续场景无法追溯来源。

轻量故事本体可以让这些内容显性化。

### MVP 数据内容

```yaml
story_bible:
  characters:
    - id: char_001
      name: "林晚"
      aliases: ["晚晚"]
      narrative_role: "protagonist"
      goals:
        explicit: "查清母亲死亡真相"
        hidden: "证明自己值得被爱"
      secrets:
        - id: secret_001
          description: "她不知道周砚与母亲旧案有关"
      voice_profile:
        rhythm: "短句，克制，情绪高时反问"
        defense_mechanism: "用冷静掩饰恐惧"
      source_refs:
        - chapter_id: chapter_001
          paragraph_range: "12-18"

  relationship_edges:
    - id: rel_001
      from: char_001
      to: char_002
      type: "mutual_attraction_with_mistrust"
      current_state: "互相吸引但严重不信任"
      evidence_level: "explicit"
      source_refs:
        - chapter_id: chapter_002
          paragraph_range: "18-26"

  knowledge_states:
    - character_id: char_001
      knows:
        - event_003
      does_not_know:
        - secret_001
```

### UI 表现

主界面可以叫：

- 故事圣经
- 人物关系档案
- 原著资产

包含三块：

- 人物卡。
- 关系列表。
- 秘密/已知信息列表。

### 开发重点

- 稳定 ID。
- 人物卡编辑。
- 关系边编辑。
- scene 引用角色 ID 时校验是否存在。
- Schema 中定义字段类型与必填项。

### Skill 重点

`StoryOntologySkill` 负责从小说解析结果中生成：

- 角色目标。
- 隐藏欲望。
- 人物关系。
- 秘密。
- 已知/未知状态。
- 语言风格。
- 原文依据。

关键约束：

- 没有原文证据的内容必须标为 `inferred`。
- 不允许把推断内容写成确定事实。
- 每条关系尽量附带 `source_refs`。
- 角色语言风格必须来自原文样本或明确标为推断。

---

### 6.3 模块 C：因果链与伏笔守护

### 目标

让 AI 生成的剧本不只是“场景集合”，而是有因果、有伏笔、有兑现关系的改编结构。

### MVP 数据内容

```yaml
events:
  - id: event_001
    title: "林晚发现旧照片"
    chapter_refs:
      - chapter_id: chapter_001
        paragraph_range: "30-36"
    participants:
      - char_001
    event_type: "discovery"
    summary: "林晚在母亲遗物中发现一张被撕掉半边的旧照片。"

causal_graph:
  edges:
    - from: event_001
      to: event_004
      relation: "motivates"
      explanation: "旧照片促使林晚开始调查母亲旧案。"

foreshadowing:
  - id: foreshadow_001
    setup_event: event_001
    setup_scene: scene_001
    payoff_event: event_007
    payoff_scene: scene_006
    status: "planned"
    description: "旧照片上的缺失人物将在第六场揭示为周砚父亲。"
```

### UI 表现

MVP 可做成列表，不必做真正可拖拽图谱：

- 事件列表。
- 因果边列表。
- 伏笔/兑现列表。
- 每场戏旁边显示“本场承接事件”和“本场埋设伏笔”。

### 开发重点

- 事件 ID 管理。
- 伏笔 setup/payoff 引用校验。
- 场景与事件关系展示。
- 未兑现伏笔 warning。

### Skill 重点

`NovelReaderSkill` 和 `ContinuityAuditorSkill` 共同负责：

- 抽取关键事件。
- 判断事件因果关系。
- 标注伏笔候选。
- 判断伏笔是否在剧本中得到兑现。
- 检查人物是否知道不该知道的信息。

关键约束：

- 因果关系必须用自然语言解释。
- 如果只是时间先后，不要标为因果。
- 伏笔必须区分 `setup` 和 `payoff`。
- 不确定的伏笔状态标为 `candidate`，不要强行确认。

---

### 6.4 模块 D：可控改编策略

### 目标

让用户决定 AI 的改编尺度，避免“复印机”和“魔改疯子”两个极端。

### MVP 功能

- 忠实度选择：低 / 中 / 高。
- 目标格式：短剧 / 网剧 / 电影 / 通用。
- 保留重点：名场面 / 关系线 / 原著台词 / 伏笔。
- 生成改编说明。

### YAML 结构示例

```yaml
adaptation_config:
  target_format: "web_series"
  fidelity_level: "high"
  preserve_priorities:
    - "iconic_scenes"
    - "relationship_arc"
    - "foreshadowing"
  dialogue_style: "restrained_with_subtext"
```

### Skill 重点

`AdaptationPlannerSkill` 根据配置输出：

- 哪些事件保留。
- 哪些事件合并。
- 哪些情节压缩。
- 哪些场景必须出现。
- 为什么这样改。

示例输出：

```yaml
adaptation_plan:
  retained_events:
    - event_001
    - event_004
  merged_events:
    - from: [event_002, event_003]
      into: scene_002
      reason: "两段原著都服务于同一关系误会，可合并为一场冲突。"
  protected_elements:
    - foreshadow_001
    - rel_001
```

### 开发重点

- 策略选择 UI。
- 将策略传入生成 pipeline。
- 展示 AI 的改编说明。

---

### 6.5 模块 E：角色声音与潜台词

### 目标

解决 AI 剧本最明显的问题：台词过于直白、太工整、所有角色像同一个人。

### MVP 数据内容

```yaml
dialogue:
  - character_id: char_001
    line: "你到底还有多少事没告诉我？"
    surface_intent: "质问对方隐瞒事实"
    subtext: "她真正害怕的是自己从未被信任"
    emotional_state: "anger_covering_fear"
    action_hint: "她没有看他，而是盯着他攥紧的手"
```

### UI 表现

- 每句台词旁边显示潜台词。
- 显示角色声音标签。
- 支持“更克制 / 更锋利 / 更生活化 / 更有距离感”等重写按钮。

### Skill 重点

`DialogueDoctorSkill` 负责：

- 从角色 voice profile 生成不同人物的对白。
- 检查解释型对白。
- 把内心独白转为动作、沉默、道具、微反应。
- 为每句台词补充 surface intent 和 subtext。

关键约束：

- 不要让角色直接说出全部心理活动。
- 每个角色的句长、语气、回避方式要不同。
- 潜台词不一定写进对白，但要写进 YAML 字段。
- 行动提示要可表演，不要写抽象心理。

---

### 6.6 模块 F：YAML 剧本生成、校验与导出

### 目标

满足比赛硬性要求，并把 Schema 设计做成产品亮点。

### MVP 功能

- 生成 YAML。
- 展示 YAML 预览。
- 支持用户编辑。
- 校验 YAML 是否符合 Schema。
- 报告缺失字段或引用错误。
- 下载 `.yaml`。

### 开发重点

- YAML 解析与格式化。
- Schema 校验。
- 引用完整性校验：
  - scene 引用的 character 必须存在。
  - causal_graph 引用的 event 必须存在。
  - foreshadowing 引用的 scene/event 必须存在。
- 下载文件。

### Skill 重点

`ScreenplayYamlWriterSkill` 负责按 Schema 生成初稿。

可增加一个可选的 `YamlRepairSkill`：

- 当校验失败时，把错误信息和原 YAML 发给模型。
- 要求只修复结构错误，不改写创作内容。

---

## 7. Skill 与开发边界总表

| 模块 | Skill 负责 | 开发负责 |
| --- | --- | --- |
| 多章节输入 | 不负责章节管理，只读取结构化输入 | 粘贴/上传、章节拆分、ID、字数统计 |
| 原著解析 | 抽取人物、事件、地点、物件、伏笔候选 | 保存解析结果、展示列表、允许编辑 |
| 故事本体 | 推断目标、秘密、关系、知识状态、voice profile | 稳定 ID、人物卡 UI、关系引用校验 |
| 改编策略 | 判断保留/合并/压缩，解释原因 | 策略选择控件、参数传递、版本保存 |
| 剧本生成 | 按 Schema 写 YAML 场景、动作、对白 | YAML 预览、编辑、下载、格式化 |
| 潜台词 | 生成 subtext、surface intent、action hint | 台词对照 UI、重写按钮、编辑保存 |
| 因果/伏笔 | 抽取因果边、伏笔 setup/payoff、审查问题 | 事件/伏笔列表、引用校验、warning 面板 |
| Schema | 遵守字段要求，按规则输出 | 定义 Schema、校验、错误提示 |

核心原则：

> **创作判断交给 Skill，结构可信交给代码。**

---

## 8. 建议编写的 6 个核心 Skill

### 8.1 NovelReaderSkill

输入：

- 章节文本。
- 段落编号。

输出：

- characters。
- locations。
- objects。
- events。
- foreshadowing_candidates。
- source_refs。

关键限制：

- 不要生成剧本。
- 只做原著解析。
- 推断内容必须标注 `evidence_level: inferred`。
- 每个事件必须有原文来源。

### 8.2 StoryOntologySkill

输入：

- NovelReaderSkill 输出。
- 原文片段。

输出：

- story_bible。
- relationship_edges。
- knowledge_states。
- character voice profiles。

关键限制：

- 不要把所有关系都写成确定事实。
- 关系必须有 `explicit`、`inferred` 或 `ambiguous`。
- 对角色语言风格的判断必须引用原文样本或说明是推断。

### 8.3 AdaptationPlannerSkill

输入：

- story_bible。
- events。
- causal_graph。
- adaptation_config。

输出：

- retained_events。
- merged_events。
- deleted_or_deferred_events。
- protected_elements。
- scene_plan。

关键限制：

- 高忠实度时不得删除核心人物关系和关键伏笔。
- 所有合并/删除都要写 reason。
- 不直接写最终对白。

### 8.4 ScreenplayYamlWriterSkill

输入：

- scene_plan。
- story_bible。
- adaptation_config。
- Schema 摘要。

输出：

- 完整 screenplay YAML。

关键限制：

- 只输出 YAML。
- 所有 scene 必须引用 source_refs。
- 所有 character_id 必须来自 story_bible。
- 每场至少包含 dramatic_purpose、action、dialogue。

### 8.5 DialogueDoctorSkill

输入：

- 某一场或多场 scene。
- character voice profiles。
- 用户选择的改写方向。

输出：

- 改写后的 dialogue。
- subtext。
- action_hint。
- 修改说明。

关键限制：

- 不要把潜台词直接说出口。
- 不要让所有角色句式相同。
- 动作提示必须可表演、可看见。

### 8.6 ContinuityAuditorSkill

输入：

- story_bible。
- events。
- foreshadowing。
- scenes。

输出：

- continuity_warnings。
- unresolved_foreshadowing。
- character_voice_warnings。
- missing_source_refs。

关键限制：

- 只做审查，不大规模重写。
- 每条 warning 要给出涉及的 scene_id / character_id / event_id。
- 不确定的问题标为 `needs_human_review`。

---

## 9. YAML Schema 设计方向

### 9.1 Schema 是什么

Schema 是这份 YAML 的“结构规则”。

它规定：

- 顶层有哪些字段。
- 每个字段是什么类型。
- 哪些字段必填。
- 哪些字段可选。
- 哪些 ID 必须互相引用。
- 为什么要这样设计。

比赛要求额外写一篇文档定义剧本 YAML Schema，并说明设计原因。这里是产品亮点之一。

### 9.2 为什么 Schema 是亮点

普通参赛作品的 YAML 可能只是：

```yaml
title:
scenes:
  - location:
    action:
    dialogue:
```

这只是“剧本排版结构”。

本产品的 Schema 应该表达：

> 剧本不是孤立文本，而是由人物目标、关系状态、因果链、伏笔和原文引用共同支撑的改编结果。

因此 Schema 中应包含：

- `source`：原著章节与段落。
- `story_bible`：轻量故事本体。
- `events`：关键事件。
- `causal_graph`：因果关系。
- `foreshadowing`：伏笔与兑现。
- `adaptation_config`：改编策略。
- `scenes`：剧本场景。
- `audit_report`：连续性与潜台词审查。

这会让 Schema 文档显得有设计深度，因为它不是在定义“剧本长什么样”，而是在定义“AI 改编过程如何可追溯、可审查、可迭代”。

### 9.3 推荐顶层结构

```yaml
schema_version: "1.0"

project:
  title: ""
  logline: ""
  target_format: ""

source:
  chapters: []

adaptation_config:
  target_format: ""
  fidelity_level: ""
  preserve_priorities: []

story_bible:
  characters: []
  relationship_edges: []
  knowledge_states: []

events: []

causal_graph:
  edges: []

foreshadowing: []

scenes: []

audit_report:
  continuity_warnings: []
  unresolved_foreshadowing: []
  dialogue_warnings: []
```

### 9.4 场景结构建议

```yaml
scenes:
  - id: scene_001
    title: "雨夜重逢"
    source_refs:
      - chapter_id: chapter_001
        paragraph_range: "12-24"
    dramatic_purpose:
      - "建立主角关系"
      - "埋下旧案伏笔"
    location:
      name: "旧巷口"
      time: "night"
      interior_exterior: "EXT"
    characters:
      - char_001
      - char_002
    related_events:
      - event_001
    causal_links:
      causes:
        - event_001
      effects:
        - event_004
    foreshadowing:
      setups:
        - foreshadow_001
      payoffs: []
    action:
      - "林晚停在巷口，看见周砚手里攥着一块旧怀表。"
    dialogue:
      - character_id: char_001
        line: "你怎么会在这里？"
        surface_intent: "质问对方出现原因"
        subtext: "她不愿承认自己一直在等他"
        action_hint: "她把伞柄攥得更紧"
```

---

## 10. 72h 开发路线

### Day 1：搭骨架和数据结构

目标：让产品能完整跑通输入到 YAML 输出。

优先事项：

1. 搭建基础 Web 应用。
2. 实现多章节输入。
3. 定义核心 TypeScript/JSON 数据结构。
4. 写第一版 YAML Schema。
5. 写 NovelReaderSkill / StoryOntologySkill 的 prompt。
6. 跑通“小说 -> 故事本体”的 AI 调用。

可展示结果：

- 输入 3 章小说。
- 生成角色卡、事件卡、伏笔候选。

### Day 2：生成剧本与可控改编

目标：让产品能生成像样的 YAML 剧本，并体现可控改编。

优先事项：

1. 实现改编参数面板。
2. 写 AdaptationPlannerSkill。
3. 写 ScreenplayYamlWriterSkill。
4. 实现 YAML 预览与下载。
5. 接入 Schema 校验。
6. 展示 source_refs、related_events、foreshadowing。

可展示结果：

- 用户选择高忠实度。
- AI 生成带原文引用和伏笔引用的 YAML 剧本。

### Day 3：打磨亮点与 demo 叙事

目标：把产品从“能跑”打磨成“有故事、有卖点”。

优先事项：

1. 接入 DialogueDoctorSkill。
2. 接入 ContinuityAuditorSkill。
3. 做审查面板：
   - 未兑现伏笔。
   - 人物知识状态冲突。
   - 台词过度解释。
4. 写 Schema 设计文档。
5. 准备一份示例小说输入和示例 YAML 输出。
6. 打磨 UI 文案和演示路径。

可展示结果：

- 点击某句台词，显示表层意图和潜台词。
- 点击某场戏，显示来自哪个章节、承接哪个事件、埋了哪个伏笔。
- 导出符合 Schema 的 YAML。

---

## 11. Demo 演示脚本

建议演示时按以下故事讲：

### 第一步：展示普通 AI 的问题

“小说转剧本最难的不是格式转换，而是改编判断。普通 AI 很容易丢掉伏笔、写穿潜台词、让人物声音变得平均化。”

### 第二步：导入 3 章小说

展示产品满足题目硬性要求。

### 第三步：生成故事圣经

展示人物卡、关系边、秘密、已知/未知信息。

讲法：

“我们先不急着写剧本，而是先让 AI 读懂这个故事世界。”

### 第四步：选择改编策略

展示忠实度和保留重点。

讲法：

“作者可以决定 AI 是更忠实原著，还是更主动进行影视化压缩。”

### 第五步：生成 YAML 剧本

展示某一场戏：

- 有动作。
- 有对白。
- 有潜台词。
- 有 source_refs。
- 有 causal_links。
- 有 foreshadowing。

讲法：

“这不是一段黑箱文本，而是一场有来源、有目的、有因果位置的戏。”

### 第六步：审查面板

展示未兑现伏笔或人物知识状态 warning。

讲法：

“AI 不只生成，还会提醒作者：这里可能有连续性问题，需要人工确认。”

### 第七步：导出 YAML 与 Schema 文档

讲法：

“最终输出不是一次性文本，而是可被编辑器、工作流和后续 AI 继续读取的结构化剧本资产。”

---

## 12. 成功标准

### 12.1 硬性标准

- 能输入 3 个章节以上小说。
- 能生成结构化 YAML。
- 能导出 YAML。
- 有独立 Schema 文档。
- Schema 文档说明设计原因。

### 12.2 产品完成度标准

- 用户能看懂完整流程。
- YAML 字段不是堆砌，而是服务改编逻辑。
- 每场戏能追溯到原文。
- 至少能展示人物卡、事件卡、伏笔卡。
- 至少能展示一条连续性或潜台词审查结果。

### 12.3 亮点标准

- 不是普通“一键生成剧本”。
- 有“轻量故事本体”的结构化思想。
- 有“潜台词/角色声音”的创作者共情。
- 有“因果/伏笔守护”的技术故事。
- 有“Schema 约束 AI 输出”的工程可信度。

---

## 13. 风险与规避

### 风险 1：Scope 过大

规避：

- 不做预算风险。
- 不做图数据库。
- 不做复杂本体编辑器。
- 不做多人协作。
- 不做 Final Draft / Fountain 导出。

### 风险 2：AI 输出不稳定

规避：

- 所有 skill 要求 YAML/JSON 结构化输出。
- 开发层做 Schema 校验。
- 校验失败时走修复 skill。
- UI 允许用户手动编辑。

### 风险 3：Ontology 概念太学术

规避：

- 产品 UI 叫“故事圣经”。
- 文档中再解释它是 Lightweight Story Ontology。
- 只保留人物、关系、秘密、知识状态、事件、伏笔几个核心概念。

### 风险 4：潜台词质量不稳定

规避：

- 不承诺最终成稿质量。
- 定位为“可继续打磨的初稿”。
- 强调 AI 帮作者暴露问题、提供变体，而不是代替最终判断。

---

## 14. 推荐最终命名

可以考虑以下产品名方向：

1. **ScriptWeaver**
   - 强调把小说线索编织成剧本。

2. **StoryBible Studio**
   - 强调故事圣经和结构化改编。

3. **SceneForge**
   - 强调把小说锻造成场景。

4. **伏笔工房**
   - 中文感强，卖点清晰。

5. **改编室**
   - 简洁，贴近编剧工作流。

如果是比赛 demo，推荐使用：

> **改编室：AI 小说转 YAML 剧本工作台**

副标题：

> 用轻量故事本体守住原著因果、伏笔与人物声音。

---

## 15. 最终建议

本项目不要再横向扩展功能。最适合 72h 的最终范围是：

```text
多章节小说输入
  -> 轻量故事本体生成
  -> 改编策略选择
  -> YAML 剧本生成
  -> 潜台词/角色声音审查
  -> 因果/伏笔/连续性审查
  -> YAML + Schema 文档导出
```

这条路线同时满足：

- 题目要求。
- 产品完成度。
- 创作者共情。
- 技术故事。
- Schema 文档深度。

最终对外叙事可以定为：

> 我们没有做一个会胡编的 AI 编剧，而是做了一个带 Schema 约束的改编工作台。它先把小说拆成轻量故事本体，再生成可追溯的 YAML 剧本，让人物关系、因果链、伏笔、潜台词都能被作者审查和继续打磨。
