# Car Crawler Agent

## Description
This project is a Scrapy-based web scraper designed to extract vehicle listings from automotive marketplace websites. It is scalable, maintainable, and adaptable to different site structures. As a test implementation, it successfully extracts data from chileautos.cl.

## Features
- Modular spider architecture
- Configurable through environment variables
- Automatic request throttling
- Rotating user agents
- Data validation pipeline
- Error handling and retry mechanisms

## Requirements
- Python 3.8+
- Scrapy 2.8+

## Installation
```bash
pip install -r requirements.txt
```

## Configuration
Create a `.env` file in the project root:
```ini
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=scrapy_db
```

## Running the Spider
```bash
scrapy crawl chileautos
```

## Project Structure
```
scrapper/
├── core/
│   ├── spiders/
│   │   └── chileautos/
│   │       ├── spider.py    # Main spider implementation
│   │       └── config.py    # Spider-specific settings
│   ├── middlewares.py       # Custom middleware
│   ├── pipelines.py         # Data processing pipelines
│   ├── settings.py          # Project settings
│   └── logger.py            # Logging configuration
├── requirements.txt         # Dependencies
└── README.md                 # This file
```

## License
MIT License
