# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 22:34:19 2024

@author: jvilp
"""

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import plotly.express as px
import dash_ag_grid as dag
import numpy as np

import pandas as pd
from datetime import date
from modal_momentum import get_modal_momentum
from backtest_strategy import Backtest_strategy
from portfolio_universe import Portfolio_universe
from enum_class import Rebalancing_frequency, Transaction_cost, Strategy

# http://127.0.0.1:8054/

app = dash.Dash(__name__)

data_price_nasdaq = pd.read_csv("C:/Users/jvilp/OneDrive/Documents/bloom_272/Nadaq_data_PX_LAST.csv", sep=";") # Nasdaq
data_volume_nasdaq = pd.read_csv("C:/Users/jvilp/OneDrive/Documents/bloom_272/Nadaq_data_VOLUME.csv", sep=";")



data_SPX = pd.read_csv("C:/Users/jvilp/OneDrive/Documents/bloom_272/SPX_data.csv", sep=";") # S&P 500
data_SPX_price = data_SPX[data_SPX["FIELD"]=="PX_LAST"].copy()
data_SPX_volume = data_SPX[data_SPX["FIELD"]=="PX_VOLUME"].copy()
data_SPX_price = data_SPX_price.drop(columns=["FIELD"])
data_SPX_volume = data_SPX_volume.drop(columns=["FIELD"])

data_RTY = pd.read_csv("C:/Users/jvilp/OneDrive/Documents/bloom_272/RTY_data.csv", sep=";") # Russel 2000
data_RTY_price = data_RTY[data_RTY["FIELD"]=="PX_LAST"].copy()
data_RTY_volume = data_RTY[data_RTY["FIELD"]=="PX_VOLUME"].copy()
data_RTY_price = data_RTY_price.drop(columns=["FIELD"])
data_RTY_volume = data_RTY_volume.drop(columns=["FIELD"])

data_RAY = pd.read_csv("C:/Users/jvilp/OneDrive/Documents/bloom_272/RAY_data.csv", sep=";") # Russel 3000
data_RAY_price = data_RAY[data_RAY["FIELD"]=="PX_LAST"].copy()
data_RAY_volume = data_RAY[data_RAY["FIELD"]=="PX_VOLUME"].copy()
data_RAY_price = data_RAY_price.drop(columns=["FIELD"])
data_RAY_volume = data_RAY_volume.drop(columns=["FIELD"])

data_RIY = pd.read_csv("C:/Users/jvilp/OneDrive/Documents/bloom_272/RIY_data.csv", sep=";") # Russel 1000
data_RIY_price = data_RIY[data_RIY["FIELD"]=="PX_LAST"].copy()
data_RIY_volume = data_RIY[data_RIY["FIELD"]=="PX_VOLUME"].copy()
data_RIY_price = data_RIY_price.drop(columns=["FIELD"])
data_RIY_volume = data_RIY_volume.drop(columns=["FIELD"])

title_app = html.H1(children='Backtest Framework for Quantitative Strategy', style={'textAlign':'center'})

lst_field = get_modal_momentum()
field_1 = html.Div(children=lst_field[0:5], style = {"display": "flex", "gap":"1px"})
field_2 = html.Div(children=lst_field[5:10], style = {"display": "flex", "gap":"1px"})
field_3 = html.Div(children=lst_field[10:15], style = {"display": "flex", "gap":"1px"})
field_4 = html.Div(children=lst_field[15:], style = {"display": "flex", "gap":"1px"})
button_submit = html.Button("RUN BACKTEST", id="modal_submit_button", n_clicks=0, style = {'background-color': '#FFA500'})
graph_strat = dcc.Graph(id='graph_strat')
table = grid = dag.AgGrid(
    id="table_metric",
)

app.layout = html.Div([
    title_app,
    button_submit,
    field_1,
    field_2,
    field_3,
    field_4,
    graph_strat
    ])
#Output(component_id="table_metric", component_property="rowData"),

@callback(
    Output(component_id="graph_strat", component_property="figure"),
        
    Input(component_id="modal_submit_button", component_property="n_clicks"),
    
    State(component_id="field_modal_start_date", component_property="date"),
    State(component_id="field_modal_end_date", component_property="date"),
    
    State(component_id="field_modal_strategy", component_property="value"),
    State(component_id="field_modal_rebalancing", component_property="value"),
    
    State(component_id="field_modal_horizon_mom", component_property="value"),
    State(component_id="field_modal_horizon_rev", component_property="value"),
    
    State(component_id="field_modal_top_mom", component_property="value"),
    State(component_id="field_modal_down_mom", component_property="value"),
    
    State(component_id="field_modal_top_rev", component_property="value"),
    State(component_id="field_modal_down_rev", component_property="value"),
    
    State(component_id="field_modal_top_volume", component_property="value"),
    State(component_id="field_modal_down_volume", component_property="value"), 
    
    State(component_id="field_modal_constant_cost", component_property="value"), 
    State(component_id="field_modal_linear_cost", component_property="value"), 
    
    State(component_id="field_modal_benchmark", component_property="value"),
    State(component_id="field_modal_choice_data", component_property="value"),
    prevent_initial_call = True
)

def actualize_graph(nc, start_date, end_date, strategy, rebalancing, horizon_mom, horizon_rev, top_mom, down_mom, top_rev, down_rev, top_volume, down_volume, constant_fee, linear_fee, display_bench, data):
    # Portfolio Universe 
    transaction_cost = Transaction_cost.AFFINE
    if rebalancing == "Monthly":
        rebalancing_frequency = Rebalancing_frequency.MONTHLY
    elif rebalancing == "Quarterly":
        rebalancing_frequency = Rebalancing_frequency.QUARTERLY
    elif rebalancing == "Monthly":
        rebalancing_frequency = Rebalancing_frequency.YEARLY
    else:
        raise Exception("rebalancing error")
    
    portfolio_universe = Portfolio_universe(start_date, end_date, rebalancing_frequency, transaction_cost)
    portfolio_universe.transcation_cost_param(constant_fee=constant_fee, linear_fee=linear_fee)
    
    if data == "Nasdaq":        
        portfolio_universe.add_price_data(data_price_nasdaq, date_ticker='date')
        portfolio_universe.add_volume_data(data_volume_nasdaq, date_ticker='date')
    elif data == "SPX":        
        portfolio_universe.add_price_data(data_SPX_price, date_ticker='date')
        portfolio_universe.add_volume_data(data_SPX_volume, date_ticker='date')
    elif data == "Russel1000":        
        portfolio_universe.add_price_data(data_RIY_price, date_ticker='date')
        portfolio_universe.add_volume_data(data_RIY_volume, date_ticker='date')
    elif data == "Russel2000":        
        portfolio_universe.add_price_data(data_RTY_price, date_ticker='date')
        portfolio_universe.add_volume_data(data_RTY_volume, date_ticker='date')
    elif data == "Russel3000":        
        portfolio_universe.add_price_data(data_RAY_price, date_ticker='date')
        portfolio_universe.add_volume_data(data_RAY_volume, date_ticker='date')
    else:
        raise Exception("Unknown data")
   
    
    # Backtest
    if strategy == "Momentum":
        strategy = Strategy.MOMENTUM
        backtest_strategy = Backtest_strategy(portfolio_universe, strategy)
        backtest_strategy.momentum_param(nb_periods_horizon=horizon_mom, top_prct=top_mom, down_prct=down_mom)
    elif strategy == "Reversal":
        strategy = Strategy.REVERSAL
        backtest_strategy = Backtest_strategy(portfolio_universe, strategy)
        backtest_strategy.reversal_param(nb_periods_horizon=horizon_rev, top_prct=top_rev, down_prct=down_rev)
    elif strategy == "Co Mom Rev":
        strategy = Strategy.CO_MOM_REV
        backtest_strategy = Backtest_strategy(portfolio_universe, strategy)
        backtest_strategy.co_mom_rev_param(nb_periods_horizon_mom=horizon_mom, nb_periods_horizon_rev=horizon_rev, top_prct_mom=top_mom, down_prct_mom=down_mom, top_prct_rev=top_rev, down_prct_rev=down_rev, top_prct_volume=top_volume, down_prct_volume=down_volume)
    else:
        raise Exception("strat error")
        
    backtest_strategy.run_strategy() 
    #backtest_strategy.compute_metric()
    
    if display_bench == "True":      
        portfolio_universe.compute_bench()         
        
        date = list(portfolio_universe.data_price['date'])
        strategy = list(backtest_strategy.strategy_value)
        bench = list(portfolio_universe.bench_value)
        
        data_graph =  pd.DataFrame({
        'date': date + date,
        'level': strategy + bench ,
        'indice': len(strategy)*["strategy"] + len(bench)*["benchmark"]})
        data_graph= data_graph.sort_values(by="date")
        
        fig = px.line(data_graph, x='date', y='level', color="indice", title='Level graph of selected strategy')
    else: 
        date = list(portfolio_universe.data_price['date'])
        strategy = list(backtest_strategy.strategy_value)
        
        data_graph =  pd.DataFrame({
        'date': date,
        'level': strategy,
        'indice': len(strategy)*["strategy"]})
        data_graph= data_graph.sort_values(by="date")
        
    fig = px.line(data_graph, x='date', y='level', color="indice", title='Level graph of selected strategy')
        
    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8054, dev_tools_hot_reload=False)