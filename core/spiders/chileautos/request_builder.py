# core/spiders/chileautos/request_builder.py
import scrapy

class RequestBuilder:
    def __init__(self, config):
        self.config = config
        self.items_per_page = 12
        
    def generate_requests(self):
        """Generates initial requests with pagination"""
        yield scrapy.Request(
            url=f"{self.config.base_url}&offset=0",
            callback=self.config.spider.parse,
            meta={'page': 1}
        )

    def next_page_request(self, current_page):
        """Generates next page request"""
        next_offset = current_page * self.items_per_page
        return scrapy.Request(
            url=f"{self.config.base_url}&offset={next_offset}",
            callback=self.config.spider.parse,
            meta={'page': current_page + 1}
        )