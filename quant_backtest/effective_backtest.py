
"""
有效策略回测 - 解决与买入持有差距太大的问题
"""

import sys
import os
sys.path.insert(0, '/workspace/quant_backtest')

import pandas as pd
import numpy as np
from datetime import datetime
from data.fetcher import StockDataFetcher
from strategies.ma_cross import DualMAStrategy
from strategies.effective_strategies import (
    LongTermTrendStrategy,
    BuyHoldLikeStrategy,
    AggressiveTrendStrategy
)
import backtrader as bt


def run_backtest(data, strategy_class, params=None):
    """运行回测并返回结果"""
    if params is None:
        params = {}
    
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(0.0003)
    
    df = data.copy()
    df['datetime'] = pd.to_datetime(df['date'])
    df = df.set_index('datetime')
    data_feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data_feed)
    
    cerebro.addstrategy(strategy_class, **params)
    cerebro.run()
    
    final_value = cerebro.broker.getvalue()
    return final_value


def main():
    print("=" * 80)
    print("  有效策略回测 - 解决与买入持有差距太大问题")
    print("=" * 80)
    
    print("\n[1] 获取市场数据...")
    fetcher = StockDataFetcher()
    data = fetcher.get_index_data('sh.000001', '2019-01-01', '2025-06-01')
    fetcher.logout()
    
    print("\n[2] 计算买入持有收益...")
    start_price = data['close'].iloc[0]
    end_price = data['close'].iloc[-1]
    bh_return = (end_price / start_price - 1) * 100
    bh_value = 1000000 * (end_price / start_price)
    print(f"  买入持有收益率: {bh_return:+.2f}%")
    print(f"  买入持有市值: {bh_value:,.2f}")
    
    print("\n[3] 定义策略列表...")
    strategies = [
        ("原策略-20/60", DualMAStrategy, {'fast_period': 20, 'slow_period': 60}),
        ("长期趋势", LongTermTrendStrategy, {'ma_period': 60, 'confirm_period': 5}),
        ("类买入持有", BuyHoldLikeStrategy, {'ma_period': 60, 'threshold': 0.95}),
        ("激进趋势", AggressiveTrendStrategy, {'fast_period': 10, 'slow_period': 60}),
    ]
    
    print("\n[4] 运行各策略回测...")
    results = []
    for name, strategy_class, params in strategies:
        print(f"\n  测试: {name}")
        
        final_value = run_backtest(data, strategy_class, params)
        total_return = (final_value / 1000000 - 1) * 100
        excess_return = total_return - bh_return
        
        results.append({
            '策略名称': name,
            '最终市值': final_value,
            '总收益率': total_return,
            '超额收益': excess_return
        })
        
        print(f"    最终市值: {final_value:,.2f}")
        print(f"    总收益率: {total_return:+.2f}%")
        print(f"    超额收益: {excess_return:+.2f}%")
    
    print(f"\n\n{'=' * 80}")
    print(f"  策略对比汇总")
    print(f"{'=' * 80}")
    
    results.append({
        '策略名称': '买入持有',
        '最终市值': bh_value,
        '总收益率': bh_return,
        '超额收益': 0
    })
    
    df = pd.DataFrame(results)
    df = df.sort_values('总收益率', ascending=False)
    
    pd.set_option('display.width', 200)
    pd.set_option('display.float_format', '{:,.2f}'.format)
    
    print(df.to_string(index=False))
    
    print(f"\n\n{'=' * 80}")
    print(f"  分析总结")
    print(f"{'=' * 80}")
    
    non_bh = results[:-1]
    best_strategy = non_bh[np.argmax([r['总收益率'] for r in non_bh])]
    
    print(f"\n  Best strategy: {best_strategy['策略名称']}")
    print(f"  Total return: {best_strategy['总收益率']:+.2f}%")
    print(f"  Excess return: {best_strategy['超额收益']:+.2f}%")
    
    if best_strategy['超额收益'] > 0:
        print("  Success! Outperformed buy and hold!")
    else:
        print("  Did not outperform buy and hold.")
    
    print(f"\n  Key improvements:")
    print("    1. Reduce sell frequency, don't take profit easily in uptrends")
    print("    2. Use longer-term trend to reduce false signals")
    print("    3. Only sell when real trend reversal happens")
    
    output_file = '/workspace/quant_backtest/有效策略对比.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n  Results saved to: {output_file}")


if __name__ == '__main__':
    main()

