"""
止损模块
"""

import backtrader as bt


class FixedStopLoss:
    """固定止损"""
    
    def __init__(self, stop_loss_pct=0.08):
        self.stop_loss_pct = stop_loss_pct
        self.buy_price = None
        
    def check(self, current_price):
        """检查是否触发止损"""
        if self.buy_price is None:
            return False
        
        return current_price < self.buy_price * (1 - self.stop_loss_pct)
    
    def update(self, buy_price):
        """更新买入价格"""
        self.buy_price = buy_price


class TrailingStopLoss:
    """跟踪止损"""
    
    def __init__(self, trailing_pct=0.12):
        self.trailing_pct = trailing_pct
        self.highest_price = None
        
    def check(self, current_price):
        """检查是否触发跟踪止损"""
        if self.highest_price is None:
            return False
        
        return current_price < self.highest_price * (1 - self.trailing_pct)
    
    def update(self, current_price):
        """更新最高价"""
        if self.highest_price is None:
            self.highest_price = current_price
        else:
            self.highest_price = max(self.highest_price, current_price)


class TimeStopLoss:
    """时间止损"""
    
    def __init__(self, max_holding_days=20, profit_threshold=0):
        self.max_holding_days = max_holding_days
        self.profit_threshold = profit_threshold
        self.buy_date = None
        self.buy_price = None
        
    def check(self, current_price, holding_days):
        """检查是否触发时间止损"""
        if self.buy_date is None:
            return False
        
        if holding_days > self.max_holding_days:
            if current_price < self.buy_price * (1 + self.profit_threshold):
                return True
        
        return False
    
    def update(self, buy_price, buy_date_idx):
        """更新买入信息"""
        self.buy_price = buy_price
        self.buy_date = buy_date_idx


class StopLossManager:
    """止损管理器"""
    
    def __init__(self, stop_loss_pct=0.08, trailing_pct=0.12, max_holding_days=20):
        self.fixed_stop = FixedStopLoss(stop_loss_pct)
        self.trailing_stop = TrailingStopLoss(trailing_pct)
        self.time_stop = TimeStopLoss(max_holding_days)
        
    def check_all(self, current_price, holding_days):
        """检查所有止损"""
        if self.fixed_stop.check(current_price):
            return 'fixed_stop'
        
        if self.trailing_stop.check(current_price):
            return 'trailing_stop'
        
        if self.time_stop.check(current_price, holding_days):
            return 'time_stop'
        
        return None
    
    def update(self, buy_price, buy_date_idx, current_price):
        """更新止损数据"""
        self.fixed_stop.update(buy_price)
        self.trailing_stop.update(current_price)
        self.time_stop.update(buy_price, buy_date_idx)
