# -*- coding: utf-8 -*-
"""
Created on Sat May  8 20:07:53 2020

@author: Cornisto
"""

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import re
import datetime
import os


def ParseResultPage(url):
    """
    Function that sends request to te website and parses the response
    
    Parameters:
        url - URL adress of the website
    Returns:
        BeautifulSoup object if searched element is found, None otherwise
    Raises:
        RequestException: If any error connected to request occurs
        HTTPError: If HTTP error occurs
    """
    
    try:
        page = requests.get(url)
    except requests.exceptions.RequestException:
        return None
    except requests.exceptions.HTTPError:
        return None
    #filtering out promoted offers if possible
    if page.text.find('<div class="listing-title">') != -1:
        soup = BeautifulSoup(page.text[page.text.find('<div class="listing-title">'):], 'html.parser')
    else:
        soup = BeautifulSoup(page.text, 'html.parser')
    
    return soup
    

def GetNextPageUrl(soup):
    """
    Function that find url adress of the next page in search results
    
    Parameters:
        soup - BeautifulSoup object
    Returns:
        Url adress of the next result page
    """
    
    next_page_url = None
    for offers in soup.find_all('li',{'class':'pager-next'}):
       link = offers.find('a', {'class':''}, href=True)
       if link is None:
           continue
       else:
           next_page_url = link['href']
           
    return next_page_url


def GetOffersUrls(soup):
    """
    Function that collects all url adresses of apartment offers available on the current result page
    
    Parameters:
        soup - BeautifulSoup object
    Returns:
        List of url adresses of the offers
    """
    
    links_list = []
    for offers in soup.find_all('div', {'class':'offer-item-details'}):
       link = offers.find('a',href=True)
       if link is None:
           continue
       links_list.append(link['href'])
       
    return links_list




def ParseOfferPage(url):
    """
    Function that sends request to te website and parses the response
    
    Parameters:
        url - URL adress of the page
    Returns:
        BeautifulSoup object if searched element is found, None otherwise
    Raises:
        RequestException: If any error connected to request occurs
        HTTPError: If HTTP error occurs
    """
    
    try:
        page = requests.get(url)
    except requests.exceptions.RequestException:
        return None
    except requests.exceptions.HTTPError:
        return None
    soup = BeautifulSoup(page.text, 'html.parser')
    
    return soup


def GetOfferBasicInfo(soup, url):
    """
    Function that collects basic information about the apartment from the offer page
    
    Parameters:
        soup - BeautifulSoup object containing apartment details 
        url - URL adress of the page
    Returns:
        DataFrame object containing informaiton about the apartment
    """
    
    info_list = {}
    info_section = soup.find('section', {'class':'section-overview'})
    for infos in info_section.find_all('li'):
       if infos is None:
           continue
       else:
           try:
               info_list[infos.text.split(':')[0]] = [infos.text.split(':')[1]]
           except IndexError:
               continue 
    result_df = pd.DataFrame.from_dict(info_list)
    result_df['link'] = url
    result_df['Dzielnica'], result_df['Osiedle'], result_df['Ulica'], result_df['Tytuł Oferty'] = GetLocationInfo(soup)
    result_df['Cena'] = GetOfferPrice(soup)
    
    return result_df
    


def GetOfferPrice(soup):
    """
    Function that collects price of the apartment
    
    Parameters:
        soup - BeautifulSoup object containing apartment information 
    Returns:
        Float value representing apartment price, if not specified - 0
    """
    
    price = 0
    price_section = soup.find('header', {'class':'css-jcl595'})
    if price_section:
        price_labels = price_section.find_all('div', {'class':'css-1vr19r7'})
        if price_labels:
            for price_label in price_labels:
                price_search = re.search('(\d+\s*\d+\s*)zł', price_label.text, re.IGNORECASE)
                if price_search:
                    price = price_search.group(1).replace(' ', '')
                    try:
                        price = float(price)
                    except ValueError:
                        price = 0
    return price


