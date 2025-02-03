# core/spiders/chileautos/item_parser.py
from scrapy import Selector
from ...items import CarItem
import logging

class ItemParser:
    def __init__(self, cleaner):
        self.cleaner = cleaner
        self.logger = logging.getLogger(__name__)
        
    def parse_car(self, response):
        """Parses vehicle detail page"""
        item = CarItem()
        
        # Extract basic data
        item['url'] = response.url
        item['title'] = response.css('h1::text').get()
        
        # Validate required data
        if not self._validate_item(item):
            return None
            
        # Extract rest of data
        self._extract_price(item, response)
        self._extract_mileage(item, response)
        self._extract_year(item, response)
        
        return item
        
    def _validate_item(self, item):
        """Validates item has all required fields"""
        if not item.get('title'):
            self.logger.warning(f"Discarded item - missing title: {item['url']}")
            return False
            
        if not item.get('url'):
            self.logger.warning("Discarded item - missing URL")
            return False
            
        return True

    def _extract_price(self, item, response):
        price_selectors = [
            '.price::text',
            '.price-value::text',
            '.item-price .price::text'
        ]
        
        for selector in price_selectors:
            price_text = response.css(selector).get()
            if price_text:
                item['price'] = self.cleaner.clean_price(price_text)
                break
        else:
            item['price'] = 0
            
    def _extract_mileage(self, item, response):
        """Extracts vehicle mileage"""
        mileage_selectors = [
            '.item-mileage::text',
            '.mileage::text',
            'span[data-value]::attr(data-value)',  # New selector for direct value
            '.odometer::text',  # Another possible selector
            'div[data-name="kilometraje"] input::attr(value)'  # Selector for mileage input
        ]
        
        for selector in mileage_selectors:
            mileage_text = response.css(selector).get()
            if mileage_text:
                self.logger.debug(f"Found mileage with selector {selector}: {mileage_text}")
                item['mileage'] = self.cleaner.clean_mileage(mileage_text)
                if item['mileage'] > 0:  # Only return if we find valid value
                    return
        
        # If we reach this point, we didn't find a valid value
        self.logger.warning(f"Could not find mileage for {response.url}")
        item['mileage'] = 0
            
    def _extract_year(self, item, response):
        item['year'] = self.cleaner.extract_year(item.get('title', ''))