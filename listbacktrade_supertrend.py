# -*- coding: utf-8 -*-
"""ListBacktrade_supertrend.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15QhyH5gHB8S8jX_Ku6-HrCtHMSGGV-kt
"""

#!pip install backtrader # -e git+https://github.com/jaguschj/backtrader.git

#pip install pivottablejs
#!pip install ipywidgets
#!pip install ipysheet

#!pip install plotly

import os
#import plotly.express as px

#import numpy as np
import pandas as pd
from datetime import datetime,timedelta,date
import backtrader as bt
from supertrend import SuperTrendStrategy
from cash_sizer import CashSizer
#import matplotlib.pyplot as plt
#from google.colab import files
#from IPython.display import Image
#from IPython.display import FileLink, FileLinks

#from pivottablejs import pivot_ui
#from IPython.display import HTML
#from ipysheet import from_dataframe
import argparse


pd.set_option('display.max_rows', 100)

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline


#from google.colab import drive
#drive.mount('/content/drive')

rundir = os.getcwd()
DIR=os.path.join(rundir,'plots')
if not os.path.exists(DIR):
    os.mkdir(DIR) 

#from bt.strategies import SuperTrendStrategy
#from bt.sizers import CashSizer


def run_st(symb='DTE.DE',period=7,multiplier=3.5,backyears=2):
  #symbol=dbset['symbol']
  #period = int(dbset['period']+0.5)
  #multiplier = dbset['multiplier']
  today=datetime.today()
  fromdate = today - timedelta(days=int(backyears*252))
  cerebro = bt.Cerebro()
  cerebro.addstrategy(SuperTrendStrategy,period=period, multiplier=multiplier)

  data0 = bt.feeds.YahooFinanceData(dataname=symb, fromdate=fromdate,
                                    todate=today)
  cerebro.adddata(data0)
  cerebro.broker.setcash(100000.0)

  # Add a FixedSize sizer according to the stake
  #cerebro.addsizer(bt.sizers.FixedSize, stake=10)
  #cerebro.addsizer(bt.sizers.FixedSize, stake=200)
  #cerebro.addsizer(bt.sizers.FixedReverser, stake=500)
  #cerebro.addsizer(bt.sizers.PercentSizerInt, percents=90)
  #cerebro.addsizer(bt.sizers.PercentSizer, percents = 90)
  #cerebro.addsizer(bt.sizers.AllInSizerInt)
  cerebro.addsizer(CashSizer,cash_invest=50000)

  cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name = "sharpe")
  cerebro.addanalyzer(bt.analyzers.DrawDown, _name = "drawdown")
  cerebro.addanalyzer(bt.analyzers.Returns, _name = "returns")

  # Set the commission
  cerebro.broker.setcommission(commission=0.005)


  back = cerebro.run()
  #cerebro.plot()
  #plt.show()
  chart_file = os.path.join(DIR,'result_%s.png'%symb)
  #chart_file = 'result_%s.png'%symb
  cerebro.plot()[0][0].savefig(chart_file, dpi=300)
  #Image(open(chart_file, 'rb').read())
  #cerebro.plot(width=42,height=30)[0]
  total = back[0].broker.get_value()
  cash  = back[0].broker.get_cash()
  #asset = 1
  print(symb)
  #print(back[0].analyzers.getnames())
  rt=back[0].analyzers.returns.get_analysis()['rnorm100']
  dd=back[0].analyzers.drawdown.get_analysis()['max']['drawdown']
  sr=back[0].analyzers.sharpe.get_analysis()['sharperatio']
  print ('Return: %.2f Drawdown: %.2f Sharperatio: %.2f'%(rt,dd,sr))
  print ('cash',cash,'total',total)
  spt_ind,buysig,sellsig=back[0].getindicators_lines()
  price = data0.lines[7].array # adj close?
  close,spt,buy,sell=(price[-1],spt_ind.array[-1],buysig.array[-1], sellsig.array[-1])
  lastdate=data0.datetime.date()
  print(lastdate)
  
  dist_tosig = (close-spt)/spt
  if (close<spt): # down trend
    dist_tosig=-dist_tosig
  return (rt,dd,sr,total,buy,sell,spt,dist_tosig,close,chart_file,lastdate)

