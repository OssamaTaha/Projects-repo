# Code for ETL operations on Country-GDP data

# Importing the required libraries
import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3

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
    log_progress("Starting extraction process")
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure we notice bad responses
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'wikitable sortable'})

        if table is None:
            log_progress("Table not found on the webpage")
            raise ValueError("Table not found on the webpage")

        headers = [header.text.strip() for header in table.find_all('th')]
        rows = table.find_all('tr')[1:]
        
        data = []
        for row in rows:
            cols = row.find_all('td')
            data.append([col.text.strip() for col in cols])

        df = pd.DataFrame(data, columns=headers)
        df = df[table_attribs]  # Select the relevant columns

        log_progress("Extraction process completed")
        return df
    
    except Exception as e:
        log_progress(f"Error during extraction: {e}")
        raise

def transform(df, csv_path):
    ''' This function accesses the CSV file for exchange rate
    information, and adds three columns to the data frame, each
    containing the transformed version of Market Cap column to
    respective currencies'''
    log_progress("Starting transformation process")
    
    try:
        exchange_rates = pd.read_csv(csv_path)
        
        df['Market cap (USD)'] = df['Market cap'].apply(lambda x: float(x.replace('$', '').replace('B', '')) * 1e9)
        df = df.drop(columns=['Market cap'])
        
        df = df.merge(exchange_rates, on='Currency', how='left')
        
        df['Market cap (EUR)'] = df['Market cap (USD)'] * df['USD to EUR']
        df['Market cap (JPY)'] = df['Market cap (USD)'] * df['USD to JPY']
        df['Market cap (GBP)'] = df['Market cap (USD)'] * df['USD to GBP']

        log_progress("Transformation process completed")
        return df

    except Exception as e:
        log_progress(f"Error during transformation: {e}")
        raise

def load_to_csv(df, output_path):
    ''' This function saves the final data frame as a CSV file in
    the provided path. Function returns nothing.'''
    log_progress("Starting load to CSV process")
    
    try:
        df.to_csv(output_path, index=False)
        log_progress("Load to CSV process completed")
    
    except Exception as e:
        log_progress(f"Error during load to CSV: {e}")
        raise

def load_to_db(df, sql_connection, table_name):
    ''' This function saves the final data frame to a database
    table with the provided name. Function returns nothing.'''
    log_progress("Starting load to DB process")
    
    try:
        df.to_sql(table_name, sql_connection, if_exists='replace', index=False)
        log_progress("Load to DB process completed")

    except Exception as e:
        log_progress(f"Error during load to DB: {e}")
        raise

def run_query(query_statement, sql_connection):
    ''' This function runs the query on the database table and
    prints the output on the terminal. Function returns nothing. '''
    log_progress("Starting query execution process")
    
    try:
        cursor = sql_connection.cursor()
        cursor.execute(query_statement)
        result = cursor.fetchall()
        
        for row in result:
            print(row)
        
        log_progress("Query execution process completed")
    
    except Exception as e:
        log_progress(f"Error during query execution: {e}")
        raise

''' Here, you define the required entities and call the relevant
functions in the correct order to complete the project. Note that this
portion is not inside any function.'''

url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attribs = ["Bank name", "Market cap"]
csv_path = 'exchange_rates.csv'
output_path = 'largest_banks.csv'
db_path = 'etl_data.db'
table_name = 'largest_banks'

# Extracting data
df = extract(url, table_attribs)

# Transforming data
df = transform(df, csv_path)

# Loading data to CSV
load_to_csv(df, output_path)

# Loading data to DB
conn = sqlite3.connect(db_path)
load_to_db(df, conn, table_name)

# Running a sample query
query = f"SELECT * FROM {table_name} LIMIT 5;"
run_query(query, conn)

conn.close()
