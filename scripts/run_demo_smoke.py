from __future__ import annotations

import json
from pathlib import Path

# 最小冒烟验证
# 不启动任何服务器，直接用 Python 验证 demo checklist 的核心路径：
#   - 加载 demo_novel_3_chapters.json → 确认 ≥ 3 章
#   - 加载 demo_screenplay.json → 确认有场景存在
#   - 打印 fake artifact 路径 → 提示下一步去后端校验 demo_invalid_refs.yaml

# ---
#   与其他层的关系

#   scripts/           ← 离线工具，不依赖 FastAPI，纯 Python 脚本
#       ↓ 读
#   fixtures/          ← 静态数据
#   schemas/           ← JSON/YAML Schema
#       ↓ 被引用
#   validators/        ← 后端校验，启动后才生效

#   与 validator 的分工：scripts/validate_fixtures.py 检查"文件本身格式对不对"（这个 JSON 能不能 parse），validators/ 检查"数据含义对不对"（ID
#   引用是否悬空、schema 是否匹配）。一个在写数据后立刻跑，一个在后端运行时跑。

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    novel = json.loads((ROOT / "fixtures" / "demo_novel_3_chapters.json").read_text(encoding="utf-8"))
    screenplay = json.loads((ROOT / "fixtures" / "demo_screenplay.json").read_text(encoding="utf-8"))
    chapters = novel["chapters"]
    if len(chapters) < 3:
        raise RuntimeError("Expected at least three chapters")
    print(f"Loaded {len(chapters)} chapters")
    print("Fake story_bible artifact: fixtures/demo_story_bible.json")
    print("Fake screenplay_json artifact: fixtures/demo_screenplay.json")
    print(f"Screenplay scenes: {len(screenplay['scenes'])}")
    print("Validate broken refs with fixtures/demo_invalid_refs.yaml in the backend validator step")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

