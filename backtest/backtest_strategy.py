import pandas as pd
import numpy as np
from enum_class import Strategy
import pandas as pd


class Backtest_strategy(): # production code
    
    def __init__(self, portfolio_universe, strategy):
        self.portfolio_universe = portfolio_universe
        self.strategy = strategy
        self.strategy_param = None
        
    def run_strategy(self):
        if self.strategy_param is None:
            raise Exception("Specify some parameter for the strategy")
            
        if self.strategy == Strategy.MOMENTUM:
            self.run_momentum()
            
        elif self.strategy == Strategy.REVERSAL:
            self.run_reversal()
        
        elif self.strategy == Strategy.CO_MOM_REV:
            self.run_co_mom_rev()
            
        else:
            raise Exception("Unknown strategy")
            
    
    def momentum_param(self, nb_periods_horizon:int=1, top_prct:float=0.2, down_prct:float=0.2):
        self.strategy_param = {}
        self.strategy_param["nb_periods_horizon"] = nb_periods_horizon
        self.strategy_param["top_prct"] = top_prct
        self.strategy_param["down_prct"] = down_prct
        
        
    def run_momentum(self):
        if not set(self.strategy_param.keys()) == set(["nb_periods_horizon", "top_prct", "down_prct"]):
            raise Exception("Enter param with function momentum param")
        else:
            horizon = self.strategy_param["nb_periods_horizon"]
            top_prct = self.strategy_param["top_prct"]
            down_prct = self.strategy_param["top_prct"]
            rebalancing_frequency = self.portfolio_universe.rebalancing_frequency
        
        portfolio = self.portfolio_universe.data_price
        date_ticker = self.portfolio_universe.date_ticker_price
        portfolio = portfolio.sort_values(by = [date_ticker]).reset_index(drop=True)

        ticker_col = list(portfolio.columns.drop(date_ticker))
        
        portfolio_returns = portfolio.copy()
        portfolio_returns[ticker_col] = portfolio_returns[ticker_col].pct_change(periods=1)
        
        portfolio_returns_horizon = portfolio.copy()       
        portfolio_returns_horizon[ticker_col] = portfolio_returns_horizon[ticker_col].pct_change(periods=horizon)
                
        momentum_weights = pd.DataFrame(0, index=portfolio.index, columns=ticker_col)
        momentum_weights[ticker_col] = momentum_weights[ticker_col].astype(float)
        for i in range(0, len(portfolio), rebalancing_frequency):
            ticker_col = list(portfolio_returns_horizon.loc[i].drop(date_ticker).replace(0, pd.NA).dropna().index)
            if len(ticker_col) == 0:
                pass # si pas de rendement poids null / on ne s'expose pas 
            elif i < horizon:
                momentum_weights.iloc[i][ticker_col] = 1/len(ticker_col)
            else:                
                sorted_returns = portfolio_returns_horizon.iloc[i][ticker_col].replace(0, pd.NA).dropna().sort_values() # rendement trié sur horizon défini
                
                n_assets = len(sorted_returns)
                top_count = int(top_prct * n_assets)
                bottom_count = int(down_prct * n_assets)
                
                top_percent = list(sorted_returns.index[n_assets-top_count:n_assets])
                bottom_percent = list(sorted_returns.index[0:bottom_count])
                
                momentum_weights.loc[i, top_percent] = 1 / len(top_percent)
                momentum_weights.loc[i, bottom_percent] = - 1 / len(bottom_percent)
                
                
        diff_weights = momentum_weights.diff().abs().sum(axis=1)  
        nb_transaction = (momentum_weights.diff() != 0).sum(axis=1)
        
        momentum_weights = momentum_weights.shift(1)
        momentum_weights.loc[0] = 0     
        momentum_returns = (momentum_weights * portfolio_returns).sum(axis=1)
        
        value_portfolio = [100]
        transaction_cost = [0]
        for t in range(1,len(momentum_returns)):
            transaction_cost_t = self.portfolio_universe.compute_transaction_cost(transaction_amount=value_portfolio[-1]*diff_weights[t], nb_transaction=nb_transaction[t])
            value_portfolio_t = value_portfolio[-1] * (1 + momentum_returns[t] - transaction_cost_t)
            
            value_portfolio.append(value_portfolio_t)
            transaction_cost.append(transaction_cost_t)
        
        momentum_value = pd.Series(value_portfolio, index=momentum_returns.index)
        
        default_index = list(momentum_returns.index[momentum_returns - transaction_cost < -1])
        if len(default_index) > 0:            
            momentum_value[default_index[0]:] = 0
        
        self.strategy_weights = momentum_weights
        self.strategy_value = momentum_value
        self.transaction_cost_value = transaction_cost
    
    
    def reversal_param(self, nb_periods_horizon:int=1, top_prct:float=0.2, down_prct:float=0.2):
        self.strategy_param = {}
        self.strategy_param["nb_periods_horizon"] = nb_periods_horizon
        self.strategy_param["top_prct"] = top_prct
        self.strategy_param["down_prct"] = down_prct
    
    
    def run_reversal(self):
        if not set(self.strategy_param.keys()) == set(["nb_periods_horizon", "top_prct", "down_prct"]):
            raise Exception("Enter param with function reversal param")
        else:
            horizon = self.strategy_param["nb_periods_horizon"]
            top_prct = self.strategy_param["top_prct"]
            down_prct = self.strategy_param["top_prct"]
            rebalancing_frequency = self.portfolio_universe.rebalancing_frequency
        
        portfolio = self.portfolio_universe.data_price
        date_ticker = self.portfolio_universe.date_ticker_price
        portfolio = portfolio.sort_values(by = [date_ticker]).reset_index(drop=True)
        
        ticker_col = list(portfolio.columns.drop(date_ticker))
        
        portfolio_returns = portfolio.copy()
        portfolio_returns[ticker_col] = portfolio_returns[ticker_col].pct_change(periods=1)
        
        portfolio_returns_horizon = portfolio.copy()       
        portfolio_returns_horizon[ticker_col] = portfolio_returns_horizon[ticker_col].pct_change(periods=horizon)
                
        reversal_weights = pd.DataFrame(0, index=portfolio.index, columns=ticker_col)
        reversal_weights[ticker_col] = reversal_weights[ticker_col].astype(float)
        for i in range(0, len(portfolio), rebalancing_frequency):
            ticker_col = list(portfolio_returns_horizon.loc[i].drop(date_ticker).replace(0, pd.NA).dropna().index)
            if len(ticker_col) == 0:
                pass # si pas de rendement poids null / on ne s'expose pas 
            elif i < horizon:
                reversal_weights.iloc[i][ticker_col] = 1/len(ticker_col)
            else:                
                sorted_returns = portfolio_returns_horizon.iloc[i][ticker_col].replace(0, pd.NA).dropna().sort_values() # rendement trié sur horizon défini
                
                n_assets = len(sorted_returns)
                top_count = int(top_prct * n_assets)
                bottom_count = int(down_prct * n_assets)
                
                top_percent = list(sorted_returns.index[n_assets-top_count:n_assets])
                bottom_percent = list(sorted_returns.index[0:bottom_count])
                
                reversal_weights.loc[i, top_percent] = - 1 / len(top_percent)
                reversal_weights.loc[i, bottom_percent] = 1 / len(bottom_percent)
                
                
        diff_weights = reversal_weights.diff().abs().sum(axis=1)  
        nb_transaction = (reversal_weights.diff() != 0).sum(axis=1)
        
        reversal_weights = reversal_weights.shift(1)
        reversal_weights.loc[0] = 0     
        reversal_weights = (reversal_weights * portfolio_returns).sum(axis=1)
        
        value_portfolio = [100]
        transaction_cost = [0]
        for t in range(1,len(reversal_weights)):
            transaction_cost_t = self.portfolio_universe.compute_transaction_cost(transaction_amount=value_portfolio[-1]*diff_weights[t], nb_transaction=nb_transaction[t])
            value_portfolio_t = value_portfolio[-1] * (1 + reversal_weights[t] - transaction_cost_t)
            
            value_portfolio.append(value_portfolio_t)
            transaction_cost.append(transaction_cost_t)
        
        reversal_value = pd.Series(value_portfolio, index=reversal_weights.index)
        
        default_index = list(reversal_weights.index[reversal_weights - transaction_cost < -1])
        if len(default_index) > 0:            
            reversal_weights[default_index[0]:] = 0
            
        self.strategy_weights = reversal_weights
        self.strategy_value = reversal_value
        self.transaction_cost_value = transaction_cost
    
    
    def co_mom_rev_param(self, nb_periods_horizon_mom:int=1, nb_periods_horizon_rev:int=1, top_prct_mom:float=0.2, down_prct_mom:float=0.2, top_prct_rev:float=0.2, down_prct_rev:float=0.2, top_prct_volume:float=0.5, down_prct_volume:float=0.5):
        self.strategy_param = {}
        self.strategy_param["nb_periods_horizon_mom"] = nb_periods_horizon_mom
        self.strategy_param["nb_periods_horizon_rev"] = nb_periods_horizon_rev
        
        self.strategy_param["top_prct_mom"] = top_prct_mom
        self.strategy_param["down_prct_mom"] = down_prct_mom
        
        self.strategy_param["top_prct_rev"] = top_prct_rev
        self.strategy_param["down_prct_rev"] = down_prct_rev
        
        self.strategy_param["top_prct_volume"] = top_prct_volume
        self.strategy_param["down_prct_volume"] = down_prct_volume
    
    
    def run_co_mom_rev(self):
        if not set(self.strategy_param.keys()) == set(['nb_periods_horizon_mom', 
                                                       'nb_periods_horizon_rev', 
                                                       'top_prct_mom', 
                                                       'down_prct_mom', 
                                                       'top_prct_rev', 
                                                       'down_prct_rev', 
                                                       'top_prct_volume', 
                                                       'down_prct_volume']):
            raise Exception("Enter param with function co mom rev param")
        else:
            horizon_mom = self.strategy_param["nb_periods_horizon_mom"]
            horizon_rev = self.strategy_param["nb_periods_horizon_rev"]
            
            top_prct_mom = self.strategy_param["top_prct_mom"]
            down_prct_mom = self.strategy_param["top_prct_mom"]
            
            top_prct_rev = self.strategy_param["top_prct_rev"]
            down_prct_rev = self.strategy_param["top_prct_rev"]
            
            top_prct_volume = self.strategy_param["top_prct_volume"]
            down_prct_volume = self.strategy_param["down_prct_volume"]
            
            rebalancing_frequency = self.portfolio_universe.rebalancing_frequency
        
        portfolio = self.portfolio_universe.data_price
        date_ticker_price = self.portfolio_universe.date_ticker_price
        portfolio = portfolio.sort_values(by = [date_ticker_price]).reset_index(drop=True)
        
        ticker_col = list(portfolio.columns.drop(date_ticker_price))
        
        portfolio_returns = portfolio.copy()
        portfolio_returns_mom = portfolio.copy()
        portfolio_returns_rev = portfolio.copy()
        
        portfolio_returns[ticker_col] = portfolio_returns[ticker_col].pct_change(periods=1)
        portfolio_returns_mom[ticker_col] = portfolio_returns_mom[ticker_col].pct_change(periods=horizon_mom)
        portfolio_returns_rev[ticker_col] = portfolio_returns_rev[ticker_col].pct_change(periods=horizon_rev)
        
        volume = self.portfolio_universe.data_volume
        date_ticker_volume = self.portfolio_universe.date_ticker_volume
        volume = volume.sort_values(by = [date_ticker_volume]).reset_index(drop=True)
                
        co_mom_rev_weights = pd.DataFrame(0, index=portfolio.index, columns=ticker_col)
        co_mom_rev_weights[ticker_col] = co_mom_rev_weights[ticker_col].astype(float)
        for i in range(0, len(portfolio), rebalancing_frequency):
            ticker_col_price = list(portfolio_returns.loc[i].drop(date_ticker_price).replace(0, pd.NA).dropna().index)
            ticker_vol_volume = list(volume.loc[i].drop(date_ticker_volume).replace(0, pd.NA).dropna().index)
            ticker_col = list(set(ticker_col_price) & set(ticker_vol_volume))
            
            if len(ticker_col) == 0:
                pass # si pas de rendement et volume poids null / on ne s'expose pas 
            elif i < max(horizon_rev, horizon_mom):
                co_mom_rev_weights.iloc[i][ticker_col] = 1/len(ticker_col)
            else:     
                n_assets = len(ticker_col)
                
                
                # Momentum

                n_assets_up_mom = int(top_prct_mom * n_assets)
                n_assets_down_mom = int(down_prct_mom * n_assets)
                
                sorted_returns_mom = portfolio_returns_mom.iloc[i][ticker_col].sort_values()
                
                up_percent_mom = list(sorted_returns_mom.index[n_assets-n_assets_up_mom:n_assets]) # assets that perform the most
                down_percent_mom = list(sorted_returns_mom.index[0:n_assets_down_mom]) # assets that perform the least
                
                n_assets_up_percent_mom = len(up_percent_mom)
                n_assets_down_percent_mom = len(down_percent_mom)
                
                n_assets_up_high_turnover_mom = int(n_assets_up_percent_mom * top_prct_volume)
                n_assets_down_high_turnover_mom = int(n_assets_down_percent_mom * top_prct_volume)
                
                sorted_volume_up_mom = volume.iloc[i-horizon_mom+1:i][up_percent_mom].sum().sort_values()
                sorted_volume_down_mom = volume.iloc[i-horizon_mom+1:i][down_percent_mom].sum().sort_values()
                
                ticker_up_high_turnover_mom = list(sorted_volume_up_mom.index[n_assets_up_percent_mom-n_assets_up_high_turnover_mom:n_assets_up_percent_mom]) # assets that perform the most and most liquid
                ticker_down_high_turnover_mom = list(sorted_volume_down_mom.index[n_assets_down_percent_mom-n_assets_down_high_turnover_mom:n_assets_down_percent_mom]) # assets that perform the least and most liquid
                
                
                # Reversal
                
                n_assets_up_rev = int(top_prct_rev * n_assets)
                n_assets_down_rev = int(down_prct_rev * n_assets)
                
                sorted_returns_rev = portfolio_returns_rev.iloc[i][ticker_col].sort_values()
                
                up_percent_rev = list(sorted_returns_rev.index[n_assets-n_assets_up_rev:n_assets]) # assets that perform the most
                down_percent_rev = list(sorted_returns_rev.index[0:n_assets_down_rev]) # assets that perform the least
                
                n_assets_up_percent_rev = len(up_percent_rev)
                n_assets_down_percent_rev = len(down_percent_rev)
                
                n_assets_up_low_turnover_rev = int(n_assets_up_percent_rev * down_prct_volume)
                n_assets_down_low_turnover_rev = int(n_assets_down_percent_rev * down_prct_volume)
                
                sorted_volume_up_rev = volume.iloc[i-horizon_rev+1:i][up_percent_rev].sum().sort_values()
                sorted_volume_down_rev = volume.iloc[i-horizon_rev+1:i][down_percent_rev].sum().sort_values()
                
                ticker_up_low_turnover_rev = list(sorted_volume_up_rev.index[0:n_assets_up_low_turnover_rev]) # assets that perform the most and most illiquid
                ticker_down_low_turnover_rev = list(sorted_volume_down_rev.index[0:n_assets_down_low_turnover_rev]) # assets that perform the least and most illiquid
                
                
                # Weights           
                
                n_assets_long = (len(ticker_down_low_turnover_rev) + len(ticker_up_high_turnover_mom))
                n_assets_short = (len(ticker_up_low_turnover_rev) + len(ticker_down_high_turnover_mom))
                
                co_mom_rev_weights.loc[i, ticker_up_low_turnover_rev] = - 1 / n_assets_short
                co_mom_rev_weights.loc[i, ticker_down_low_turnover_rev] = 1 / n_assets_long
                
                co_mom_rev_weights.loc[i, ticker_down_high_turnover_mom] = - 1 / n_assets_short
                co_mom_rev_weights.loc[i, ticker_up_high_turnover_mom] = 1 / n_assets_long
                
               
        diff_weights = co_mom_rev_weights.diff().abs().sum(axis=1)  
        nb_transaction = (co_mom_rev_weights.diff() != 0).sum(axis=1)
        
        
        co_mom_rev_weights = co_mom_rev_weights.shift(1)
        co_mom_rev_weights.loc[0] = 0     
        co_mom_rev_return = (co_mom_rev_weights * portfolio_returns).sum(axis=1)
        
        value_portfolio = [100]
        transaction_cost = [0]
        for t in range(1,len(co_mom_rev_return)):
            transaction_cost_t = self.portfolio_universe.compute_transaction_cost(transaction_amount=value_portfolio[-1]*diff_weights[t], nb_transaction=nb_transaction[t])
            value_portfolio_t = value_portfolio[-1] * (1 + co_mom_rev_return[t] - transaction_cost_t)
            
            value_portfolio.append(value_portfolio_t)
            transaction_cost.append(transaction_cost_t)
        
        co_mom_rev_value = pd.Series(value_portfolio, index=co_mom_rev_weights.index)
        
        default_index = list(co_mom_rev_return.index[co_mom_rev_return - transaction_cost < -1])
        if len(default_index) > 0:            
            co_mom_rev_weights[default_index[0]:] = 0
            
        self.strategy_weights = co_mom_rev_weights
        self.strategy_value = co_mom_rev_value
        self.transaction_cost_value = transaction_cost
        
        
    def compute_metric(self):
        returns_month = (self.strategy_value / self.strategy_value.shift(1)) - 1
        
        vol_month = np.sqrt(np.var(returns_month))    # ajouter vol daily /month/ year 
        
        #sharpe = ((self.strategy_value[-1]/ self.strategy_value[0])-1)/vol_month # à corriger en mettant le rendement meme freqence que vol
        max_draw_down = min(returns_month)
        historical_var_95 = returns_month.dropna().quantile(0.95)
        perf_annual = ((self.strategy_value[-1]/ self.strategy_value[0]))**(12/len(returns_month))-1
        
        metric = {
            'vol': [vol_month],
            'sharpe': [None],
            'draw_down': [max_draw_down],
            'perf_annual': [perf_annual],
            'historical_var_95': [historical_var_95]
        }
        df_metric = pd.DataFrame(metric)
        
        return df_metric
        
        
        
        
