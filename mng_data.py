# -*- coding: utf-8 -*-
"""
Created on Mon May  3 09:04:11 2021

@author: JensJ
"""

import yfinance as yf

import pandas as pd
from pathlib import Path


p = Path('.')
DATAP = p / 'data'



def update_data(listname,prd='4y',intv='1d'):
    dfl = pd.read_csv(listname,index_col=0)
    tickers = dfl.symbol.values
    
    for ticker in tickers:
        ticker=ticker.strip()
        print(ticker)
        data = yf.download(ticker, group_by="Ticker", period=prd, interval=intv)
        data['ticker'] = ticker  # add this column becasue the dataframe doesn't contain a column with the ticker
        fname = DATAP / f'ticker_{ticker}.csv'
        data.to_csv(fname)  # ticker_AAPL.csv for example

def read_list(listname):
    dfl =  pd.read_csv(listname,index_col=0)
    return dfl

def read_data(listname):
    # set the path to the files
    dfl = read_list(listname)
    #files = list()
    # read the files into a dataframe
    df_list = list()
    for ticker in dfl.symbol:
        filename = DATAP / f'ticker_{ticker}.csv'
        #files.append(filename)
    
    
    # find the files
    #files = list(DATAP.glob('ticker_*.csv'))
    
    #for file in files:
        df_list.append(pd.read_csv(filename))
    
    # combine dataframes
    df = pd.concat(df_list) 
    return df

def read_single(ticker):
    
    filename = DATAP / f'ticker_{ticker}.csv'
    print('reading %s'%filename)
    df = pd.read_csv(filename,index_col=0)
    return df
    
    


if __name__ =='__main__':
    listname = 'extra.csv'
    update_data(listname)
    df = read_data(listname)
    