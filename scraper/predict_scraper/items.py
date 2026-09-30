import scrapy


class JobItem(scrapy.Item):
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    contract_type = scrapy.Field()
    remote = scrapy.Field()
    salary_min = scrapy.Field()
    salary_max = scrapy.Field()
    salary_currency = scrapy.Field()
    sectors = scrapy.Field()
    summary = scrapy.Field()
    key_missions = scrapy.Field()
    experience_level_minimum = scrapy.Field()
    published_at_date = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()