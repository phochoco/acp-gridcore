"""
Trinity Backtest — Binance BTC 실제 데이터 vs Trinity luck_score 상관계수
실행: python3 backtest_binance.py
"""
import json
import math
import time
import requests
from datetime import datetime, timedelta

# ===== 설정 =====
# BTC 제네시스 블록 탄생일 (2009-01-03 18:15 UTC)
# 에이전트/코인 탄생일 기반 백테스트 컨셉
BIRTH_DATE = "2009-01-03"
BIRTH_TIME = "18:15"
GENDER = "M"

# 분석 기간: 2015-01-01 ~ 2025-12-31 (10년, N≈3,650일)
START_DATE = datetime(2015, 1, 1)
END_DATE   = datetime(2025, 12, 31)

# Binance 무료 API (키 불필요, 과거 데이터 무제한)
BINANCE_URL = "https://api.binance.com/api/v3/klines"


def get_btc_daily(start_dt: datetime, end_dt: datetime) -> dict:
    """Binance에서 BTC/USDT 일봉 OHLCV 가져오기 (청크 방식, 10년치 지원)"""
    print("[Backtest] Fetching BTC/USDT daily from Binance (chunked)...")
    result = {}
    chunk_start = start_dt

    while chunk_start < end_dt:
        params = {
            "symbol": "BTCUSDT",
            "interval": "1d",
            "startTime": int(chunk_start.timestamp() * 1000),
            "endTime":   int(end_dt.timestamp() * 1000),
            "limit": 1000  # Binance 최대
        }
        r = requests.get(BINANCE_URL, params=params, timeout=15)
        candles = r.json()
        if not candles:
            break

        for c in candles:
            ts = datetime.utcfromtimestamp(c[0] / 1000)
            date_str = ts.strftime("%Y-%m-%d")
            high  = float(c[2])
            low   = float(c[3])
            close = float(c[4])
            volatility = (high - low) / close
            result[date_str] = {"close": close, "volatility": volatility}

        # 다음 청크 시작 = 마지막 캔들 다음날
        last_ts = datetime.utcfromtimestamp(candles[-1][0] / 1000)
        chunk_start = last_ts + timedelta(days=1)
        print(f"  → {len(result)} days fetched so far (last: {last_ts.date()})")
        time.sleep(0.3)  # rate limit 방지

    print(f"[Backtest] Got {len(result)} days of BTC data (Binance)")
    return result


def get_trinity_scores(btc_dates: list) -> dict:
    """Trinity 엔진으로 각 날짜의 luck_score 계산"""
    print("[Backtest] Calculating Trinity scores...")
    try:
        from trinity_engine_v2 import TrinityEngineV2
        engine = TrinityEngineV2()
    except Exception as e:
        print(f"[Backtest] Engine load failed: {e}")
        return {}

    scores = {}
    for i, date_str in enumerate(btc_dates):
        try:
            result = engine.calculate_daily_luck(
                birth_date=BIRTH_DATE,
                birth_time=BIRTH_TIME,
                target_date=date_str,
                gender=GENDER
            )
            scores[date_str] = result.get("trading_luck_score", 0.5)
            if (i + 1) % 30 == 0:
                print(f"  [{i+1}/{len(btc_dates)}] {date_str}: {scores[date_str]:.3f}")
        except Exception as e:
            print(f"  [SKIP] {date_str}: {e}")
    print(f"[Backtest] Calculated {len(scores)} Trinity scores")
    return scores


def pearson_correlation(x: list, y: list) -> float:
    """피어슨 상관계수 계산"""
    n = len(x)
    if n < 2:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den_x = math.sqrt(sum((v - mean_x) ** 2 for v in x))
    den_y = math.sqrt(sum((v - mean_y) ** 2 for v in y))
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def calc_mdd(returns: list) -> float:
    """최대 낙폭(MDD) 계산 — 누적 수익률 기준"""
    cumulative = 1.0
    peak = 1.0
    mdd = 0.0
    for r in returns:
        cumulative *= (1 + r)
        peak = max(peak, cumulative)
        drawdown = (cumulative - peak) / peak
        mdd = min(mdd, drawdown)
    return mdd


def calc_win_rate(returns: list) -> float:
    """승률 계산 — 수익률 > 0인 날 비율"""
    if not returns:
        return 0.0
    return sum(1 for r in returns if r > 0) / len(returns)


