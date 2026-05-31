"""
止损模块
提供多种止损方式
"""

import backtrader as bt


class StopLossStrategy(bt.Strategy):
    """
    止损策略基类
    可与其他策略组合使用
    """
    
    params = (
        ('stop_loss_pct', 0.08),      # 8%固定止损
        ('trailing_pct', 0.12),        # 12%跟踪止损
        ('time_stop_days', 20),        # 20日时间止损
        ('printlog', False),
    )
    
    def __init__(self):
        self.buy_price = None
        self.buy_date = None
        self.highest_price = None
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
                self.buy_price = order.executed.price
                self.buy_date = len(self)
                self.highest_price = self.buy_price
                self.log(f'买入, 价格: {self.buy_price:.2f}')
            elif order.issell():
                self.log(f'卖出, 价格: {order.executed.price:.2f}')
            
            self.order = None
    
    def next(self):
        # 如果有待处理订单，跳过
        if self.order:
            return
        
        # 如果没有持仓，重置止损数据
        if not self.position:
            self.buy_price = None
            self.buy_date = None
            self.highest_price = None
            return
        
        current_price = self.data.close[0]
        
        # 更新最高价
        if self.highest_price is None:
            self.highest_price = current_price
        else:
            self.highest_price = max(self.highest_price, current_price)
        
        # 1. 固定止损
        if self.buy_price and current_price < self.buy_price * (1 - self.params.stop_loss_pct):
            self.log(f'触发固定止损, 当前价格: {current_price:.2f}, 买入价格: {self.buy_price:.2f}')
            self.order = self.close()
            return
        
        # 2. 跟踪止损
        if self.highest_price and current_price < self.highest_price * (1 - self.params.trailing_pct):
            self.log(f'触发跟踪止损, 当前价格: {current_price:.2f}, 最高价格: {self.highest_price:.2f}')
            self.order = self.close()
            return
        
        # 3. 时间止损
        if self.buy_date and (len(self) - self.buy_date) > self.params.time_stop_days:
            if current_price < self.buy_price:
                self.log(f'触发时间止损, 持有天数: {len(self) - self.buy_date}, 当前价格: {current_price:.2f}')
                self.order = self.close()
                return


class CombinedStrategy(bt.Strategy):
    """
    组合策略：均线+RSI+止损
    """
    
    params = (
        ('fast_period', 20),
        ('slow_period', 60),
        ('rsi_period', 14),
        ('rsi_buy_threshold', 40),
        ('rsi_sell_threshold', 60),
        ('stop_loss_pct', 0.08),
        ('trailing_pct', 0.12),
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)
        
        self.buy_price = None
        self.highest_price = None
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
                self.buy_price = order.executed.price
                self.highest_price = self.buy_price
                self.log(f'买入, 价格: {self.buy_price:.2f}')
            elif order.issell():
                self.log(f'卖出, 价格: {order.executed.price:.2f}')
            
            self.order = None
    
    def next(self):
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        # 止损检查
        if self.position and self.buy_price:
            # 更新最高价
            self.highest_price = max(self.highest_price, current_price)
            
            # 固定止损
            if current_price < self.buy_price * (1 - self.params.stop_loss_pct):
                self.log(f'止损出局, 价格: {current_price:.2f}')
                self.order = self.close()
                return
            
            # 跟踪止损
            if current_price < self.highest_price * (1 - self.params.trailing_pct):
                self.log(f'跟踪止损出局, 价格: {current_price:.2f}')
                self.order = self.close()
                return
        
        # 交易信号
        if not self.position:
            if self.crossover > 0:
                self.log(f'买入信号, 价格: {current_price:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.buy()
        else:
            if self.crossover < 0:
                self.log(f'卖出信号, 价格: {current_price:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.sell()
