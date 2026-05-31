"""
量化投资策略回测 - 完整演示
"""

import sys
import os
sys.path.insert(0, '/workspace/quant_backtest')

from data.fetcher import StockDataFetcher
from backtest.engine import run_single_backtest, run_multiple_strategies
from backtest.analyzer import PerformanceAnalyzer
from strategies.ma_cross import DualMAStrategy, MA_Only_UpStrategy
from strategies.ma_rsi import MA_RSI_Strategy, MA_RSI_FilterStrategy
from strategies.ma_rsi_stop import CombinedStrategy

def print_banner():
    print("\n" + "="*70)
    print("  量化投资策略回测系统 - 完整演示")
    print("="*70)


def main():
    print_banner()
    
    # 1. 获取数据
    print("\n[1] 获取市场数据...")
    print("    (由于baostock服务暂时不可用，使用模拟数据)")
    
    fetcher = StockDataFetcher()
    
    # 使用3年数据进行回测
    data = fetcher.get_index_data('sh.000001', '2022-01-01', '2025-05-30')
    fetcher.logout()
    
    print(f"    数据量: {len(data)} 条")
    print(f"    日期范围: {data['date'].min()} 至 {data['date'].max()}")
    
    # 2. 定义策略列表
    print("\n[2] 定义测试策略...")
    
    strategies = [
        ("双均线(20,60)", DualMAStrategy, {'fast_period': 20, 'slow_period': 60}),
        ("双均线(10,30)", DualMAStrategy, {'fast_period': 10, 'slow_period': 30}),
        ("均线+RSI", MA_RSI_Strategy, {
            'fast_period': 20, 'slow_period': 60, 
            'rsi_period': 14,
            'rsi_buy_threshold': 40, 'rsi_sell_threshold': 60
        }),
        ("均线+严格RSI", MA_RSI_FilterStrategy, {
            'fast_period': 20, 'slow_period': 60,
            'rsi_period': 14,
            'rsi_buy_threshold': 35, 'rsi_sell_threshold': 65
        }),
        ("均线+止损", CombinedStrategy, {
            'fast_period': 20, 'slow_period': 60,
            'rsi_period': 14,
            'stop_loss_pct': 0.08, 'trailing_pct': 0.12
        }),
    ]
    
    # 3. 运行回测
    print("\n[3] 运行回测...")
    
    results = []
    for name, strategy_class, params in strategies:
        print(f"\n    回测: {name}...")
        
        result = run_single_backtest(data, strategy_class, params)
        
        analyzer = PerformanceAnalyzer(result, initial_cash=1000000)
        metrics = analyzer.get_metrics()
        metrics['策略名称'] = name
        
        results.append(metrics)
        
        # 打印简要结果
        print(f"      总收益: {metrics['总收益率']:.2f}%")
        print(f"      夏普比率: {metrics['夏普比率']:.3f}")
        print(f"      最大回撤: {metrics['最大回撤']:.2f}%")
        print(f"      交易次数: {metrics['总交易次数']}")
    
    # 4. 结果汇总
    print("\n[4] 回测结果汇总...")
    
    print("\n" + "="*70)
    print("  策略对比结果")
    print("="*70)
    
    print(f"\n{'策略名称':<20} {'总收益':<12} {'夏普比率':<10} {'最大回撤':<12} {'交易次数':<10}")
    print("-" * 70)
    
    for r in results:
        print(f"{r['策略名称']:<20} {r['总收益率']:>10.2f}% {r['夏普比率']:>10.3f} {r['最大回撤']:>10.2f}% {r['总交易次数']:>10}")
    
    # 5. 分析结论
    print("\n[5] 分析结论...")
    
    # 找出最优策略
    best_by_return = max(results, key=lambda x: x['总收益率'])
    best_by_sharpe = max(results, key=lambda x: x['夏普比率'])
    best_by_dd = min(results, key=lambda x: x['最大回撤'])
    
    print(f"\n  • 总收益最高: {best_by_return['策略名称']} ({best_by_return['总收益率']:.2f}%)")
    print(f"  • 夏普比率最高: {best_by_sharpe['策略名称']} ({best_by_sharpe['夏普比率']:.3f})")
    print(f"  • 回撤最小: {best_by_dd['策略名称']} ({best_by_dd['最大回撤']:.2f}%)")
    
    # 6. 风险提示
    print("\n" + "="*70)
    print("  风险提示")
    print("="*70)
    print("""
  ⚠️  本回测结果基于模拟数据，仅供参考
  
  注意事项:
  • 模拟数据可能无法完全反映真实市场特征
  • 历史表现不代表未来收益
  • 实际交易需考虑手续费、滑点、流动性等因素
  • 建议在实盘前进行充分验证
    """)
    
    print("\n✅ 回测演示完成!")
    print("="*70)


if __name__ == '__main__':
    main()
