
"""
仓位展示回测 - 显示仓位变化
"""

import sys
import os
sys.path.insert(0, '/workspace/quant_backtest')

import pandas as pd
import numpy as np
from data.fetcher import StockDataFetcher
from strategies.ma_cross import DualMAStrategy
from strategies.ultimate_strategies import (
    AlmostBuyAndHoldStrategy,
    NeverSellStrategy,
    TrendFollowMinimal
)
import backtrader as bt


def main():
    print("=" * 80)
    print("  策略仓位变化展示")
    print("=" * 80)
    
    print("\n[1] 获取市场数据...")
    fetcher = StockDataFetcher()
    data = fetcher.get_index_data('sh.000001', '2019-01-01', '2025-06-01')
    fetcher.logout()
    
    print("\n[2] 计算买入持有...")
    start_price = data['close'].iloc[0]
    end_price = data['close'].iloc[-1]
    bh_return = (end_price / start_price - 1) * 100
    bh_value = 1000000 * (end_price / start_price)
    print(f"  买入持有收益率: {bh_return:+.2f}%")
    print(f"  最终市值: {bh_value:,.2f}")
    
    print("\n[3] 运行各策略...")
    
    strategy_info = [
        ("永不卖出", NeverSellStrategy, {}),
        ("几乎买入持有", AlmostBuyAndHoldStrategy, {'ma_period': 120, 'sell_threshold': 0.85}),
        ("极简趋势", TrendFollowMinimal, {'ma_fast': 20, 'ma_slow': 120}),
        ("原策略-20/60", DualMAStrategy, {'fast_period': 20, 'slow_period': 60}),
    ]
    
    results = []
    
    for name, strategy_class, params in strategy_info:
        print(f"\n  运行: {name}")
        
        # 创建跟踪器类
        class TrackedStrategy(strategy_class):
            def __init__(self):
                super().__init__()
                self.pos_history = []
            
            def next(self):
                super().next()
                dt = self.datas[0].datetime.date(0)
                self.pos_history.append({
                    'date': dt,
                    'size': self.position.size
                })
        
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(1000000.0)
        cerebro.broker.setcommission(0.0003)
        
        df = data.copy()
        df['datetime'] = pd.to_datetime(df['date'])
        df = df.set_index('datetime')
        data_feed = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data_feed)
        
        cerebro.addstrategy(TrackedStrategy, **params)
        strat_results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        # 收集数据
        strat = strat_results[0]
        pos_df = pd.DataFrame(strat.pos_history)
        pos_df.columns = ['date', name]
        
        results.append({
            'name': name,
            'positions': pos_df,
            'final_value': final_value
        })
        
        print(f"  最终市值: {final_value:,.2f}")
    
    print("\n\n" + "=" * 80)
    print("  各策略每月末持仓展示")
    print("=" * 80)
    
    # 合并数据
    combined_df = None
    for res in results:
        name = res['name']
        df = res['positions'].copy()
        df['date'] = pd.to_datetime(df['date'])
        df['year_month'] = df['date'].dt.to_period('M')
        # 每月取最后一天
        df = df.drop_duplicates(subset='year_month', keep='last')
        
        if combined_df is None:
            combined_df = df[['year_month', name]]
        else:
            combined_df = combined_df.merge(df[['year_month', name]], on='year_month', how='outer')
    
    # 填充NaN
    combined_df = combined_df.ffill().fillna(0)
    print("\n每月末持仓股数:")
    print(combined_df.to_string(index=False))
    
    # 保存
    output_file = '/workspace/quant_backtest/策略仓位变化.csv'
    combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ 仓位变化已保存到: [策略仓位变化.csv](file:///workspace/quant_backtest/策略仓位变化.csv)")


if __name__ == '__main__':
    main()

