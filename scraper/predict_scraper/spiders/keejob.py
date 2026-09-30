import scrapy
from predict_scraper.items import JobItem


class KeejobSpider(scrapy.Spider):
    name = "keejob"
    allowed_domains = ["keejob.com"]

    categories = {
        "informatique_tech": "https://www.keejob.com/offres-emploi/metiers/recrutement-informatique-multimedia/",
        "marketing_digital": "https://www.keejob.com/offres-emploi/metiers/recrutement-marketing-publicite-communication/",
        "data_bi_consulting": "https://www.keejob.com/offres-emploi/metiers/recrutement-consultant-etude-conseil/",
    }

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    max_pages = 50

    async def start(self):
        for category_name, url in self.categories.items():
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={"page": 1, "category": category_name},
            )

    def parse(self, response):
        articles = response.css("article")
        category = response.meta["category"]
        self.logger.info(f"[{category}] {len(articles)} offres trouvées sur {response.url}")

        for article in articles:
            item = JobItem()

            title = article.css("h2 a::text").get()
            item["title"] = title.strip() if title else None

            href = article.css("h2 a::attr(href)").get()
            item["url"] = response.urljoin(href) if href else None

            company = article.css("p a::text").get()
            item["company"] = company.strip() if company else None

            sectors = article.css("span:has(i.fa-industry)::text").getall()
            item["sectors"] = [s.strip() for s in sectors if s.strip()]

            contract_span = article.css("span:has(i.fa-briefcase)")
            if contract_span:
                contract_text = "".join(contract_span.css("::text").getall())
                item["contract_type"] = contract_text.strip() or None
            else:
                item["contract_type"] = None

            location_parts = article.css("i.fa-map-marker-alt").xpath(
                "following-sibling::span//text()"
            ).getall()
            location_clean = ", ".join(
                " ".join(p.split()) for p in location_parts if p.strip()
            )
            item["location"] = location_clean or None

            date_parts = article.css("i.fa-clock").xpath(
                "following-sibling::text() | following-sibling::span//text()"
            ).getall()
            date_clean = " ".join(p.strip() for p in date_parts if p.strip())
            item["published_at_date"] = date_clean or None

            summary = article.css("div.mb-3 p::text").get()
            item["summary"] = summary.strip() if summary else None

            item["source"] = f"keejob_{category}"

            yield item

        current_page = response.meta.get("page", 1)
        if articles and current_page < self.max_pages:
            next_page = current_page + 1
            base_url = self.categories[category]
            next_url = f"{base_url}?page={next_page}"
            yield scrapy.Request(
                next_url,
                callback=self.parse,
                meta={"page": next_page, "category": category},
            )