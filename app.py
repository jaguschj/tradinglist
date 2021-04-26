#import plotly.express as px
import os
import fnmatch
#import json
import plotly.graph_objects as go

#import plotly.io as pio
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from dash.dependencies import Input, Output, State

from dash_table.Format import Format, Scheme

import base64

from IPython.display import display, HTML




#import numpy as np
import pandas as pd

#app = dash.Dash(external_stylesheets=[dbc.themes.MINTY])
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#external_stylesheets=[dbc.themes.GRID]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

platform=os.getenv('app_env','productive')
if platform == 'productive':
    srcfolder = '/home/jens/src/tradinglist'

else:
    (srcfolder,selffile)=os.path.split(os.path.abspath(__file__))
plotfolder = os.path.join(srcfolder,'plots')
listfolder = plotfolder
print('working  %s'%platform)
print('working in %s'%listfolder)

#plotfolder = 'plots'
#listfolder = 'plots'

def highlight(s):
    if s.sell > 0:
        return ['background-color: red']*14
    if s.buy > 0:
        return ['background-color: lightgreen']*14
    if s.dist2ind <0.05:
      if s.close < s.indicator:
          return ['background-color: lightblue']*14
      elif s.close > s.indicator:
          return ['background-color: yellow']*14
    else:
        if s.name % 2 :
          return ['background-color: white']*14
        else:
          return ['background-color: lightgrey']*14


#df_sort.style.format({'url': make_clickable})

def table_out(filename):
    
      df_sort = pd.read_csv(filename,index_col=0)
      # display.HTML()
      return  display(HTML(display(df_sort.style.apply(highlight, axis=1))))


def get_list_files(folder):
    options=[]
    for file in os.listdir(folder):
        if fnmatch.fnmatch(file, '*list.csv'):
            options.append({'label':file, 'value':os.path.join(folder,file)})    
    return options

options=get_list_files(listfolder)
if options:
    value=options[0]['value']
else:
    value=''

list_selector = [ html.H5("List Selector"),
                  dcc.Dropdown(id='list_selector',
                        options=options,
                        value=value
                        )
                 ]

tabs_div=[ dcc.Tabs(id='tabs-example', value='tab-1', children=[
                    dcc.Tab(label='Trading List', value='tab-1'),
                    dcc.Tab(label='Charts', value='tab-2',
                            children=[html.Div(id='plot-picture')]),
                    dcc.Tab(label='Plot List', value='tab-3',
                            #children=[html.Div(className='row',
                                    children=[dbc.Row([
                                    dbc.Col([
                                        html.Div(id='basic-interactions',className='three columns')
                                        #dcc.Graph(id='basic-interactions')#,figure=None)
                                        ],
    style={'width': '30vH', 'float': 'right'},
                                    #width=dict(size=3,order='last'),
                                    align='end'
                                    ), 
                                    #dbc.Col([html.Div(id='hover-data',#children=[],
#    style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'middle'},
    #style={'width': True,'margin-right': '500px', 'margin':'200px','float': 'right'},
    #width=dict(size=9,order=1)
                                            #),
                                ])]#,align='end'
                            #)]
                            )
                    #]),
               ])]

app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Trading Assets Overview"),
                html.H5("Jens Jagusch"),
            ], width=True),
            # dbc.Col([
            #     html.Img(src="assets/MIT-logo-red-gray-72x38.svg", alt="MIT Logo", height="30px"),
            # ], width=1)
        ], align="end"),
        html.Hr(),
        dbc.Row( [dbc.Col(
        
            [html.Div(list_selector),
                  html.Div(id='dd-output-container'),
                   html.Div(tabs_div),
                   html.Div(id='tabs-example-content'),
                  ]),
                
#        dbc.Col([
#                #    dcc.Link(id='link',pathname='posts/results_AAPL.png')
#                #    
#                html.Div(className='row', children=[
#                    
#            html.Pre(id='hover-datax',style=styles['pre'],children=[
#            dcc.Markdown(("""
#              Click on points in the graph.
#            """))
#            ]),
#             ])
#            ])
                          
            #html.Pre(id='hover-data', style=styles['pre'],
            #className='three columns'),
            ]),

    html.Hr(),
    ],
    fluid=True
    )


