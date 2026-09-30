import json
import scrapy
from predict_scraper.items import JobItem


class JungleSpider(scrapy.Spider):
    name = "jungle"

    algolia_url = "https://CSEKHVMS53-dsn.algolia.net/1/indexes/wttj_jobs_production_fr/query"
    algolia_headers = {
        "X-Algolia-API-Key": "4bd8f6215d0cc52b26430765769e65a0",
        "X-Algolia-Application-Id": "CSEKHVMS53",
        "Content-Type": "application/json",
        "Referer": "https://www.welcometothejungle.com/",
        "Origin": "https://www.welcometothejungle.com",
    }

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    hits_per_page = 20
    max_pages = 50  # limite de sécurité, ajustable

    async def start(self):
        yield self._make_request(page=0)

    def _make_request(self, page):
        payload = {
            "query": "informatique",
            "hitsPerPage": self.hits_per_page,
            "page": page,
        }
        return scrapy.Request(
            self.algolia_url,
            method="POST",
            headers=self.algolia_headers,
            body=json.dumps(payload),
            callback=self.parse,
            meta={"page": page},
        )

    def parse(self, response):
        data = json.loads(response.text)
        hits = data.get("hits", [])
        current_page = response.meta["page"]
        nb_pages = data.get("nbPages", 1)

        self.logger.info(
            f"Page {current_page + 1}/{nb_pages} — {len(hits)} offres trouvées"
        )

        for hit in hits:
            yield self._build_item(hit)

        next_page = current_page + 1
        if next_page < nb_pages and next_page < self.max_pages:
            yield self._make_request(page=next_page)

    def _build_item(self, hit):
        item = JobItem()
        item["title"] = hit.get("name") or hit.get("title")

        org = hit.get("organization") or {}
        item["company"] = org.get("name")

        offices = hit.get("offices") or []
        if offices:
            city = offices[0].get("local_city") or offices[0].get("city")
            country = offices[0].get("country")
            item["location"] = f"{city}, {country}" if city else country
        else:
            item["location"] = None

        item["contract_type"] = hit.get("contract_type")
        item["remote"] = hit.get("remote")
        item["salary_min"] = hit.get("salary_minimum")
        item["salary_max"] = hit.get("salary_maximum")
        item["salary_currency"] = hit.get("salary_currency")
        item["sectors"] = [s.get("name") for s in hit.get("sectors", [])]
        item["summary"] = hit.get("summary")
        item["key_missions"] = hit.get("key_missions")
        item["experience_level_minimum"] = hit.get("experience_level_minimum")
        item["published_at_date"] = hit.get("published_at_date")
        item["source"] = "welcometothejungle"

        slug = hit.get("slug")
        org_slug = org.get("slug")
        if slug and org_slug:
            item["url"] = f"https://www.welcometothejungle.com/fr/companies/{org_slug}/jobs/{slug}"
        else:
            item["url"] = None

        return item