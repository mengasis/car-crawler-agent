# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CoreItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class CarItem(scrapy.Item):
    """Item representing a car with its basic information."""
    title = scrapy.Field()
    price = scrapy.Field()
    mileage = scrapy.Field()
    year = scrapy.Field()
    url = scrapy.Field()
