from flask import Flask, render_template, request, redirect, url_for
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

app = Flask(__name__)

def extract(url, table_attribs):
    response = requests.get(url)
    webtext = response.text
    soup = BeautifulSoup(webtext, 'html.parser')
    df = pd.DataFrame(columns=table_attribs)
    tbodies = soup.find_all('tbody')
    rows = tbodies[2].find_all('tr')

    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            if col[0].find('a') is not None and col[2].text.strip() != '—':
                data_dict = {"Country": col[0].a.contents[0],
                             "GDP_USD_millions": col[2].contents[0]}
                df1 = pd.DataFrame(data_dict, index=[0])
                df = pd.concat([df, df1], ignore_index=True)
    return df

def transform(df):
    df = df[df["GDP_USD_millions"] != '—']
    GDP_list = df["GDP_USD_millions"].tolist()
    GDP_list = [float("".join(x.split(','))) for x in GDP_list]
    GDP_list = [np.round(x / 1000, 2) for x in GDP_list]
    df["GDP_USD_millions"] = GDP_list
    df = df.rename(columns={"GDP_USD_millions": "GDP_USD_billions"})
    return df

def load_to_csv(df, csv_path):
    df.to_csv(csv_path, index=False)

def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
    query_output = pd.read_sql(query_statement, sql_connection)
    return query_output

def log_progress(message):
    timestamp_format = '%Y-%b-%d-%H:%M:%S'
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    with open("./etl_project_log.txt", "a") as f:
        f.write(timestamp + ' : ' + message + '\n')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        log_progress('Preliminaries complete. Initiating ETL process')
        url = request.form['url']
        table_attribs = ["Country", "GDP_USD_millions"]
        db_name = 'World_Economies.db'
        table_name = 'Countries_by_GDP'
        csv_path = './Countries_by_GDP.csv'
        
        df = extract(url, table_attribs)
        log_progress('Data extraction complete. Initiating Transformation process')
        df = transform(df)
        log_progress('Data transformation complete. Initiating loading process')
        load_to_csv(df, csv_path)
        log_progress('Data saved to CSV file')
        
        sql_connection = sqlite3.connect(db_name)
        log_progress('SQL Connection initiated.')
        load_to_db(df, sql_connection, table_name)
        log_progress('Data loaded to Database as table. Running the query')
        query_statement = f"SELECT * from {table_name} WHERE GDP_USD_billions >= 100"
        query_output = run_query(query_statement, sql_connection)
        log_progress('Process Complete.')
        sql_connection.close()
        
        return render_template('index.html', tables=[query_output.to_html(classes='data', header="true")])
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
