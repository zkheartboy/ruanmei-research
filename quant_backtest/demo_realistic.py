"""
真实市场数据回测 - 完整演示
使用增强模拟数据（包含牛市、熊市、震荡市）
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

import pandas as pd
import numpy as np
from datetime import datetime

def print_banner():
    print("\n" + "="*70)
    print("  量化投资策略回测 - 真实市场数据版本")
    print("="*70)

def analyze_market_features(data):
    """分析市场特征"""
    print("\n" + "-"*70)
    print("  市场特征分析")
    print("-"*70)
    
    returns = data['close'].pct_change().dropna()
    volatility = returns.std() * np.sqrt(252)
    total_return = (data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100
    
    print(f"    日期范围: {data['date'].min()} - {data['date'].max()}")
    print(f"    交易日数: {len(data)}")
    print(f"    起点价格: {data['close'].iloc[0]:.2f}")
    print(f"    终点价格: {data['close'].iloc[-1]:.2f}")
    print(f"    总收益率: {total_return:.2f}%")
    print(f"    年化波动率: {volatility * 100:.2f}%")
    print(f"    最大日涨幅: {returns.max() * 100:.2f}%")
    print(f"    最大日跌幅: {returns.min() * 100:.2f}%")
    
    # 计算涨跌天数
    up_days = len(returns[returns > 0])
    down_days = len(returns[returns < 0])
    print(f"    上涨天数: {up_days} ({up_days/len(returns)*100:.1f}%)")
    print(f"    下跌天数: {down_days} ({down_days/len(returns)*100:.1f}%)")

def main():
    print_banner()
    
    # 1. 获取数据
    print("\n[1] 获取市场数据...")
    fetcher = StockDataFetcher()
    
    # 使用2019-2025年数据（包含牛熊周期）
    data = fetcher.get_index_data('sh.000001', '2019-01-01', '2025-06-01')
    fetcher.logout()
    
    # 2. 分析市场特征
    analyze_market_features(data)
    
    # 3. 定义策略列表
    print("\n[2] 准备回测策略...")
    
    strategies = [
        ("双均线(20,60)", DualMAStrategy, {'fast_period': 20, 'slow_period': 60}),
        ("双均线(10,30)", DualMAStrategy, {'fast_period': 10, 'slow_period': 30}),
        ("双均线(10,60)", DualMAStrategy, {'fast_period': 10, 'slow_period': 60}),
        ("均线+RSI", MA_RSI_Strategy, {
            'fast_period': 20, 'slow_period': 60,
            'rsi_period': 14
        }),
        ("均线+严格RSI", MA_RSI_FilterStrategy, {
            'fast_period': 20, 'slow_period': 60,
            'rsi_period': 14,
            'rsi_buy_threshold': 35,
            'rsi_sell_threshold': 65
        }),
        ("均线+止损", CombinedStrategy, {
            'fast_period': 20, 'slow_period': 60,
            'rsi_period': 14,
            'stop_loss_pct': 0.08,
            'trailing_pct': 0.12
        }),
    ]
    
    # 4. 运行回测
    print("\n[3] 运行回测...")
    
    results = []
    for name, strategy_class, params in strategies:
        print(f"\n    回测: {name}...")
        
        result = run_single_backtest(data, strategy_class, params)
        
        analyzer = PerformanceAnalyzer(result, initial_cash=1000000)
        metrics = analyzer.get_metrics()
        metrics['策略名称'] = name
        
        results.append(metrics)
        
        # 打印详细结果
        print(f"      最终市值: {metrics['最终市值']:.2f}")
        print(f"      总收益率: {metrics['总收益率']:.2f}%")
        print(f"      夏普比率: {metrics['夏普比率']:.3f}")
        print(f"      最大回撤: {metrics['最大回撤']:.2f}%")
        print(f"      交易次数: {metrics['总交易次数']}")
        
        if '胜率' in metrics and metrics['总交易次数'] > 0:
            print(f"      胜率: {metrics['胜率']:.1f}%")
        if '盈利次数' in metrics:
            print(f"      盈利次数: {metrics['盈利次数']}")
        if '亏损次数' in metrics:
            print(f"      亏损次数: {metrics['亏损次数']}")
    
    # 5. 结果汇总
    print("\n" + "="*70)
    print("  策略对比结果")
    print("="*70)
    
    # 创建对比表格
    print("\n" + "┌" + "─"*22 + "┬" + "─"*12 + "┬" + "─"*10 + "┬" + "─"*12 + "┬" + "─"*10 + "┐")
    print("│ 策略名称           │ 总收益率   │ 夏普比率  │ 最大回撤   │ 交易次数  │")
    print("├" + "─"*22 + "┼" + "─"*12 + "┼" + "─"*10 + "┼" + "─"*12 + "┼" + "─"*10 + "┤")
    
    for r in results:
        print(f"│ {r['策略名称']:20s} │ {r['总收益率']:10.2f}% │ {r['夏普比率']:9.3f} │ {r['最大回撤']:10.2f}% │ {r['总交易次数']:9d} │")
    
    print("└" + "─"*22 + "┴" + "─"*12 + "┴" + "─"*10 + "┴" + "─"*12 + "┴" + "─"*10 + "┘")
    
    # 6. 分析结论
    print("\n[4] 分析结论...")
    
    # 找出最优策略
    best_by_return = max(results, key=lambda x: x['总收益率'])
    best_by_sharpe = max(results, key=lambda x: x['夏普比率'])
    best_by_dd = min(results, key=lambda x: x['最大回撤'])
    
    print(f"\n    🎯 总收益率最高: {best_by_return['策略名称']}")
    print(f"       收益率: {best_by_return['总收益率']:.2f}%")
    
    print(f"\n    📈 夏普比率最高: {best_by_sharpe['策略名称']}")
    print(f"       夏普比率: {best_by_sharpe['夏普比率']:.3f}")
    
    print(f"\n    🛡️  回撤最小: {best_by_dd['策略名称']}")
    print(f"       最大回撤: {best_by_dd['最大回撤']:.2f}%")
    
    # 与买入持有对比
    buy_hold_return = (data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100
    print(f"\n    💎 买入持有收益: {buy_hold_return:.2f}%")
    
    # 计算超额收益
    for r in results:
        excess = r['总收益率'] - buy_hold_return
        if excess > 0:
            print(f"       {r['策略名称']}: 超额收益 {excess:.2f}% ✅")
        else:
            print(f"       {r['策略名称']}: 超额收益 {excess:.2f}%")
    
    # 7. 保存结果
    print("\n[5] 保存回测结果...")
    
    results_df = pd.DataFrame(results)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'/workspace/quant_backtest/backtest_results_{timestamp}.csv'
    results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"    ✅ 结果已保存到: {output_file}")
    
    # 8. 建议
    print("\n" + "="*70)
    print("  后续建议")
    print("="*70)
    print("""
    1. 参数优化
       - 使用Walk-Forward方法优化各策略参数
       - 测试不同的均线组合（5/20, 10/40, 15/60等）
       - 优化RSI阈值
    
    2. 多市场测试
       - 在沪深300、中证500、创业板指数上测试
       - 在主要ETF上验证（510300, 510500等）
    
    3. 策略组合
       - 结合多个策略降低单一策略风险
       - 尝试在不同市场环境下切换策略
    
    4. 实盘准备
       - 增加滑点和手续费的敏感性测试
       - 研究实时数据源接入
       - 开发风险监控系统
    """)
    
    print("\n✅ 完整回测演示完成!")
    print("="*70)

if __name__ == '__main__':
    main()
