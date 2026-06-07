# 剧本 YAML Schema 设计文档

**Schema 版本**：1.1  
**设计者**：改编室产品团队  
**日期**：2026-06-07

---

## 一、Schema 概述

本 Schema 定义了"AI 小说转剧本"工具输出的 YAML 结构化剧本的完整数据格式。

### 1.1 设计目标

本 Schema 不只是一份"剧本排版规范"。它的核心设计目标是：

> **将 AI 改编剧本的过程从一次性的"文本生成"转变为可追溯、可审查、可迭代的"工程文件"输出。**

具体而言，Schema 要承载三个层次的诉求：

1. **可追溯**：每一场戏、每一句台词、每一个角色特征，都要能追溯到原文的具体章节和段落
2. **可审查**：角色的知情状态、伏笔的兑现情况、改编的取舍决策，都必须显式记录，让创作者能判断 AI 的改编是否合理
3. **可迭代**：通过稳定 ID 体系，让局部修改不会引发全局数据断裂，支持后续的定向重生成

### 1.2 理论基础：本体论（Ontology）

本 Schema 最底层的设计思想来自**本体论（Ontology）**。

本体论是一个哲学概念，后来被计算机科学借用，指一种对某个领域内"存在哪些实体、各自有什么属性、彼此之间有什么关系"的形式化定义。在 AI 和 Agent 系统里，它常以知识图谱或结构化记忆的形态落地——让机器不只是处理文字，而是知道自己在讨论什么。

映射到小说转剧本这个场景：

| Ontology 概念 | 在本 Schema 中的对应 | 说明 |
|---|---|---|
| **实体（Entity）** | `characters`、`events`、`foreshadowing`、`locations`、`objects` | 故事世界中存在什么 |
| **属性（Attribute）** | `goals`、`voice_profile`、`secrets`、`event_flow` | 每个实体有什么特征 |
| **关系（Relation）** | `relationship_edges`、`causal_graph`、`knowledge_states`、`continuity_anchors` | 实体之间如何关联 |
| **推理标注（Provenance）** | `evidence_level`（explicit / inferred / candidate）、`source_refs` | 每条信息的可信度和来源 |

这个设计带来的核心架构收益是**"本体"与"表现"分离**：

- **本体层**（`story_bible`、`events`、`causal_graph`、`foreshadowing`）：定义"这个故事世界是什么"——角色是谁、他们之间什么关系、发生了什么事件、因果关系如何、埋了什么伏笔。这些信息是稳定的，不随具体台词变化。
- **表现层**（`scenes`）：定义"这个故事在当前剧本里怎么呈现"——每一场戏怎么写、每句台词怎么说。这些信息是可以被修改、重写、替换的。
- **索引层**（`script_structure`、`core_elements`）：连接本体和表现，提供跨层导航。

分离之后，修改一句话不会动摇整个故事世界的定义；修改一个角色设定时，系统能顺着引用链路找到所有受影响的台词——这就是解决"修改时全局坍塌"的架构基础。

### 1.3 与普通剧本 YAML 的差异

普通参赛作品的 YAML 可能只是：

```yaml
title: 某某小说
scenes:
  - location: 客厅
    dialogue:
      - 角色A: 你好
      - 角色B: 你好
```

这是"排版结构"——它只描述了剧本长什么样。

本 Schema 定义的是"改编推理结构"——它记录了：

- 原著中的角色、事件、关系、伏笔是什么
- AI 做了哪些改编决策（保留/合并/删除）
- 剧本中每场戏承接了哪些原著事件，埋设了哪些伏笔
- 每句台词的表层意图、潜台词、情绪状态、可表演动作

---

## 二、顶层结构设计

### 2.1 完整顶层字段