def set_color(buy,sell,dist2ind,indicator,close):
    #colors = ['lime','orangered',',''']
    if buy >0:
        return 'lime'
    if sell>0:
        return 'orangered'
    if dist2ind < 0.05:
        if indicator>close:
            return 'lightcyan'
        if indicator < close:
            return 'mistyrose'
    return 'wheat'

def plot_table(filename):
    folder = 'plots'
    df = pd.read_csv(filename,index_col=0)
    dfn = df.rename(columns={'symbol':'Symbol','name':'Company','multiplier':'f','period':'p',
               'ret':'Return','drawd':'Drawdown','shaper':'Sharperatio',
               'value':'asset','url':'Chart','dist2ind':'d2i'})
    dfr = dfn.round({'f':1,'Return':2,'Drawdown':2,'Sharperatio':2,
                   'asset':1,'indicator':2,'close':2,'d2i':3})
    #dfr.Chart = dfr.Chart.map(lambda x: '[%s](<http://localhost:8000/%s>)'%(x,x))
    dfr['color']=dfr.apply(lambda x: set_color(x.buy,x.sell,x.d2i,x.indicator,x.close),axis=1)
    dfr = dfr.iloc[::-1]

    layout = go.Layout(
        xaxis=dict(range=[-10, 50]),
        height=1000,
        width = 400)

    fig = go.Figure(data=[go.Bar(y=dfr.Company,
                                 x=dfr.Return,
                                 marker=dict(color=dfr.color),
                                 text = dfr.Company,
                                 hovertemplate=
                                        "<b>%{text}</b><br><br>" +
                                        "%{customdata[0]}<br>" +
                                        "Sharpe: %{customdata[1]:.3f}<br>" +
                                        "Return: %{x:.3f}<br>" +
                                        "ind: %{customdata[2]:.2f}<br>" +
                                        "d2i: %{customdata[4]}<br>" +
                                        "close: %{customdata[3]:.2f}<br>" +
                                        "<extra>Drawdown: %{customdata[5]}</extra>",
                                 customdata=dfr[['Symbol','Sharperatio','indicator','close','d2i','Drawdown']], # hover text goes here))))
                                 #name = 'returns'
                                 orientation='h'
                                 )],
                        layout=layout)
    #return html.Div([dcc.Graph(id='basic-interactions',figure=fig)])
    return html.Div(children=[html.Div(dcc.Graph(id='basic-interactions',figure=fig),
                              className='three columns'),
                            html.Div(id='hover-data',
                                     className='nine columns',
                                     style={'margin-top':'200px'})])
    #return fig
    

def show_picture(filename):
    pass

def b64_image(image_filename):
    with open(image_filename, 'rb') as f: image = f.read() 
    return 'data:image/png;base64,' + base64.b64encode(image).decode('utf-8')

def make_table(dataframe):
    return dbc.Table.from_dataframe(
        dataframe,
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        style={

        }
    )

def parse_table(filename):
    folder,fname = os.path.split(filename)
    
    df = pd.read_csv(filename,index_col=0)
    dfn = df.rename(columns={'symbol':'Symbol','name':'Company','multiplier':'f','period':'p',
               'ret':'Return','drawd':'Drawdown','shaper':'Sharperatio',
               'value':'asset','url':'Chart','dist2ind':'d2i'})
    dfr = dfn.round({'f':1,'Return':2,'Drawdown':2,'Sharperatio':2,
                   'asset':1,'indicator':2,'close':2,'d2i':3})
    dfr.Chart = dfr.Chart.map(lambda x: '[%s](<http://localhost:8000/%s>)'%(x,x))
