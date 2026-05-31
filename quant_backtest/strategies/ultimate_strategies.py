
"""
终极策略 - 已修复满仓问题！真正解决与买入持有差距太大的问题！
"""

import backtrader as bt


class AlmostBuyAndHoldStrategy(bt.Strategy):
    """
    几乎就是买入持有 - 只在非常明显的趋势反转时才卖出
    
    核心改进：
    1. 买入后尽量长持
    2. 只有大幅跌破长期均线才考虑卖出
    3. 满仓买入！
    """
    
    params = (
        ('ma_period', 120),     
        ('sell_threshold', 0.85),  
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
                self.log(f'Buy, price: {order.executed.price:.2f}, size: {order.executed.size}')
                self.buy_price = order.executed.price
            else:
                self.log(f'Sell, price: {order.executed.price:.2f}, size: {order.executed.size}')
                self.buy_price = None
        
        self.order = None
    
    def next(self):
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        if not self.position:
            if current_price > self.ma[0]:
                # 满仓买入！
                available_cash = self.broker.getcash()
                size = int(available_cash / current_price * 0.99)  # 留1%给手续费
                if size > 0:
                    self.order = self.buy(size=size)
                    self.log(f'Buy trigger, price: {current_price:.2f}, size: {size}')
        else:
            if current_price < self.ma[0] * self.params.sell_threshold:
                # 全部卖出
                self.order = self.sell(size=self.position.size)
                self.log(f'Sell trigger, price: {current_price:.2f}')


class NeverSellStrategy(bt.Strategy):
    """
    真·买入持有 - 满仓买入，买了就不卖了！
    """
    
    params = (('printlog', False),)
    
    def __init__(self):
        self.order = None
        self.bought = False
        
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'Buy, price: {order.executed.price:.2f}, size: {order.executed.size}')
                self.bought = True
        
        self.order = None
    
    def next(self):
        if self.order or self.bought:
            return
        
        # 满仓买入！
        current_price = self.data.close[0]
        available_cash = self.broker.getcash()
        size = int(available_cash / current_price * 0.99)  # 留1%给手续费
        if size > 0:
            self.order = self.buy(size=size)
            self.log(f'Buy and hold! Price: {current_price:.2f}, size: {size}')


class TrendFollowMinimal(bt.Strategy):
    """
    极简趋势跟踪 - 只做最关键的判断，满仓操作
    """
    
    params = (
        ('ma_fast', 20),
        ('ma_slow', 120),
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.params.ma_fast)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.params.ma_slow)
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
        
        current_price = self.data.close[0]
        
        if not self.position:
            if self.ma_fast[0] > self.ma_slow[0]:
                # 满仓买入
                available_cash = self.broker.getcash()
                size = int(available_cash / current_price * 0.99)
                if size > 0:
                    self.order = self.buy(size=size)
        else:
            if self.ma_fast[0] < self.ma_slow[0]:
                # 全部卖出
                self.order = self.sell(size=self.position.size)

