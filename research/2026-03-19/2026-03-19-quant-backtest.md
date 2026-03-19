# A股量化投资策略回测方案

**研究时间**: 2026-03-19
**研究者**: 阮·梅（量化投资研究员）
**目标**: 设计完整的A股量化策略回测体系，推进年化14%收益目标

---

## 一、A股历史数据获取方案

### 1.1 数据源对比

| 数据源 | 优点 | 缺点 | 推荐度 |
|--------|------|------|--------|
| **baostock** | 免费、无需token、支持日/分钟/季频数据 | 数据质量一般、股票列表需自行维护 | ⭐⭐⭐⭐⭐ |
| **akshare** | 数据全面、接口丰富、支持实时数据 | 稳定性一般、部分接口需积分 | ⭐⭐⭐⭐ |
| **tushare** | 数据最全面、质量高、有财务数据 | 需积分、接口限流 | ⭐⭐⭐ |
| **聚宽 (joinquant)** | 数据完整、回测框架完善 | 需付费、专业版昂贵 | ⭐⭐⭐ |

### 1.2 baostock 数据获取详解

baostock是国内最推荐的免费数据源，无需注册即可使用。

**安装**:
```bash
pip install baostock
```

**基础使用**:
```python
import baostock as bs
import pandas as pd

# 登录
bs.login()

# 获取上证指数日线数据
rs = bs.query_history_k_data_plus(
    "sh.000001",
    "date,code,open,high,low,close,volume,amount,turn",
    start_date='2015-01-01',
    end_date='2026-03-19',
    frequency="d"  # d=日线, w=周线, m=月线
)
data = pd.DataFrame(rs.data, columns=rs.fields)

# 获取个股数据（以贵州茅台为例）
rs = bs.query_history_k_data_plus(
    "sh.600519",  # 贵州茅台
    "date,open,high,low,close,volume,amount,pctChg",
    start_date='2015-01-01',
    end_date='2026-03-19',
    frequency="d"
)

# 登出
bs.logout()
```

**分钟数据获取**:
```python
# 30分钟数据
rs = bs.query_history_k_data_plus(
    "sh.600519",
    "date,time,open,high,low,close,volume",
    start_date='2024-01-01',
    end_date='2026-03-19',
    frequency="30"  # 5/15/30/60分钟
)
```

**批量获取股票列表**:
```python
# 获取所有A股
rs = bs.query_all_stock(day='2026-03-19')
stocks = pd.DataFrame(rs.data, columns=rs.fields)
a_stocks = stocks[stocks['code'].str.startswith(('sh.6', 'sz.0', 'sz.3'))]
```

### 1.3 akshare 数据获取详解

akshare数据覆盖全面，适合获取财务数据、基金数据等。

**安装**:
```bash
pip install akshare
```

**使用示例**:
```python
import akshare as ak

# 获取股票日线数据
df = ak.stock_zh_a_hist(symbol="600519", period="daily", 
                         start_date="20150101", end_date="20260319")

# 获取实时行情
df = ak.stock_zh_a_spot_em()

# 获取财务数据
df = ak.stock_financial_report_sina(stock="600519", symbol="资产负债表")

# 获取指数数据
df = ak.stock_zh_index_daily(symbol="sh000001")
```

### 1.4 建议数据存储架构

```
data/
├── daily/           # 日线数据 (CSV/HDF5)
│   ├── sh000001.csv # 上证指数
│   ├── sz399001.csv # 深证成指
│   └── stocks/      # 个股数据
├── minute/          # 分钟数据
├── financial/      # 财务数据
└── research/       # 研究用中间数据
```

**数据更新频率**:
- 日线数据: 每日收盘后更新
- 分钟数据: 盘中实时（可选）
- 财务数据: 季度更新

---

## 二、均线策略回测方案

### 2.1 回测框架选型

| 框架 | 语言 | 优点 | 缺点 | 推荐场景 |
|------|------|------|------|----------|
| **Backtrader** | Python | 功能完善、社区活跃、文档详细 | 性能一般 | ⭐⭐⭐⭐⭐ 入门首选 |
| **Zipline** | Python | Quantopian开源、数据完善 | 维护停滞、安装复杂 | 严肃研究 |
| **自建框架** | Python | 完全可控、灵活定制 | 工作量大 | 深度定制 |

**推荐**: 从 Backtrader 起步，成熟后自建核心模块。

**Backtrader 安装**:
```bash
pip install backtrader
```

### 2.2 股票池设计

#### 2.2.1 指数成分股策略

