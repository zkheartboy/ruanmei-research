"""
数据源配置
"""

# baostock配置
BAOSTOCK_CONFIG = {
    'timeout': 30,
    'retry': 3,
}

# akshare备用配置
AKSHARE_CONFIG = {
    'max_retries': 3,
    'timeout': 30,
}

# 数据字段映射
DATA_FIELDS = {
    'baostock': {
        'daily': 'date,code,open,high,low,close,volume,amount,turn,pctChg',
        'minute': 'date,time,code,open,high,low,close,volume',
    },
    'akshare': {
        'daily': ['日期', '股票代码', '开盘', '最高', '最低', '收盘', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率'],
    }
}

# 股票代码前缀映射
CODE_PREFIX = {
    'sh': 'sh.',   # 上交所
    'sz': 'sz.',   # 深交所
}