```yaml
schema_version: "1.1"      # Schema 版本号
project: {}                 # 项目元数据
source: {}                  # 原著来源引用
adaptation_config: {}       # 改编策略配置
script_structure: {}        # 故事梗概→大纲→文学剧本 三段式结构
story_bible: {}             # 轻量故事本体（角色、关系、知情状态）
core_elements: {}           # 核心要素索引（动作、情节、情境、主题）
events: []                  # 关键叙事事件
causal_graph: {}            # 事件因果关系图
foreshadowing: []           # 伏笔 setup→payoff 追踪
adaptation_plan: {}         # 改编操作计划（保留/合并/删除决策）
scenes: []                  # 剧本场景（最终输出）
audit_report: {}            # 连续性 & 潜台词审查报告
```

### 2.2 为什么要 13 个顶层字段？

这 13 个字段不是堆砌出来的。它们背后有明确的设计逻辑：

| 字段 | 设计原因 |
|------|---------|
| `schema_version` | 未来 Schema 会迭代，版本号保证向后兼容 |
| `project` | 项目级元数据，与具体改编内容解耦 |
| `source` | 原著章节引用，保证整个输出可追溯到原文 |
| `adaptation_config` | 用户设定的改编策略，让 AI 的"自由度"参数化、可复现 |
| `script_structure` | 保留"梗概→大纲→文学剧本"的训练链路，体现改编思维过程 |
| `story_bible` | **Schema 的核心**：轻量故事本体，承载角色、关系、知情状态、冲突池、可视化约束 |
| `core_elements` | 对文学剧本核心要素做索引——动作、情节、情境、主题、主人公——方便校验器做完整性检查 |
| `events` | 关键叙事事件列表，是因果图和场景引用的锚点 |
| `causal_graph` | 事件的因果关系——"时间先后≠因果"，所以单独建模 |
| `foreshadowing` | 伏笔的 setup→payoff 追踪，解决"摘要过程吞噬伏笔"的痛点 |
| `adaptation_plan` | AI 的改编决策记录——保留了哪些、合并了哪些、删除了哪些、为什么 |
| `scenes` | 最终剧本场景，是本体的"表现层" |
| `audit_report` | 校验结果嵌入输出，让创作者看到哪些地方需要人工确认 |

### 2.3 设计原则："本体"与"表现"分离

整个 Schema 最核心的设计原则来自**本体论（Ontology）**：

- **本体层**：`story_bible`、`events`、`causal_graph`、`foreshadowing`、`adaptation_config` —— 描述"这个故事世界是什么"
- **表现层**：`scenes` —— 描述"在剧本里这场戏怎么写"
- **索引层**：`script_structure`、`core_elements` —— 连接本体和表现，方便校验和导航

**为什么要分三层？**

因为如果角色设定和具体台词混在一起，编剧修改一句台词就等于修改了输出文件——下次让 AI 重新生成，角色性格必须从修改后的台词里反向推断，这是不可靠的。而分离之后，修改台词不影响角色本体，修改角色本体时可以定向找到所有受影响的台词。

---

## 三、核心字段设计详解

### 3.1 `story_bible`：轻量故事本体

```yaml
story_bible:
  characters:
    - id: char_001
      name: 林晚
      aliases: [晚晚]
      narrative_role: protagonist
      goals:
        explicit: 查清母亲死亡真相
        hidden: 证明自己值得被爱
      secrets:
        - id: secret_001
          description: 她不知道周砚与母亲旧案有关
      voice_profile:
        rhythm: 短句，克制，情绪高时反问
        diction: 精准，不拖泥带水
        defense_mechanism: 用冷静掩饰恐惧
      source_refs:
        - chapter_id: chapter_001
          paragraph_range: p_012-p_018

  relationship_edges:
    - id: rel_001
      from: char_001
      to: char_002
      type: mutual_attraction_with_mistrust
      current_state: 互相吸引但严重不信任
      evidence_level: explicit
      source_refs:
        - chapter_id: chapter_002
          paragraph_range: p_018-p_026

  knowledge_states:
    - character_id: char_001
      knows: [event_001, event_003]
      does_not_know: [secret_001]

  continuity_anchors:
    - id: anchor_001
      anchor_type: addressing_rule
      summary: 周砚对林晚的称呼从"林小姐"逐渐变为"晚晚"
      applies_to: [char_001, char_002]
      source_refs:
        - chapter_id: chapter_001
          paragraph_range: p_002-p_003

  dramatic_assets:
    conflict_pool:
      - id: conflict_001
        conflict_axis: 安顿需求 vs 合租风险
        participants: [char_001, char_002]
        related_events: [event_001, event_002]
    filmic_constraints:
      - id: filmic_001
        constraint_type: internal_state_to_action
        summary: 林晚每次不安时都会攥紧手边的物件，需要转为可演动作
        related_characters: [char_001]
```