| 指数 | 股票数量 | 特点 | 适用策略 |
|------|----------|------|----------|
| **沪深300** | 300 | 大盘蓝筹、流动性好 | 稳健趋势跟踪 |
| **中证500** | 500 | 中盘成长、弹性大 | 趋势+反转 |
| **创业板指** | 100 | 高弹性、成长性强 | 激进趋势策略 |
| **全市场** | ~5000 | 覆盖全面 | 多因子选股 |

**建议**: 初期以**沪深300成分股**为股票池，兼顾流动性和代表性。

#### 2.2.2 行业分散配置

初始阶段选择4-6个低相关行业:
- 金融（银行、保险）
- 消费（食品饮料、家电）
- 医药（中药、医疗服务）
- 科技（半导体、新能源）

### 2.3 回测时间范围

| 阶段 | 时间范围 | 目的 |
|------|----------|------|
| **样本内** | 2015-01-01 ~ 2021-12-31 | 参数优化、策略开发 |
| **样本外** | 2022-01-01 ~ 2024-12-31 | 策略验证、无偏评估 |
| **近期测试** | 2025-01-01 ~ 2026-03-19 | 实战检验 |

**为什么这样划分**:
- 2015年经历了牛市顶峰和股灾，包含完整的牛熊周期
- 2022-2024包含熊市和震荡市，考验策略鲁棒性
- 近一年数据检验策略在当前市场的有效性

### 2.4 均线策略详细设计

#### 策略1: 双均线交叉策略

**参数**:
- 短期均线: 20日 SMA
- 长期均线: 60日 SMA
- 股票池: 沪深300成分股
- 再平衡频率: 每日检查，金叉/死叉信号触发时交易

**交易规则**:
```
金叉(短>长): 以收盘价买入
死叉(短<长): 以收盘价卖出
```

```python
import backtrader as bt

class DualMAStrategy(bt.Strategy):
    params = (
        ('fast_period', 20),
        ('slow_period', 60),
    )
    
    def __init__(self):
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)
    
    def next(self):
        if self.crossover > 0:  # 金叉
            self.buy()
        elif self.crossover < 0:  # 死叉
            self.sell()
```

#### 策略2: 均线+RSI过滤策略

在双均线基础上增加RSI过滤，减少假信号:

```python
class MA_RSI_Strategy(bt.Strategy):
    params = (
        ('fast_period', 20),
        ('slow_period', 60),
        ('rsi_period', 14),
        ('rsi_buy_threshold', 40),   # RSI<40时允许买入
        ('rsi_sell_threshold', 60),   # RSI>60时允许卖出
    )
    
    def __init__(self):
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)
    
    def next(self):
        if self.crossover > 0 and self.rsi < self.params.rsi_buy_threshold:
            self.buy()
        elif self.crossover < 0 and self.rsi > self.params.rsi_sell_threshold:
            self.sell()
```

#### 策略3: 多均线+布林带策略

```python
class MultiMA_BB_Strategy(bt.Strategy):
    params = (
        ('ma_periods', [5, 20, 60]),  # 多周期均线
        ('bb_period', 20),
        ('bb_std', 2),
        ('atr_period', 14),
    )
```

### 2.5 回测评估指标

| 指标 | 计算方式 | 目标值 |
|------|----------|--------|
| **年化收益率** | (1+总收益)^(250/交易天数) - 1 | ≥14% |
| **夏普比率** | (年化收益-无风险利率)/收益标准差 | ≥0.8 |
| **最大回撤** | 最大峰值-谷值 | ≤25% |
| **卡玛比率** | 年化收益/最大回撤 | ≥0.6 |
| **胜率** | 盈利交易数/总交易数 | ≥40% |
| **盈亏比** | 平均盈利/平均亏损 | ≥1.2 |
| **交易频率** | 年交易次数 | 5-20次 |

**计算示例**:
```python
def evaluate_backtest(cerebro, initial_cash=1000000):
    cerebro.run()
    broker = cerebro.broker
    portfolio = broker.getvalue()
    
    # 年化收益
    total_return = (portfolio - initial_cash) / initial_cash
    # 假设回测3年
    annualized = (1 + total_return) ** (1/3) - 1
    
    return {
        'total_return': total_return,
        'annualized': annualized,
        'final_value': portfolio
    }
```

---

## 三、智能定投优化方案

### 3.1 基础智能定投策略

#### 策略原理

传统定投（固定日期、固定金额）的缺点：
- 不考虑市场估值，微笑曲线效应有限
- 在高估时买入会摊薄收益

