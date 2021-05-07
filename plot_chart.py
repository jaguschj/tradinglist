# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 15:53:47 2021

@author: JensJ
"""
import os
import fnmatch
import pandas as pd

#import pandas_ta as ta
#import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from pathlib import Path

#import mng_data
rundir,sourcefile=os.path.split(__file__)
p = Path(rundir)
DATAP = p / 'data'




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
        df_list.append(pd.read_csv(filename,index_col=0,parse_dates=True))
    
    # combine dataframes
    df = pd.concat(df_list) 
    return df

def read_single(ticker):
    
    filename = DATAP / f'ticker_{ticker}.csv'
    print('reading %s'%filename)
    df = pd.read_csv(filename,index_col=0,parse_dates=True)
    return df
    


def atr(df,period,drift=1):
    df['pclose']=df.Close.shift(1)
    df['thigh']= df['High'].where(df['High']>df['pclose'],df['pclose'])
    df['tlow']= df['Low'].where(df['Low']<df['pclose'],df['pclose'])
    
    y = df['thigh']-df['tlow']
    df['atr'] = y.rolling(period,center=False).mean()
    df['tmid'] = (df['thigh']+df['tlow'])*0.5
    #df['tmid'] = (df['High']+df['Low'])*0.5
    #df['atr']=ta.atr(df.High,df.Low,df.Close,length=period).copy()
    #df.apply(lambda x: ta.atr(x.High,x.Low,x.Close,length=period))
    return df

def supertrend_bands(df,period=5,multiplier=2.2,drift=1):
    df = atr(df,period,drift)
    delta = df.atr*multiplier
    #df['mid'] = (df.High+df.Low)*0.5
    df['bu']= df.tmid+delta
    df['bl']= df.tmid-delta
    return df

def spt_(df):
    df.dropna(inplace=True)
    df['tr'] = -1
    df['fu'] = df['bu'].copy()
    df['fl'] = df['bl'].copy()
    # warning due to value setting on a slice
    for irow in range(1,len(df)):
        im1 = irow - 1
        if df.tr.iloc[im1] > 0: # up
            if df.Close.iloc[irow] < df.fl.iloc[im1]: # change trend
                df.fu.iloc[irow] = min(df.fu.iloc[im1],df.bu.iloc[irow])
                #df.fl.iloc[irow] = df.bl.iloc[irow]
                df.tr.iloc[irow] = -1
            else:
                #df.fu.iloc[irow] = df.bu.iloc[irow]
                df.fl.iloc[irow] = max(df.fl.iloc[im1],df.bl.iloc[irow])
                df.tr.iloc[irow] = 1
        if df.tr.iloc[im1] < 0:  # down
            if df.Close.iloc[irow] < df.fu.iloc[im1]:
                df.fu.iloc[irow] = min(df.fu.iloc[im1],df.bu.iloc[irow])
                #df.fl.iloc[irow] = df.bl.iloc[irow]
                df.tr.iloc[irow] = -1
            else:               # change trend
                #df.fu.iloc[irow] = df.bu.iloc[irow]
                df.fl.iloc[irow] = max(df.fl.iloc[im1],df.bl.iloc[irow])
                df.tr.iloc[irow] = 1
    df['supertrend']=df['fu'].where((df['tr']>0),df.fl)#.copy()
    df['spt_u']=df['fu'].where((df['tr']>0),None)#.copy()
    df['spt_l']=df['fl'].where((df['tr']<0),None)#.copy()
    return df

def supertrend(df,period=5,multiplier=2.3,drift=1):
    
    df = supertrend_bands(df,period=period,multiplier=multiplier,drift=drift)
    dfst = spt_(df)
    dfst['group'] = dfst['tr'].ne(dfst['tr'].shift()).cumsum()
    dfg = dfst.groupby('group')
    dfs = []
    for name, data in dfg:
        dfs.append(data)
    return dfst
    


def longshort_periods(df,keycol='tr'):
    # create list of dataframes split by change in keycol
    df['group'] = df[keycol].ne(df[keycol].shift()).cumsum()
    df = df.groupby('group')
    dfs = []
    for name, data in df:
        dfs.append(data)
    return dfs

        

def traces_long_short(dfs):
    # add traces with periods of long/short
    last_set = dfs[-1].iloc[-2:-1]
    traces=[go.Scatter(x=last_set.index, y = last_set.Close,
                              line = dict(color='rgba(0,0,0,0)'),
                              name = 'trend',
                              legendgroup='trend',
                              showlegend=True,
                              visible='legendonly',
                              )
                      ]
    for df in dfs:
        profitloss = df.Close.iloc[-1]-df.Open.iloc[0]

        traces.append(go.Scatter(x=df.index, y = df.Close,
                              line = dict(color='rgba(0,0,0,0)'),
                              name = 'close',
                              legendgroup='trend',
                              visible='legendonly',                              
                              showlegend=False)
                      )
        if df.tr.iloc[0]>0: # long
            if profitloss>0:
                color = 'rgba(0.,0.99,0,0.2)'
                width = 0
            else:
                color = 'rgba(0.,0.2,0.7,0.2)'
                width = 4
            traces.append(go.Scatter(x=df.index, y = df.fl,
                              line = dict(color=color,width=width),
                              name = 'up',
                              fill='tonexty', 
                              fillcolor = color,
                              visible='legendonly',
                              legendgroup='trend',
                              showlegend=False)
                          )
        else:  # short
            if profitloss<0:
                color = 'rgba(0.99,0.0,0,0.2)'
                width = 0
            else:
                color = 'rgba(0.5,0.,0.5,0.2)'
                width = 4
            traces.append(go.Scatter(x=df.index, y = df.fu,
                              line = dict(color=color,width=width),
                              name='down',
                              fill='tonexty', 
                              fillcolor = color,
                              visible='legendonly',
                              legendgroup='trend',                              
                              showlegend=False)
                       )
    return traces

def traces_profit(dfs):
    traces=[]
    # add traces with periods of long/short
    xix = [0,-1,-1]
    yix = [0,0,-1]
    
    plong=0
    pshort=0
    for df in dfs:
        profitloss = df.Close.iloc[-1]-df.Open.iloc[0]
        
        
        x = df.iloc[xix].index
        y = df.iloc[yix].Close
        traces.append(go.Scatter(x=df.index, y = df.Close,
                              line = dict(color='rgba(0,0,0,0)'),
                              name = 'close',
                              legendgroup='profit',
                              showlegend=False)
                      )
        if df.tr.iloc[0]>0: # long
            plong+=profitloss
            if profitloss>0:
                color = 'rgba(0.,0.99,0,0.2)'
                width = 0
            else:
                color = 'rgba(0.,0.2,0.7,0.2)'
                width = 4
            traces.append(go.Scatter(x=x, y = y,
                              line = dict(color=color,width=width),
                              name = 'up',
                              fill='tonexty', 
                              fillcolor = color,
                              legendgroup='profit',
                              showlegend=False)
                          )
        else:  # short
            pshort+=profitloss
            if profitloss<0:
                color = 'rgba(0.99,0.0,0,0.2)'
                width = 0
            else:
                color = 'rgba(0.5,0.,0.5,0.2)'
                width = 4
            traces.append(go.Scatter(x=x, y = y,
                              line = dict(color=color,width=width),
                              name='down',
                              fill='tonexty', 
                              fillcolor = color,
                              legendgroup='profit',                              
                              showlegend=False)
                       )
    first_set = dfs[1].iloc[:1]
    last_set = dfs[-1].iloc[-2:-1]
    initialvalue = first_set.iloc[0].Close
    try:
        finalvalue = last_set.iloc[-1].Close
        holdtime = (last_set.index-first_set.index).days[0]/365
    except:
        print(first_set)
        print(last_set)
        finalvalue = dfs[-2].iloc[-1].Close
        holdtime = 4.

    #holdvalue = abs(finalvalue-initialvalue)

    hold_rent = ((finalvalue/initialvalue)**(1/holdtime)-1)*100
    long_rent = ((plong/initialvalue+1)**(1/holdtime)-1)*100
    short_rent = ((-pshort/initialvalue+1)**(1/holdtime)-1)*100
    traces.append(go.Scatter(x=last_set.index, y = last_set.Close,
                              line = dict(color='rgba(0,0,0,0)'),
                              name = 'profit',
                              legendgroup='profit',
                              showlegend=True)
                      )
            
    return traces,(hold_rent,long_rent,short_rent)
    
    

def SetColor(x):
    if(x < 0):
        return "green"
    elif(x == 0 ):
        return "yellow"
    elif(x > 0):
        return "red"
    

def plot_share(share_name,data,period=5,multiplier=2.3,tildate=None,volatility=0,log=False):
    '''
    

    Parameters
    ----------
    share_name : TYPE string
        Name of share.
    data :DataFrame
        share data with Date, rdate and Close.
    tildate : date
        do plot until that date
    volatility: float
        plot lines for that value
    Returns
    -------
    None.

    '''

    avg=40
    #ix_last_date=data['revDate'].idxmax()
    #dtil=(tildate-data['revDate'].max()).days
    #print (data.revDate)
    #print(type(tildate   ))
    #opt_dates=data.revDate
    
    y=data['Close']
    #latest_close=y.loc[data['Date'].idxmax()]
    data_avg=y.rolling(avg,center=False).mean()
    
    #sb = supertrend_bands(data)
    st = supertrend(data,period=period,multiplier=multiplier)
    
    # volatility: 
    #https://stackoverflow.com/questions/43284304/how-to-compute-volatility-standard-deviation-in-rolling-window-in-pandas
    y_vola=y.pct_change().rolling(avg).std()*(252**0.5)
    
    
    fig = make_subplots(rows=2,cols=1,
                        subplot_titles=[share_name,'Volatility'],
                        row_heights=[0.8,0.2],
                        shared_xaxes=True,
                        specs=[[{"secondary_y": True}],[{"secondary_y": False}]]
                        )
    
    fig.add_trace(go.Candlestick(x=data.index,#['Date'],
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name = 'OHLC',
                ),                  
                  row=1,col=1,
                secondary_y=True)
    fig.update_layout(xaxis_rangeslider_visible=False)    
    dfs = longshort_periods(st,'tr')
    straces = traces_long_short(dfs)
    for trace in straces:
        fig.add_trace(trace,row=1,col=1,secondary_y=True)
    ptraces,(hrent,lrent,srent) = traces_profit(dfs)
    for trace in ptraces:
        fig.add_trace(trace,row=1,col=1,secondary_y=True)
        

    # include a go.Bar trace for volumes
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'],
                         name='Volume',
                         marker_color='rgb(158,202,225)'),
                  row=1,col=1,
               secondary_y=False)
    # add subplot
    fig.add_trace(go.Scatter(x=y_vola.index, 
                    y=y_vola,
                    name='Volatility',
                    line = dict(color='orange',width=2),
                  fill='tozeroy',
                      ),
                  row=2,col=1,
                  )
# =============================================================================
    fig.layout.yaxis.range=[data.Volume.min(),data.Volume.max()*2]#,row=1,col=1
    fig.layout.yaxis2.showgrid=False
    if log:
        fig.update_yaxes(title_text="y-axis in logarithmic scale", type="log", row=1, col=1)
        fig.layout.yaxis2.type='log'#update_yaxes2(title_text="y-axis in logarithmic scale", type="log", row=1, col=2)
    #fig.show()
    
    # fig.add_trace(go.Scatter(x=[opt_dates.min(),opt_dates.max()],
    #                 y=[(1+volatility)*latest_close,(1+volatility)*latest_close],
    #                 mode='lines',
    #                 name='vola %.2f'%volatility) )
    # fig.add_trace(go.Scatter(x=[opt_dates.min(),opt_dates.max()],
    #                 y=[(1-volatility)*latest_close,(1-volatility)*latest_close],
    #                 mode='lines',
    #                 name='vola %.2f'%volatility) )
    
    lastdate = data.index[-1]
    volatility = y_vola[lastdate]*100
    #lastdate = ' 30.04.21' #data.index.iloc[-1].str
    tabs = '\t'*2
    title =  lastdate.strftime('%d.%m.%y')
    title += tabs+'Price %.2f'%data.Close.iloc[-1]
    title += tabs + 'Volatility %.2f'%volatility
    title += tabs + 'period,factor (%d, %.1f)'%(period,multiplier)
    title += '\trent %% p.a. (hold: %.1f, long: %.1f, short: %.1f)'%(hrent,lrent,srent)
    #title += tabs + '%s'%share_name
    fig.update_layout(title=title,
    #,width=1500,
    height=1200)
    
    fig.update_xaxes(showgrid=True)
    platform=os.getenv('app_env','productive')
    if platform !='productive':
        fig.write_html('%s.html'%(share_name))
    #fig.show()
    return fig


if __name__=='__main__':
    today=datetime.today()
    symbol='BAS.DE'
    #filename = symbol+'x.csv'
    
    listname = 'Dax.csv'
    dfl = pd.read_csv(listname,index_col=0)
    #symbol = dfl.symbol.iloc[4]
    print(symbol)
    df = read_data(listname)
    sharename=dfl['name'].loc[dfl.symbol==symbol].values[0]
    history = df[df['ticker']==symbol].copy()
    
    #history.set_index('Date',inplace=True)
# =============================================================================
# 
#     if os.path.exists(filename):
#         #history=pd.read_csv(filename)
#         sharename = filename[:-5]
#         history = pd.read_csv(filename,index_col=0)
#     else:
#         ticker = get_ticker(symbol)    
#         history=ticker.history(period='2y')
#         dividends=ticker.dividends
#         dividends.to_csv(filename[:-5]+'_div.csv')
#         history.to_csv(filename)
#         sharename = ticker.info['shortName']
# =============================================================================
    history = read_single(symbol)
    fig = plot_share(sharename,history,tildate=today)
    fig.show()
    
    
    