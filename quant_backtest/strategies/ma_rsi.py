"""
均线+RSI过滤策略
在双均线基础上增加RSI指标过滤，减少假信号
"""

import backtrader as bt


class MA_RSI_Strategy(bt.Strategy):
    """
    均线+RSI过滤策略
    
    买入条件:
    1. 短期均线从下方穿越长期均线（金叉）
    2. RSI < 买入阈值（处于超卖区域）
    
    卖出条件:
    1. 短期均线从上方穿越长期均线（死叉）
    2. RSI > 卖出阈值（处于超买区域）
    """
    
    params = (
        ('fast_period', 20),            # 短期均线周期
        ('slow_period', 60),            # 长期均线周期
        ('rsi_period', 14),             # RSI周期
        ('rsi_buy_threshold', 40),      # RSI买入阈值
        ('rsi_sell_threshold', 60),      # RSI卖出阈值
        ('printlog', False),
    )
    
    def __init__(self):
        # 计算均线
        self.ma_fast = bt.indicators.SMA(
            self.data.close, 
            period=self.params.fast_period
        )
        self.ma_slow = bt.indicators.SMA(
            self.data.close, 
            period=self.params.slow_period
        )
        
        # 计算RSI
        self.rsi = bt.indicators.RSI(
            self.data.close, 
            period=self.params.rsi_period
        )
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)
        
        # 订单状态
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
                self.log(f'买入, 价格: {order.executed.price:.2f}, RSI: {self.rsi[0]:.2f}')
            else:
                self.log(f'卖出, 价格: {order.executed.price:.2f}, RSI: {self.rsi[0]:.2f}')
        
        self.order = None
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            # 无持仓，检查买入信号
            # 条件1: 金叉
            # 条件2: RSI处于超卖区域（可选）
            if self.crossover > 0:
                self.log(f'买入信号, 价格: {self.data.close[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.buy()
        else:
            # 有持仓，检查卖出信号
            # 条件1: 死叉
            # 条件2: RSI处于超买区域（可选）
            if self.crossover < 0:
                self.log(f'卖出信号, 价格: {self.data.close[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.sell()


class MA_RSI_FilterStrategy(bt.Strategy):
    """
    均线+RSI严格过滤策略
    
    只有当RSI处于超卖区域才允许买入，
    只有当RSI处于超买区域才允许卖出
    """
    
    params = (
        ('fast_period', 20),
        ('slow_period', 60),
        ('rsi_period', 14),
        ('rsi_buy_threshold', 35),      # 严格买入阈值
        ('rsi_sell_threshold', 65),      # 严格卖出阈值
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
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
            self.order = None
    
    def next(self):
        if self.order:
            return
        
        rsi_value = self.rsi[0]
        
        if not self.position:
            # 严格过滤：只有在RSI超卖时才能买入
            if self.crossover > 0 and rsi_value < self.params.rsi_buy_threshold:
                self.log(f'买入, 价格: {self.data.close[0]:.2f}, RSI: {rsi_value:.2f}')
                self.order = self.buy()
        else:
            # 严格过滤：只有在RSI超买时才能卖出
            if self.crossover < 0 and rsi_value > self.params.rsi_sell_threshold:
                self.log(f'卖出, 价格: {self.data.close[0]:.2f}, RSI: {rsi_value:.2f}')
                self.order = self.sell()
