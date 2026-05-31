
"""
年化收益分析脚本
计算回测的每年年化收益
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
import backtrader as bt


class TimeReturnAnalyzer(bt.Analyzer):
    """
    自定义时间收益分析器
    记录每年的收益率
    """
    def __init__(self):
        self.rets = {}
        self.start_value = None
        self.prev_year = None
        
    def start(self):
        self.start_value = self.strategy.broker.getvalue()
        self.rets = {}
        
    def next(self):
        current_date = self.data.datetime.date(0)
        current_year = current_date.year
        
        if self.prev_year is not None and current_year != self.prev_year:
            # 新的一年开始
            current_value = self.strategy.broker.getvalue()
            year_return = (current_value - self.start_value) / self.start_value
            self.rets[self.prev_year] = year_return
            self.start_value = current_value
            
        self.prev_year = current_year
        
    def stop(self):
        # 最后一年
        if self.prev_year is not None:
            current_value = self.strategy.broker.getvalue()
            year_return = (current_value - self.start_value) / self.start_value
            self.rets[self.prev_year] = year_return
            
    def get_analysis(self):
        return self.rets


def run_with_yearly_analysis(data, strategy_class, strategy_params=None):
    """
    运行回测并分析年度收益
    """
    if strategy_params is None:
        strategy_params = {}
    
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
    cerebro.addstrategy(strategy_class, **strategy_params)
    
    # 添加分析器
    cerebro.addanalyzer(TimeReturnAnalyzer, _name='yearlyreturns')
    
    # 运行回测
    results = cerebro.run()
    
    return {
        'yearly_returns': results[0].analyzers.yearlyreturns.get_analysis(),
        'final_value': cerebro.broker.getvalue()
    }


def main():
    print("=" * 70)
    print("  量化投资策略回测 - 年度收益分析")
    print("=" * 70)
    
    # 1. 获取数据
    print("\n[1] 获取市场数据...")
    fetcher = StockDataFetcher()
    data = fetcher.get_index_data('sh.000001', '2019-01-01', '2025-06-01')
    fetcher.logout()
    
    # 定义策略列表
    strategies = [
        ("双均线(20,60)", DualMAStrategy, {'fast_period': 20, 'slow_period': 60}),
        ("双均线(10,30)", DualMAStrategy, {'fast_period': 10, 'slow_period': 30}),
    ]
    
    print("\n[2] 分析各策略年度收益...")
    
    all_results = []
    
    for name, strategy_class, params in strategies:
        print(f"\n  分析: {name}")
        
        result = run_with_yearly_analysis(data, strategy_class, params)
        yearly_returns = result['yearly_returns']
        
        print(f"    最终市值: {result['final_value']:,.2f}")
        
        # 存储结果
        strategy_result = {
            '策略': name,
            '总收益率': (result['final_value'] / 1000000 - 1) * 100
        }
        
        for year in sorted(yearly_returns.keys()):
            strategy_result[f'{year}年收益'] = yearly_returns[year] * 100
            
        all_results.append(strategy_result)
        
        # 打印年度收益
        print(f"    年度收益率:")
        for year in sorted(yearly_returns.keys()):
            print(f"      {year}: {yearly_returns[year] * 100:+.2f}%")
    
    # 计算买入持有年度收益
    print(f"\n\n{'=' * 70}")
    print(f"  买入持有策略年度收益")
    print(f"{'=' * 70}")
    
    # 计算年度收益
    data_sorted = data.sort_values('date')
    data_sorted['year'] = data_sorted['date'].dt.year
    
    bh_yearly_returns = {}
    prev_close = None
    prev_year = None
    first_year_close = None
    last_year_close = None
    
    for year, group in data_sorted.groupby('year'):
        year_start = group['close'].iloc[0]
        year_end = group['close'].iloc[-1]
        
        if prev_close is not None:
            bh_yearly_returns[prev_year] = (year_start / prev_close - 1) * 100
        
        prev_close = year_end
        prev_year = year
        
        if first_year_close is None:
            first_year_close = year_start
        last_year_close = year_end
    
    # 添加最后一年
    if prev_year is not None and prev_close is not None:
        bh_yearly_returns[prev_year] = 0  # 最后一年未结束
    
    print(f"  总收益率: {(last_year_close / first_year_close - 1) * 100:.2f}%")
    print(f"  年度收益率:")
    for year in sorted(bh_yearly_returns.keys()):
        print(f"    {year}: {bh_yearly_returns[year]:+.2f}%")
    
    # 汇总表格
    print(f"\n\n{'=' * 70}")
    print(f"  策略年度收益对比表")
    print(f"{'=' * 70}")
    
    # 构建结果DataFrame
    bh_result = {
        '策略': '买入持有',
        '总收益率': (last_year_close / first_year_close - 1) * 100
    }
    for year in bh_yearly_returns:
        bh_result[f'{year}年收益'] = bh_yearly_returns[year]
    
    all_results.append(bh_result)
    
    df = pd.DataFrame(all_results)
    pd.set_option('display.width', 200)
    pd.set_option('display.float_format', '{:,.2f}'.format)
    
    print(df.to_string(index=False))
    
    # 保存结果
    output_file = '/workspace/quant_backtest/年度收益分析.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ 结果已保存到: {output_file}")


if __name__ == '__main__':
    main()

