
"""
调试策略 - 查看永不卖出策略到底做了什么交易！
"""

import sys
import os
sys.path.insert(0, '/workspace/quant_backtest')

import pandas as pd
import numpy as np
from data.fetcher import StockDataFetcher
import backtrader as bt


class NeverSellDebugStrategy(bt.Strategy):
    """
    永不卖出策略 - 带详细日志的调试版本！
    """
    
    params = (('printlog', True),)
    
    def __init__(self):
        self.order = None
        self.bought = False
        
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} | {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f'BUY EXECUTED! Price: {order.executed.price:.2f}, Size: {order.executed.size}')
            else:
                self.log(f'SELL EXECUTED! Price: {order.executed.price:.2f}, Size: {order.executed.size}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order FAILED! Status: {order.status}')
        
        self.order = None
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f'TRADE CLOSED! Profit: {trade.pnl:.2f}')
    
    def start(self):
        self.log('Starting backtest...')
        self.log(f'Starting cash: {self.broker.getvalue():,.2f}')
    
    def next(self):
        # 每天都打印当前状态
        date = self.datas[0].datetime.date(0)
        current_price = self.data.close[0]
        current_value = self.broker.getvalue()
        
        # 只在关键节点打印
        if date.day == 1 or not self.bought or len(self) == len(self.data) - 1:
            self.log(f'Price: {current_price:.2f}, Value: {current_value:,.2f}, Position: {self.position.size}')
        
        if self.order or self.bought:
            return
        
        # 买入！
        self.log(f'Placing BUY order...')
        self.order = self.buy()
        self.bought = True
    
    def stop(self):
        self.log('Backtest completed!')
        self.log(f'Final value: {self.broker.getvalue():,.2f}')


def main():
    print("=" * 80)
    print("  DEBUG - 永不卖出策略调试")
    print("=" * 80)
    
    print("\n[1] 获取市场数据...")
    fetcher = StockDataFetcher()
    data = fetcher.get_index_data('sh.000001', '2019-01-01', '2025-06-01')
    fetcher.logout()
    
    print("\n[2] 计算理论买入持有收益...")
    start_price = data['close'].iloc[0]
    end_price = data['close'].iloc[-1]
    bh_return = (end_price / start_price - 1) * 100
    bh_value = 1000000 * (end_price / start_price)
    print(f"  初始价格: {start_price:.2f}")
    print(f"  最终价格: {end_price:.2f}")
    print(f"  理论买入持有收益率: {bh_return:+.2f}%")
    print(f"  理论买入持有市值: {bh_value:,.2f}")
    
    print("\n[3] 运行带日志的回测...")
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(0.0003)
    
    df = data.copy()
    df['datetime'] = pd.to_datetime(df['date'])
    df = df.set_index('datetime')
    data_feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data_feed)
    
    cerebro.addstrategy(NeverSellDebugStrategy)
    
    print(f"\n{'=' * 80}")
    print("  策略运行日志")
    print(f"{'=' * 80}\n")
    
    cerebro.run()
    
    final_value = cerebro.broker.getvalue()
    print(f"\n{'=' * 80}")
    print("  最终结果")
    print(f"{'=' * 80}")
    print(f"  策略最终市值: {final_value:,.2f}")
    print(f"  理论买入持有: {bh_value:,.2f}")
    print(f"  差异: {final_value - bh_value:,.2f}")
    print(f"  差异比例: {((final_value / bh_value) - 1) * 100:.2f}%")


if __name__ == '__main__':
    main()

