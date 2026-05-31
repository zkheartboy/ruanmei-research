
"""
数据获取模块 - 真实数据专用版
只获取真实数据，失败直接报错，不使用模拟数据
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# 尝试导入数据源
try:
    import baostock as bs
    BAOSTOCK_AVAILABLE = True
except Exception as e:
    BAOSTOCK_AVAILABLE = False
    print(f"⚠️ baostock导入失败: {e}")

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except Exception as e:
    AKSHARE_AVAILABLE = False
    print(f"⚠️ akshare导入失败: {e}")

class StockDataFetcher:
    """股票数据获取器 - 只获取真实数据"""
    
    def __init__(self):
        self.logged_in = False
        
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
        获取日线数据 - 只使用真实数据，失败直接报错
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
        
        # 没有可用数据源，直接报错
        raise RuntimeError(f"ERROR: 无法获取 {code} 的真实数据！所有数据源都失败了。")
    
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
        
        print(f"    ✅ baostock获取成功: {len(df)} 条真实数据")
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
        
        df = df.dropna()
        
        print(f"    ✅ akshare获取成功: {len(df)} 条真实数据")
        return df
    
    def get_index_data(self, index_code, start_date, end_date):
        """获取指数数据"""
        return self.get_daily_data(index_code, start_date, end_date)
    
    def get_etf_data(self, etf_code, start_date, end_date):
        """获取ETF数据"""
        return self.get_daily_data(etf_code, start_date, end_date)

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

