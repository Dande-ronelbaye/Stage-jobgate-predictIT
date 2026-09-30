import os
import sys
import tempfile
import subprocess
import asyncio
from scrapy.http import HtmlResponse


class PatchrightMiddleware:
    """
    Lance chaque requête dans un sous-processus Python isolé qui utilise
    Patchright (évite le conflit de boucle asyncio Twisted/Playwright sur Windows).
    """

    async def process_request(self, request, spider):
        loop = asyncio.get_event_loop()
        html = await loop.run_in_executor(None, self._fetch_sync, request.url)
        return HtmlResponse(
            url=request.url,
            body=html,
            encoding="utf-8",
            request=request,
            status=200,
        )

    def _fetch_sync(self, url):
        fd, output_path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            worker_script = os.path.join(os.path.dirname(__file__), "browser_worker.py")
            subprocess.run(
                [sys.executable, worker_script, url, output_path],
                check=True,
                timeout=60,
            )
            with open(output_path, "r", encoding="utf-8") as f:
                return f.read()
        finally:
            os.remove(output_path)