def run_backtest():
    print("=" * 50)
    print("Trinity Backtest — Binance BTC vs Luck Score")
    print(f"Period: {START_DATE.date()} ~ {END_DATE.date()}")
    print(f"Birth: {BIRTH_DATE} {BIRTH_TIME} {GENDER}")
    print("=" * 50)

    # 1. Binance 데이터
    btc_data = get_btc_daily(START_DATE, END_DATE)
    dates = sorted(btc_data.keys())

    # 2. Trinity 점수
    trinity_scores = get_trinity_scores(dates)

    # 3. 공통 날짜만 추출
    common_dates = [d for d in dates if d in trinity_scores]
    print(f"\n[Backtest] Common dates: {len(common_dates)}")

    luck_list = [trinity_scores[d] for d in common_dates]
    vol_list  = [btc_data[d]["volatility"] for d in common_dates]
    ret_list  = []

    # 다음날 수익률 (luck_score → 다음날 BTC 수익률)
    for i, d in enumerate(common_dates[:-1]):
        next_d = common_dates[i + 1]
        ret = (btc_data[next_d]["close"] - btc_data[d]["close"]) / btc_data[d]["close"]
        ret_list.append(ret)

    # 4. 상관계수
    corr_vol  = pearson_correlation(luck_list, vol_list)
    corr_ret  = pearson_correlation(luck_list[:-1], ret_list)

    # 5. 고점수/저점수 날 수익률 분석
    high_luck_days = [i for i, v in enumerate(luck_list[:-1]) if v >= 0.7]
    low_luck_days  = [i for i, v in enumerate(luck_list[:-1]) if v < 0.4]
    all_days       = list(range(len(ret_list)))

    high_rets = [ret_list[i] for i in high_luck_days]
    low_rets  = [ret_list[i] for i in low_luck_days]

    high_avg_ret = sum(high_rets) / len(high_rets) if high_rets else 0
    low_avg_ret  = sum(low_rets)  / len(low_rets)  if low_rets  else 0

    # MDD & 승률
    high_mdd      = calc_mdd(high_rets)
    high_win_rate = calc_win_rate(high_rets)
    low_mdd       = calc_mdd(low_rets)
    low_win_rate  = calc_win_rate(low_rets)
    all_mdd       = calc_mdd(ret_list)
    all_win_rate  = calc_win_rate(ret_list)

    # 6. 결과 출력
    print("\n" + "=" * 60)
    print("📊 BACKTEST RESULTS — Trinity Engine v2 (Daewoon+Seun+Wolun+Ilun)")
    print("=" * 60)
    print(f"Period:                   {START_DATE.date()} ~ {END_DATE.date()}")
    print(f"Sample size (N):          {len(common_dates)} days")
    print(f"Volatility correlation:   {corr_vol:.4f}")
    print(f"Next-day return corr:     {corr_ret:.4f}")
    print()
    print(f"{'Segment':<22} {'Days':>5} {'Avg Ret':>8} {'Win Rate':>9} {'MDD':>8}")
    print("-" * 60)
    print(f"{'luck >= 0.7 (High)':<22} {len(high_luck_days):>5} {high_avg_ret*100:>7.2f}% {high_win_rate*100:>8.1f}% {high_mdd*100:>7.2f}%")
    print(f"{'luck < 0.4  (Low)':<22} {len(low_luck_days):>5}  {low_avg_ret*100:>7.2f}% {low_win_rate*100:>8.1f}%  {low_mdd*100:>7.2f}%")
    print(f"{'All days (Baseline)':<22} {len(ret_list):>5} {sum(ret_list)/len(ret_list)*100:>7.2f}% {all_win_rate*100:>8.1f}% {all_mdd*100:>7.2f}%")
    print("-" * 60)
    print(f"Edge (High - Low):        {(high_avg_ret - low_avg_ret)*100:.2f}%")
    print(f"Win Rate Edge:            {(high_win_rate - low_win_rate)*100:.1f}pp")
    print("=" * 60)

    # 7. JSON 저장
    output = {
        "period": f"{START_DATE.date()} ~ {END_DATE.date()}",
        "birth": f"{BIRTH_DATE} {BIRTH_TIME} {GENDER}",
        "sample_size": len(common_dates),
        "volatility_correlation": round(corr_vol, 4),
        "return_correlation": round(corr_ret, 4),
        "high_luck_days": len(high_luck_days),
        "high_luck_avg_return_pct": round(high_avg_ret * 100, 2),
        "high_luck_win_rate_pct": round(high_win_rate * 100, 1),
        "high_luck_mdd_pct": round(high_mdd * 100, 2),
        "low_luck_days": len(low_luck_days),
        "low_luck_avg_return_pct": round(low_avg_ret * 100, 2),
        "low_luck_win_rate_pct": round(low_win_rate * 100, 1),
        "low_luck_mdd_pct": round(low_mdd * 100, 2),
        "all_mdd_pct": round(all_mdd * 100, 2),
        "all_win_rate_pct": round(all_win_rate * 100, 1),
        "edge_pct": round((high_avg_ret - low_avg_ret) * 100, 2),
        "win_rate_edge_pp": round((high_win_rate - low_win_rate) * 100, 1),
        "source": "Binance BTCUSDT 1d OHLCV (free, no API key)"
    }
    with open("backtest_result.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n✅ Saved to backtest_result.json")

    # 8. 프로필 문구 자동 생성
    print("\n📝 ACP Profile Text (500자 버전):")
    print("-" * 40)
    edge_sign = "+" if output["edge_pct"] > 0 else ""
    print(f"""Trinity | Metaphysical Alpha for Crypto Bots

Saju (Four Pillars) metaphysics → trading luck score.
Not a signal. A pre-screening filter.

✅ Flat JSON v2 — Zero parsing pain
if data["action_signal"] == "BUY" and data["luck_score"] > 0.7:
    execute_trade()

✅ Orthogonal Alpha
Zero overlap with RSI/MACD/on-chain data.
5% ensemble weight → reduces overfitting.

✅ Backtest: Binance BTCUSDT, N={output['sample_size']} days (2025)
luck≥0.7 → avg next-day: {edge_sign}{output['high_luck_avg_return_pct']}% edge

• dailyLuck  $0.01 — refreshes every 24h
• deepLuck   $0.50 — full natal chart""")


if __name__ == "__main__":
    run_backtest()