#    dfr.Chart = dfr.Chart.map(lambda x: '[%s](<%s>)'%(x,x))
    #dfr.Chart=dfr.Chart.apply(HTML)
    #print(dfn.columns)
    style_cell_conditional=[
        {
            'if': {'column_id': c},
            'textAlign': 'left'} for c in ['Symbol', 'Company']]
    style_cell_conditional.append({
            'if': {'column_id': 'asset'},
            'format':Format(precision=1)
            }
        )
    
    #style_cell_conditional.append([{
    #        'if': {'column_id': c},
    #        'type': 'numeric',
    #        'format':'money'
    #        } for c in ['indicator', 'close']
    #    ]
    #    )
    
    style_data_conditional=[      
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'
        },
        {   'if': {'filter_query': '{sell} = 1.0'},
            'backgroundColor': 'orangered',
            'color': 'white'
            },
        {   'if': {'filter_query': '{buy} = 1.0'},
            'backgroundColor': 'lime',
            'color': 'black'
            },
        {   'if': {'filter_query': '{d2i} < 0.05 and {close} > {indicator}'},
            'backgroundColor': 'mistyrose',
            'color': 'black'
            },
        {   'if': {'filter_query': '{d2i} < 0.05 and {close} < {indicator}'},
            'backgroundColor': 'lightcyan',
            'color': 'black'
            },
        ]

    
    #columns=[{'name': i, 'id': i} for i in dfr.columns],
    #for c in columns:
    #    if c['name'] in 
    #columns=[
    #    
    #    dict(id='Return', name='Return', type='numeric', format=Format(precision=2)),
    #    ]
    columns = [{'name': i, 'id': i} for i in dfr.columns[:-1]]
    #columns[-1] = {'name': 'Chart','id':'Chart','type':'text','presentation':'markdown'}
    return   html.Div([
            html.H3('%s'%fname),        
            dash_table.DataTable(  
                data=dfr.to_dict('records'),
                columns=columns,            
                style_cell_conditional=style_cell_conditional,
                style_data_conditional=style_data_conditional,
                style_header={
        'backgroundColor': 'rgb(230, 230, 230)',
        'fontWeight': 'bold'
                            },
                css=[
            #
            dict(selector='td table', rule='font-size: 20px;'),
            dict(selector='td[data-dash-column="Chart"] table', rule='font-family: cursive;'),
            ]
                #hover=True
            )])

def hwrite(mytab):
    print(type(mytab))
    #tdict = json.encoder.
    #json.
    #tj = json.
    with open('html.txt','w') as fh:
       fh.write((str(mytab)))
    #pio.write_html(tdict,file= 'html.txt')
    
#@app.callback(Output('plot-picture','children'),
#                Input())
#def render_picture(linkname):
#    return html.Div(html.Img(id= 'myplot', src='plots/result_AAL.png'))
    

@app.callback(Output('tabs-example-content', 'children'),
              [Input('tabs-example', 'value'),
              Input('list_selector', 'value')])
def render_content(tab,listname):
    if tab == 'tab-1':
        output=parse_table(listname)
        #hwrite(output)
        return [output]
        
    elif tab == 'tab-2':
        image_filename='plots/result_AAL.png'
        return html.Div([ html.Img(src=b64_image(image_filename),width="1200")])
    elif tab == 'tab-3':
        return plot_table(listname)
                    
@app.callback(
    Output('hover-data', 'children'),
    [Input('basic-interactions', 'hoverData')])
def display_hover_data(hoverData):
    if hoverData is None:
        return []#html.Div()
    #print (hoverData)
    #mydir = os.getcwd()
    symb = hoverData['points'][0]['customdata'][0]
    image_filename = os.path.join(plotfolder,r'result_%s.png'%symb)
    #image_filename = r'plots\result_%s.png'%symb
    if not os.path.exists(image_filename):
        return html.Div('%s does not exist'%image_filename)
    #with open(image_filename, 'rb') as f: image = f.read() 
    #return 'data:image/png;base64,' + base64.b64encode(image).decode('utf-8')
    #return html.Div([html.Img(src=b64_image(image_filename),width="1000")])
    return [html.Img(src=b64_image(image_filename),width="1000")]
    #return image_filename
    #return html.Iframe(<iframe width="640" height="480" frameborder="0" seamless="seamless" scrolling="no" src="https://plot.ly/~Dreamshot/411.embed?width=640&height=480" ></iframe>
    
    #return 

    #return json.dumps(hoverData, indent=2)
                    
              
# =============================================================================
# 
# @app.callback(
#     [Output('display', 'children')],
#     [Input('list_selector', 'value')])
# def display_table(value):
#     
#     output=parse_table(value)
#     hwrite(output)
#     #output =table_out(value) 
#     #return [table_out(value),output]
#     return [output]
# 
# =============================================================================

try:  # wrapping this, since a forum post said it may be deprecated at some point.
    app.title = "Trading Lister"
except:
    print("Could not set the page title!")

    
if __name__=='__main__':
    
    app.run_server(debug=True)
else:
    server = app.server
    
