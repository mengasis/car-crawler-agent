# core/spiders/chileautos/data_cleaners.py
import re
import logging
from typing import Optional

class DataCleaner:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def clean_price(self, price_text):
        """Cleans and converts price text to number"""
        if not price_text:
            return 0
        clean = re.sub(r'[^\d]', '', price_text)
        return float(clean) if clean else 0

    def clean_mileage(self, mileage_text):
        """Cleans and converts mileage to integer"""
        if not mileage_text:
            return 0
            
        try:
            clean = re.sub(r'[^\d.,]', '', mileage_text)
            # Complete cleaning logic...
            return int(float(clean))
        except Exception as e:
            self.logger.error(f"Error cleaning mileage: {str(e)}")
            return 0

    def extract_year_from_title(self, title: str) -> Optional[int]:
        """Extract year from vehicle title"""
        if not title:
            return 0
        year_match = re.search(r'\b20\d{2}\b', title)
        return int(year_match.group()) if year_match else 0