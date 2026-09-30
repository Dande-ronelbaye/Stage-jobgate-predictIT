import sys
import os

# Ajoute le dossier parent au chemin d'import pour que Python trouve 'predict_scraper'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
# Maintenant il devrait trouver le package
from predict_scraper.spiders.tanitjobs import TanitjobsSpider

process = CrawlerProcess(get_project_settings())
process.crawl(TanitjobsSpider)
process.start()