"""
量化投资回测主程序
方向一：实际回测验证

主要功能：
1. 获取A股历史数据
2. 运行双均线策略回测
3. 运行均线+RSI策略回测
4. 参数优化与对比分析
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.fetcher import StockDataFetcher
from backtest.engine import run_single_backtest, run_multiple_strategies
from backtest.analyzer import PerformanceAnalyzer, compare_strategies
from backtest.optimizer import ParameterOptimizer, PARAM_GRIDS
from strategies.ma_cross import DualMAStrategy, MA_Only_UpStrategy
from strategies.ma_rsi import MA_RSI_Strategy, MA_RSI_FilterStrategy
from strategies.ma_rsi_stop import CombinedStrategy
from config.settings import (
    INITIAL_CASH, COMMISSION, 
    BACKTEST_START, BACKTEST_END,
    ETF_LIST, INDEX_CODES
)


def print_banner():
    """打印横幅"""
    print("\n" + "="*70)
    print("  量化投资策略回测系统 - 方向一：实际回测验证")
    print("="*70)


def fetch_all_data(start_date=BACKTEST_START, end_date=BACKTEST_END):
    """
    获取所有测试数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        dict: {名称: DataFrame}
    """
    print("\n[1/5] 获取A股历史数据...")
    print(f"    时间范围: {start_date} 至 {end_date}")
    
    fetcher = StockDataFetcher()
    all_data = {}
    
    # 获取指数数据
    print("\n  正在获取指数数据...")
    for name, code in INDEX_CODES.items():
        print(f"    - {name} ({code})...")
        try:
            df = fetcher.get_index_data(code, start_date, end_date)
            all_data[name] = df
            print(f"      ✅ 获取成功: {len(df)} 条数据")
        except Exception as e:
            print(f"      ❌ 获取失败: {e}")
    
    # 获取ETF数据
    print("\n  正在获取ETF数据...")
    for name, code in ETF_LIST.items():
        print(f"    - {name} ({code})...")
        try:
            df = fetcher.get_etf_data(code, start_date, end_date)
            all_data[name] = df
            print(f"      ✅ 获取成功: {len(df)} 条数据")
        except Exception as e:
            print(f"      ❌ 获取失败: {e}")
    
    fetcher.logout()
    
    return all_data


def run_strategy_comparison(data, strategy_list, name='测试'):
    """
    运行策略对比
    
    Args:
        data: 数据
        strategy_list: [(策略类, 参数), ...]
        name: 测试名称
    
    Returns:
        DataFrame: 对比结果
    """
    print(f"\n[3/5] 运行{name}策略对比...")
    
    results = run_multiple_strategies(data, strategy_list, INITIAL_CASH)
    
    print(f"\n  对比结果:")
    print(results.to_string(index=False))
    
    return results


def run_parameter_optimization(data, strategy_class, param_grid_key, sample_size=100):
    """
    运行参数优化
    
    Args:
        data: 数据
        strategy_class: 策略类
        param_grid_key: 参数网格键名
        sample_size: 样本数量（用于加速优化）
    
    Returns:
        DataFrame: 优化结果
    """
    print(f"\n[4/5] 运行参数优化...")
    print(f"    策略: {strategy_class.__name__}")
    print(f"    参数网格: {param_grid_key}")
    
    # 如果数据太多，取最后sample_size条
    if len(data) > sample_size:
        print(f"    数据量 {len(data)} > {sample_size}，使用最近数据")
        data = data.tail(sample_size)
    
    param_grid = PARAM_GRIDS.get(param_grid_key, {})
    
    if not param_grid:
        print(f"    ❌ 未找到参数网格: {param_grid_key}")
        return None
    
    optimizer = ParameterOptimizer(data, strategy_class)
    results = optimizer.grid_search(param_grid, INITIAL_CASH)
    
    if len(results) > 0:
        print(f"\n  最优参数组合 (Top 5):")
        top_results = optimizer.get_top_n(5, 'sharpe_ratio')
        print(top_results.to_string(index=False))
    
    return results


def generate_report(all_results, output_file='backtest_report.md'):
    """
    生成回测报告
    
    Args:
        all_results: 所有结果
        output_file: 输出文件名
    """
    print(f"\n[5/5] 生成回测报告...")
    
    report = []
    report.append("# 量化投资策略回测报告")
    report.append("")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("---")
    report.append("")
    
    for name, result_df in all_results.items():
        report.append(f"## {name}")
        report.append("")
        report.append(result_df.to_markdown(index=False))
        report.append("")
    
    report_content = "\n".join(report)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"    ✅ 报告已保存到: {output_file}")


def main():
    """主函数"""
    print_banner()
    
    # 1. 获取数据
    all_data = fetch_all_data()
    
    if not all_data:
        print("\n❌ 数据获取失败，程序退出")
        return
    
    # 保存获取的数据
    print("\n[2/5] 保存数据...")
    os.makedirs('data/daily', exist_ok=True)
    for name, df in all_data.items():
        filename = f"data/daily/{name.replace(' ', '_')}.csv"
        df.to_csv(filename, index=False)
        print(f"    ✅ {name} -> {filename}")
    
    # 选择主要测试数据
    main_data = all_data.get('上证指数')
    
    if main_data is None or len(main_data) == 0:
        print("\n❌ 主测试数据为空，程序退出")
        return
    
    print(f"\n  使用上证指数数据进行回测，共 {len(main_data)} 条数据")
    
    # 2. 策略对比测试
    strategy_list = [
        (DualMAStrategy, {'fast_period': 20, 'slow_period': 60}),
        (DualMAStrategy, {'fast_period': 10, 'slow_period': 30}),
        (MA_Only_UpStrategy, {'ma_period': 60}),
        (MA_RSI_Strategy, {'fast_period': 20, 'slow_period': 60, 'rsi_period': 14}),
        (CombinedStrategy, {
            'fast_period': 20, 'slow_period': 60, 
            'rsi_period': 14,
            'stop_loss_pct': 0.08, 'trailing_pct': 0.12
        }),
    ]
    
    comparison_results = run_strategy_comparison(main_data, strategy_list, "主要")
    
    # 3. ETF对比测试
    etf_results = {}
    for name, df in all_data.items():
        if name in ETF_LIST:
            try:
                result = run_single_backtest(df, DualMAStrategy, 
                                           {'fast_period': 20, 'slow_period': 60})
                analyzer = PerformanceAnalyzer(result, INITIAL_CASH)
                metrics = analyzer.get_metrics()
                etf_results[name] = pd.DataFrame([metrics])
            except Exception as e:
                print(f"    ⚠️ {name} 回测失败: {e}")
    
    if etf_results:
        print("\n  ETF回测结果:")
        for name, df in etf_results.items():
            print(f"    - {name}: {df['总收益率'].values[0]:.2f}%")
    
    # 4. 参数优化（使用较短时间范围加速）
    optimizer_results = {}
    
    # 双均线参数优化
    ma_opt_results = run_parameter_optimization(
        main_data, DualMAStrategy, 'dual_ma', sample_size=500
    )
    if ma_opt_results is not None:
        optimizer_results['双均线参数优化'] = ma_opt_results
    
    # 5. 生成报告
    all_results = {
        '策略对比': comparison_results,
        **optimizer_results
    }
    
    if etf_results:
        all_results['ETF对比'] = pd.concat(etf_results.values(), ignore_index=True)
    
    generate_report(all_results, 'quant_backtest_report.md')
    
    print("\n" + "="*70)
    print("  回测完成!")
    print("="*70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()
