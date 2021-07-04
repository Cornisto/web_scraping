# -*- coding: utf-8 -*-
"""
Created on Sat Jun 20 20:07:53 2021

@author: Cornisto
"""


from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys




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
    
    if page.text.find('<table class="qTableFull">') != -1:
        soup = BeautifulSoup(page.text[page.text.find('<table class="qTableFull">'):], 'html.parser')
    else:
        return None
    
    return soup


def ParseResultTable(soup):
    """
    Function that parses HTML table into Pandas DataFrame
    
    Parameters:
        soup - BeautifulSoup object
    Returns:
        DataFrame object containing results
    """
    
    table = soup.find('table', attrs={'class':'qTableFull'})
    table_rows = table.find_all('tr')
    
    l = []
    for tr in table_rows:
        td = tr.find_all('td')
        row = [tr.text for tr in td]
        l.append(row)
        
    results = pd.DataFrame(l, columns=["Data", "Otwarcie", "Max", "Min", "Zamknięcie", "Wolumen", "Obrót"])
    results.dropna(inplace=True)
    results["Data"] = results["Data"].apply(lambda x: datetime.strptime(x, "%d.%m.%Y"))
    
    return results


def CalculateAvg(df, current_date, num_months):
    """
    Function that calculates average price of stock from the last n months 
    
    Parameters:
        df - DataFrame containing stock prices
        current_date - datetime from which the average n-months price should be calculated 
        num_months - number of last months that should be included in calculation
    Returns:
        Series object containing average price
    """
    
    return df.loc[(df["Data"] >= current_date - relativedelta(months=num_months)) & (df["Data"] < current_date), "Zamknięcie"].mean()


def DownloadAndProcessData(stock_name: str, start_date: str):
    """
    Function that parses HTML table into Pandas DataFrame
    
    Parameters:
        stock_name - name of the stock to download data for
        start_date - date from which we want results up to the current date in format yyyy-mm-dd
    Returns:
        DataFrame object containing results
    """
    
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        print('Specified date does not match format: yyyy-mm-dd!')
        sys.exit()
        
    print(f'Downloading data for {stock_name}...')
    url = 'https://www.biznesradar.pl/notowania-historyczne/' + stock_name
    
    all_results = pd.DataFrame(columns=['Data', 'Otwarcie', 'Max', 'Min', 'Zamknięcie', 'Wolumen', 'Obrót'])
    
    soup = ParseResultPage(url)
    
    if soup is not None:
        results = ParseResultTable(soup)
        all_results = all_results.append(results, ignore_index=True)
    
    for i in range(2, 15):
        soup = ParseResultPage(url + ',' + str(i))
    
        if soup is not None:
            results = ParseResultTable(soup)
            all_results = all_results.append(results, ignore_index=True)
    
    # To calculate average from last year one year before specified start_date is needed
    all_results = all_results.loc[all_results['Data'] >= start_date - timedelta(days=365), :].sort_values(by=['Data']).reset_index(drop=True)
    
    all_results['Otwarcie'] = all_results['Otwarcie'].str.replace(' ', '')
    all_results['Max'] = all_results['Max'].str.replace(' ', '')
    all_results['Min'] = all_results['Min'].str.replace(' ', '')
    all_results['Zamknięcie'] = all_results['Zamknięcie'].str.replace(' ', '')                                            
    all_results['Wolumen'] = all_results['Wolumen'].str.replace(' ', '')
    all_results['Obrót'] = all_results['Obrót'].str.replace(' ', '')                                             

    all_results.loc[:, ['Otwarcie', 'Max', 'Min', 'Zamknięcie', 'Wolumen', 'Obrót']] = all_results.loc[:, ['Otwarcie', 'Max', 'Min', 'Zamknięcie', 'Wolumen', 'Obrót']].apply(pd.to_numeric)
    
    df_tmp = all_results.loc[:, ['Data', 'Zamknięcie']].copy()
    all_results['1M'] = all_results['Data'].apply(lambda x: CalculateAvg(df_tmp, x, 1)).round(3)
    all_results['3M'] = all_results['Data'].apply(lambda x: CalculateAvg(df_tmp, x, 3)).round(3)
    all_results['6M'] = all_results['Data'].apply(lambda x: CalculateAvg(df_tmp, x, 6)).round(3)
    all_results['1R'] = all_results['Data'].apply(lambda x: CalculateAvg(df_tmp, x, 12)).round(3)
    all_results = all_results.loc[all_results['Data'] >= start_date]
    all_results['Data'] = all_results['Data'].dt.date
    
    return all_results




    



if __name__ == '__main__':
    
    orlen_data = DownloadAndProcessData('PKN-ORLEN', '2020-01-01')
    lotos_data = DownloadAndProcessData('LOTOS', '2021-01-01')
    pgnig_data = DownloadAndProcessData('PGNIG', '2020-01-01')

    with pd.ExcelWriter('stock_prices.xlsx') as writer:  
        orlen_data.to_excel(writer, sheet_name='PKN-ORLEN', index=False)
        lotos_data.to_excel(writer, sheet_name='LOTOS', index=False)
        pgnig_data.to_excel(writer, sheet_name='PGNIG', index=False)
        writer.save()


