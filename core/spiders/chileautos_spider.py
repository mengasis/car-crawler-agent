import re
import logging
import time
import json
import os
from urllib.parse import urljoin
import scrapy
from scrapy.spiders import Spider
from ..items import CarItem

class ChileautosSpider(Spider):
    name = 'chileautos'
    allowed_domains = ['chileautos.cl']
    items_per_page = 12
    items_processed = 0
    items_dropped = 0
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'COOKIES_ENABLED': True,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def __init__(self, *args, **kwargs):
        super(ChileautosSpider, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(__name__)
        self.pages_processed = 0
        self.max_pages = int(kwargs.get('max_pages', 0))  # 0 means no limit
        self.processed_urls = set()  # URLs already tracked
        
        # Load filter configuration
        self.filters = self.load_filters()
        
        # Build base URL with filters
        self.base_url = self.build_base_url()
        
        # Apply max_pages from filters if not in arguments
        if not self.max_pages and self.filters.get('max_pages'):
            self.max_pages = self.filters['max_pages']

    def log(self, message, level=logging.INFO):
        self._logger.log(level, message)

    def load_filters(self):
        """Load filters from JSON file"""
        filters_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'filters.json')
        try:
            with open(filters_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('filters', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.log(f"Error loading filters: {str(e)}", level=logging.ERROR)
            return {}

    def build_base_url(self):
        """Construct base URL with brand filters"""
        base = 'https://www.chileautos.cl/vehiculos/'
        
        if not self.filters.get('brands'):
            return base
            
        # Build brand query
        brands = self.filters['brands']
        if len(brands) == 1:
            brand_query = f"Marca.{brands[0]}"
        else:
            brand_query = "(Or." + "._.".join(f"Marca.{brand}" for brand in brands) + ".)"
        
        query = f"?q=(And.Servicio.ChileAutos._.{brand_query})"
        self.log(f"Constructed URL: {base + query}", level=logging.INFO)
        return base + query

    def start_requests(self):
        """Start requests with pagination using URL offsets."""
        self.log("Starting car spider with URL offset pagination")
        if self.max_pages:
            self.log(f"Will process up to {self.max_pages} pages")
        
        # Start with first page (offset=0)
        yield scrapy.Request(
            url=f"{self.base_url}&offset=0",
            callback=self.parse,
            meta={'page': 1}
        )

    def parse(self, response):
        """Parse the listing page and generate requests for next pages."""
        current_page = response.meta['page']
        self.pages_processed += 1
        self.log(f"Processing page {current_page}")

        # Extract car links from current page
        car_links = response.css('.listing-items .listing-item a.js-encode-search::attr(href)').getall()
        
        for link in car_links:
            absolute_url = urljoin(response.url, link)
            
            if absolute_url not in self.processed_urls:
                self.processed_urls.add(absolute_url)
                yield scrapy.Request(
                    url=absolute_url,
                    callback=self.parse_car,
                    meta={'page': current_page}
                )

        if not self.max_pages or current_page < self.max_pages:
            next_offset = current_page * self.items_per_page
            next_url = f"{self.base_url}&offset={next_offset}"
            
            if next_url not in self.processed_urls:
                self.processed_urls.add(next_url)
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse,
                    meta={'page': current_page + 1}
                )

    def clean_price(self, price_text):
        """Clean and convert price text to number."""
        if not price_text:
            return 0
        # Extract only numbers
        clean = re.sub(r'[^\d]', '', price_text)
        return float(clean) if clean else 0

    def clean_mileage(self, mileage_text):
        """Clean and convert mileage text to number."""
        if not mileage_text:
            return 0
        try:
            clean = re.sub(r'[^\d.,]', '', mileage_text)
            if '.' in clean and ',' in clean:
                last_dot = clean.rindex('.')
                last_comma = clean.rindex(',')
                if last_dot > last_comma:
                    clean = clean.replace(',', '')
                else:
                    clean = clean.replace('.', '').replace(',', '.')
            else:
                if clean.count('.') == 1 and len(clean.split('.')[-1]) <= 2:
                    pass
                elif '.' in clean:
                    clean = clean.replace('.', '')
                if clean.count(',') == 1 and len(clean.split(',')[-1]) <= 2:
                    clean = clean.replace(',', '.')
                elif ',' in clean:
                    clean = clean.replace(',', '')
            
            return int(float(clean))
        except Exception as e:
            self.log(f"Error cleaning mileage text '{mileage_text}': {str(e)}", level=logging.ERROR)
            return 0

    def extract_year(self, title_text):
        """Extract year from car title."""
        if not title_text:
            return 0
        # Look for a 4-digit number that could be a year
        year_match = re.search(r'\b20\d{2}\b', title_text)
        return int(year_match.group()) if year_match else 0

    def parse_car(self, response):
        """Extract car information from detail page."""
        self.log("="*80)
        self.log(f"Processing car listing #{self.items_processed + 1}")
        self.log(f"URL: {response.url}")
        
        try:
            item = CarItem()
            item['url'] = response.url
            
            # Extract title
            item['title'] = response.css('h1::text').get('').strip()
            
            # Extract price - look for the price in multiple possible locations
            price_text = None
            price_selectors = [
                '.price::text',
                '.price-value::text',
                '.item-price .price::text',
                '.vehicle-price::text'
            ]
            for selector in price_selectors:
                price_text = response.css(selector).get()
                if price_text:
                    break
            item['price'] = self.clean_price(price_text)
            
            # Extract mileage - look for mileage in multiple possible locations
            mileage_text = None
            mileage_selectors = [
                '[data-type="Odometer"]::text',
                '.key-details__value[data-type="Odometer"]::text',
                '.vehicle-mileage::text',
                '.mileage::text',
                '.details-list__value::text',
                '.vehicle-details__item--mileage::text',
                '.details__item-value[data-test="mileage"]::text',
                '.listing-item__specs--mileage::text',
                '//span[contains(text(),"Kilometraje")]/following-sibling::span/text()',
                '//div[contains(@class,"mileage")]//text()',
                '.specs-list__item:contains("Kilometraje") .specs-list__value::text'
            ]
            
            for selector in mileage_selectors:
                if selector.startswith('//'):
                    mileage_text = response.xpath(selector).get()
                else:
                    mileage_text = response.css(selector).get()
                
                if mileage_text:
                    self.log(f"Found mileage with selector: {selector}")
                    self.log(f"Raw mileage text: {mileage_text}")
                    break
            
            if not mileage_text:
                text = ' '.join(response.css('*::text').getall())
                import re
                km_matches = re.findall(r'(\d+[\d.,]*)\s*(?:km|kms|kilómetros|kilometros)', text.lower())
                if km_matches:
                    mileage_text = km_matches[0]
                    self.log(f"Found mileage in page text: {mileage_text}")
            
            item['mileage'] = self.clean_mileage(mileage_text)
            if item['mileage'] == 0:
                self.log(f"Warning: Could not extract mileage from {response.url}", level=logging.WARNING)
            
            # Extract year from title
            item['year'] = self.extract_year(item['title'])
            
            # Validate required fields before yielding
            if not all([item['title'], item['price'], item['mileage'], item['url']]):
                self.items_dropped += 1
                missing_fields = [field for field in ['title', 'price', 'mileage', 'url'] 
                                if not item.get(field)]
                self.log(f"Dropped car listing due to missing required fields: {missing_fields}", level=logging.WARNING)
                return
                
            self.items_processed += 1
            self.log("-"*40)
            self.log(f"Successfully extracted car #{self.items_processed}")
            self.log(f"Title: {item['title']}")
            self.log(f"Price: ${item['price']:,.0f}")
            self.log(f"Mileage: {item['mileage']:,}km")
            self.log(f"Year: {item['year']}")
            self.log("-"*40)
            yield item
            
        except Exception as e:
            self.log(f"Error processing car listing {response.url}: {str(e)}", level=logging.ERROR)
            self.items_dropped += 1
        finally:
            self.log("="*80)

    def closed(self, reason):
        """Clean up resources when spider closes."""
        self.log("Spider finished. Summary:")
        self.log(f"Total pages processed: {self.pages_processed}")
        self.log(f"Total items processed successfully: {self.items_processed}")
        self.log(f"Total items dropped: {self.items_dropped}")
        if self.items_processed + self.items_dropped > 0:
            success_rate = (self.items_processed/(self.items_processed+self.items_dropped))*100
            self.log(f"Success rate: {success_rate:.1f}%")
        items_per_page = self.items_processed / self.pages_processed if self.pages_processed else 0
        self.log(f"Average items per page: {items_per_page:.1f}")