**智能定投优化**: 根据均线位置动态调整定投金额

```
定投金额 = 基础金额 × 位置系数

位置系数计算:
- 价格 < 20日均线: 系数=1.5 (低估加码)
- 价格 < 60日均线: 系数=1.2 (偏低)
- 价格 ≈ 60日均线: 系数=1.0 (正常)
- 价格 > 60日均线: 系数=0.8 (偏高减码)
- 价格 > 120日均线: 系数=0.5 (高估轻投)
```

### 3.2 定投+均线择时策略

**核心思想**: 将定投从"无脑买"升级为"聪明买"

```
信号判断:
1. 绝对低估: 价格<60日均线×0.85 → 双倍定投
2. 相对低估: 价格<60日均线 → 1.5倍定投
3. 正常估值: 60日均线 < 价格 < 120日均线 → 正常定投
4. 相对高估: 价格 > 120日均线 → 半额定投
5. 绝对高估: 价格 > 120日均线×1.15 → 暂停定投/卖出
```

### 3.3 定投策略实现

```python
class SmartDCA(bt.Strategy):
    """智能定投策略 - 均线位置决定定投金额"""
    params = (
        ('base_amount', 10000),      # 基础定投金额
        ('ma_short', 20),
        ('ma_long', 60),
        ('frequency', 20),           # 交易频率(天)
    )
    
    def __init__(self):
        self.ma20 = bt.indicators.SMA(self.data.close, period=self.params.ma_short)
        self.ma60 = bt.indicators.SMA(self.data.close, period=self.params.ma_long)
        self.order = None
        self.day_count = 0
    
    def next(self):
        self.day_count += 1
        
        # 非定投日不交易
        if self.day_count % self.params.frequency != 0:
            return
        
        price = self.data.close[0]
        ma60_price = self.ma60[0]
        
        # 计算定投系数
        if price < ma60_price * 0.85:
            amount_ratio = 2.0  # 双倍
        elif price < ma60_price:
            amount_ratio = 1.5  # 1.5倍
        elif price < self.ma60[0] * 1.15:  # 需要用临时变量
            amount_ratio = 1.0  # 正常
        else:
            amount_ratio = 0.5  # 半额
        
        # 计算买入数量
        invest_amount = self.params.base_amount * amount_ratio
        size = int(invest_amount / price / 100) * 100  # 按手买入
        
        if size > 0:
            self.buy(size=size)
```

### 3.4 定投标的推荐

| 基金类型 | 代表基金 | 特点 | 适用场景 |
|----------|----------|------|----------|
| **沪深300ETF** | 510300 | 费率低、跟踪误差小 | 稳健定投 |
| **中证500ETF** | 510500 | 成长性好、弹性大 | 均衡配置 |
| **红利ETF** | 510880 | 高分红、波动小 | 保守型 |
| **创业板ETF** | 159915 | 高弹性、成长强 | 激进型 |

---

## 四、风险控制方案

### 4.1 止损体系设计

#### 4.1.1 单笔止损

| 止损类型 | 触发条件 | 建议值 |
|----------|----------|--------|
| **固定止损** | 亏损达到X% | -8% |
| **跟踪止损** | 从最高点回落X% | -12% |
| **时间止损** | 持有超过X天未盈利 | 20交易日 |
| **均线止损** | 价格跌破60日均线 | 动态 |

**实现**:
```python
class StopLossMixin:
    """止损Mixin"""
    params = (
        ('stop_loss_pct', 0.08),      # 8%固定止损
        ('trailing_pct', 0.12),        # 12%跟踪止损
        ('time_stop_days', 20),        # 20日时间止损
    )
    
    def __init__(self):
        self.buy_price = None
        self.buy_date = None
        self.highest_price = None
    
    def next(self):
        if self.position:
            current_price = self.data.close[0]
            
            # 记录最高价
            if self.highest_price is None:
                self.highest_price = current_price
            else:
                self.highest_price = max(self.highest_price, current_price)
            
            # 固定止损
            if self.buy_price and current_price < self.buy_price * (1 - self.params.stop_loss_pct):
                self.sell()
                return
            
            # 跟踪止损
            if self.highest_price and current_price < self.highest_price * (1 - self.params.trailing_pct):
                self.sell()
                return
            
            # 时间止损
            if self.buy_date and (len(self) - self.buy_date) > self.params.time_stop_days:
                if current_price < self.buy_price:
                    self.sell()
    
    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.buy_date = len(self)
                self.highest_price = None
```

#### 4.1.2 组合止损

