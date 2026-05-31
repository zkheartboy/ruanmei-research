
"""
真正有效的策略 - 解决与买入持有差距太大的问题
"""

import backtrader as bt


class LongTermTrendStrategy(bt.Strategy):
    """
    长期趋势策略 - 牛市中尽量长持
    
    核心改进：
    1. 使用更长期的趋势判断
    2. 只有真正趋势反转才卖出，不在上涨中轻易止盈
    3. 大幅降低卖出频率
    """
    
    params = (
        ('ma_period', 60),      
        ('confirm_period', 5),  
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma = bt.indicators.EMA(self.data.close, period=self.params.ma_period)
        self.ma_long = bt.indicators.SMA(self.data.close, period=120)
        self.order = None
        self.buy_price = None
        
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'Buy, price: {order.executed.price:.2f}')
                self.buy_price = order.executed.price
            else:
                self.log(f'Sell, price: {order.executed.price:.2f}')
                self.buy_price = None
        
        self.order = None
    
    def next(self):
        if self.order:
            return
        
        current_price = self.data.close[0]
        in_uptrend = current_price > self.ma_long[0]
        
        if not self.position:
            if current_price > self.ma[0] and in_uptrend:
                self.order = self.buy()
                self.log(f'Buy signal, price: {current_price:.2f}')
        else:
            if current_price < self.ma_long[0]:
                self.order = self.sell()
                self.log(f'Sell signal, price: {current_price:.2f}')


class BuyHoldLikeStrategy(bt.Strategy):
    """
    类买入持有策略 - 只在大级别趋势下跌时才卖出
    
    超级简单有效：
    1. 价格在均线上方就持有
    2. 只有跌破均线一定幅度才考虑卖出
    3. 不做频繁交易
    """
    
    params = (
        ('ma_period', 60),
        ('threshold', 0.95),  
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma = bt.indicators.SMA(self.data.close, period=self.params.ma_period)
        self.order = None
        self.buy_price = None
        
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'Buy, price: {order.executed.price:.2f}')
                self.buy_price = order.executed.price
            else:
                self.log(f'Sell, price: {order.executed.price:.2f}')
                self.buy_price = None
        
        self.order = None
    
    def next(self):
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        if not self.position:
            if current_price > self.ma[0]:
                self.order = self.buy()
        else:
            if current_price < self.ma[0] * self.params.threshold:
                self.order = self.sell()


class AggressiveTrendStrategy(bt.Strategy):
    """
    激进趋势策略 - 尽可能抓住大趋势
    """
    
    params = (
        ('fast_period', 10),
        ('slow_period', 60),
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma_fast = bt.indicators.EMA(self.data.close, period=self.params.fast_period)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)
        self.order = None
        
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        self.order = None
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            if self.crossover > 0 or self.ma_fast[0] > self.ma_slow[0]:
                self.order = self.buy()
        else:
            if self.crossover < 0:
                self.order = self.sell()

