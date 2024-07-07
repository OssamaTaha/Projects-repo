# Code for ETL operations on Country-GDP data

# Importing the required libraries
import datetime
import requests
from bs4 import BeautifulSoup
import numpy as np
import sqlite3
import pandas as pd

def log_progress(message):
    ''' This function logs the mentioned message of a given stage of the
    code execution to a log file. Function returns nothing'''
    with open('code_log.txt', 'a') as log_file:
        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{time_stamp} : {message}\n"
        log_file.write(log_entry)

def extract(url, table_attribs):
    ''' This function aims to extract the required
    information from the website and save it to a data frame. The
    function returns the data frame for further processing. '''
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    tbody = soup.find("tbody")
    rows = tbody.find_all("tr")
    data = []
    bank_names = []
    market_caps = []

    for row in rows[1:]:  # Start from index 1 to skip the header row
        cols = row.find_all('td')
        bank_name = cols[1].text.strip()
        market_cap = cols[2].text.strip()
        bank_names.append(bank_name)
        market_caps.append(market_cap)

    df = pd.DataFrame({
    'Bank name': bank_names,
    'MC_USD_Billion': market_caps
    })

    df['MC_USD_Billion'] = df['MC_USD_Billion'].apply(lambda x: float(x.replace('$', '').replace('B', '')))
    return df 

def transform(df, csv_path):
    ''' This function accesses the CSV file for exchange rate
    information, and adds three columns to the data frame, each
    containing the transformed version of Market Cap column to
    respective currencies'''
    csv_path = './exchange_rate.csv'
    exchange_rate= pd.read_csv("csv_path")
    exchange_rate = exchange_rate.set_index('Currency').to_dict()['Rate']
    df['MC_EUR_Billion'] = [np.round(x*exchange_rate['EUR'],2) for x in df['MC_USD_Billion']]
    df['MC_GBP_Billion'] = [np.round(x*exchange_rate['GBP'],2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [np.round(x*exchange_rate['INR'],2) for x in df['MC_USD_Billion']]

    return df

def load_to_csv(df, output_path):
    ''' This function saves the final data frame as a CSV file in
    the provided path. Function returns nothing.'''

    df.to_csv(output_path, index=False)

def load_to_db(df, sql_connection, table_name):
    ''' This function saves the final data frame to a database
    table with the provided name. Function returns nothing.'''
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
    ''' This function runs the query on the database table and
    prints the output on the terminal. Function returns nothing. '''
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)

''' Here, you define the required entities and call the relevant
functions in the correct order to complete the project. Note that this
portion is not inside any function.'''

url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attribs = ["Bank name", "Market cap"]
db_name = 'Banks.db'
table_name = 'Largest_banks'
csv_path = './exchange_rates.csv'

# Call the functions
log_progress('Preliminaries complete. Initiating ETL process')
df = extract(url, table_attribs)
log_progress('Data extraction complete. Initiating Transformation process')
df = transform(df,csv_path)
log_progress('Data transformation complete. Initiating loading process')
load_to_csv(df, csv_path)
log_progress('Data saved to CSV file')
sql_connection = sqlite3.connect(db_name)
log_progress('SQL Connection initiated.')
load_to_db(df, sql_connection, table_name)
log_progress('Data loaded to Database as table. Running the query')
query_statement = f"SELECT * from {table_name} WHERE GDP_USD_billions >= 100"
run_query(query_statement, sql_connection)
log_progress('Process Complete.')
sql_connection.close()
