import sys
import asyncio

# === CORRECTIF DÉFINITIF WINDOWS INTERCEPTÉ AU CHARGEMENT ===
if sys.platform == 'win32':
    # Force Windows à utiliser Proactor pour gérer les sous-processus de Patchright
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import scrapy
from scrapy import signals
from patchright.async_api import async_playwright


class TanitjobsSpider(scrapy.Spider):
    name = "tanitjobs"
    start_urls = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TanitjobsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.opened)
        return spider

    def spider_opened(self):
        # Récupère proprement la boucle d'événement active gérée par le réacteur de Scrapy
        loop = asyncio.get_event_loop()
        loop.create_task(self.run_custom_crawl())

    async def run_custom_crawl(self):
        self.logger.info("🔗 Connexion au navigateur Chrome (Port 9222)...")

        p = await async_playwright().start()

        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = context.pages[0]

            target_url = "https://www.tanitjobs.com/jobs/?searchKeywords=informatique"
            self.logger.info(f"🌍 Pilotage de Chrome vers : {target_url}")

            await page.goto(target_url, wait_until="networkidle")
            await page.wait_for_timeout(5000)

            content = await page.content()
            sel = scrapy.Selector(text=content)

            offres = sel.css('article.job-listing, div.job-item, .listing-item, [id^="job-"]')
            self.logger.info(f"🔍 Nombre d'offres détectées : {len(offres)}")

            if "Just a moment..." in content:
                self.logger.warning("⚠️ Fenêtre toujours bloquée par Cloudflare. Coche le captcha manuellement.")

            for offre in offres:
                title = offre.css('h2.loop-item-title a::text, .job-title a::text, h3 a::text, .title a::text').get()
                company = offre.css('.employer-name::text, .company-name::text, .company::text, .employer::text').get()

                if title:
                    item = {
                        'title': title.strip(),
                        'company': company.strip() if company else "Non spécifié"
                    }
                    self.crawler.engine.scraper.slot.itemproc.process_item(item, self)

            await browser.disconnect()

        except Exception as e:
            self.logger.error(f"❌ Erreur durant l'exécution : {e}")
        finally:
            await p.stop()
            self.crawler.engine.close_spider(self, reason="finished_custom_crawl")