#### 设计原因

**角色卡（characters）**：
- `goals` 分为 `explicit`（显性目标）和 `hidden`（隐藏欲望）——因为戏剧冲突的核心往往在于"角色想要的东西"和"角色真正需要的东西"之间的差距。AI 如果不区分这两者，就会把潜台词说穿。
- `voice_profile` 包含 `rhythm`、`diction`、`defense_mechanism` —— 三个维度分别控制句长节奏、用词选择、情绪回避方式。这是解决"千人一面"的数据基础。
- `source_refs` 标注出处——让创作者能验证 AI 的角色理解是否来自原文依据。

**关系边（relationship_edges）**：
- 每条关系有 `evidence_level`（explicit / inferred / candidate）—— 这是对 AI "推断"的显式标注。创作者可以一眼看出哪些关系是原文明确写的，哪些是 AI 猜的。
- `type` 使用细粒度标签（如 `mutual_attraction_with_mistrust`）而非笼统的"朋友/敌人"——因为小说中的关系往往是复合的、矛盾的。

**知情状态（knowledge_states）**：
- `knows` 和 `does_not_know` 引用事件 ID 或秘密 ID，不写自然语言——因为自然语言无法被程序校验。引用事件 ID 后，校验器可以自动检查：Scene 5 中角色 A 使用了只有角色 B 才知道的信息 → 报 warning。
- 这是解决"角色突然知道了不该知道的信息"这一连续性问题的基础设施。

**连续性锚点（continuity_anchors）**：
- 7 种锚点类型（称呼规则、人设固定点、关系状态、关键道具、时间线事实、世界规则、身份锚点）——覆盖了编剧修改时最容易产生"漂移"的维度
- 当用户修改某个角色的设定时，系统可以检索所有引用该角色 ID 的锚点，按锚点类型判断哪些需要更新
- 这是实现"修改不崩塌"的核心数据结构

**戏剧资产（dramatic_assets）**：
- `conflict_pool` 收录原文中已有的冲突轴（欲望差、信息差、立场差、关系压力、时间压力、能力差）——保证改编不会丢掉原著的戏剧张力
- `filmic_constraints` 记录"哪些内心信息必须转化为可演、可见、可听的表达"——这是潜台词不变成直白台词的前提

### 3.2 `events`：关键叙事事件

```yaml
events:
  - id: event_001
    title: 林晚发现旧照片
    event_type: discovery
    participants: [char_001]
    summary: 林晚在母亲遗物中发现一张被撕掉半边的旧照片。
    complete_event: true
    event_flow: [发现照片, 辨认人物, 决定调查]
    must_keep_together: true
    conflict_axis: 好奇心 vs 母亲的警告
    source_refs:
      - chapter_id: chapter_001
        paragraph_range: p_030-p_036
```

#### 设计原因

- `complete_event` 标记该事件是否具备完整的事件结构（触发→行动→冲突→结果）。完整事件不应被 AI 无依据拆碎。
- `event_flow` 用数组记录连续动作序列，避免 AI 把"发现→辨认→决定"拆成三个重复事件。
- `must_keep_together` 标记该事件在高忠实度模式下不可拆分——保护名场面不被碎片化。

