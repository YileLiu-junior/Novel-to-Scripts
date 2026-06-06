from __future__ import annotations

# 结构化 ID 生成规范 核心是一个通用工厂函数 + 5 个语义化包装：
#numbered_id(prefix, index)    →  "{prefix}_{index:03d}"
#                                    ↑ 通用：任意前缀 + 3位零填充序号

#集中定义，全项目引用 from app.core.ids import chapter_id 即可，避免各处手拼字符串造成不一致
def numbered_id(prefix: str, index: int) -> str:
    if index < 1:
        raise ValueError("index must be 1 or greater")
    return f"{prefix}_{index:03d}"


def chapter_id(index: int) -> str:
    return numbered_id("chapter", index)


def paragraph_id(index: int) -> str:
    return numbered_id("p", index)


def scene_id(index: int) -> str:
    return numbered_id("scene", index)


def line_id(index: int) -> str:
    return numbered_id("line", index)


def warning_id(index: int) -> str:
    return numbered_id("warning", index)

