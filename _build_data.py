# -*- coding: utf-8 -*-
"""
把 做T参考工具/数据 下的 4 个 CSV 压成前端可直接引用的 data.js
- 日线: 全量
- 5分钟: 只保留最近 N 个交易日(默认 250), 减小体积
用法:  D:\Python37\python.exe _build_data.py [N]
"""
import sys, os, json
import pandas as pd
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "数据")
TZ8 = timezone(timedelta(hours=8))

def keep_days(n):
    n = int(n)
    return max(n, 1)

def to_ms(s, has_time):
    if has_time:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    else:
        dt = datetime.strptime(s, "%Y-%m-%d") + timedelta(hours=15)  # 日线取收盘 15:00
    return int(dt.replace(tzinfo=TZ8).timestamp() * 1000)

def to_ms_sh(s, has_time):
    # 上证日线日期为 20170103
    if has_time:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    else:
        dt = datetime.strptime(s, "%Y%m%d") + timedelta(hours=15)
    return int(dt.replace(tzinfo=TZ8).timestamp() * 1000)

def r3(x):
    return round(float(x), 3)

def series(df, time_col, has_time, ms_func):
    return {
        "t": [ms_func(str(v), has_time) for v in df[time_col]],
        "o": [r3(v) for v in df["open"]],
        "h": [r3(v) for v in df["high"]],
        "l": [r3(v) for v in df["low"]],
        "c": [r3(v) for v in df["close"]],
        "v": [int(round(float(v))) for v in df["vol"]],
    }

def main():
    n = keep_days(sys.argv[1]) if len(sys.argv) > 1 else 250

    # 主 ETF 159952 日线
    m1d = pd.read_csv(os.path.join(DATA, "159952_1d.csv"), encoding="utf-8-sig")
    m1d = m1d.sort_values("trade_date").reset_index(drop=True)
    main_daily = series(m1d, "trade_date", False, to_ms)

    # 主 ETF 159952 5分钟(截最近 n 个交易日)
    m5 = pd.read_csv(os.path.join(DATA, "159952_5min.csv"), encoding="utf-8-sig")
    m5 = m5.sort_values("trade_time").reset_index(drop=True)
    dates = sorted(m5["trade_date"].unique())[-n:]
    m5 = m5[m5["trade_date"].isin(dates)].reset_index(drop=True)
    main_min5 = series(m5, "trade_time", True, to_ms)

    # 上证指数 日线
    i1d = pd.read_csv(os.path.join(DATA, "上证指数_000001SH_1d.csv"), encoding="utf-8-sig")
    i1d = i1d.sort_values("trade_date").reset_index(drop=True)
    index_daily = series(i1d, "trade_date", False, to_ms_sh)

    # 上证指数 5分钟(截最近 n 个交易日)
    i5 = pd.read_csv(os.path.join(DATA, "上证指数_000001SH_5min_2017_2026.csv"), encoding="utf-8-sig")
    i5 = i5.sort_values("trade_time").reset_index(drop=True)
    i5["trade_date"] = i5["trade_time"].str[:10]
    dates = sorted(i5["trade_date"].unique())[-n:]
    i5 = i5[i5["trade_date"].isin(dates)].reset_index(drop=True)
    index_min5 = series(i5, "trade_time", True, to_ms_sh)

    obj = {
        "main": {"name": "159952 广发创业板ETF", "code": "159952.SZ"},
        "index": {"name": "上证指数", "code": "000001.SH"},
        "daily": {"main": main_daily, "index": index_daily},
        "min5": {"main": main_min5, "index": index_min5},
    }
    js = "window.DATA = " + json.dumps(obj, separators=(",", ":")) + ";\n"
    out = os.path.join(HERE, "data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write(js)
    print("written:", out, "%.2f MB" % (os.path.getsize(out) / 1048576))
    for k in ("daily", "min5"):
        for s in ("main", "index"):
            print(k, s, "bars =", len(obj[k][s]["t"]))

if __name__ == "__main__":
    main()
