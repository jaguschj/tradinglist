# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 15:53:47 2021

@author: JensJ
"""
import os
import fnmatch
import pandas as pd

import pandas_ta as ta
#import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime


def atr(df,period,drift=1):
    df['atr']=ta.atr(df.High,df.Low,df.Close,length=period)
    #df.apply(lambda x: ta.atr(x.High,x.Low,x.Close,length=period))
    return df

def supertrend_bands(df,period=5,multiplier=2.2,drift=1):
    df = atr(df,period,drift)
    delta = df.atr*multiplier
    df['mid'] = (df.High+df.Low)*0.5
    df['bu']= df.mid+delta
    df['bl']= df.mid-delta
    return df

def spt_(df):
    df.dropna(inplace=True)
    df['tr'] = -1
    df['fu'] = df['bu'].copy()
    df['fl'] = df['bl'].copy()
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
    df['supertrend']=df['fu'].where((df['tr']>0),df.fl)
    df['spt_u']=df['fu'].where((df['tr']>0),None)
    df['spt_l']=df['fl'].where((df['tr']<0),None)
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
    
def get_ticker(symbol):
    
    print(">>", symbol, end=' ... ')
    try:
        ticker = yf.Ticker(symbol)    
    
    # always should have info and history for valid symbols
        assert(ticker.info is not None and ticker.info != {})
        assert(ticker.history(period="max").empty is False)

        # following should always gracefully handled, no crashes
        ticker.cashflow
        ticker.balance_sheet
        ticker.financials
        ticker.sustainability
        ticker.major_holders
        ticker.institutional_holders

        print("OK")
    except:
        print('Problem')
    return  ticker


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
    traces=[go.Scatter(x=None, y = None,
                              line = dict(color='rgba(0,0,0,0)'),
                              name = 'trend',
                              legendgroup='trend',
                              showlegend=True)
                      ]
    for df in dfs:
        profitloss = df.Close.iloc[-1]-df.Open.iloc[0]

        traces.append(go.Scatter(x=df.index, y = df.Close,
                              line = dict(color='rgba(0,0,0,0)'),
                              name = 'close',
                              legendgroup='trend',
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
                              legendgroup='trend',                              
                              showlegend=False)
                       )
    return traces
    
    

def SetColor(x):
    if(x < 0):
        return "green"
    elif(x == 0 ):
        return "yellow"
    elif(x > 0):
        return "red"
    

def plot_share(share_name,data,tildate=None,volatility=0,log=False):
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
    
    sb = supertrend_bands(data)
    st = supertrend(data)
    
    # volatility: 
    #https://stackoverflow.com/questions/43284304/how-to-compute-volatility-standard-deviation-in-rolling-window-in-pandas
    y_vola=y.pct_change().rolling(avg).std()*(252**0.5)
    
    
    fig = make_subplots(rows=2,cols=1,
                        subplot_titles=['Chart','Volatility'],
                        row_heights=[0.8,0.2],
                        shared_xaxes=True,
                        specs=[[{"secondary_y": True}],[{"secondary_y": False}]]
                        )
    
    fig.add_trace(go.Candlestick(x=data.index,#['Date'],
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name = 'OHLC'),
                  row=1,col=1,
                secondary_y=True)
    dfs = longshort_periods(st,'tr')
    straces = traces_long_short(dfs)
    for trace in straces:
        fig.add_trace(trace,row=1,col=1,secondary_y=True)
    # fig.add_trace(go.Scatter(x=st.index, y=st.supertrend,
    #                      name='super trend',
    #                      #line = dict(color=list(map(SetColor, st.tr)))
    #                      line_color='green',
    #                      ), 
    #               row=1,col=1,
    #            secondary_y=True)
    
    # fig.add_trace(go.Scatter(x=data.index, y=data['Close'],
    #                      name='Close',
    #                      fill='tonexty',
    #                      fillcolor='rgba(0,250,0,0.4)'
    #                      #fillcolor=st.tr
    #                      ),
    #               row=1,col=1,
    #            secondary_y=True)
#    fig.add_trace(go.Scatter(x=st.index, y=st.spt_u,
#                         name='super trend',
#                         #line = dict(color=list(map(SetColor, st.tr)))
#                         line_color='red',
#                         #fill='tonexty'
#                         ), 
#                  row=1,col=1,
#               secondary_y=True)
    #fig.add_trace(go.Scatter(x=st.index, y=st.fl,
    #                     name='lower band'),
    #              row=1,col=1,
    #           secondary_y=True)

    # include a go.Bar trace for volumes
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'],
                         name='Volume'),
                  row=1,col=1,
               secondary_y=False)
    # add subplot
    fig.add_trace(go.Scatter(x=data.index, 
                    y=y_vola,
                    name='Volatility',
                  fill='tozeroy',
                      ),
                  row=2,col=1,
                  )
# =============================================================================
#     fig.add_trace(go.Scatter(x=st.index, 
#                     y=st.tr,
#                     name='Trend'),
#                   row=2,col=1,
#                   )
# =============================================================================
    fig.layout.yaxis.range=[data.Volume.min(),data.Volume.max()*2]#,row=1,col=1
    fig.layout.yaxis2.showgrid=False
    if log:
        fig.update_yaxes(title_text="y-axis in logarithmic scale", type="log", row=1, col=1)
        fig.layout.yaxis2.type='log'#update_yaxes2(title_text="y-axis in logarithmic scale", type="log", row=1, col=2)
    fig.show()
    
    # fig.add_trace(go.Scatter(x=[opt_dates.min(),opt_dates.max()],
    #                 y=[(1+volatility)*latest_close,(1+volatility)*latest_close],
    #                 mode='lines',
    #                 name='vola %.2f'%volatility) )
    # fig.add_trace(go.Scatter(x=[opt_dates.min(),opt_dates.max()],
    #                 y=[(1-volatility)*latest_close,(1-volatility)*latest_close],
    #                 mode='lines',
    #                 name='vola %.2f'%volatility) )
    
    '''
    fig.add_shape(
        # filled Rectangle
        go.layout.Shape(
            type="rect",
            x0=opt_dates.min(),
            y0=(1-volatility)*latest_close,
            x1=opt_dates.max(),
            y1=(1+volatility)*latest_close,
            line=dict(
                color="RoyalBlue",
                width=2,
            ),
            fillcolor="LightSkyBlue",
            opacity=0.3,
        ))
      '''              
    volatility = y_vola.iloc[-1]
    fig.update_layout(title='%s   Volatility: %.2f'%(share_name,volatility),
                      )
    #,width=1500,height=400)
    
    fig.update_xaxes(showgrid=True)
    #fig.write_html('%s.html'%(share_name))
    #fig.show()
    return fig


if __name__=='__main__':
    today=datetime.today()
    symbol='BAS.DE'
    filename = symbol+'x.csv'
    if os.path.exists(filename):
        #history=pd.read_csv(filename)
        sharename = filename[:-5]
        history = pd.read_csv(filename,index_col=0)
    else:
        ticker = get_ticker(symbol)    
        history=ticker.history(period='2y')
        dividends=ticker.dividends
        dividends.to_csv(filename[:-5]+'_div.csv')
        history.to_csv(filename)
        sharename = ticker.info['shortName']
    plot_share(sharename,history,today).show()
    
    period=12
    dfatr=atr(history,period)
    
    
    