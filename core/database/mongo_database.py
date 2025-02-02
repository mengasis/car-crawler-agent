from typing import Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection


class MongoDatabase:
    """MongoDB database connection and operations handler."""

    def __init__(self, uri: str, db_name: str):
        """Initialize MongoDB connection."""
        self.client: MongoClient = MongoClient(uri)
        self.db: Database = self.client[db_name]

    def insert_one(self, collection_name: str, data: Dict[str, Any]) -> str:
        """Insert a single document into a collection."""
        collection: Collection = self.db[collection_name]
        result = collection.insert_one(data)
        return str(result.inserted_id)

    def close(self) -> None:
        """Close the MongoDB connection."""
        self.client.close()