### 3.3 `causal_graph`：因果关系图

```yaml
causal_graph:
  edges:
    - from: event_001
      to: event_004
      relation: motivates
      explanation: 旧照片促使林晚开始调查母亲旧案，直接导致她与周砚在档案馆相遇。
```

#### 设计原因

- 因果边独立建模，而非内嵌在事件中——因为因果关系天然是**跨事件**的，且一个事件可能被多个事件同时导致/同时导致多个事件
- `explanation` 用自然语言解释因果逻辑——这是给人类创作者看的，让 AI 的因果推断可以被质疑和修正
- 硬约束：**时间先后不等于因果。**`causal_graph` 只收录有明确因果逻辑关系的边，不收录"A 发生了然后 B 发生了"的时间顺序

### 3.4 `foreshadowing`：伏笔追踪

```yaml
foreshadowing:
  - id: foreshadow_001
    setup_event_id: event_001
    setup_scene_id: scene_001
    payoff_event_id: event_007
    payoff_scene_id: scene_006
    status: planned
    description: 旧照片上缺失的半边人物将在第六场揭示为周砚父亲。
```

#### 设计原因

- 伏笔是小说转剧本过程中最容易丢失的信息——它往往只是一个"茶杯的特写"或"一句看似无关的对白"，在语义蒸馏阶段被当作噪声过滤掉
- `setup` 和 `payoff` 分开标注，`status` 追踪兑现状态（candidate → planned → fulfilled → unresolved）
- `payoff_scene_id` 为空时，校验器报"未兑现伏笔"warning——这是审查面板的核心数据来源

### 3.5 `scenes`：剧本场景

```yaml
scenes:
  - id: scene_001
    title: 雨夜重逢
    scene_heading:
      sequence: 1
      location: 旧巷口
      interior_exterior: EXT
      time_of_day: night
      text: "1. 旧巷口 外景 夜"
    source_refs:
      - chapter_id: chapter_001
        paragraph_range: p_012-p_024
    dramatic_purpose:
      - 建立主角关系
      - 埋下旧案伏笔
    location:
      name: 旧巷口
      time: 夜
      interior_exterior: EXT
    characters: [char_001, char_002]
    related_events: [event_001]
    causal_links:
      causes: [event_001]
      effects: [event_004]
    foreshadowing:
      setups: [foreshadow_001]
      payoffs: []
    action:
      - △林晚停在巷口，看见周砚手里攥着一块旧怀表。
    content_blocks:
      - id: block_001
        block_type: action
        text: 旧巷口，夜雨。林晚撑着伞停在巷口。
      - id: block_002
        block_type: dialogue
        character_id: char_001
        dialogue_line_id: line_001
        text: 林晚：（把伞柄攥得更紧）你怎么会在这里？
    dialogue:
      - id: line_001
        character_id: char_001
        line: 你怎么会在这里？
        surface_intent: 质问对方出现原因
        subtext: 她不愿承认自己一直在等他
        emotional_state: 恐惧而期待
        action_hint: 把伞柄攥得更紧
```

#### 设计原因

**场景级字段**：
- `dramatic_purpose`（戏剧目的）用数组标注每一场戏要达成什么——没有目的的戏就是废戏。创作者可以快速扫描哪些场景缺乏戏剧功能。
- `causal_links` 标注本场戏在因果链中的位置——承接了什么、导致了什么
- `foreshadowing` 中的 `setups` 和 `payoffs` 让创作者可以按场景追踪伏笔的埋设和回收

