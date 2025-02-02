# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from database.mongo_database import MongoDatabase
from config.settings import MONGO_URI, MONGO_DB_NAME, CARS_COLLECTION
from domain.car import Car


class MongoDBPipeline:
    def __init__(self):
        """Initialize MongoDB connection."""
        self.db = None

    def open_spider(self, spider):
        """Create MongoDB connection when spider opens."""
        self.db = MongoDatabase(MONGO_URI, MONGO_DB_NAME)

    def close_spider(self, spider):
        """Close MongoDB connection when spider closes."""
        if self.db:
            self.db.close()

    def process_item(self, item, spider):
        """Process and store scraped item in MongoDB."""
        if isinstance(item, Car):
            self.db.insert_one(CARS_COLLECTION, item.to_dict())
        return item
