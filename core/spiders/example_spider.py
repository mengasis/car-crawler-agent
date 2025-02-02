import re
import logging
import scrapy
from core.items import CarItem
from urllib.parse import urljoin


class CarSpider(scrapy.Spider):
    name = 'cars'
    allowed_domains = ['chileautos.cl']
    start_urls = ['https://www.chileautos.cl/vehiculos/autos-vehículo/'] 
    
    def __init__(self, *args, **kwargs):
        super(CarSpider, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        self.items_processed = 0
        self.items_dropped = 0

    def clean_price(self, price_text):
        """Clean and convert price text to number."""
        if not price_text:
            return 0
        # Extract only numbers from price text
        clean = re.sub(r'[^\d]', '', price_text)
        return float(clean) if clean else 0

    def clean_mileage(self, mileage_text):
        """Clean and convert mileage text to number."""
        if not mileage_text:
            return 0
        # Extract only numbers
        clean = re.sub(r'[^\d]', '', mileage_text)
        return int(clean) if clean else 0

    def extract_year(self, title_text):
        """Extract year from car title."""
        if not title_text:
            return 0
        # Look for a 4-digit number that could be a year
        year_match = re.search(r'\b(19|20)\d{2}\b', title_text)
        return int(year_match.group()) if year_match else 0

    def parse(self, response):
        """Extract car information from each listing."""
        self.logger.info("Starting to parse car listings...")
        
        # Select all car items (exclude ads)
        car_items = response.css('div.listing-item.card:not(.advert-fuse)')
        total_items = len(car_items)
        self.logger.info(f"Found {total_items} car listings to process")
        
        for index, car in enumerate(car_items, 1):
            self.logger.info(f"Processing car {index}/{total_items}")
            item = CarItem()
            
            # Extract car URL
            url_path = car.css('.card-header a.js-encode-search::attr(data-href)').get('')
            if url_path:
                item['url'] = urljoin('https://www.chileautos.cl', url_path)
                self.logger.debug(f"Found URL: {item['url']}")
            
            # Extract full title
            title = car.css('h3 a::text').get('').strip()
            item['title'] = title
            self.logger.debug(f"Found title: {title}")
            
            # Extract price from data-webm-price attribute
            price = car.attrib.get('data-webm-price', '0')
            item['price'] = float(price) if price.isdigit() else 0
            self.logger.debug(f"Found price: {item['price']}")
            
            # Extract mileage from li with data-type="Odometer"
            mileage_text = car.css('li[data-type="Odometer"]::text').get('')
            item['mileage'] = self.clean_mileage(mileage_text)
            self.logger.debug(f"Found mileage: {item['mileage']}")
            
            # Extract year from title
            item['year'] = self.extract_year(title)
            self.logger.debug(f"Found year: {item['year']}")
            
            # Only yield item if it has all required fields
            if item['title'] and item['price'] > 0 and item['mileage'] > 0 and item['url']:
                self.items_processed += 1
                self.logger.info(f"Successfully extracted car {self.items_processed}: {item['title']}")
                self.logger.info(f"Details: Price=${item['price']:,.0f}, {item['mileage']:,}km, Year {item['year']}")
                yield item
            else:
                self.items_dropped += 1
                self.logger.warning(f"Dropped car listing due to missing required fields: {item}")

    def closed(self, reason):
        """Log final statistics when spider closes."""
        self.logger.info("Spider finished. Summary:")
        self.logger.info(f"Total items processed successfully: {self.items_processed}")
        self.logger.info(f"Total items dropped: {self.items_dropped}")
        self.logger.info(f"Success rate: {(self.items_processed/(self.items_processed+self.items_dropped))*100:.1f}%")
