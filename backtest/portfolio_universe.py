import pandas as pd
from datetime import date
from enum_class import Transaction_cost, Rebalancing_frequency



class Portfolio_universe(): # research code
    
    def __init__(self, start_date:date, end_date:date, rebalancing_frequency:int, transaction_cost:Transaction_cost):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.get_rebalancing_frequency(rebalancing_frequency)
        self.transaction_cost = transaction_cost
        
        
    def get_rebalancing_frequency(self, rebalancing_frequency:Rebalancing_frequency):
        if rebalancing_frequency == Rebalancing_frequency.MONTHLY:
            self.rebalancing_frequency = 1
            
        elif rebalancing_frequency == Rebalancing_frequency.QUARTERLY:
            self.rebalancing_frequency = 4
            
        elif rebalancing_frequency == Rebalancing_frequency.YEARLY:
            self.rebalancing_frequency = 12
        
        else:
            raise Exception("Unknown rebalancing frequency")
        
    def add_price_data(self, data_price:pd.DataFrame=None, date_ticker:str = None):
        self.date_ticker_price = date_ticker
        self.data_price = data_price
        self.data_price[date_ticker] = pd.to_datetime(self.data_price[date_ticker])
        
        self.data_price = self.data_price[(self.data_price[date_ticker] >= self.start_date) & (self.data_price[date_ticker] <= self.end_date)]

    
    def add_volume_data(self, data_volume:pd.DataFrame=None, date_ticker:str = None):
        self.date_ticker_volume = date_ticker
        self.data_volume = data_volume
        self.data_volume[date_ticker] = pd.to_datetime(self.data_volume[date_ticker])       
        
        self.data_volume = self.data_volume[(self.data_volume[date_ticker] >= self.start_date) & (self.data_volume[date_ticker] <= self.end_date)]


    def compute_bench(self):
        portfolio = self.data_price
        portfolio = portfolio.sort_values(by = [self.date_ticker_price]).reset_index(drop=True)
        
        ticker_col = list(portfolio.columns.drop(self.date_ticker_price))
        
        portfolio_returns = portfolio.copy()
        portfolio_returns_mom = portfolio.copy()
        portfolio_returns_rev = portfolio.copy()
        
        portfolio_returns[ticker_col] = portfolio_returns[ticker_col].pct_change(periods=1)
        
        bench_weights = pd.DataFrame(0, index=portfolio.index, columns=ticker_col)
        bench_weights[ticker_col] = bench_weights[ticker_col].astype(float)
        
        for i in range(0, len(portfolio), 1):
            ticker_col = list(portfolio_returns.loc[i].drop(self.date_ticker_price).replace(0, pd.NA).dropna().index)
            bench_weights.loc[i, ticker_col] = portfolio.loc[i, ticker_col]/portfolio.loc[i, ticker_col].sum()
            
        bench_weights = bench_weights.shift(1)
        bench_weights.loc[0] = 0     
        bench_returns = (bench_weights * portfolio_returns).sum(axis=1)
        bench_value = 100*(1 + bench_returns).cumprod()
        
        self.bench_value = bench_value
        
    def transcation_cost_param(self, constant_fee=0, linear_fee=0):
        self.constant_fee = constant_fee
        self.linear_fee = linear_fee
        

    def compute_transaction_cost(self, transaction_amount:float, nb_transaction:int):
        if self.transaction_cost == Transaction_cost.CONSTANT:
            return self.constant_fee * nb_transaction
        
        elif self.transaction_cost == Transaction_cost.LINEAR:
            return self.linear_fee * transaction_amount
        
        elif self.transaction_cost == Transaction_cost.AFFINE:
            return self.constant_fee * nb_transaction + self.linear_fee * transaction_amount
        
        elif self.transaction_cost == Transaction_cost.NULL:
            return 0
        
        else:
            raise Exception("Unknown transaction cost type")
    


    
    
    
        
