"""
Real Bitcoin Backtest using yfinance
100% Real Market Data - No API Key Required
"""
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta

# --- [1. 설정: 비트코인 사주 정보 (제네시스 블록)] ---
# UTC: 2009-01-03 18:15:05
# KST: 2009-01-04 03:15:05 (UTC+9)
BTC_BIRTH = {
    "year": 2009, 
    "month": 1, 
    "day": 4, 
    "hour": 3
}

# --- [2. 트리니티 엔진 로드] ---
try:
    from trinity_engine import TrinityEngine
    engine = TrinityEngine()
    print("✅ Trinity Engine Loaded Successfully.")
except ImportError:
    print("❌ TrinityEngine not found! Please check file name.")
    exit()

def get_real_btc_data():
    """yfinance를 통해 실제 BTC-USD 데이터 가져오기 (API Key 불필요)"""
    print("🔄 Fetching REAL Bitcoin data from Yahoo Finance...")
    
    # 최근 413일 데이터 조회
    end_date = datetime.now()
    start_date = end_date - timedelta(days=413)
    
    try:
        # yfinance로 다운로드 (진행바 끔)
        df = yf.download("BTC-USD", start=start_date, end=end_date, progress=False)
        
        if df.empty:
            print("❌ Failed to download data.")
            return pd.DataFrame()

        # 데이터 가공 (yfinance는 인덱스가 날짜임)
        df = df.reset_index()
        
        # 컬럼 이름 통일 (Date, Close, Volume)
        # yfinance 버전에 따라 컬럼이 다를 수 있어 처리
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        
        # 필수 컬럼만 남기기
        df = df[['Date', 'Close', 'Volume']].copy()
        df.columns = ['date', 'price', 'volume']
        
        # 날짜 문자열로 변환
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # 지표 계산
        df['price_change'] = df['price'].pct_change() * 100
        df['volume_change'] = df['volume'].pct_change() * 100
        df['volatility'] = df['price_change'].abs()
        
        df = df.dropna()
        
        print(f"✅ Downloaded {len(df)} days of REAL market data.")
        return df
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return pd.DataFrame()

def run_real_backtest():
    # 1. 실제 데이터 가져오기
    df = get_real_btc_data()
    if df.empty: 
        print("❌ No data available. Exiting.")
        return

    print(f"🔮 Calculating Metaphysics Luck Scores (Birth: {BTC_BIRTH['year']}-{BTC_BIRTH['month']:02d}-{BTC_BIRTH['day']:02d})...")

    # 2. 운세 점수 계산
    luck_scores = []
    total = len(df)
    
    # 비트코인 생일 문자열 생성
    btc_birth_date = f"{BTC_BIRTH['year']}-{BTC_BIRTH['month']:02d}-{BTC_BIRTH['day']:02d}"
    btc_birth_time = f"{BTC_BIRTH['hour']:02d}:15"
    
    for idx, row in df.iterrows():
        target_date = row['date']
        
        try:
            # Trinity Engine 호출 (올바른 시그니처)
            result = engine.calculate_daily_luck(
                birth_date=btc_birth_date,  # "2009-01-04"
                birth_time=btc_birth_time,   # "03:15"
                target_date=target_date,     # "2025-01-01"
                gender="M"
            )
            
            # 결과에서 trading_luck_score 추출
            if isinstance(result, dict):
                score = result.get('trading_luck_score', 0.5)
            else:
                score = 0.5
                
            luck_scores.append(score)
            
        except Exception as e:
            print(f"⚠️ Error on {target_date}: {e}")
            luck_scores.append(0.5)  # 에러 시 중립값

        if (idx + 1) % 50 == 0:
            print(f"Processing... {idx + 1}/{total}")

    df['luck_score'] = luck_scores

    # 3. 진짜 상관계수 분석
    corr_price = df['luck_score'].corr(df['price_change'])
    corr_vol = df['luck_score'].corr(df['volume_change'])
    corr_vola = df['luck_score'].corr(df['volatility'])

    print("\n" + "="*60)
    print(f"📊 REAL-WORLD BACKTEST RESULTS (N={len(df)})")
    print("="*60)
    print(f"1. Price Correlation (가격 방향) : {corr_price:.5f}")
    print(f"2. Volume Correlation (거래량)   : {corr_vol:.5f}")
    print(f"3. Volatility Correlation (변동성): {corr_vola:.5f}")
    print("-" * 60)
    
    # 4. 결론 도출
    threshold = 0.05  # 유의미한 기준점
    
    print("📢 [TRUTH REVEALED]")
    
    found_edge = False
    
    if abs(corr_price) > threshold:
        direction = "Follow Logic" if corr_price > 0 else "Reverse Logic"
        print(f"✅ PRICE EDGE FOUND! ({corr_price:.4f}) -> Use {direction}")
        found_edge = True
        
    if abs(corr_vola) > threshold:
        print(f"✅ VOLATILITY EDGE FOUND! ({corr_vola:.4f}) -> Predict Big Moves")
        found_edge = True
        
    if abs(corr_vol) > threshold:
        print(f"✅ VOLUME EDGE FOUND! ({corr_vol:.4f}) -> Predict Market Activity")
        found_edge = True
        
    if not found_edge:
        print("⚠️ No significant correlation found in simple Saju.")
        print("👉 Recommendation: Integrate Astrology (Phase 2) or adjust birth time.")
    
    # 5. 결과 저장
    result = {
        "correlation_price": float(corr_price),
        "correlation_volume": float(corr_vol),
        "correlation_volatility": float(corr_vola),
        "sample_size": len(df),
        "data_source": "Yahoo Finance (yfinance)",
        "methodology": f"Bitcoin Genesis Block ({BTC_BIRTH['year']}-{BTC_BIRTH['month']:02d}-{BTC_BIRTH['day']:02d} {BTC_BIRTH['hour']:02d}:15 KST) based analysis"
    }
    
    with open('real_backtest_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n✅ Results saved to real_backtest_result.json")
    return result

if __name__ == "__main__":
    run_real_backtest()
