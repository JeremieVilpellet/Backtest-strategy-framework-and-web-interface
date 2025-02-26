import pandas as pd
from datetime import date

from backtest_strategy import Backtest_strategy
from portfolio_universe import Portfolio_universe
from enum_class import Rebalancing_frequency, Transaction_cost, Strategy

## Data



data_RIY = pd.read_csv("C:/Users/jvilp/OneDrive/Documents/bloom_272/RIY_data.csv", sep=";") # Russel 1000
data_RIY_price = data_RIY[data_RIY["FIELD"]=="PX_LAST"].copy()
data_RIY_volume = data_RIY[data_RIY["FIELD"]=="PX_VOLUME"].copy()
data_RIY_price = data_RIY_price.drop(columns=["FIELD"])
data_RIY_volume = data_RIY_volume.drop(columns=["FIELD"])

## Portfolio universe 
start_date = date(2009,1,1)
end_date = date(2018,1,1)
rebalancing_frequency = Rebalancing_frequency.MONTHLY
transaction_cost = Transaction_cost.AFFINE

portfolio_universe = Portfolio_universe(start_date, end_date, rebalancing_frequency, transaction_cost)
portfolio_universe.add_price_data(data_RIY_price , date_ticker='date')
portfolio_universe.add_volume_data(data_RIY_volume , date_ticker='date')
portfolio_universe.transcation_cost_param(constant_fee=0, linear_fee=0)

## Backtest Strategy

# Momentum
strategy = Strategy.MOMENTUM
backtest_strategy = Backtest_strategy(portfolio_universe, strategy)
backtest_strategy.momentum_param(nb_periods_horizon=12, top_prct=0.2, down_prct=0.2)
backtest_strategy.run_strategy()








