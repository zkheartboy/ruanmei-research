"""
双均线交叉策略
最简单的趋势跟踪策略
"""

import backtrader as bt


class DualMAStrategy(bt.Strategy):
    """
    双均线交叉策略
    
    买入信号: 短期均线从下方穿越长期均线（金叉）
    卖出信号: 短期均线从上方穿越长期均线（死叉）
    """
    
    params = (
        ('fast_period', 20),    # 短期均线周期
        ('slow_period', 60),    # 长期均线周期
        ('printlog', False),    # 是否打印日志
    )
    
    def __init__(self):
        # 计算均线指标
        self.ma_fast = bt.indicators.SMA(
            self.data.close, 
            period=self.params.fast_period,
            plotname='Fast MA'
        )
        self.ma_slow = bt.indicators.SMA(
            self.data.close, 
            period=self.params.slow_period,
            plotname='Slow MA'
        )
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)
        
        # 订单状态
        self.order = None
        
    def log(self, txt, dt=None):
        """日志记录"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """订单通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行, 价格: {order.executed.price:.2f}, '
                        f'成本: {order.executed.value:.2f}, '
                        f'手续费: {order.executed.comm:.2f}')
            else:
                self.log(f'卖出执行, 价格: {order.executed.price:.2f}, '
                        f'成本: {order.executed.value:.2f}, '
                        f'手续费: {order.executed.comm:.2f}')
        
        self.order = None
    
    def next(self):
        """每个交易日执行"""
        # 检查是否有待处理订单
        if self.order:
            return
        
        # 检查持仓
        if not self.position:
            # 无持仓，检查买入信号
            if self.crossover > 0:  # 金叉
                self.log(f'买入信号, 价格: {self.data.close[0]:.2f}')
                self.order = self.buy()
        else:
            # 有持仓，检查卖出信号
            if self.crossover < 0:  # 死叉
                self.log(f'卖出信号, 价格: {self.data.close[0]:.2f}')
                self.order = self.sell()
    
    def stop(self):
        """策略结束"""
        self.log(f'策略结束, 最终市值: {self.broker.getvalue():.2f}', dt=None)


class MA_Only_UpStrategy(bt.Strategy):
    """
    仅做多均线策略
    只在均线上方时持有，跌破均线时卖出
    """
    
    params = (
        ('ma_period', 60),      # 均线周期
        ('printlog', False),
    )
    
    def __init__(self):
        self.ma = bt.indicators.SMA(self.data.close, period=self.params.ma_period)
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
        
        if not self.position:
            if self.data.close[0] > self.ma[0]:
                self.order = self.buy()
        else:
            if self.data.close[0] < self.ma[0]:
                self.order = self.sell()
