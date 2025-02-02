# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, PyMongoError
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter

# Load environment variables
load_dotenv()

# Get MongoDB configuration from environment variables
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'scrapy_db')

class MongoDBConnectionError(Exception):
    """Custom exception for MongoDB connection errors."""
    pass

class MongoDBPipeline:
    """Pipeline for storing car items in MongoDB."""
    
    collection_name = 'cars'

    def __init__(self):
        self.client = None
        self.db = None
        self.items_processed = 0
        self.items_dropped = 0
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def check_connection(self):
        """Test MongoDB connection and database access."""
        try:
            # Try to connect with a shorter timeout
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Force a connection check
            self.client.server_info()
            
            # Test database access
            self.db = self.client[MONGO_DB_NAME]
            self.db.list_collection_names()
            
            self.logger.info("MongoDB connection test successful")
        except ServerSelectionTimeoutError as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise MongoDBConnectionError(f"Could not connect to MongoDB: {str(e)}")
        except PyMongoError as e:
            self.logger.error(f"Error accessing MongoDB: {str(e)}")
            raise MongoDBConnectionError(f"Error accessing MongoDB: {str(e)}")

    def open_spider(self, spider):
        """Initialize MongoDB connection when spider starts."""
        self.logger.info("Initializing MongoDB connection...")
        try:
            # Test connection before proceeding
            self.check_connection()
            self.logger.info(f"Successfully connected to MongoDB database: {MONGO_DB_NAME}")
        except MongoDBConnectionError as e:
            self.logger.error("Spider initialization failed due to MongoDB connection error")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during spider initialization: {str(e)}")
            raise

    def close_spider(self, spider):
        """Close MongoDB connection when spider finishes."""
        self.logger.info("Closing MongoDB connection...")
        if self.client:
            self.client.close()
        self.logger.info("Pipeline finished. Summary:")
        self.logger.info(f"Total items processed: {self.items_processed}")
        self.logger.info(f"Total items dropped: {self.items_dropped}")
        if self.items_processed + self.items_dropped > 0:
            success_rate = (self.items_processed/(self.items_processed+self.items_dropped))*100
            self.logger.info(f"Success rate: {success_rate:.1f}%")

    def process_item(self, item, spider):
        """Process and validate item before storing."""
        self.logger.debug(f"Processing item: {item}")
        adapter = ItemAdapter(item)
        
        # Validate required fields
        if not adapter.get('title'):
            self.items_dropped += 1
            raise DropItem(f"Item dropped - missing title: {item}")
            
        # Validate price
        price = adapter.get('price', 0)
        if not price or price <= 0:
            self.items_dropped += 1
            raise DropItem(f"Item dropped - invalid price: {item}")
            
        # Validate mileage
        mileage = adapter.get('mileage', 0)
        if not mileage or mileage <= 0:
            self.items_dropped += 1
            raise DropItem(f"Item dropped - invalid mileage: {item}")
            
        # Validate URL
        if not adapter.get('url'):
            self.items_dropped += 1
            raise DropItem(f"Item dropped - missing URL: {item}")
        
        try:
            # Verify connection is still alive before inserting
            self.client.server_info()
            
            # Insert into MongoDB
            self.db[self.collection_name].insert_one(adapter.asdict())
            self.items_processed += 1
            self.logger.info(f"Successfully stored car: {adapter.get('title')}")
            self.logger.info(f"Details: Price=${price:,.0f}, {mileage:,}km, Year {adapter.get('year')}")
            return item
        except ServerSelectionTimeoutError as e:
            self.items_dropped += 1
            self.logger.error(f"MongoDB connection lost: {str(e)}")
            raise MongoDBConnectionError(f"Lost connection to MongoDB: {str(e)}")
        except PyMongoError as e:
            self.items_dropped += 1
            self.logger.error(f"Failed to store item in MongoDB: {str(e)}")
            raise DropItem(f"Failed to store item: {str(e)}")
