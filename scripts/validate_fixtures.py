from __future__ import annotations

import json
from pathlib import Path

# 这个脚本的目的是验证 fixtures 目录下的 JSON/YAML 文件格式正确，避免测试时因为格式问题而报错。纯离线，不依赖FastAPI或项目其他部分。
# 运行方式：在项目根目录下执行 python scripts/validate_fixtures.py

# 用途：任何人改完 fixture 数据后，跑一下这个脚本就能立刻发现格式错误，不用等到后端启动再报错。

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    fixture_paths = [
        ROOT / "fixtures" / "source_manifest.json",
        ROOT / "fixtures" / "demo_novel_3_chapters.json",
        ROOT / "fixtures" / "demo_story_bible.json",
        ROOT / "fixtures" / "demo_story_bible_invalid_refs.json",
        ROOT / "fixtures" / "demo_screenplay.json",
        ROOT / "fixtures" / "demo_audit_report.json",
        ROOT / "schemas" / "screenplay.schema.json",
    ]
    for path in fixture_paths:
        load_json(path)
        print(f"OK json {path.relative_to(ROOT)}")

    try:
        import yaml
    except ImportError:
        print("SKIP yaml validation: PyYAML is not installed")
        return 0

    for path in [
        ROOT / "fixtures" / "demo_screenplay.yaml",
        ROOT / "fixtures" / "demo_invalid_refs.yaml",
        ROOT / "schemas" / "screenplay.schema.yaml",
    ]:
        yaml.safe_load(path.read_text(encoding="utf-8"))
        print(f"OK yaml {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
