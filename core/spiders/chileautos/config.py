# core/spiders/chileautos/config.py
import os
import json
import logging

class ChileautosConfig:
    def __init__(self, spider):
        self.spider = spider
        self.logger = logging.getLogger(__name__)
        self.filters = self._load_filters()
        self.base_url = self._build_base_url()
        
    def _load_filters(self):
        """Loads filters from JSON file"""
        filters_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'filters.json'
        )
        if not os.path.exists(filters_path):
            raise FileNotFoundError(f"Filters not found at: {filters_path}")
        try:
            with open(filters_path, 'r', encoding='utf-8') as f:
                return json.load(f).get('filters', {})
        except Exception as e:
            self.logger.error(f"Error loading filters: {str(e)}")
            return {}

    def _build_base_url(self):
        """Builds base URL with brand filters"""
        base = 'https://www.chileautos.cl/vehiculos/'

        if not self.filters.get('brands'):
            return base
            
        brands = self.filters['brands']
        brand_query = "(Or." + "._.".join(f"Marca.{brand}" for brand in brands) + ".)" 

        return f"{base}?q=(And.Servicio.ChileAutos._.{brand_query})"

    def __str__(self):
        """String representation of the config object"""
        return str(self.filters.get('max_pages', 'No limit'))