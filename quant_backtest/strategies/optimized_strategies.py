
"""
优化后的策略 - 大幅改进与买入持有的差距
"""

import backtrader as bt


class OptimizedDualMAStrategy(bt.Strategy):
    """
    优化的双均线策略
    
    改进点：
    1. 更激进的均线周期（5/20）
    2. 大趋势判断，减少上涨初期卖出
    3. 更好的信号确认机制
    """
    
    params = (
        ('fast_period', 5),      
        ('slow_period', 20),     
        ('trend_period', 60),    
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma_fast = bt.indicators.SMA(
            self.data.close, 
            period=self.params.fast_period
        )
        self.ma_slow = bt.indicators.SMA(
            self.data.close, 
            period=self.params.slow_period
        )
        self.ma_trend = bt.indicators.SMA(
            self.data.close, 
            period=self.params.trend_period
        )
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)
        self.order = None
        
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出, 价格: {order.executed.price:.2f}')
        self.order = None
    
    def next(self):
        if self.order:
            return
        
        current_price = self.data.close[0]
        in_uptrend = current_price > self.ma_trend[0]
        
        if not self.position:
            if self.crossover > 0 and in_uptrend:
                self.order = self.buy()
                self.log(f'买入触发, 价格: {current_price:.2f}')
        else:
            if self.crossover < 0 or current_price < self.ma_slow[0]:
                self.order = self.sell()
                self.log(f'卖出触发, 价格: {current_price:.2f}')


class TrendingStrategy(bt.Strategy):
    """
    大趋势跟踪策略 - 更激进，更好捕捉单边行情
    """
    
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma_fast = bt.indicators.EMA(
            self.data.close, period=self.params.fast_period
        )
        self.ma_slow = bt.indicators.EMA(
            self.data.close, period=self.params.slow_period
        )
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
            if self.ma_fast[0] > self.ma_slow[0]:
                self.order = self.buy()
        else:
            if self.ma_fast[0] < self.ma_slow[0]:
                self.order = self.sell()


class SimpleTrendStrategy(bt.Strategy):
    """
    极简趋势策略 - 尽可能保持仓位，只在趋势反转时才卖出
    """
    
    params = (
        ('period', 20),
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma = bt.indicators.EMA(self.data.close, period=self.params.period)
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
            if self.data.close[0] > self.ma[0]:
                self.order = self.buy()
        else:
            if self.data.close[0] < self.ma[0] * 0.98:
                self.order = self.sell()

