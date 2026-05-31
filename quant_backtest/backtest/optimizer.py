"""
参数优化模块
网格搜索最优参数
"""

import itertools
from tqdm import tqdm
from backtest.engine import run_single_backtest
import pandas as pd


class ParameterOptimizer:
    """参数优化器"""
    
    def __init__(self, data, strategy_class):
        self.data = data
        self.strategy_class = strategy_class
        self.results = []
        
    def grid_search(self, param_grid, initial_cash=1000000):
        """
        网格搜索
        
        Args:
            param_grid: 参数网格，dict，key为参数名，value为参数列表
            initial_cash: 初始资金
        
        Returns:
            DataFrame: 优化结果
        """
        # 生成所有参数组合
        keys, values = zip(*param_grid.items())
        param_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        print(f"共 {len(param_combinations)} 种参数组合")
        
        for params in tqdm(param_combinations, desc="参数优化"):
            try:
                result = run_single_backtest(
                    self.data,
                    self.strategy_class,
                    params,
                    initial_cash
                )
                
                # 提取关键指标
                final_value = result.get('final_value', initial_cash)
                total_return = (final_value / initial_cash - 1) * 100
                
                sharpe = result.get('sharpe', 0)
                sharpe = sharpe if sharpe else 0
                
                dd = result.get('drawdown', {})
                max_dd = dd.get('max', {}).get('drawdown', 0) if dd else 0
                
                trades = result.get('trades', {})
                total_trades = trades.get('total', {}).get('total', 0) if trades else 0
                
                self.results.append({
                    'params': str(params),
                    **params,
                    'final_value': final_value,
                    'total_return': total_return,
                    'sharpe_ratio': sharpe,
                    'max_drawdown': max_dd,
                    'total_trades': total_trades,
                })
            except Exception as e:
                print(f"参数 {params} 回测失败: {e}")
        
        df = pd.DataFrame(self.results)
        
        # 按夏普比率排序
        df = df.sort_values('sharpe_ratio', ascending=False)
        
        return df
    
    def get_top_n(self, n=10, metric='sharpe_ratio'):
        """
        获取最优N组参数
        
        Args:
            n: 前N个
            metric: 排序指标
        
        Returns:
            DataFrame: 最优参数
        """
        if not self.results:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.results)
        df = df.sort_values(metric, ascending=False)
        
        return df.head(n)


# 预定义参数网格
PARAM_GRIDS = {
    'dual_ma': {
        'fast_period': [5, 10, 15, 20, 25, 30],
        'slow_period': [30, 45, 60, 90, 120],
    },
    'ma_rsi': {
        'fast_period': [10, 15, 20, 25],
        'slow_period': [40, 50, 60, 80],
        'rsi_period': [10, 14, 20],
        'rsi_buy_threshold': [30, 35, 40],
        'rsi_sell_threshold': [60, 65, 70],
    },
    'ma_rsi_stop': {
        'fast_period': [10, 15, 20, 25],
        'slow_period': [40, 50, 60, 80],
        'rsi_period': [10, 14, 20],
        'rsi_buy_threshold': [30, 35, 40],
        'rsi_sell_threshold': [60, 65, 70],
        'stop_loss_pct': [0.06, 0.08, 0.10],
        'trailing_pct': [0.10, 0.12, 0.15],
    },
}


def run_walk_forward_optimization(data, strategy_class, param_grid, 
                                  train_window=500, test_window=100):
    """
    Walk-Forward 优化
    
    Args:
        data: DataFrame
        strategy_class: 策略类
        param_grid: 参数网格
        train_window: 训练窗口大小（天数）
        test_window: 测试窗口大小（天数）
    
    Returns:
        DataFrame: 优化结果
    """
    results = []
    
    total_days = len(data)
    n_windows = (total_days - train_window) // test_window
    
    print(f"Walk-Forward 优化: {n_windows} 个窗口")
    
    for i in range(n_windows):
        train_end = train_window + i * test_window
        test_start = train_end
        test_end = min(test_start + test_window, total_days)
        
        train_data = data.iloc[:train_end]
        test_data = data.iloc[test_start:test_end]
        
        print(f"\n窗口 {i+1}: 训练 [{0}-{train_end}], 测试 [{test_start}-{test_end}]")
        
        # 在训练数据上优化
        optimizer = ParameterOptimizer(train_data, strategy_class)
        train_results = optimizer.grid_search(param_grid)
        
        if len(train_results) > 0:
            # 取最优参数
            best_params_idx = train_results['sharpe_ratio'].idxmax()
            best_params = train_results.loc[best_params_idx].to_dict()
            
            # 在测试数据上验证
            test_result = run_single_backtest(test_data, strategy_class, best_params)
            
            final_value = test_result.get('final_value', 1000000)
            test_return = (final_value / 1000000 - 1) * 100
            
            results.append({
                'window': i + 1,
                'train_return': best_params.get('total_return', 0),
                'train_sharpe': best_params.get('sharpe_ratio', 0),
                'test_return': test_return,
                'test_sharpe': test_result.get('sharpe', 0),
                'best_params': str({k: v for k, v in best_params.items() 
                                  if k not in ['final_value', 'total_return', 
                                               'sharpe_ratio', 'max_drawdown', 'total_trades']}),
            })
    
    return pd.DataFrame(results)
