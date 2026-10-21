import hashlib
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def test_original_csv_files_are_unchanged():
    expected = {
        "rank_by_year.csv": "e1551391b6ff06c31e84d4482191c71a30be5df7a3d670674cd32b265275b5af",
        "country_lists.csv": "68775a366fd4192514a6dd1a701d6faeb7f8bfcefd80e9d92d31ce4981e7b653",
    }
    for name, digest in expected.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest


def test_journal_preserves_the_actual_new_prompt():
    saved = (ROOT / "docs" / "prompt_iteration_01.md").read_text(encoding="utf-8")
    journal = (ROOT / "docs" / "journal_de_bord.md").read_text(encoding="utf-8")
    actual_prompt = saved.split("## Prompt\n\n", 1)[1].strip()
    reproduced_prompt = journal.split("```text\n", 1)[1].split("\n```", 1)[0].strip()
    assert actual_prompt == reproduced_prompt


def test_final_journal_has_three_pages_and_real_embedded_figures():
    with pymupdf.open(ROOT / "livrables" / "journal_de_bord_v1.pdf") as document:
        assert len(document) == 3
        assert "1. Prompt initial et contexte" in document[0].get_text()
        assert "2. Proposition brute" in document[1].get_text()
        assert "3. Audit et critique" in document[1].get_text()
        assert "4. Arbitrage et version" in document[2].get_text()
        for page in (document[1], document[2]):
            images = page.get_images()
            assert any(image[2] > 500 and image[3] > 200 for image in images)
        for page in document:
            for block in page.get_text("blocks"):
                x0, y0, x1, y1 = block[:4]
                assert 0 <= x0 <= x1 <= page.rect.width + 1
                assert 0 <= y0 <= y1 <= page.rect.height + 1