**对白级字段**：
- `surface_intent`（表层意图）和 `subtext`（潜台词）分列——这是直接回应"缺乏潜台词转译"的痛点。AI 不能把潜台词写进台词正文，但必须把潜台词的分析写进 YAML，让创作者审查。
- `emotional_state`（情绪状态）——不写"悲伤"，写"恐惧而期待""愤怒掩盖恐惧"。复合情绪标签比简单情绪词更有戏剧价值。
- `action_hint`（动作提示）——必须是可表演、可被摄影机拍到的具体动作。不写"她感到不安"，写"她把伞柄攥得更紧"。这是"Show, Don't Tell"原则的数据化。

**content_blocks**：
- action 和 dialogue 块交替排列，模拟真实剧本脚本的阅读节奏
- 每条 dialogue 块通过 `dialogue_line_id` 引用 `dialogue` 数组中的详细条目，做到"正文可读 + 元数据可查"

### 3.6 `adaptation_config` 与 `adaptation_plan`

```yaml
adaptation_config:
  target_format: web_series
  fidelity_level: high
  preserve_priorities: [relationship_arc, foreshadowing]
  dialogue_style: restrained_with_subtext

adaptation_plan:
  retained_events: [event_001, event_004]
  merged_events:
    - from: [event_002, event_003]
      into: event_merged_001
      reason: 两段原著都服务于同一关系误会，合并为一场冲突后节奏更紧凑
  deleted_or_deferred_events:
    - event_id: event_005
      reason: 次要支线，推迟到后续剧集
  protected_elements: [主角关系弧线, 核心伏笔回收]
  scene_plan:
    - scene_id: scene_001
      purpose: 建立世界观与主角登场
      source_events: [event_001]
```

#### 设计原因

- `adaptation_config` 是用户对 AI 的控制面板——忠实度、目标格式、保留重点、台词风格，全部参数化
- `adaptation_plan` 是 AI 对用户的"改编解释"——不能说"我决定删掉这个事件"，必须说"删掉的原因是什么"
- `scene_plan` 是剧本的"场景-事件映射表"——每个场景覆盖了哪些原著事件，有明确的引用关系，方便校验器检查：是否有事件被遗漏？是否有场景没有原著依据？

### 3.7 `audit_report`：审查报告

```yaml
audit_report:
  continuity_warnings:
    - target_type: scene
      target_id: scene_005
      message: 角色 char_001 在此场景中使用了只有 char_002 知道的信息(event_007)
      severity: warning
      needs_human_review: true
  unresolved_foreshadowing:
    - foreshadow_id: foreshadow_003
      message: 伏笔"第三章的茶杯特写"未在剧本中找到兑现点
  dialogue_warnings:
    - target_id: line_012
      message: 台词过度解释角色动机，建议增加潜台词空间
  schema_warnings: []
```

#### 设计原因

- 审查报告嵌入输出，让产品从"生成器"变成"审查工作台"
- 每条 warning 指向具体的 ID（scene_id / character_id / event_id / line_id），方便前端做点击定位
- `needs_human_review` 标记不确定的问题——AI 不替创作者做最终判断

---

## 四、ID 体系设计

### 4.1 命名规范

| 实体 | ID 格式 | 示例 |
|------|---------|------|
| 角色 | `char_NNN` | `char_001` |
| 事件 | `event_NNN` | `event_001` |
| 场景 | `scene_NNN` | `scene_001` |
| 关系边 | `rel_NNN` | `rel_001` |
| 伏笔 | `foreshadow_NNN` | `foreshadow_001` |
| 冲突 | `conflict_NNN` | `conflict_001` |
| 可视化约束 | `filmic_NNN` | `filmic_001` |
| 连续性锚点 | `anchor_NNN` | `anchor_001` |
| 对白行 | `line_NNN` | `line_001` |
| 内容块 | `block_NNN` | `block_001` |
| 章 | `chapter_NNN` | `chapter_001` |
| 段落 | `p_NNN` | `p_001` |

### 4.2 设计原因

