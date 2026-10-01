import time
import urllib.robotparser
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup

from app.config import Settings
from app.scraping.fetchers import Fetcher
from app.storage.stores import RawStore

SKIP_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip", ".mp4", ".mp3",
            ".doc", ".docx", ".xls", ".xlsx", ".css", ".js", ".ico", ".webp")


def normalize(url: str) -> str:
    url, _ = urldefrag(url)
    p = urlparse(url)
    return p._replace(query="", path=p.path.rstrip("/") or "/").geturl()


class Crawler:
    """BFS acotado al dominio, respetando robots.txt y con pausa entre peticiones."""

    def __init__(self, fetcher: Fetcher, raw_store: RawStore, settings: Settings):
        self.fetcher, self.raw, self.cfg = fetcher, raw_store, settings
        self.host = urlparse(settings.base_url).netloc
        self.robots = urllib.robotparser.RobotFileParser()

    def _load_robots(self):
        try:
            self.robots.set_url(urljoin(self.cfg.base_url, "/robots.txt"))
            self.robots.read()
        except Exception:
            self.robots = None

    def _allowed(self, url: str) -> bool:
        p = urlparse(url)
        if p.netloc != self.host or p.path.lower().endswith(SKIP_EXT):
            return False
        return self.robots is None or self.robots.can_fetch(self.cfg.user_agent, url)

    @staticmethod
    def _links(base: str, html: str):
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            yield normalize(urljoin(base, href))

    def run(self) -> int:
        self._load_robots()
        start = normalize(self.cfg.base_url)
        queue, seen, saved = deque([start]), set(), 0
        while queue and saved < self.cfg.max_pages:
            url = queue.popleft()
            if url in seen or not self._allowed(url):
                continue
            seen.add(url)
            res = self.fetcher.fetch(url)
            if res:
                status, html = res
                if status == 200:
                    self.raw.save(url, html, status)
                    saved += 1
                    print(f"[{saved}/{self.cfg.max_pages}] {url}")
                    queue.extend(l for l in self._links(url, html) if l not in seen)
            time.sleep(self.cfg.request_delay)
        return saved
