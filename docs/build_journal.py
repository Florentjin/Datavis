"""Génère livrables/journal_de_bord.pdf à partir de docs/journal_de_bord.md.

Usage : .venv\\Scripts\\python.exe docs\\build_journal.py
Dépendances : paquet `markdown` (requirements-dev.txt) et Microsoft Edge (ou Chrome).
"""

import shutil
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "journal_de_bord.md"
HTML = ROOT / "docs" / "_journal_de_bord.html"
PDF = ROOT / "livrables" / "journal_de_bord.pdf"
BROWSERS = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
)


def find_browser() -> str:
    for candidate in (*BROWSERS, shutil.which("msedge"), shutil.which("chrome")):
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit("Edge ou Chrome introuvable.")


def main() -> None:
    body = markdown.markdown(
        SOURCE.read_text(encoding="utf-8"), extensions=["fenced_code", "tables", "md_in_html"]
    )
    HTML.write_text(f'<!doctype html><html lang="fr"><meta charset="utf-8">{body}</html>', encoding="utf-8")
    before = PDF.stat().st_mtime if PDF.exists() else None
    try:
        subprocess.run(
            [find_browser(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={PDF}", HTML.as_uri()],
            check=True, capture_output=True, timeout=120,
        )
    finally:
        HTML.unlink(missing_ok=True)
    if not PDF.exists() or PDF.stat().st_mtime == before:
        sys.exit(f"PDF non mis à jour : fermez {PDF.name} s'il est ouvert, puis relancez.")
    print(f"PDF généré : {PDF}")


if __name__ == "__main__":
    main()
