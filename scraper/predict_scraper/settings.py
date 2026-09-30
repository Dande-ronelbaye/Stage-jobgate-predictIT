BOT_NAME = "predict_scraper"

SPIDER_MODULES = ["predict_scraper.spiders"]
NEWSPIDER_MODULE = "predict_scraper.spiders"

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 2

COOKIES_ENABLED = True

ITEM_PIPELINES = {
    "predict_scraper.pipelines.JsonWriterPipeline": 300,
}

FEED_EXPORT_ENCODING = "utf-8"