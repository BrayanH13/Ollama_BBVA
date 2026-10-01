"""Patrón Strategy: cómo se descarga una página. Se puede añadir un PlaywrightFetcher
(para sitios que renderizan con JavaScript) sin tocar el crawler."""
from abc import ABC, abstractmethod
from typing import Optional

import requests


class Fetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> Optional[tuple[int, str]]:
        """Devuelve (status, html) o None si no es HTML / falló."""


class RequestsFetcher(Fetcher):
    def __init__(self, user_agent: str, timeout: int = 20):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept-Language": "es-CO,es;q=0.9"})
        self.timeout = timeout

    def fetch(self, url):
        try:
            r = self.session.get(url, timeout=self.timeout)
        except requests.RequestException as e:
            print(f"  ! error en {url}: {e}")
            return None
        if "text/html" not in r.headers.get("Content-Type", ""):
            return None
        r.encoding = r.encoding or "utf-8"
        return r.status_code, r.text
