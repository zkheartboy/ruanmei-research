"""
快速回测测试脚本
"""

import sys
import os
sys.path.insert(0, '/workspace/quant_backtest')

from data.fetcher import StockDataFetcher
from backtest.engine import run_single_backtest
from strategies.ma_cross import DualMAStrategy

print("="*60)
print("快速回测测试")
print("="*60)

# 1. 获取少量数据测试
print("\n[1] 测试数据获取...")
fetcher = StockDataFetcher()

# 使用较短时间范围快速测试
test_data = fetcher.get_index_data('sh.000001', '2023-01-01', '2025-12-31')
print(f"获取到 {len(test_data)} 条数据")
print(test_data.head())

fetcher.logout()

# 2. 运行简单回测
print("\n[2] 运行双均线策略回测...")
print("参数: fast_period=20, slow_period=60")

result = run_single_backtest(
    test_data,
    DualMAStrategy,
    {'fast_period': 20, 'slow_period': 60}
)

# 3. 显示结果
print("\n[3] 回测结果:")
print(f"最终市值: {result.get('final_value', 0):.2f}")
print(f"夏普比率: {result.get('sharpe', 0):.3f}")

dd = result.get('drawdown', {})
print(f"最大回撤: {dd.get('max', {}).get('drawdown', 0):.2f}%")

trades = result.get('trades', {})
print(f"总交易次数: {trades.get('total', {}).get('total', 0)}")

print("\n✅ 测试完成!")
