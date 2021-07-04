# Web scraping projects

## About
This repository contains various web scraping scripts including data processing with usage of Python packages:
* Requests
* BeautifulSoup
* Selenium
* Pandas

## Scripts
1. *gpw_stock_prices.py* - script used to scrape stock prices data from *biznesradar.pl* website and calculate the average price from the previous n months for each day. Results are outputted in the .xls file.
2. *apartment_offers_scrape* - this directory contains:  
  &nbsp;&nbsp;&nbsp; * *apartment_offers_scrape.py* - Python script used to scrape apartment prices from *otodom.pl* website and extract the details from the offers  
  &nbsp;&nbsp;&nbsp; * *apartments_db.sql* - contains SQL scripts used to create tables storing scraped data and procedure used for data aggregation