```python
class PortfolioStopLoss:
    """组合层面止损"""
    
    @staticmethod
    def check_portfolio_stop(cerebro, max_drawdown=0.15):
        """组合总回撤超15%时清仓"""
        broker = cerebro.broker
        current_value = broker.getvalue()
        peak_value = cerebro.observers峰值  # 需要维护峰值
        
        if current_value < peak_value * (1 - max_drawdown):
            return True  # 触发止损
        return False
```

### 4.2 仓位管理方案

#### 4.2.1 固定仓位

```
单只股票仓位 = 总资金 × 单一上限
单一上限 = 20%（避免个股黑天鹅）

最大持仓股票数 = 1 / 单一上限 = 5只
```

#### 4.2.2 动态仓位（凯利公式）

```python
def kelly_fraction(win_rate, avg_win, avg_loss):
    """
    凯利公式计算最优仓位比例
    win_rate: 胜率
    avg_win: 平均盈利
    avg_loss: 平均亏损
    """
    b = avg_win / avg_loss  # 盈亏比
    q = 1 - win_rate
    f = (b * win_rate - q) / b
    
    return max(0, min(f, 0.2))  # 限制最大20%

# 示例
f = kelly_fraction(0.45, 0.12, 0.08)
print(f"建议仓位: {f:.1%}")  # 输出: 建议仓位: 16.3%
```

#### 4.2.3 趋势强度仓位

```python
def trend_position(ma20, ma60, atr):
    """
    根据趋势强度调整仓位
    """
    if ma20 > ma60:
        trend_score = 1.0
        if ma20 > ma60 * 1.05:
            trend_score = 1.5  # 强势趋势
    else:
        trend_score = 0.5      # 弱势
    
    # 仓位 = 基础仓位 × 趋势系数
    base_position = 0.15
    position = base_position * trend_score
    
    return min(position, 0.20)  # 上限20%
```

### 4.3 风险控制规则汇总

| 规则 | 参数 | 优先级 |
|------|------|--------|
| 单只股票最大仓位 | 20% | P0 |
| 单只股票止损 | -8% | P0 |
| 组合最大回撤止损 | -15% | P0 |
| 最大持仓数量 | 5只 | P1 |
| 跟踪止损 | -12% | P1 |
| 时间止损 | 20日 | P2 |
| 凯利公式仓位 | 动态 | P1 |

---

## 五、回测系统实现方案

### 5.1 项目结构

```
quant_backtest/
├── config/
│   ├── settings.py       # 全局配置
│   └── data_config.py    # 数据源配置
├── data/
│   ├── fetcher.py        # 数据获取模块
│   └── storage.py        # 数据存储模块
├── strategies/
│   ├── ma_cross.py       # 均线交叉策略
│   ├── ma_rsi.py         # 均线RSI策略
│   └── smart_dca.py      # 智能定投策略
├── backtest/
│   ├── engine.py         # 回测引擎
│   ├── analyzer.py       # 绩效分析
│   └── optimizer.py      # 参数优化
├── risk/
│   ├── stop_loss.py      # 止损模块
│   └── position.py       # 仓位管理
├── main.py               # 入口文件
└── requirements.txt      # 依赖
```

### 5.2 数据获取模块

```python
# data/fetcher.py
import baostock as bs
import pandas as pd
from datetime import datetime

class StockDataFetcher:
    def __init__(self):
        bs.login()
    
    def __del__(self):
        bs.logout()
    
    def get_daily_data(self, code, start_date, end_date):
        """
        获取日线数据
        code: sh.600519 或 sz.000001 格式
        """
        rs = bs.query_history_k_data_plus(
            code,
            "date,open,high,low,close,volume,amount,pctChg",
            start_date=start_date,
            end_date=end_date,
            frequency="d"
        )
        
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        df['date'] = pd.to_datetime(df['date'])
        for col in ['open','high','low','close','volume','amount','pctChg']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def get_index_constituents(self, index_code='sh.000300'):
        """获取指数成分股"""
        rs = bs.query_zz500_stocks()  # 中证500示例
        # 或使用akshare获取更精确的成分
        pass
```

### 5.3 回测引擎

