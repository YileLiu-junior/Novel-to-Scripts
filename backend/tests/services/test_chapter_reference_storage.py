from __future__ import annotations

import unittest

from app.services.generation_orchestrator import _strip_chapter_text


class ChapterReferenceStorageTest(unittest.TestCase):
    def test_strips_text_and_paragraphs_from_chapters_list(self) -> None:
        data = {
            "chapters": [
                {
                    "id": "chapter_001",
                    "title": "第一章",
                    "text": "长文本" * 100,
                    "paragraphs": [
                        {"id": "p_001", "text": "段落一" * 50},
                        {"id": "p_002", "text": "段落二" * 50},
                    ],
                }
            ],
            "events": [{"id": "event_001", "title": "事件"}],
        }
        stripped = _strip_chapter_text(data)

        ch = stripped["chapters"][0]
        self.assertEqual(ch["id"], "chapter_001")
        self.assertEqual(ch["title"], "第一章")
        self.assertNotIn("text", ch, "full text must be stripped")
        self.assertEqual(ch["paragraph_count"], 2, "paragraph_count metadata preserved")

    def test_strips_chapters_used_in_story_assets(self) -> None:
        data = {
            "story_bible": {"characters": []},
            "chapters_used": [
                {
                    "id": "chapter_001",
                    "text": "正文内容",
                    "paragraphs": [{"id": "p_001", "text": "段落"}],
                }
            ],
        }
        stripped = _strip_chapter_text(data)

        ch = stripped["chapters_used"][0]
        self.assertNotIn("text", ch)
        self.assertNotIn("paragraphs", ch)
        self.assertEqual(ch["paragraph_count"], 1)

    def test_preserves_non_chapter_fields_unchanged(self) -> None:
        data = {
            "story_bible": {"characters": [{"id": "char_001", "name": "白浅"}]},
            "events": [{"id": "event_001", "summary": "事件摘要"}],
            "causal_graph": {"edges": []},
        }
        stripped = _strip_chapter_text(data)

        self.assertEqual(stripped["story_bible"], data["story_bible"])
        self.assertEqual(stripped["events"], data["events"])
        self.assertEqual(stripped["causal_graph"], data["causal_graph"])

    def test_handles_missing_chapter_fields_gracefully(self) -> None:
        data = {"other": "value"}
        stripped = _strip_chapter_text(data)
        self.assertEqual(stripped, data)

    def test_strips_novel_analysis_chapters(self) -> None:
        data = {
            "chapters": [
                {
                    "id": "chapter_001",
                    "title": "第一章（1）",
                    "order": 1,
                    "text": "若水神君嫁去东海的大姑娘不满三年就给东海水君添了个男丁...",
                    "paragraphs": [
                        {"id": "p_001", "order": 1, "text": "第一章（1）"},
                        {"id": "p_002", "order": 2, "text": "若水神君..."},
                    ],
                    "source_anchor": None,
                    "source_file": None,
                }
            ],
            "events": [],
            "character_candidates": [],
        }
        stripped = _strip_chapter_text(data)

        ch = stripped["chapters"][0]
        self.assertNotIn("text", ch)
        self.assertNotIn("paragraphs", ch)
        self.assertEqual(ch["paragraph_count"], 2)
        self.assertEqual(ch["id"], "chapter_001")
        self.assertEqual(ch["title"], "第一章（1）")


if __name__ == "__main__":
    unittest.main()