#################################### basic  #######
def make_clickable(val):
    # target _blank to open new window
    #filename = val.split('result_')[-1]
    
    #return 'html.A(html.P({},href={},target="_blank"'.format(val, val)
    return val


def create_list(symdf):
  db_bestfit=[]
  multiplier=3
  period = 12

  for index,row in symdf.iloc[:].iterrows():
    print(row)
    symb=row.symbol
    name=row['name']
    print(name)
    try:
        rt,dd,sr,value,buy,sell,spt,dist_tosig,close,chart,lastdate = run_st(symb=symb, period=period, multiplier=multiplier)
        dbset=dict(symbol=symb,name=name,multiplier=multiplier,period=period,ret=rt,drawd=dd,shaper=sr,value=value,
               buy=buy,sell=sell,indicator=spt,dist2ind=dist_tosig,close=close,cdate=lastdate,url=make_clickable(chart))
        db_bestfit.append(dbset)
    except:
        print('Error in backtrading on %s'%symb)
        
  db_df = pd.DataFrame(db_bestfit)
  return db_df


# create table

# make nice table output

def run(symbolsfile):    
    
    symbolsfilebase=os.path.basename(symbolsfile)
    #df_sort.style.format({'url': make_clickable})
    collect={'Liste_jj.csv':None,'nasdaq.csv':0,'nyse.csv':0,'Dax.csv':0}
    #collect={'nasdaq.csv':0,'nyse.csv':0}
    assert symbolsfilebase in collect.keys()
    
    rescollect=[]
    #for symfile,index_col in collect.items():
    index_col=collect[symbolsfilebase]
    symdf = pd.read_csv(symbolsfile,index_col=index_col)
    symdf.symbol=symdf.symbol.apply(lambda x: x.lstrip().rstrip())
    symbols = symdf.symbol.iloc[:]
    symbols.iloc[0]
    db_df = create_list(symdf)
    df_sort=db_df.sort_values(by='shaper',ascending=False)  
    df_sort.reset_index(drop=True,inplace=True) 
    symfile_list = symbolsfile[:-4]+'list.csv'
    rescollect.append(symfile_list)
    filename = os.path.join(DIR,symfile_list)
    df_sort.to_csv(filename)
    

def highlight(s):
    if s.sell > 0:
        return ['background-color: red']*len(s)
    if s.buy > 0:
        return ['background-color: lightgreen']*len(s)
    if s.dist2ind <0.05:
      if s.close < s.indicator:
          return ['background-color: lightblue']*len(s)
      elif s.close > s.indicator:
          return ['background-color: yellow']*len(s)
    else:
        if s.name % 2 :
          return ['background-color: white']*len(s)
        else:
          return ['background-color: lightgrey']*len(s)

def format_row_wise(styler, formatter):
    for row, row_formatter in formatter.items():
        row_num = styler.index.get_loc(row)

        for col_num in range(len(styler.columns)):
            styler._display_funcs[(row_num, col_num)] = row_formatter
    return styler

def list2HTML(filename):
    
      #filename = os.path.join(DIR,file)
      df_sort = pd.read_csv(filename,index_col=0)
      #out=HTML(df_sort.style.apply(highlight, axis=1))
      df_sort.to_html('abc.html',formatters=[highlight]*14)
      return 

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='run through lists',
    )

    parser.add_argument('--listname', default='DAX.csv', type=str,
                        help='List out of ')

    args = parser.parse_args()

    run(args.listname) 
    #filename='plots\Liste_jjlist.csv'
    #list2HTML(filename)
    
    
        
    
    
    