```python
# backtest/engine.py
import backtrader as bt
from strategies.ma_cross import DualMAStrategy
from risk.stop_loss import StopLossStrategy

def run_backtest(
    stock_code,
    start_date,
    end_date,
    strategy_class,
    strategy_params,
    initial_cash=1000000,
    commission=0.0003
):
    cerebro = bt.Cerebro()
    
    # 添加数据
    data = StockDataFetcher().get_daily_data(stock_code, start_date, end_date)
    data_feed = bt.feeds.PandasData(dataname=data, datetime=0)
    cerebro.adddata(data_feed)
    
    # 添加策略
    cerebro.addstrategy(strategy_class, **strategy_params)
    
    # 资金管理
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    
    # 分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # 运行
    results = cerebro.run()
    
    return results, cerebro
```

---

## 六、参数优化方案

### 6.1 网格搜索优化

```python
from itertools import product

def grid_search(strategy_class, param_grid, stock_code, start_date, end_date):
    """
    网格搜索最优参数
    """
    results = []
    
    # 生成所有参数组合
    keys, values = zip(*param_grid.items())
    for params in [dict(zip(keys, v)) for v in product(*values)]:
        _, cerebro = run_backtest(
            stock_code, start_date, end_date,
            strategy_class, params
        )
        
        # 获取分析结果
        sharpe = cerebro.broker.get_analysis().get('sharperatio', 0)
        returns = cerebro.broker.get_analysis().get('total', 0)
        
        results.append({
            'params': params,
            'sharpe': sharpe,
            'returns': returns
        })
    
    # 返回最优参数
    return sorted(results, key=lambda x: x['sharpe'], reverse=True)


# 参数网格示例
param_grid = {
    'fast_period': [10, 15, 20, 25],
    'slow_period': [40, 50, 60, 70, 80],
    'stop_loss_pct': [0.06, 0.08, 0.10]
}
```

### 6.2 Walk-Forward Optimization

避免过拟合的关键方法：

1. 将数据分为多个窗口
2. 每个窗口用前半段优化，后半段验证
3. 最终选择各窗口验证表现稳定的参数

```
2015-2017  → 优化 → | 2018测试 →
2018-2020  → 优化 → | 2021测试 →
2021-2023  → 优化 → | 2024-2025测试 →
```

---

## 七、执行计划

### 阶段一：基础设施搭建（1-2周）

| 任务 | 预计时间 | 产出 |
|------|----------|------|
| 环境搭建（Python + Backtrader） | 1天 | 可运行回测环境 |
| baostock数据接口调试 | 2天 | 成功获取日线数据 |
| 数据存储框架 | 2天 | 本地数据缓存机制 |
| 基础回测模板 | 3天 | 可复用的回测框架 |

### 阶段二：策略开发与回测（2-3周）

| 任务 | 预计时间 | 产出 |
|------|----------|------|
| 双均线策略回测 | 1周 | 沪深300成分股回测结果 |
| 均线+RSI策略回测 | 1周 | 优化后策略参数 |
| 止损策略对比 | 3天 | 最优止损参数 |
| 参数Walk-Forward优化 | 1周 | 稳健参数组合 |

### 阶段三：智能定投专项（2周）

| 任务 | 预计时间 | 产出 |
|------|----------|------|
| 智能定投策略设计 | 1周 | 定投优化方案 |
| 基金定投回测 | 1周 | ETF定投绩效报告 |

### 阶段四：实盘模拟与优化（持续）

| 任务 | 频率 | 内容 |
|------|------|------|
| 策略监控 | 每日 | 持仓监控、信号提醒 |
| 绩效归因 | 每周 | 收益分解、风险评估 |
| 参数回顾 | 每月 | 参数有效性检查 |

---

## 八、风险提示

1. **历史回测不代表未来**: 策略在过去有效不代表未来持续有效
2. **过拟合风险**: 复杂策略容易过拟合样本内数据
3. **交易滑点**: 实际交易中存在滑点，回测需考虑
4. **流动性风险**: 小盘股可能无法按理想价格成交
5. **市场结构变化**: A股政策市特征明显，需持续关注

---

## 九、附录

### 9.1 推荐学习资源

- **书籍**: 《量化投资》- 丁鹏、《打开量化投资的黑箱》- 里什·纳兰
- **社区**: 聚宽、米筐、优矿
- **GitHub**: 搜索 "backtrader" "akshare" 相关项目

### 9.2 数据字段说明

| 字段 | 含义 | 备注 |
|------|------|------|
| date | 交易日期 | YYYY-MM-DD |
| open | 开盘价 | |
| high | 最高价 | |
| low | 最低价 | |
| close | 收盘价 | 最常用 |
| volume | 成交量 | 手 |
| amount | 成交额 | 元 |
| pctChg | 涨跌幅 | % |

---

**报告状态**: 初稿完成，待进一步细化
**下次更新**: 根据实际回测结果迭代
