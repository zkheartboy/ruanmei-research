"""
仓位管理模块
"""

import numpy as np


def kelly_fraction(win_rate, avg_win, avg_loss):
    """
    凯利公式计算最优仓位比例
    
    Args:
        win_rate: 胜率 (0-1)
        avg_win: 平均盈利比例
        avg_loss: 平均亏损比例
    
    Returns:
        float: 最优仓位比例
    """
    b = avg_win / avg_loss  # 盈亏比
    q = 1 - win_rate
    f = (b * win_rate - q) / b
    
    # 限制最大仓位为20%
    return max(0, min(f, 0.2))


def fixed_position(position_pct=0.2):
    """
    固定仓位
    """
    return position_pct


def trend_position(ma_fast, ma_slow, atr, base_position=0.15):
    """
    根据趋势强度调整仓位
    
    Args:
        ma_fast: 短期均线值
        ma_slow: 长期均线值
        atr: ATR值
        base_position: 基础仓位
    
    Returns:
        float: 建议仓位
    """
    if ma_fast > ma_slow:
        trend_score = 1.0
        if ma_fast > ma_slow * 1.05:
            trend_score = 1.5  # 强势趋势
    else:
        trend_score = 0.5      # 弱势
    
    position = base_position * trend_score
    
    return min(position, 0.20)  # 上限20%


def volatility_position(returns, target_volatility=0.15, base_position=0.2):
    """
    根据波动率调整仓位
    
    Args:
        returns: 收益率序列
        target_volatility: 目标波动率
        base_position: 基础仓位
    
    Returns:
        float: 建议仓位
    """
    current_vol = returns.std() * np.sqrt(252)  # 年化波动率
    
    if current_vol > 0:
        position = base_position * (target_volatility / current_vol)
    else:
        position = base_position
    
    return min(position, 0.30)  # 最高30%


def risk_parity_position(positions, volatilities):
    """
    风险平价仓位
    
    Args:
        positions: 各资产仓位
        volatilities: 各资产波动率
    
    Returns:
        dict: 调整后的仓位
    """
    inv_vol = {k: 1/v for k, v in volatilities.items()}
    total = sum(inv_vol.values())
    
    return {k: inv_vol[k] / total for k in positions.keys()}


# 预计算示例
if __name__ == '__main__':
    # 示例: 胜率45%, 平均盈利12%, 平均亏损8%
    f = kelly_fraction(0.45, 0.12, 0.08)
    print(f"建议仓位: {f:.1%}")
