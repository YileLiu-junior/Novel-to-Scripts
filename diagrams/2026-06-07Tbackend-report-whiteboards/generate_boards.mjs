import { createRequire } from "module";
import { mkdir, writeFile } from "fs/promises";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const sharp = require("sharp");

const outDir = dirname(fileURLToPath(import.meta.url));

const C = {
  black: "#0A0A0A",
  white: "#FFFFFF",
  pink: "#F2D4CF",
  green: "#E5EDD6",
  gray: "#F5F5F5",
  darkgray: "#333333",
};

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function svgWrap(width, height, body) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="4" orient="auto" markerUnits="strokeWidth">
      <path d="M0 0 L10 4 L0 8 z"/>
    </marker>
  </defs>
  <rect x="0" y="0" width="${width}" height="${height}" fill="${C.white}"/>
  ${body}
</svg>`;
}

function rect(x, y, w, h, fill = C.white, stroke = C.black, strokeWidth = 3) {
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="0" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}"/>`;
}

function shadowRect(x, y, w, h, fill = C.white, shadow = 6) {
  return `${rect(x + shadow, y + shadow, w, h, C.black, C.black, 3)}
${rect(x, y, w, h, fill, C.black, 3)}`;
}

function line(x1, y1, x2, y2, arrow = true, width = 3) {
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${C.black}" stroke-width="${width}" ${arrow ? 'marker-end="url(#arrow)"' : ""}/>`;
}

function polyline(points, arrow = true, width = 3) {
  return `<polyline points="${points}" fill="none" stroke="${C.black}" stroke-width="${width}" ${arrow ? 'marker-end="url(#arrow)"' : ""}/>`;
}

function textBlock(lines, x, y, opts = {}) {
  const {
    size = 24,
    weight = 500,
    fill = C.black,
    lineHeight = Math.round(size * 1.35),
    anchor = "start",
  } = opts;
  const tspans = lines.map((lineText, index) => {
    const dy = index === 0 ? 0 : lineHeight;
    return `<tspan x="${x}" dy="${dy}">${esc(lineText)}</tspan>`;
  }).join("");
  return `<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" letter-spacing="0">${tspans}</text>`;
}

function label(text, x, y, size = 18, weight = 700, fill = C.darkgray) {
  return `<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" fill="${fill}" letter-spacing="0">${esc(text)}</text>`;
}

function numberedCard({ n, title, lines, x, y, w, h, fill }) {
  return `${shadowRect(x, y, w, h, fill, 5)}
${textBlock([n], x + 22, y + 80, { size: 78, weight: 900 })}
${textBlock([title], x + 135, y + 42, { size: 28, weight: 850 })}
${textBlock(lines, x + 135, y + 84, { size: 22, weight: 500, fill: C.darkgray, lineHeight: 32 })}`;
}

function workflowStep({ n, title, lines, x, y, w, h, fill }) {
  return `${rect(x, y, w, h, fill)}
${textBlock([n], x + 18, y + 70, { size: 64, weight: 900 })}
${textBlock([title], x + 104, y + 40, { size: 24, weight: 850 })}
${textBlock(lines, x + 104, y + 78, { size: 19, weight: 500, fill: C.darkgray, lineHeight: 28 })}`;
}

function miniCell({ title, lines, x, y, w, h, fill = C.white }) {
  return `${rect(x, y, w, h, fill)}
${textBlock([title], x + 22, y + 40, { size: 24, weight: 850 })}
${textBlock(lines, x + 22, y + 78, { size: 19, weight: 500, fill: C.darkgray, lineHeight: 27 })}`;
}

function compactCell({ title, lines, x, y, w, h, fill = C.white }) {
  return `${rect(x, y, w, h, fill)}
${textBlock([title], x + 18, y + 34, { size: 21, weight: 900 })}
${textBlock(lines, x + 18, y + 65, { size: 17, weight: 500, fill: C.darkgray, lineHeight: 24 })}`;
}

function boardReport() {
  const width = 2200;
  const height = 1650;
  const parts = [];

  parts.push(shadowRect(36, 32, 2128, 170, C.white, 6));
  parts.push(textBlock(["结构化小说改编后端"], 68, 92, { size: 54, weight: 900 }));
  parts.push(textBlock(["汇报方案 · 架构设计 · 产品卖点 · Skill Workflow"], 70, 145, { size: 30, weight: 700, fill: C.darkgray }));
  parts.push(textBlock(["不是一次 prompt 写剧本，而是把 AI 输出变成可检查、可追踪、可导出的 adaptation assets。"], 780, 94, { size: 28, weight: 750 }));
  parts.push(textBlock(["代码负责结构、引用、状态、导出可靠性；AI 负责内容生成与改编判断。"], 780, 138, { size: 24, weight: 500, fill: C.darkgray }));
  parts.push(textBlock(["V0+V1"], 1988, 128, { size: 42, weight: 900 }));

  const cardY = 250;
  const cardW = 514;
  const gap = 22;
  [
    {
      n: "01",
      title: "产品主张",
      fill: C.green,
      lines: ["把小说章节转成结构化剧本资产", "每一步有 artifact 和可审计证据", "demo 讲的是 reliability，不是玄学文采"],
    },
    {
      n: "02",
      title: "架构设计",
      fill: C.white,
      lines: ["schema-first：schema.json", "Pydantic domain 聚合根承载资产", "API / service / skill / repository 分层"],
    },
    {
      n: "03",
      title: "实现卖点",
      fill: C.pink,
      lines: ["chapter_### / p_### 稳定 ID", "job 可查：status / step / error", "YAML 与 Markdown 可导出、可下载"],
    },
    {
      n: "04",
      title: "工程护栏",
      fill: C.gray,
      lines: ["Normalizer 清洗结构，不改业务内容", "Schema + Reference 定位问题", "Exporter 只转换格式，不修复内容"],
    },
  ].forEach((item, index) => {
    parts.push(numberedCard({
      ...item,
      x: 36 + index * (cardW + gap),
      y: cardY,
      w: cardW,
      h: 230,
    }));
  });

  parts.push(shadowRect(36, 525, 2128, 260, C.white, 6));
  parts.push(label("END-TO-END WORKFLOW", 66, 568, 20, 900));
  const stepY = 595;
  const stepW = 324;
  const stepH = 150;
  const startX = 66;
  const steps = [
    { n: "1", title: "Project", fill: C.green, lines: ["创建 project.json", "保存 title / logline", "本地 project index"] },
    { n: "2", title: "Chapters", fill: C.white, lines: ["至少三章", "生成 chapter_###", "段落 p_###"] },
    { n: "3", title: "Skills", fill: C.pink, lines: ["Reader / Ontology", "Planner / Writer", "统一 structured wrapper"] },
    { n: "4", title: "Screenplay JSON", fill: C.white, lines: ["注入 config / source", "归一化 scenes", "聚合 story assets"] },
    { n: "5", title: "Validation", fill: C.gray, lines: ["schema findings", "reference findings", "audit_report"] },
    { n: "6", title: "Export", fill: C.green, lines: ["screenplay_yaml", "screenplay.md / txt", "schema download"] },
  ];
  steps.forEach((item, index) => {
    const x = startX + index * (stepW + 18);
    parts.push(workflowStep({ ...item, x, y: stepY, w: stepW, h: stepH }));
    if (index < steps.length - 1) {
      parts.push(line(x + stepW + 4, stepY + stepH / 2, x + stepW + 18, stepY + stepH / 2, true, 3));
    }
  });

  parts.push(shadowRect(36, 830, 1018, 470, C.white, 6));
  parts.push(label("SKILL 辅助作用", 66, 875, 20, 900));
  const skillCells = [
    {
      title: "NovelReaderSkill",
      fill: C.green,
      lines: ["读章节与段落 ID", "抽取 characters / events / foreshadowing", "输出 source refs，给后续追踪"],
    },
    {
      title: "StoryOntologySkill",
      fill: C.white,
      lines: ["把 novel analysis 变成 story bible", "角色关系、knowledge states、voice profiles", "形成可复用的故事资产层"],
    },
    {
      title: "AdaptationPlannerSkill",
      fill: C.pink,
      lines: ["消费 story bible + adaptation config", "决定 retained / merged / deferred events", "产出 protected elements 与 scene_plan"],
    },
    {
      title: "ScreenplayWriterSkill",
      fill: C.gray,
      lines: ["消费 scene_plan 与 canonical assets", "输出 schema-shaped screenplay JSON", "历史名含 YAML，但真实 YAML 属 exporter"],
    },
  ];
  skillCells.forEach((cell, index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    parts.push(miniCell({
      ...cell,
      x: 66 + col * 490,
      y: 905 + row * 180,
      w: 470,
      h: 160,
    }));
  });
  parts.push(rect(66, 1246, 960, 48, C.black, C.black, 0));
  parts.push(textBlock(["Skill 不写数据库、不决定 job、不导出 YAML；orchestrator 负责串联、保存、校验。"], 86, 1277, { size: 22, weight: 800, fill: C.white }));

  parts.push(shadowRect(1110, 830, 1054, 470, C.white, 6));
  parts.push(label("设计角度分析", 1140, 875, 20, 900));
  const angleCells = [
    {
      title: "LLM 输出不可靠",
      fill: C.gray,
      lines: ["用 normalizer 删除非法 null、补最小合法字段", "再交给 schema validator 报真实结构问题"],
    },
    {
      title: "内容必须可追溯",
      fill: C.green,
      lines: ["source.chapters、events、scenes、dialogue 都有 ID", "reference validator 指向具体 entity IDs"],
    },
    {
      title: "前后端要并行",
      fill: C.white,
      lines: ["HTTP API + DTO 是唯一入口", "frontend 只按 schema 和 api_client 解析"],
    },
    {
      title: "Demo 要稳定",
      fill: C.pink,
      lines: ["job_id 立即返回，后台跑 pipeline", "artifact index 允许复查每一步产物"],
    },
  ];
  angleCells.forEach((cell, index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    parts.push(miniCell({
      ...cell,
      x: 1140 + col * 510,
      y: 905 + row * 180,
      w: 490,
      h: 160,
    }));
  });

  parts.push(shadowRect(36, 1350, 2128, 230, C.white, 6));
  parts.push(label("汇报讲法：建议 6 段式", 66, 1395, 20, 900));
  const reportItems = [
    ["1 破题", ["AI 生成不是重点", "重点是可审计 workflow"]],
    ["2 架构", ["schema-first", "domain 聚合 + service 编排"]],
    ["3 流程", ["chapters → skills", "artifacts → validation"]],
    ["4 Demo", ["三章输入 + job 轮询", "artifact 列表 + 导出"]],
    ["5 卖点", ["可追踪、可校验", "可复跑、前后端解耦"]],
    ["6 边界", ["不做外部队列/多用户", "不做视频图像生成"]],
  ];
  reportItems.forEach(([head, bodyLines], index) => {
    const x = 66 + index * 345;
    parts.push(rect(x, 1425, 325, 115, index % 2 === 0 ? C.gray : C.white));
    parts.push(textBlock([head], x + 20, 1462, { size: 24, weight: 900 }));
    parts.push(textBlock(bodyLines, x + 20, 1498, { size: 18, weight: 500, fill: C.darkgray, lineHeight: 26 }));
  });

  return svgWrap(width, height, parts.join("\n"));
}

function layerBlock({ title, subtitle, x, y, w, h, fill, lines }) {
  return `${shadowRect(x, y, w, h, fill, 5)}
${textBlock([title], x + 24, y + 42, { size: 24, weight: 900 })}
${textBlock([subtitle], x + 24, y + 74, { size: 17, weight: 700, fill: C.darkgray })}
${textBlock(lines, x + 24, y + 104, { size: 16, weight: 500, fill: C.darkgray, lineHeight: 22 })}`;
}

function boardArchitecture() {
  const width = 2200;
  const height = 1800;
  const parts = [];

  parts.push(shadowRect(36, 32, 2128, 165, C.white, 6));
  parts.push(textBlock(["当前后端架构层设计"], 68, 92, { size: 54, weight: 900 }));
  parts.push(textBlock(["Local Project Store · 不是 SQLite Database"], 70, 145, { size: 30, weight: 800, fill: C.darkgray }));
  parts.push(textBlock(["项目本地存储是当前 persistence 真相源：JSON / YAML / Text 文件 + atomic replace。"], 900, 95, { size: 28, weight: 800 }));
  parts.push(textBlock(["旧 db/session.py 与 db/tables.py 属占位/遗留；当前 repository 实际读写 data/projects/{project_id}/..."], 900, 138, { size: 23, weight: 500, fill: C.darkgray }));

  parts.push(shadowRect(36, 240, 510, 1185, C.white, 6));
  parts.push(label("LAYER BOUNDARIES", 66, 285, 20, 900));
  const layers = [
    { title: "API routes", subtitle: "HTTP + DTO only", fill: C.gray, lines: ["校验 project / chapters", "创建 job 并 enqueue", "不拼 prompt、不写文件"] },
    {
      title: "Services",
      subtitle: "Use-case orchestration",
      fill: C.white,
      lines: ["Project / Chapter / Artifact / Job", "GenerationOrchestrator.run_v1", "保存产物、更新 step"],
    },
    {
      title: "AI Skills",
      subtitle: "structured generation wrappers",
      fill: C.pink,
      lines: ["SkillWrapper → provider", "prompt_name + input_data", "不持久化、不决定流程"],
    },
    {
      title: "Validators",
      subtitle: "deterministic quality gates",
      fill: C.green,
      lines: ["Normalizer", "Schema + Reference", "Audit report mapping"],
    },
    {
      title: "Exporters",
      subtitle: "pure format conversion",
      fill: C.white,
      lines: ["YAML exporter", "Markdown/Text renderer", "schema download"],
    },
    {
      title: "Repositories",
      subtitle: "local file persistence",
      fill: C.gray,
      lines: ["Project / Chapter repo", "Artifact / Job repo", "atomic JSON/Text writes"],
    },
  ];
  layers.forEach((item, index) => {
    const y = 320 + index * 175;
    parts.push(layerBlock({ ...item, x: 66, y, w: 450, h: 155 }));
    if (index < layers.length - 1) {
      parts.push(line(291, y + 157, 291, y + 172, true, 3));
    }
  });

  parts.push(shadowRect(590, 240, 1010, 640, C.white, 6));
  parts.push(label("CURRENT EXECUTION FLOW", 620, 285, 20, 900));
  const flow = [
    { title: "POST generate/screenplay", fill: C.gray, lines: ["GenerateRequest + AdaptationConfig", "返回 202 Accepted + job_id"] },
    { title: "_prepare_generation()", fill: C.white, lines: ["ProjectService.get_project", "ChapterService.list_for_project", "reject fewer than 3 chapters"] },
    { title: "enqueue_generation()", fill: C.green, lines: ["FastAPI BackgroundTasks", "routes 不关心后台细节"] },
    { title: "GenerationOrchestrator.run_v1()", fill: C.pink, lines: ["novel_reader → story_ontology", "adaptation_planner → screenplay_writer"] },
    { title: "Normalize + Validate + Export", fill: C.white, lines: ["inject source/config/story assets", "schema + reference findings", "screenplay_yaml + audit_report"] },
  ];
  flow.forEach((item, index) => {
    const x = 625 + (index % 2) * 485;
    const y = 320 + Math.floor(index / 2) * 175;
    parts.push(miniCell({ ...item, x, y, w: 455, h: 145 }));
  });
  parts.push(polyline("1080,392 1110,392 1110,392", true, 3));
  parts.push(polyline("850,465 850,495 850,495", true, 3));
  parts.push(polyline("1080,568 1110,568 1110,568", true, 3));
  parts.push(polyline("850,640 850,670 850,670", true, 3));

  parts.push(shadowRect(1645, 240, 519, 640, C.white, 6));
  parts.push(label("CODE COMMENT SIGNALS", 1675, 285, 20, 900));
  const signals = [
    ["ProjectService", "创建稳定 local project records；routes 不碰 repository files。"],
    ["file_store.py", "集中 JSON/Text 序列化与 atomic replacement。"],
    ["Screenplay", "顶层聚合根，把 bible、events、plan、scenes、audit 串成资产。"],
    ["CoreElements", "索引层，不替代 story_bible 或正文，只让关键元素可检查。"],
    ["YamlService", "导出前强制 validation；有 error 就拒绝导出。"],
    ["workers/jobs.py", "fire-and-forget：route 立刻给 job_id，前端轮询。"],
  ];
  signals.forEach(([head, body], index) => {
    const y = 320 + index * 86;
    parts.push(rect(1675, y, 459, 70, index % 2 === 0 ? C.gray : C.white));
    parts.push(textBlock([head], 1694, y + 27, { size: 19, weight: 900 }));
    parts.push(textBlock([body], 1694, y + 52, { size: 15, weight: 500, fill: C.darkgray, lineHeight: 20 }));
  });

  parts.push(shadowRect(590, 930, 1574, 485, C.white, 6));
  parts.push(label("LOCAL PROJECT STORE", 620, 975, 20, 900));
  parts.push(rect(620, 1010, 675, 345, C.green));
  parts.push(textBlock(["data/"], 650, 1062, { size: 34, weight: 900 }));
  parts.push(textBlock([
    "projects.json",
    "projects/{project_id}/project.json",
    "projects/{project_id}/chapters/index.json",
    "projects/{project_id}/jobs/index.json",
    "projects/{project_id}/artifacts/index.json",
    "projects/{project_id}/artifacts/story_bible_v001.json",
    "projects/{project_id}/artifacts/screenplay_yaml_v001.yaml",
  ], 650, 1110, { size: 22, weight: 600, fill: C.darkgray, lineHeight: 35 }));
  parts.push(rect(1320, 1010, 814, 160, C.pink));
  parts.push(textBlock(["为什么不是 SQLite"], 1350, 1054, { size: 28, weight: 900 }));
  parts.push(textBlock([
    "V0+V1 目标是 demo reliability 和 inspectable artifacts。",
    "本地文件更利于人工检查、git diff、fixture contract 和快速调试。",
    "不引入连接池、迁移、外部队列或多用户一致性复杂度。",
  ], 1350, 1095, { size: 21, weight: 500, fill: C.darkgray, lineHeight: 31 }));
  parts.push(rect(1320, 1195, 814, 160, C.gray));
  parts.push(textBlock(["持久化不变量"], 1350, 1239, { size: 28, weight: 900 }));
  parts.push(textBlock([
    "Artifact version 按 project_id + type 递增。",
    "Job 保存 status / current_step / error / artifact_ids。",
    "写入使用临时文件 + os.replace，避免半个 JSON。",
  ], 1350, 1280, { size: 21, weight: 500, fill: C.darkgray, lineHeight: 31 }));

  parts.push(shadowRect(36, 1480, 2128, 235, C.white, 6));
  parts.push(label("ARCHITECTURAL VALUE", 66, 1525, 20, 900));
  const values = [
    ["Contract first", ["schema 是唯一真相源", "DTO 与 fixtures 对齐"]],
    ["Traceable", ["每个 AI step 保存 artifact", "失败也可复查已生成产物"]],
    ["Replaceable AI", ["服务只依赖 AiProvider", "当前运行时是 DeepSeek"]],
    ["Deterministic gates", ["校验层不调用模型/网络", "findings 带 path / target_id"]],
    ["Export reliability", ["内部 JSON 是真相", "YAML/Markdown 是可读导出"]],
  ];
  values.forEach(([head, bodyLines], index) => {
    const x = 66 + index * 415;
    parts.push(rect(x, 1560, 390, 115, index % 2 === 0 ? C.white : C.gray));
    parts.push(textBlock([head], x + 20, 1598, { size: 24, weight: 900 }));
    parts.push(textBlock(bodyLines, x + 20, 1635, { size: 17, weight: 500, fill: C.darkgray, lineHeight: 24 }));
  });

  return svgWrap(width, height, parts.join("\n"));
}

async function writeBoard(name, svg) {
  const svgPath = join(outDir, `${name}.svg`);
  const pngPath = join(outDir, `${name}.png`);
  await writeFile(svgPath, svg, "utf8");
  await sharp(Buffer.from(svg)).png().toFile(pngPath);
  return { svgPath, pngPath };
}

await mkdir(outDir, { recursive: true });
const report = await writeBoard("backend-report-skill-workflow", boardReport());
const architecture = await writeBoard("backend-layer-local-store", boardArchitecture());
console.log(JSON.stringify({ report, architecture }, null, 2));
