from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects
import dask.dataframe as dd
import pandas as pd
import datetime
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

# components
def get_country_checklist():
    return dbc.Row(
        id = 'div-country-checklist',
        children = [
            dbc.Col(dbc.Label('Selected zones:'), width = 2),
            dbc.Col(dbc.Checklist(
                id="country",
                options=['AT', 'BE', 'CH', 'CZ', 'DE', 'ES', 'FI', 'FR', 'IT', 'NL', 'NO', 'PL',  'RO', 'SE' ],
                value=  ['ES', 'NL'],
                inline=True
            )
            )
        ])


def get_daterange():
    return dbc.Row(
        id = 'div-daterange',
        children= [
            dbc.Col(dbc.Label('Start date:'), width = 2),
            dbc.Col(dcc.DatePickerSingle (
                id = 'date_start',
                display_format='Y-M-D',
                date=datetime.date(2020, 1, 1)
                ), width = 2
            ),
            dbc.Col(dbc.Label('Days:'), width = 1),
            dbc.Col(dbc.Input(
            id="date_days",
            type="number",
            debounce = False,
            value = 1,
            min = 1, max = 7,
            className="dash-bootstrap"
            ), width = 1
        )
            
        ])

# Load data -----------------------------------------------------------------
ld =    dd.read_parquet('data/load_gt60twh_2*.parquet')

dash_app = Dash(
    suppress_callback_exceptions = True,
    external_stylesheets=[dbc.themes.MATERIA]
    )

load_figure_template('MATERIA')

dash_app.layout = dbc.Container(
    [
        html.H1('Electricity Demand Dashboard'),
        html.Hr(),
        dbc.Tabs(
            id="tabs-main", active_tab='tab-about', children=[
                dbc.Tab(label='About', tab_id='tab-about'),
                dbc.Tab(label='Load',  tab_id='tab-load'),
            ]
        ),
        html.Div(id='tab-content')
    ]
)
    

@dash_app.callback(Output('tab-content', 'children'),
              Input('tabs-main', 'active_tab'))
def render_content(tab):
    if tab == 'tab-about':
        # ABOUT --------------------------------------------------------------------------------------------------------------------------
        return html.Div([
            html.H3('About'),
            html.P('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua'),
            html.P('Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.')
        ])
    elif tab == 'tab-load':
        # LOAD TIME-SERIES --------------------------------------------------------------------------------------------------------------------------
        return dbc.Container([
            get_country_checklist(),
            get_daterange(),
            dbc.Row(
                id = 'div-load-type-dropdown',
                children = [
                    dbc.Col(dbc.Label('Plot type:'), width = 2),
                    dbc.Col(dcc.Dropdown(
                        id = 'load-type-dropdown',
                        clearable = False,
                        options = ['raw', 'scaled (range)',
                        'scaled (total)', 'stacked'],
                        value = 'raw'
                    ), width = 4),
                    ]),
            html.Br(),
            dcc.Graph(id="load-01"),
        ])


@dash_app.callback(
    Output("load-01", "figure"), 
    [Input("country", "value"),
     Input("date_start", "date"),
     Input("date_days", "value"),
     Input("load-type-dropdown", "value")]
    )
def update_line_chart(countries, start_date, ndays, type_plot):
    
    df = (ld[countries])
    max_total = df.max()
    start_date = pd.Timestamp(start_date).tz_localize('UTC')
    end_date = start_date + pd.Timedelta(days = int(ndays))
    
    df = df.loc[start_date:end_date].compute()
    
    if type_plot == 'raw':
        df = df.melt(ignore_index = False)
        fig = px.line(df, 
            x=df.index, 
            y="value", color='variable')
    elif type_plot == 'scaled (total)':
        df = df / max_total
        df = df.melt(ignore_index = False)
        fig = px.line(df, 
            x=df.index, 
            y="value", color='variable')
    elif type_plot == 'scaled (range)':
        df = df / df.max()
        df = df.melt(ignore_index = False)
        fig = px.line(df, 
            x=df.index, 
            y="value", color='variable')
    elif type_plot == 'stacked':
        plot = plotly.graph_objects.Figure()
        for c in countries:
            plot.add_trace(plotly.graph_objects.Scatter(
                name = c,
                x = df.index,
                y = df[c],
                stackgroup='one'
            ))
                
        fig = plot
    return fig


if __name__ == '__main__':
    dash_app.run_server(debug=True)