from lumibot.brokers import Alpaca #broker
from lumibot.backtesting import YahooDataBacktesting #framework for backtesting
from lumibot.strategies.strategy import Strategy #trading bot
from lumibot.traders import Trader #deployment
from datetime import datetime #need for time series
from alpaca_trade_api import REST
from timedelta import Timedelta

API_KEY = "PK6BNXV8KQEY3OPVALSS"
API_SECRET = "aUtOVZiKkEeirsZmd7amRVKYQikvqV5e2KhA1rnh"
BASE_URL = "https://paper-api.alpaca.markets/v2"

ALPACA_CREDS = {
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True

}

class MLTrader(Strategy):
    def initialize(self, symbol:str="SPY", cash_at_risk:float = .5 ): #iterates once on startup
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url = BASE_URL, key_id = API_KEY, secret_key = API_SECRET)

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.cash_at_risk / last_price, 0) #how much of the cash balance able to risk  
        return cash, last_price, quantity
    
    def get_dates(self):
        today = self.get_datetime()
        end_range = today - Timedelta(days = 3)

        today_str = today.isoformat()
        end_range_str = end_range.isoformat()

        return today_str, end_range_str
    
    def get_news(self):
        today, end_range = self.get_dates()
        news = self.api.get_news(symbol = self.symbol, start = end_range, end = today)

        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        return news
        
        

    def on_trading_iteration(self): #runs everytime new data is given
        cash, last_price, quantity = self.position_sizing()

        if cash > last_price:
            if self.last_trade == None:
                news = self.get_news()
                print(news)
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "buy", 
                    type = "bracket", 
                    take_profit_price = last_price * 1.20, 
                    stop_loss_price = last_price * 0.95
                )
                self.submit_order(order)
                self.last_trade = "buy"
    
start_date = datetime(2023, 12, 15) #start and end dates for backtesting
end_date = datetime(2023, 12, 31)

broker = Alpaca(ALPACA_CREDS)
strategy = MLTrader(name = 'mlstrat', broker = broker, parameter = {"symbol":"SPY", "cash_at_risk":.5})

strategy.backtest(YahooDataBacktesting, start_date, end_date, parameters = {"symbol":"SPY", "cash_at_risk":.5})