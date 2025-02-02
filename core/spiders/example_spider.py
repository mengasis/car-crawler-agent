import scrapy
from domain.car import Car


class ExampleSpider(scrapy.Spider):
    name = 'example'
    allowed_domains = ['example.com']
    start_urls = ['http://example.com']

    def parse(self, response):
        """Parse the response and create Car instances."""
        # This is just an example. Replace with actual selectors for your target website
        for car_element in response.css('.car-item'):
            car = Car(
                title=car_element.css('.title::text').get('').strip(),
                price=float(car_element.css('.price::text').re_first(r'\d+\.\d+') or 0),
                mileage=int(car_element.css('.mileage::text').re_first(r'\d+') or 0),
                year=int(car_element.css('.year::text').re_first(r'\d+') or 0)
            )
            yield car
