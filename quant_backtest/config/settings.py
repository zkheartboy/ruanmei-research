"""
全局配置文件
"""
import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DAILY_DATA_DIR = os.path.join(DATA_DIR, 'daily')
MINUTE_DATA_DIR = os.path.join(DATA_DIR, 'minute')
FINANCIAL_DATA_DIR = os.path.join(DATA_DIR, 'financial')

# 回测参数
INITIAL_CASH = 1000000  # 初始资金100万
COMMISSION = 0.0003     # 手续费万三
SLIPPAGE = 0.0001       # 滑点万一

# 回测时间范围
BACKTEST_START = '2015-01-01'
BACKTEST_END = '2026-05-30'

# 样本内/外分割点
IN_SAMPLE_END = '2021-12-31'
OUT_OF_SAMPLE_START = '2022-01-01'

# 策略参数
STRATEGY_PARAMS = {
    'ma_cross': {
        'fast_period': 20,
        'slow_period': 60,
    },
    'ma_rsi': {
        'fast_period': 20,
        'slow_period': 60,
        'rsi_period': 14,
        'rsi_buy_threshold': 40,
        'rsi_sell_threshold': 60,
    }
}

# 风险控制参数
RISK_PARAMS = {
    'stop_loss_pct': 0.08,        # 8%固定止损
    'trailing_pct': 0.12,         # 12%跟踪止损
    'time_stop_days': 20,          # 20日时间止损
    'max_position_pct': 0.20,     # 单只股票最大仓位20%
    'max_drawdown_pct': 0.15,     # 组合最大回撤15%
}

# 目标ETF列表
ETF_LIST = {
    '沪深300ETF': 'sh.510300',
    '中证500ETF': 'sh.510500',
    '红利ETF': 'sh.510880',
    '创业板ETF': 'sz.159915',
}

# 指数代码
INDEX_CODES = {
    '上证指数': 'sh.000001',
    '深证成指': 'sz.399001',
    '沪深300': 'sh.000300',
    '中证500': 'sh.000905',
    '创业板': 'sz.399006',
}
