
"""
优化策略对比回测 - 解决与买入持有差距问题
"""

import sys
import os
sys.path.insert(0, '/workspace/quant_backtest')

import pandas as pd
import numpy as np
from datetime import datetime
from data.fetcher import StockDataFetcher
from backtest.engine import run_single_backtest
from strategies.ma_cross import DualMAStrategy
from strategies.optimized_strategies import (
    OptimizedDualMAStrategy, 
    TrendingStrategy, 
    SimpleTrendStrategy
)
import backtrader as bt


def run_backtest(data, strategy_class, params=None):
    """运行回测并返回结果"""
    if params is None:
        params = {}
    
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(0.0003)
    
    # 准备数据
    df = data.copy()
    df['datetime'] = pd.to_datetime(df['date'])
    df = df.set_index('datetime')
    data_feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data_feed)
    
    # 添加策略
    cerebro.addstrategy(strategy_class, **params)
    
    # 运行回测
    cerebro.run()
    
    final_value = cerebro.broker.getvalue()
    return final_value


def main():
    print("=" * 80)
    print("  量化策略优化对比 - 解决与买入持有差距问题")
    print("=" * 80)
    
    # 1. 获取数据
    print("\n[1] 获取市场数据...")
    fetcher = StockDataFetcher()
    data = fetcher.get_index_data('sh.000001', '2019-01-01', '2025-06-01')
    fetcher.logout()
    
    # 2. 计算买入持有收益
    print("\n[2] 计算买入持有收益...")
    start_price = data['close'].iloc[0]
    end_price = data['close'].iloc[-1]
    bh_return = (end_price / start_price - 1) * 100
    print(f"  买入持有收益率: {bh_return:+.2f}%")
    print(f"  最终市值: {1000000 * (end_price / start_price):,.2f}")
    
    # 3. 定义策略列表
    strategies = [
        ("原策略-20/60", DualMAStrategy, 
         {'fast_period': 20, 'slow_period': 60}),
        ("优化策略-5/20", OptimizedDualMAStrategy,
         {'fast_period': 5, 'slow_period': 20, 'trend_period': 60}),
        ("趋势策略-EMA", TrendingStrategy,
         {'fast_period': 10, 'slow_period': 30}),
        ("极简趋势", SimpleTrendStrategy,
         {'period': 20}),
    ]
    
    print("\n[3] 运行各策略回测...")
    
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
    
    # 4. 结果汇总
    print(f"\n\n{'=' * 80}")
    print(f"  策略对比汇总表")
    print(f"{'=' * 80}")
    
    # 添加买入持有
    results.append({
        '策略名称': '买入持有',
        '最终市值': 1000000 * (end_price / start_price),
        '总收益率': bh_return,
        '超额收益': 0
    })
    
    df = pd.DataFrame(results)
    df = df.sort_values('总收益率', ascending=False)
    
    pd.set_option('display.width', 200)
    pd.set_option('display.float_format', '{:,.2f}'.format)
    
    print(df.to_string(index=False))
    
    # 5. 分析和建议
    print(f"\n\n{'=' * 80}")
    print(f"  分析总结")
    print(f"{'=' * 80}")
    
    best_strategy = results[np.argmax([r['总收益率'] for r in results[:-1]])]
    print(f"\n  🎯 最优策略: {best_strategy['策略名称']}")
    print(f"     总收益率: {best_strategy['总收益率']:+.2f}%")
    print(f"     超额收益: {best_strategy['超额收益']:+.2f}%")
    
    print(f"\n  📊 改进点:")
    print("    1. 使用更激进的均线周期（5/20）")
    print("    2. 增加大趋势判断，不轻易止盈")
    print("    3. 使用EMA反应更快，减少延迟")
    print("    4. 降低卖出条件，避免在上涨初期卖出")
    
    # 保存结果
    output_file = '/workspace/quant_backtest/优化策略对比.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n  ✅ 结果已保存到: {output_file}")


if __name__ == '__main__':
    main()

