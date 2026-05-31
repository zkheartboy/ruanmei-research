"""
数据源可用性检查
"""
import sys
import os
sys.path.insert(0, '/workspace/quant_backtest')

print("="*60)
print("  数据源可用性检查")
print("="*60)

# 1. 检查baostock
print("\n[1] 检查baostock...")
try:
    import baostock as bs
    lg = bs.login()
    if lg.error_code == '0':
        print("    ✅ baostock连接成功!")
        bs.logout()
    else:
        print(f"    ❌ baostock登录失败: {lg.error_msg}")
except Exception as e:
    print(f"    ❌ baostock连接异常: {e}")

# 2. 检查akshare
print("\n[2] 检查akshare...")
try:
    import akshare as ak
    print("    ✅ akshare可用!")
    
    # 尝试获取一个简单的数据
    print("    尝试获取上证指数数据...")
    index_df = ak.index_zh_a_hist(symbol="000001", period="daily", start_date="20240101", end_date="20240601")
    if len(index_df) > 0:
        print(f"    ✅ 获取成功! {len(index_df)} 条数据")
        print(f"    日期范围: {index_df['日期'].min()} - {index_df['日期'].max()}")
        print(index_df.head())
    else:
        print("    ⚠️ 数据获取为空")
except Exception as e:
    print(f"    ❌ akshare不可用: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("  检查完成!")
print("="*60)
