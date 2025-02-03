# core/spiders/chileautos/spider.py
import scrapy
import logging
from scrapy.spiders import Spider
from ...items import CarItem
from .config import ChileautosConfig
from .request_builder import RequestBuilder
from .data_cleaners import DataCleaner
from .item_parser import ItemParser

class ChileautosSpider(Spider):
    name = 'chileautos'
    allowed_domains = ['chileautos.cl']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger(__name__)
        self.config = ChileautosConfig(self)
        self.request_builder = RequestBuilder(self.config)
        self.cleaner = DataCleaner(self._logger)
        self.item_parser = ItemParser(self.cleaner)
        self.logger.warning(f"Configured with page limit: {self.config.filters.get('max_pages', 'No limit')}")

        self._setup_counters()

    def _setup_counters(self):
        self.pages_processed = 0
        self.items_processed = 0
        self.processed_urls = set()

    def start_requests(self):
        yield from self.request_builder.generate_requests()

    def parse(self, response):
        current_page = response.meta['page']
        self.pages_processed += 1
        self.logger.info(f"Processing page {current_page}")

        # Extract information directly from listing page items
        items = response.css('.listing-items .listing-item')
        self.logger.info(f"Found {len(items)} items on the page")

        for item in items:
            car_item = CarItem()
            
            # Extract basic information
            car_item['url'] = response.urljoin(item.css('h3 a::attr(href)').get()) or None
            car_item['title'] = item.css('h3 a::text').get('').strip() or None
            car_item['price'] = item.css('.price::text').get('').strip() or None
            
            # Extract vehicle details
            details = {
                'Año': None,
                'Kilómetros': None
            }
            
            for detail in item.css('.key-details__item'):
                label = detail.css('.key-details__label::text').get('').strip().rstrip(':')
                value = detail.css('.key-details__value::text').get('').strip()
                if label in details:
                    details[label] = value or None
            
            car_item['year'] = details['Año']
            car_item['mileage'] = details['Kilómetros']

            self.items_processed += 1
            yield car_item

        # Paginación
        if self._should_continue_pagination(current_page):
            yield self.request_builder.next_page_request(current_page)

    def _should_continue_pagination(self, current_page):
        """Determines if pagination should continue"""
        max_pages = self.config.filters.get('max_pages')
        return not max_pages or current_page < max_pages

    @property
    def logger(self):
        return self._logger