def GetLocationInfo(soup):
    """
    Function that extracts information about apartment location
    
    Parameters:
        soup - BeautifulSoup object containing apartment information 
    Returns:
        List containing information about district, sub_district, street and offer_title
    """
    
    location_info = []
    location_section = soup.find('ul', {'class':'breadcrumb css-1ry41wf'})
    for location in location_section.find_all('li'):
       if location is None:
           continue
       else:
           link = location.find('a', href=True)
           if not link is None:
               location_info.append(link.text)
           
           if not location.span is None:
               span = location.find('span')
               if span is None:
                   continue
               else:
                   location_info.append(span.text)
    
    offer_title = location_info[-1]
    location_info = location_info[:-1]
    district = location_info[4]
    
    try:
        street = [s for s in location_info if "ul" in s][0]
    except IndexError:
        street = location_info[-1] if (location_info[-1] not in ['Sady Żoliborskie', 'Stary Żoliborz', 'Powązki', 'Cytadela', 
                                                                'Górny Mokotów', 'Dolny Mokotów', 'Służew', 'Służewiec', 'Wyględów', 'Stegny', 'Wierzbno', 'Sadyba', 'Pola Mokotowskie', 'Ksawerów', 'Sielce', 'Czerniaków',
                                                                'Kabaty', 'Pyry', 'Wyczółki', 'Natolin', 'Imielin', 'Stokłosy',
                                                                'Marymont', 'Stare Bielany', 'Piaski', 'Młociny', 'Chomiczówka', 'Wrzeciono', 'Wawrzyszew'] and len(location_info) > 5) or len(location_info) == 7 else ''
    
    #checking if street name is in the offer title
    if street == '':
        street_search = re.search('\W+(ul[\.\s]+)(\w+)\s+(\w+)\W*', offer_title, re.IGNORECASE)
        if street_search:
            if street_search.group(3)[0] == street_search.group(3)[0].upper():
                street = street_search.group(1) + street_search.group(2) + ' ' + street_search.group(3)
                
    if street == '':    
        street_search = re.search('\W+(ul[\.\s]+)(\w+)\W*', offer_title, re.IGNORECASE)
        if street_search:
            street = street_search.group(1) + street_search.group(2)
    
    sub_district = location_info[5] if (len(location_info) == 7) or (len(location_info) > 5 and street == '') else ''
    
    #searching for street name in the offer description
    if street == '':
        descr_section = soup.find('section', {'class':'section-description'})
        if not descr_section is None:
           descriptions = descr_section.find_all('p')
           if not descriptions is None:
               for descr in descriptions:
                   
                   street_search = re.search('\W+(ul[\.\s]+)(\w+)\s+(\w+)\W+', descr.text, re.IGNORECASE)
                   if street_search:
                       if street_search.group(3)[0] == street_search.group(3)[0].upper():
                           street = street_search.group(1) + street_search.group(2) + ' ' + street_search.group(3)
                       break
                   
                   street_search = re.search('\W+(ul[\.\s]+)(\w+)\W+', descr.text, re.IGNORECASE)
                   if street_search:
                       street = street_search.group(1) + street_search.group(2)
                       break
                   
                   street_search = re.search('\W+ulicy\W+(\w+)\s+(\w+)\W+', descr.text, re.IGNORECASE)
                   if street_search:
                       if street_search.group(1)[0] == street_search.group(1)[0].upper() and street_search.group(2)[0] == street_search.group(2)[0].upper():
                           street = street_search.group(1) + ' ' + street_search.group(2)
                           break
                   
                   street_search = re.search('\W+ulicy\W+(\w+)\W+', descr.text, re.IGNORECASE)
                   if street_search:
                       if street_search.group(1)[0] == street_search.group(1)[0].upper():
                           street = street_search.group(1)
                           break
                        
    return [district, sub_district, street, offer_title]



