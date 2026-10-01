import re
from collections import Counter

from bs4 import BeautifulSoup

from app.models import Document

NOISE_TAGS = ["script", "style", "noscript", "svg", "iframe", "form", "nav",
              "header", "footer", "aside", "button", "select", "template"]
MIN_CHARS = 200


class HtmlCleaner:
    def clean(self, doc_id: str, url: str, html: str) -> Document | None:
        soup = BeautifulSoup(html, "lxml")
        title = (soup.title.get_text(" ", strip=True) if soup.title else "") or url
        for t in soup(NOISE_TAGS):
            t.decompose()
        root = soup.find("main") or soup.find("article") or soup.body or soup
        lines, prev = [], None
        for raw in root.get_text("\n").splitlines():
            line = re.sub(r"\s+", " ", raw).strip()
            if len(line) < 3 or line == prev:
                continue
            lines.append(line)
            prev = line
        text = "\n".join(lines)
        return Document(doc_id, url, title, text) if len(text) >= MIN_CHARS else None

    @staticmethod
    def drop_boilerplate(docs: list[Document], ratio: float = 0.4) -> list[Document]:
        """Elimina líneas que se repiten en muchas páginas (menús, avisos, cookies...)."""
        if len(docs) < 5:
            return docs
        freq = Counter(l for d in docs for l in set(d.text.splitlines()))
        limit = ratio * len(docs)
        out = []
        for d in docs:
            kept = "\n".join(l for l in d.text.splitlines() if freq[l] <= limit)
            if len(kept) >= MIN_CHARS:
                d.text = kept
                out.append(d)
        return out
