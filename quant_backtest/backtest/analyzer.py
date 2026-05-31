"""
绩效分析器
分析回测结果，生成详细报告
"""

import pandas as pd
import numpy as np
from datetime import datetime


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self, analysis_result, initial_cash):
        self.analysis = analysis_result
        self.initial_cash = initial_cash
        
    def get_metrics(self):
        """获取关键指标"""
        final_value = self.analysis.get('final_value', self.initial_cash)
        total_return = (final_value / self.initial_cash - 1) * 100
        
        sharpe = self.analysis.get('sharpe')
        sharpe_ratio = sharpe if sharpe else 0
        
        dd = self.analysis.get('drawdown', {})
        max_drawdown = dd.get('max', {}).get('drawdown', 0) if dd else 0
        max_dd_len = dd.get('max', {}).get('len', 0) if dd else 0
        
        returns = self.analysis.get('returns', {})
        annualized = returns.get('rtot', 0) * 100 if returns else 0
        
        trades = self.analysis.get('trades', {})
        total_trades = trades.get('total', {}).get('total', 0) if trades else 0
        won_trades = trades.get('won', {}).get('total', 0) if trades else 0
        lost_trades = trades.get('lost', {}).get('total', 0) if trades else 0
        
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            '最终市值': final_value,
            '总收益率': total_return,
            '年化收益率': annualized,
            '夏普比率': sharpe_ratio,
            '最大回撤': max_drawdown,
            '最大回撤时长': max_dd_len,
            '总交易次数': total_trades,
            '盈利次数': won_trades,
            '亏损次数': lost_trades,
            '胜率': win_rate,
        }
    
    def print_report(self):
        """打印绩效报告"""
        metrics = self.get_metrics()
        
        print("\n" + "="*60)
        print("回测绩效报告")
        print("="*60)
        
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        
        # 计算卡玛比率
        annualized = metrics['年化收益率']
        max_dd = metrics['最大回撤']
        
        if max_dd > 0:
            calmar = annualized / max_dd
            print(f"卡玛比率: {calmar:.3f}")
        
        print("="*60)
    
    def to_dataframe(self):
        """转换为DataFrame"""
        return pd.DataFrame([self.get_metrics()])


def calculate_returns_metrics(returns_series, risk_free_rate=0.03):
    """
    计算收益指标
    
    Args:
        returns_series: 收益率序列
        risk_free_rate: 无风险利率（年化）
    
    Returns:
        dict: 收益指标
    """
    # 年化收益率
    total_return = (1 + returns_series).prod() - 1
    n_periods = len(returns_series)
    annualized = (1 + total_return) ** (250 / n_periods) - 1
    
    # 年化波动率
    volatility = returns_series.std() * np.sqrt(250)
    
    # 夏普比率
    sharpe = (annualized - risk_free_rate) / volatility if volatility > 0 else 0
    
    # 最大回撤
    cumulative = (1 + returns_series).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    return {
        '总收益率': total_return * 100,
        '年化收益率': annualized * 100,
        '年化波动率': volatility * 100,
        '夏普比率': sharpe,
        '最大回撤': max_drawdown * 100,
    }


def compare_strategies(results_list, names):
    """
    对比多个策略
    
    Args:
        results_list: 回测结果列表
        names: 策略名称列表
    
    Returns:
        DataFrame: 对比结果
    """
    compare_data = []
    
    for result, name in zip(results_list, names):
        analyzer = PerformanceAnalyzer(result, INITIAL_CASH=1000000)
        metrics = analyzer.get_metrics()
        metrics['策略名称'] = name
        compare_data.append(metrics)
    
    df = pd.DataFrame(compare_data)
    
    # 重新排列列顺序
    cols = ['策略名称', '总收益率', '年化收益率', '夏普比率', '最大回撤', '胜率', '总交易次数']
    available_cols = [col for col in cols if col in df.columns]
    
    return df[available_cols]