if __name__ == '__main__':
    
    #getting script directory to save results in
    save_directory = os.path.dirname(os.path.realpath(__file__))
    #using url with predefined filters 
    url = 'https://www.otodom.pl/sprzedaz/mieszkanie/?search%5Bfilter_float_price_per_m%3Ato%5D=10000&search%5Bfilter_float_price%3Ato%5D=500000&search%5Bfilter_float_m%3Afrom%5D=40&search%5Bfilter_enum_rooms_num%5D%5B0%5D=3&search%5Bfilter_enum_rooms_num%5D%5B1%5D=2&locations%5B0%5D%5Bregion_id%5D=7&locations%5B0%5D%5Bcity_id%5D=26&locations%5B0%5D%5Bdistrict_id%5D=12721&locations%5B1%5D%5Bregion_id%5D=7&locations%5B1%5D%5Bcity_id%5D=26&locations%5B1%5D%5Bdistrict_id%5D=39&locations%5B2%5D%5Bregion_id%5D=7&locations%5B2%5D%5Bcity_id%5D=26&locations%5B2%5D%5Bdistrict_id%5D=47&locations%5B3%5D%5Bregion_id%5D=7&locations%5B3%5D%5Bcity_id%5D=26&locations%5B3%5D%5Bdistrict_id%5D=50&locations%5B4%5D%5Bregion_id%5D=7&locations%5B4%5D%5Bcity_id%5D=26&locations%5B4%5D%5Bdistrict_id%5D=53&locations%5B5%5D%5Bregion_id%5D=7&locations%5B5%5D%5Bcity_id%5D=26&locations%5B5%5D%5Bdistrict_id%5D=38&nrAdsPerPage=72'
    
    offers_urls = []
    
    while url != None:
        soup = ParseResultPage(url)
        if soup != None:
            try:
                offers_urls.extend(GetOffersUrls(soup))
            except AttributeError:
                #continue
                print('error')
            url = GetNextPageUrl(soup)
        else:
            break
    
    
    basic_info = ['Powierzchnia',
                  'Liczba pokoi',
                  'Rynek',
                  'Rodzaj zabudowy',
                  'Rok budowy',
                  'Piętro',
                  'Liczba pięter',
                  'Materiał budynku',
                  'Ogrzewanie',
                  'Czynsz',
                  'Okna',
                  'Stan wykończenia',
                  'Forma własności',
                  'Dostępne od',
                  'link',
                  'Dzielnica',
                  'Osiedle', 
                  'Ulica',
                  'Tytuł Oferty',
                  'Cena']
    
    
    info = pd.DataFrame(columns=basic_info)
    
    print('Found ' + str(len(offers_urls)) + ' offers.')
    for offer_url in offers_urls:
        print(offer_url)
        try:
            soup = ParseOfferPage(offer_url)
            if soup is not None:
                offer_info = GetOfferBasicInfo(soup, offer_url).apply(lambda x: x.str.strip())
                info = info.append(offer_info)
        except Exception:
            continue

    info['upload_date'] = datetime.datetime.now()
    
    #If this column exists in the results - drop it
    try:
        info.drop('Obsługa zdalna', axis=1, inplace=True)
    except Exception:
        pass
    
    info.rename(columns={'Powierzchnia':'surface',
                  'Liczba pokoi':'num_rooms',
                  'Rynek':'market',
                  'Rodzaj zabudowy':'buiding_type',
                  'Rok budowy':'year_built',
                  'Piętro':'floor_num',
                  'Liczba pięter':'num_building_floors',
                  'Materiał budynku':'building_material',
                  'Ogrzewanie':'heating',
                  'Czynsz':'rent',
                  'Okna':'windows',
                  'Stan wykończenia':'finishing_state',
                  'Forma własności':'ownership',
                  'Dostępne od':'available_from',
                  'link':'link_adress',
                  'Dzielnica':'district',
                  'Osiedle':'borough', 
                  'Ulica':'street',
                  'Tytuł Oferty':'offer_title',
                  'Cena':'price'}, inplace=True)
        
    info['surface'] = info['surface'].apply(lambda x: re.search('(\d+,*\d+)', x).group(1) if not pd.isnull(x) and re.search('(\d+,*\d+)', x) else np.nan)
    info['surface'] = info['surface'].apply(lambda x: x.replace(',', '.'))
    info['surface'] = info['surface'].apply(pd.to_numeric)
    
    info['rent'] = info['rent'].apply(lambda x: re.search('(\d+)', x).group(1) if not pd.isnull(x) and re.search('(\d+)', x) else np.nan)
    info['rent'] = info['rent'].apply(pd.to_numeric)
    
    info['floor_num'] = info['floor_num'].apply(lambda x: re.search('(\d+)', x).group(1) if not pd.isnull(x) and re.search('(\d+)', x) else x)
    info['floor_num'] = info['floor_num'].replace('parter', 0)
    info['floor_num'] = info['floor_num'].replace('suterena', -1)
    info['floor_num'] = info['floor_num'].apply(pd.to_numeric)
    
    info['num_building_floors'] = info['num_building_floors'].apply(lambda x: re.search('(\d+)', x).group(1) if not pd.isnull(x) and re.search('(\d+)', x) else np.nan)
    info['num_building_floors'] = info['num_building_floors'].apply(pd.to_numeric)
    
    info['year_built'] = info['year_built'].apply(lambda x: re.search('(\d+)', x).group(1) if not pd.isnull(x) and re.search('(\d+)', x) else np.nan)
    info['year_built'] = info['year_built'].apply(pd.to_numeric)
    
    info['num_rooms'] = info['num_rooms'].apply(lambda x: re.search('(\d+)', x).group(1) if not pd.isnull(x) and re.search('(\d+)', x) else np.nan)
    info['num_rooms'] = info['num_rooms'].apply(pd.to_numeric)
    
    info['street'] = info['street'].apply(lambda x: re.sub('ul\.*', '', x))
    info['street'] = info['street'].str.strip()
    
    db_host = os.environ.get('DB_HOSTNAME')
    db_user = os.environ.get('DB_USER')
    db_user_pass = os.environ.get('DB_USER_PASSWORD')
    db_port = os.environ.get('DB_PORT')
    
    
    try:
        engine = create_engine(f'mysql+mysqlconnector://{db_user}:{db_user_pass}@{db_host}:{db_port}/apartments?charset=utf8', encoding='utf-8')
        conn = engine.connect()
        Session = sessionmaker(bind=engine)
        Session.configure(bind=engine)
        session = Session()
        sql = text("TRUNCATE TABLE apartments.offers_tmp;")
        conn.execute(sql)
        #uploading records
        info.to_sql(name='offers_tmp', con=conn, schema='apartments', if_exists='append', index=False)
        #processing new records
        sql = text("CALL apartments.sp_process_offers();")
        conn.execute(sql)
    except SQLAlchemyError:
        info.to_excel(f'{save_directory}/apartments_scrape_' + datetime.datetime.now().strftime('%Y%m%d') + '.xlsx', encoding='utf8')
    finally:
        conn.close()
    
    
    
    
    
    




