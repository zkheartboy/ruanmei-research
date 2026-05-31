"""
回测引擎
封装Backtrader，提供统一的回测接口
"""

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
from strategies.ma_cross import DualMAStrategy, MA_Only_UpStrategy
from strategies.ma_rsi import MA_RSI_Strategy, MA_RSI_FilterStrategy
from strategies.ma_rsi_stop import CombinedStrategy
from data.fetcher import prepare_backtrader_data
from config.settings import INITIAL_CASH, COMMISSION, SLIPPAGE


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_cash=INITIAL_CASH, commission=COMMISSION, slippage=SLIPPAGE):
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        
        # 添加滑点
        self.cerebro.broker.set_slippage_perc(slippage)
        
        # 分析器
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.03, annualize=True)
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
        
        self.results = None
        self.strategy_name = None
        
    def add_data(self, data, name='data'):
        """添加数据"""
        # 准备backtrader格式数据
        bt_data = prepare_backtrader_data(data)
        
        data_feed = bt.feeds.PandasData(
            dataname=bt_data,
            datetime=None,  # 使用索引作为日期
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )
        self.cerebro.adddata(data_feed, name=name)
        
    def add_strategy(self, strategy_class, **kwargs):
        """添加策略"""
        self.strategy_name = strategy_class.__name__
        self.cerebro.addstrategy(strategy_class, **kwargs)
        
    def run(self):
        """运行回测"""
        print(f"\n{'='*60}")
        print(f"开始回测: {self.strategy_name}")
        print(f"{'='*60}")
        
        self.results = self.cerebro.run()
        return self.results
    
    def get_final_value(self):
        """获取最终市值"""
        return self.cerebro.broker.getvalue()
    
    def get_analysis(self):
        """获取分析结果"""
        if not self.results:
            return {}
        
        strat = self.results[0]
        return {
            'strategy': self.strategy_name,
            'final_value': self.get_final_value(),
            'sharpe': strat.analyzers.sharpe.get_analysis().get('sharperatio', None),
            'drawdown': strat.analyzers.drawdown.get_analysis(),
            'returns': strat.analyzers.returns.get_analysis(),
            'trades': strat.analyzers.trades.get_analysis(),
            'timereturn': strat.analyzers.timereturn.get_analysis(),
        }
    
    def print_summary(self):
        """打印回测摘要"""
        analysis = self.get_analysis()
        
        print(f"\n{'='*60}")
        print(f"回测结果摘要: {analysis['strategy']}")
        print(f"{'='*60}")
        print(f"最终市值: {analysis['final_value']:.2f}")
        print(f"总收益: {(analysis['final_value'] / INITIAL_CASH - 1) * 100:.2f}%")
        
        sharpe = analysis.get('sharpe')
        if sharpe:
            print(f"夏普比率: {sharpe:.3f}")
        
        dd = analysis['drawdown']
        if dd:
            print(f"最大回撤: {dd.get('max', {}).get('drawdown', 0):.2f}%")
            print(f"最大回撤时长: {dd.get('max', {}).get('len', 0)}天")
        
        returns = analysis['returns']
        if returns:
            print(f"年化收益: {returns.get('rtot', 0) * 100:.2f}%")
        
        trades = analysis['trades']
        if trades:
            total = trades.get('total', {})
            won = trades.get('won', {})
            lost = trades.get('lost', {})
            print(f"总交易次数: {total.get('total', 0)}")
            print(f"盈利交易: {won.get('total', 0)}")
            print(f"亏损交易: {lost.get('total', 0)}")


def run_single_backtest(data, strategy_class, strategy_params=None, initial_cash=INITIAL_CASH):
    """
    运行单次回测
    
    Args:
        data: DataFrame，包含date, open, high, low, close, volume列
        strategy_class: 策略类
        strategy_params: 策略参数
        initial_cash: 初始资金
    
    Returns:
        dict: 回测结果
    """
    if strategy_params is None:
        strategy_params = {}
    
    engine = BacktestEngine(initial_cash=initial_cash)
    
    # 添加数据
    engine.add_data(data)
    
    # 添加策略
    engine.add_strategy(strategy_class, **strategy_params)
    
    # 运行
    engine.run()
    
    return engine.get_analysis()


def run_multiple_strategies(data, strategy_list, initial_cash=INITIAL_CASH):
    """
    运行多个策略对比
    
    Args:
        data: DataFrame
        strategy_list: [(strategy_class, params_dict), ...]
        initial_cash: 初始资金
    
    Returns:
        DataFrame: 策略对比结果
    """
    results = []
    
    for strategy_class, params in strategy_list:
        try:
            analysis = run_single_backtest(data, strategy_class, params, initial_cash)
            
            final_value = analysis.get('final_value', 0)
            total_return = (final_value / initial_cash - 1) * 100
            
            sharpe = analysis.get('sharpe')
            sharpe_value = sharpe if sharpe else 0
            
            dd = analysis.get('drawdown', {})
            max_dd = dd.get('max', {}).get('drawdown', 0) if dd else 0
            
            trades = analysis.get('trades', {})
            total_trades = trades.get('total', {}).get('total', 0) if trades else 0
            
            results.append({
                '策略': strategy_class.__name__,
                '最终市值': f'{final_value:.2f}',
                '总收益': f'{total_return:.2f}%',
                '夏普比率': f'{sharpe_value:.3f}',
                '最大回撤': f'{max_dd:.2f}%',
                '交易次数': total_trades,
            })
        except Exception as e:
            print(f"策略 {strategy_class.__name__} 回测失败: {e}")
    
    return pd.DataFrame(results)


if __name__ == '__main__':
    # 测试回测引擎
    from data.fetcher import StockDataFetcher
    
    print("测试回测引擎...")
    
    # 获取数据
    fetcher = StockDataFetcher()
    data = fetcher.get_index_data('sh.000001', '2020-01-01', '2025-12-31')
    fetcher.logout()
    
    print(f"获取到 {len(data)} 条数据")
    
    # 运行回测
    result = run_single_backtest(
        data, 
        DualMAStrategy,
        {'fast_period': 20, 'slow_period': 60}
    )
    
    print("\n回测结果:")
    print(result)