- **零填充三位数字**（`char_001` 而非 `char_1`）：字符串排序时保持字典序与数值序一致
- **前缀语义明确**：`char_` / `event_` / `scene_` 让人和程序都能一眼识别实体类型
- **禁止描述性 ID**：不接受 `char_baiqian`、`evt_arrival`。原因是 LLM 在不同轮次中对同一角色的描述可能变化（"白浅""素素""司音"可能指向同一角色），只有无意义的数字 ID 才能真正稳定

---

## 五、证据等级体系

Schema 中出现的所有 LLM 推断内容，必须标注证据等级：

| 等级 | 含义 | 使用场景 |
|------|------|---------|
| `explicit` | 原文明确陈述 | "原文写'她恨他'" |
| `inferred` | 从原文合理推断 | "原文写她每次见他都皱眉，推断有负面情绪" |
| `candidate` | 有可能性但不确认 | "可能是伏笔，但不明确" |

### 设计原因

AI 改编最大的信任问题不是"AI 可能犯错"，而是**"我不知道 AI 在哪里可能犯错"**。

证据等级把 AI 的推断过程暴露给创作者：哪些是原文明确写的，哪些是 AI 推理的，哪些是 AI 猜测的。创作者可以快速跳过 `explicit` 的内容，重点审查 `inferred` 和 `candidate` 的内容。这比任何"增强 AI 准确性"的技术手段都更实用——因为它把判断权还给了人。

---

## 六、引用完整性约束

Schema 定义了以下跨实体引用规则，违反任何一条都会触发校验 error：

| 规则 | 校验方式 |
|------|---------|
| `scene.characters[]` 中的 ID 必须存在于 `story_bible.characters[].id` | 引用校验器 |
| `dialogue.character_id` 必须存在于 `story_bible.characters[].id` | 引用校验器 |
| `relationship_edges.from / .to` 必须指向存在的角色 ID | 引用校验器 |
| `knowledge_states.character_id` 必须指向存在的角色 ID | 引用校验器 |
| `causal_graph.edges.from / .to` 必须指向存在的 event ID | 引用校验器 |
| `foreshadowing.setup_event_id / .payoff_event_id` 必须指向存在的 event ID | 引用校验器 |
| `adaptation_plan` 中引用的所有 event ID 必须存在于 `events[]` | 引用校验器 |
| `scene_plan.source_events[]` 中的 ID 必须存在于 `events[]` | 引用校验器 |
| `scene.source_refs[].chapter_id` 必须存在于 `source.chapters[].id` | 引用校验器 |

### 设计原因

AI 有一个坏习惯：编造不存在的角色或事件来填补剧情空白。如果不做引用完整性校验，一个 scene 可能引用了 `char_baiqian`，但这个角色从未在故事圣经中定义——于是前端渲染时角色信息缺失、后续编辑时引用断裂。

**引用完整性校验是代码层对 AI"幻觉"的硬防线。**它不是让 AI 少犯错，而是让 AI 犯的错能被自动发现。

---

## 七、Schema 版本策略

- `schema_version: "1.0"` —— V0/V1 时期的基础 Schema
- `schema_version: "1.1"` —— 引入 `continuity_anchors`、`dramatic_assets`、`content_blocks`、`core_elements` 和 `script_structure` 三段式
- 未来版本只做**向后兼容的字段新增**，不做破坏性变更

---

## 八、总结：Schema 的设计哲学

> **这个 Schema 不是在定义"剧本应该写成什么样"，而是在定义"AI 的改编过程应该如何被人类审查"。**

它把改编从一个"AI 输入小说→输出剧本"的黑箱，变成了一个可以用以下维度审查的透明流程：

1. **来源可追溯**（source_refs）
2. **推断可质疑**（evidence_level）
3. **伏笔可追踪**（foreshadowing.status）
4. **因果可验证**（causal_graph + explanation）
5. **潜台词可审查**（dialogue.subtext + surface_intent）
6. **引用可校验**（跨实体 ID 引用完整性）
7. **决策可解释**（adaptation_plan.reason）
