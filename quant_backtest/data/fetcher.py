"""
数据获取模块 - 增强版
支持baostock、akshare和真实模拟数据
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from tqdm import tqdm

# 尝试导入数据源
try:
    import baostock as bs
    BAOSTOCK_AVAILABLE = True
except Exception as e:
    BAOSTOCK_AVAILABLE = False

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except Exception as e:
    AKSHARE_AVAILABLE = False

class StockDataFetcher:
    """股票数据获取器 - 支持多数据源"""
    
    def __init__(self, use_backup=True):
        self.logged_in = False
        self.use_backup = use_backup
        
        if BAOSTOCK_AVAILABLE:
            self.login()
    
    def login(self):
        """登录baostock"""
        if not BAOSTOCK_AVAILABLE:
            return False
            
        try:
            lg = bs.login()
            if lg.error_code == '0':
                self.logged_in = True
                print(f"✅ baostock登录成功")
                return True
            else:
                print(f"⚠️ baostock登录失败: {lg.error_msg}")
                self.logged_in = False
                return False
        except Exception as e:
            print(f"⚠️ baostock连接失败: {e}")
            self.logged_in = False
            return False
    
    def logout(self):
        """登出baostock"""
        if BAOSTOCK_AVAILABLE and self.logged_in:
            bs.logout()
            self.logged_in = False
    
    def __del__(self):
        self.logout()
    
    def get_daily_data(self, code, start_date, end_date, adjust='qfq'):
        """
        获取日线数据 - 优先使用baostock，然后akshare，最后模拟数据
        """
        # 尝试baostock
        if BAOSTOCK_AVAILABLE and self.logged_in:
            try:
                return self._get_daily_data_baostock(code, start_date, end_date, adjust)
            except Exception as e:
                print(f"⚠️ baostock获取失败: {e}")
        
        # 尝试akshare
        if AKSHARE_AVAILABLE:
            try:
                return self._get_daily_data_akshare(code, start_date, end_date)
            except Exception as e:
                print(f"⚠️ akshare获取失败: {e}")
        
        # 使用模拟数据
        return self._generate_realistic_data(code, start_date, end_date)
    
    def _get_daily_data_baostock(self, code, start_date, end_date, adjust='qfq'):
        """使用baostock获取数据"""
        if not BAOSTOCK_AVAILABLE:
            raise Exception("baostock不可用")
            
        rs = bs.query_history_k_data_plus(
            code,
            "date,code,open,high,low,close,volume,amount,turn,pctChg",
            start_date=start_date.replace('-', ''),
            end_date=end_date.replace('-', ''),
            frequency="d",
            adjusttype=adjust
        )
        
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        if len(data_list) == 0:
            raise ValueError("baostock返回空数据")
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 'pctChg']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.dropna()
        
        print(f"    ✅ baostock获取成功: {len(df)} 条数据")
        return df
    
    def _get_daily_data_akshare(self, code, start_date, end_date):
        """使用akshare获取数据"""
        if not AKSHARE_AVAILABLE:
            raise Exception("akshare不可用")
            
        # 转换代码格式
        if 'sh.' in code:
            symbol = code.replace('sh.', '')
        elif 'sz.' in code:
            symbol = code.replace('sz.', '')
        else:
            symbol = code
        
        # 判断是指数还是股票/ETF
        if symbol in ['000001', '000300', '000905', '399001', '399006']:
            # 指数数据
            df = ak.index_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
        else:
            # 股票/ETF数据
            try:
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust="qfq"
                )
            except:
                # 尝试ETF数据
                df = ak.fund_etf_hist_em(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust="qfq"
                )
        
        # 标准化列名
        column_map = {
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
            '换手率': 'turn',
            '涨跌幅': 'pctChg'
        }
        
        df = df.rename(columns=column_map)
        
        if 'date' not in df.columns:
            raise ValueError("数据格式异常")
        
        df['date'] = pd.to_datetime(df['date'])
        df['code'] = code
        
        # 确保必需列存在
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col not in df.columns:
                df[col] = np.nan
        
        print(f"    ✅ akshare获取成功: {len(df)} 条数据")
        return df
    
    def _generate_realistic_data(self, code, start_date, end_date):
        """
        生成真实模拟数据
        包含牛市、熊市、震荡市等多种市场特征
        """
        print(f"    📊 生成真实模拟数据...")
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # 生成交易日
        dates = pd.date_range(start=start, end=end, freq='B')
        n_days = len(dates)
        
        # 根据代码确定基准价格
        if '000001' in code or 'sh.000001' in code:
            base_price = 3000.0
            price_std = 0.018
        elif '000300' in code:
            base_price = 4000.0
            price_std = 0.016
        elif '000905' in code:
            base_price = 6000.0
            price_std = 0.019
        elif '510300' in code:
            base_price = 4.0
            price_std = 0.016
        elif '510500' in code:
            base_price = 6.0
            price_std = 0.019
        elif '510880' in code:
            base_price = 3.0
            price_std = 0.015
        else:
            base_price = 100.0
            price_std = 0.025
        
        # 生成市场状态序列（牛市、熊市、震荡市）
        np.random.seed(42)  # 固定种子
        
        # 定义不同市场阶段
        market_regimes = []
        current_day = 0
        
        while current_day < n_days:
            # 随机选择市场类型
            regime_type = np.random.choice(['bull', 'bear', 'sideways'], p=[0.25, 0.25, 0.5])
            duration = np.random.randint(30, 120)  # 30-120天
            
            regime = {
                'type': regime_type,
                'start': current_day,
                'end': min(current_day + duration, n_days),
                'trend': 0.0,
                'volatility': 0.0
            }
            
            if regime_type == 'bull':
                regime['trend'] = np.random.uniform(0.0008, 0.002)
                regime['volatility'] = np.random.uniform(0.012, 0.022)
            elif regime_type == 'bear':
                regime['trend'] = np.random.uniform(-0.002, -0.0008)
                regime['volatility'] = np.random.uniform(0.018, 0.028)
            else:
                regime['trend'] = np.random.uniform(-0.0003, 0.0003)
                regime['volatility'] = np.random.uniform(0.008, 0.018)
            
            market_regimes.append(regime)
            current_day = regime['end']
        
        # 生成价格序列
        returns = np.zeros(n_days)
        current_price = base_price
        
        for regime in market_regimes:
            start_idx = regime['start']
            end_idx = regime['end']
            
            # 生成该阶段的收益
            regime_returns = np.random.normal(
                loc=regime['trend'],
                scale=regime['volatility'],
                size=end_idx - start_idx
            )
            
            # 添加一些极端事件
            for i in range(start_idx, end_idx):
                if np.random.random() < 0.02:
                    regime_returns[i - start_idx] = np.random.choice([-0.05, -0.04, 0.04, 0.05])
            
            returns[start_idx:end_idx] = regime_returns
        
        # 计算价格
        prices = current_price * np.cumprod(1 + returns)
        
        # 生成OHLC数据
        high = prices * (1 + np.random.uniform(0.002, 0.015, n_days))
        low = prices * (1 - np.random.uniform(0.002, 0.015, n_days))
        opens = np.zeros(n_days)
        opens[0] = prices[0] * (1 + np.random.uniform(-0.005, 0.005))
        for i in range(1, n_days):
            opens[i] = prices[i-1] * (1 + np.random.uniform(-0.008, 0.008))
        
        # 成交量
        base_volume = np.random.uniform(5000000, 20000000, n_days)
        volume = base_volume * (1 + np.abs(returns) * 30)  # 高波动时成交量放大
        
        df = pd.DataFrame({
            'date': dates,
            'code': code,
            'open': opens,
            'high': np.maximum(high, opens),
            'low': np.minimum(low, opens),
            'close': prices,
            'volume': volume,
            'amount': prices * volume,
            'turn': np.random.uniform(0.5, 3.5, n_days),
            'pctChg': returns * 100
        })
        
        # 检查各列顺序
        df = df.dropna()
        
        print(f"    ✅ 生成模拟数据: {len(df)} 条")
        print(f"       包含: {len(set(r['type'] for r in market_regimes))} 种市场状态")
        
        return df
    
    def get_index_data(self, index_code, start_date, end_date):
        """获取指数数据"""
        return self.get_daily_data(index_code, start_date, end_date)
    
    def get_etf_data(self, etf_code, start_date, end_date):
        """获取ETF数据"""
        return self.get_daily_data(etf_code, start_date, end_date)
    
    def get_stock_list(self, date=None):
        """获取所有股票列表"""
        if not BAOSTOCK_AVAILABLE:
            return pd.DataFrame()
            
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            rs = bs.query_all_stock(day=date.replace('-', ''))
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())
            return pd.DataFrame(data_list, columns=rs.fields)
        except:
            return pd.DataFrame()

def prepare_backtrader_data(data):
    """
    准备backtrader格式的数据
    确保日期列是datetime类型，索引是日期
    """
    df = data.copy()
    
    # 确保日期列存在
    if 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'])
    elif 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    else:
        raise ValueError("数据中找不到日期列")
    
    # 设置日期为索引
    df = df.set_index('datetime')
    
    # 确保数值列是float类型
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(float)
    
    return df

# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("测试数据获取模块")
    print("="*60)
    
    fetcher = StockDataFetcher()
    
    # 测试获取数据
    print("\n1. 测试获取数据...")
    data = fetcher.get_index_data('sh.000001', '2022-01-01', '2025-06-01')
    print(f"获取到 {len(data)} 条数据")
    print(data.head())
    
    fetcher.logout()
    print("\n✅ 测试完成!")
