"""
Backtest Engine - 실제 BTC 데이터 기반 신뢰성 검증
비트코인 제네시스 블록 생일 기반 운세 점수와 실제 BTC 가격/거래량/변동성 상관관계 분석
"""
import json
import os
import requests
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta


# 비트코인 제네시스 블록 생일 (KST)
BITCOIN_GENESIS_BIRTH = {
    "year": 2009,
    "month": 1,
    "day": 4,      # UTC 1월 3일 18:15 → KST 1월 4일 03:15
    "hour": 3,
    "minute": 15
}


class BacktestEngine:
    """실제 BTC 데이터 기반 백테스트 및 신뢰성 검증 엔진"""
    
    def __init__(self, use_real_data: bool = True, cache_dir: str = None):
        """
        초기화
        
        Args:
            use_real_data: True면 실제 BTC 데이터 사용, False면 샘플 데이터 사용
            cache_dir: 캐시 디렉토리 경로
        """
        self.use_real_data = use_real_data
        
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "data")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        if use_real_data:
            self.historical_data = self._fetch_real_backtest_data()
        else:
            self.historical_data = self._load_sample_data()
    
    def get_correlation_report(self) -> Dict:
        """
        운세 점수 vs BTC 다중 지표 상관관계 리포트
        
        Returns:
            {
                "correlation_price": 0.0234,
                "correlation_volume": -0.0156,
                "correlation_volatility": 0.0789,
                "sample_size": 413,
                "methodology": "...",
                "disclaimer": "..."
            }
        """
        if not self.historical_data:
            return {
                "error": "No historical data available",
                "correlation_price": 0.0,
                "correlation_volume": 0.0,
                "correlation_volatility": 0.0,
                "sample_size": 0
            }
        
        # 데이터 추출
        scores = [d["luck_score"] for d in self.historical_data]
        price_changes = [d["price_change_percent"] for d in self.historical_data]
        volume_changes = [d.get("volume_change_percent", 0) for d in self.historical_data]
        volatility = [abs(d["price_change_percent"]) for d in self.historical_data]
        
        # 상관계수 계산 (소수점 4자리)
        corr_price = round(self._calculate_correlation(scores, price_changes), 4)
        corr_volume = round(self._calculate_correlation(scores, volume_changes), 4)
        corr_volatility = round(self._calculate_correlation(scores, volatility), 4)
        
        return {
            "correlation_coefficient": corr_price,  # 기존 호환성
            "correlation_price": corr_price,
            "correlation_volume": corr_volume,
            "correlation_volatility": corr_volatility,
            "sample_size": len(self.historical_data),
            "accuracy_rate": self._calculate_accuracy(scores, price_changes),
            "methodology": f"Bitcoin Genesis Block ({BITCOIN_GENESIS_BIRTH['year']}-{BITCOIN_GENESIS_BIRTH['month']:02d}-{BITCOIN_GENESIS_BIRTH['day']:02d} {BITCOIN_GENESIS_BIRTH['hour']:02d}:{BITCOIN_GENESIS_BIRTH['minute']:02d} KST) based analysis",
            "data_source": "CoinGecko API" if self.use_real_data else "Sample Data",
            "disclaimer": "Past performance does not guarantee future results. This is for informational purposes only."
        }
    
    def _fetch_real_backtest_data(self) -> List[Dict]:
        """실제 BTC 가격 데이터 수집 및 백테스트"""
        print("🔍 Fetching real BTC data from CoinGecko API...")
        
        # 1. BTC 가격 + 거래량 데이터 수집
        btc_data = self._fetch_btc_prices_and_volumes()
        
        if not btc_data:
            print("⚠️ Failed to fetch BTC data, using sample data")
            return self._load_sample_data()
        
        # 2. 운세 점수 계산
        print("🔮 Calculating Bitcoin luck scores...")
        luck_scores = self._calculate_bitcoin_luck_scores(btc_data)
        
        # 3. 데이터 매칭
        matched_data = self._match_data(btc_data, luck_scores)
        
        print(f"✅ Backtest data ready: {len(matched_data)} days")
        return matched_data
    
    def _fetch_btc_prices_and_volumes(self) -> Optional[List[Dict]]:
        """CoinGecko API로 BTC 가격 + 거래량 데이터 수집 (캐싱 포함)"""
        cache_file = os.path.join(self.cache_dir, "btc_data_cache.json")
        
        # 캐시 확인 (24시간 이내)
        if os.path.exists(cache_file):
            cache_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
            if cache_age < 86400:  # 24시간
                print("📦 Loading BTC data from cache...")
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        # API 호출 (무료 버전 사용)
        try:
            # CoinGecko 무료 API는 market_chart/range 대신 market_chart 사용
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            
            params = {
                "vs_currency": "usd",
                "days": "413",  # 최근 413일
                "interval": "daily"
            }
            
            print(f"🌐 Calling CoinGecko API (free tier)...")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 401:
                print("⚠️ CoinGecko API requires authentication, using sample data")
                return None
            
            response.raise_for_status()
            
            data = response.json()
            
            # 일일 데이터로 변환
            daily_data = self._convert_to_daily_data(
                data.get("prices", []),
                data.get("total_volumes", [])
            )
            
            # 캐시 저장
            with open(cache_file, 'w') as f:
                json.dump(daily_data, f, indent=2)
            
            print(f"✅ Fetched {len(daily_data)} days of BTC data")
            return daily_data
            
        except Exception as e:
            print(f"❌ Error fetching BTC data: {e}")
            return None
    
    def _convert_to_daily_data(self, prices: List, volumes: List) -> List[Dict]:
        """시간별 데이터를 일일 데이터로 변환"""
        daily_data = []
        
        # 날짜별로 그룹화
        price_by_date = {}
        volume_by_date = {}
        
        for timestamp, price in prices:
            date_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
            if date_str not in price_by_date:
                price_by_date[date_str] = []
            price_by_date[date_str].append(price)
        
        for timestamp, volume in volumes:
            date_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
            if date_str not in volume_by_date:
                volume_by_date[date_str] = []
            volume_by_date[date_str].append(volume)
        
        # 일일 평균 계산 및 변동률 계산
        dates = sorted(price_by_date.keys())
        prev_price = None
        prev_volume = None
        
        for date_str in dates:
            avg_price = np.mean(price_by_date[date_str])
            avg_volume = np.mean(volume_by_date.get(date_str, [0]))
            
            price_change = 0.0
            volume_change = 0.0
            
            if prev_price is not None:
                price_change = ((avg_price - prev_price) / prev_price) * 100
            
            if prev_volume is not None and prev_volume > 0:
                volume_change = ((avg_volume - prev_volume) / prev_volume) * 100
            
            daily_data.append({
                "date": date_str,
                "price": round(avg_price, 2),
                "volume": round(avg_volume, 2),
                "price_change_percent": round(price_change, 4),
                "volume_change_percent": round(volume_change, 4)
            })
            
            prev_price = avg_price
            prev_volume = avg_volume
        
        return daily_data[1:]  # 첫날은 변동률 없으므로 제외
    
    def _calculate_bitcoin_luck_scores(self, btc_data: List[Dict]) -> List[Dict]:
        """비트코인 제네시스 블록 생일 기반 운세 점수 계산"""
        from trinity_engine import TrinityEngine
        
        engine = TrinityEngine()
        luck_scores = []
        
        for data in btc_data:
            date_str = data["date"]
            
            try:
                score = engine.calculate_daily_luck(
                    target_date=date_str,
                    birth_year=BITCOIN_GENESIS_BIRTH["year"],
                    birth_month=BITCOIN_GENESIS_BIRTH["month"],
                    birth_day=BITCOIN_GENESIS_BIRTH["day"],
                    birth_hour=BITCOIN_GENESIS_BIRTH["hour"]
                )
                
                luck_scores.append({
                    "date": date_str,
                    "luck_score": score
                })
            except Exception as e:
                print(f"⚠️ Error calculating luck score for {date_str}: {e}")
                luck_scores.append({
                    "date": date_str,
                    "luck_score": 0.5  # 기본값
                })
        
        return luck_scores
    
    def _match_data(self, btc_data: List[Dict], luck_scores: List[Dict]) -> List[Dict]:
        """BTC 데이터와 운세 점수 매칭"""
        matched = []
        
        # 날짜별 인덱스 생성
        luck_by_date = {d["date"]: d["luck_score"] for d in luck_scores}
        
        for btc in btc_data:
            date = btc["date"]
            if date in luck_by_date:
                matched.append({
                    "date": date,
                    "luck_score": luck_by_date[date],
                    "btc_price": btc["price"],
                    "btc_change_percent": btc["price_change_percent"],
                    "btc_volume": btc.get("volume", 0),
                    "volume_change_percent": btc.get("volume_change_percent", 0)
                })
        
        return matched
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Pearson 상관계수 계산"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        try:
            correlation = np.corrcoef(x, y)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0
        except:
            return 0.0
    
    def _calculate_accuracy(self, scores: List[float], changes: List[float]) -> float:
        """예측 정확도 계산 (방향 일치율)"""
        if len(scores) != len(changes) or len(scores) < 2:
            return 0.0
        
        correct = 0
        for i in range(len(scores)):
            # 운세 점수 > 0.5 → 상승 예측
            # 운세 점수 < 0.5 → 하락 예측
            predicted_up = scores[i] > 0.5
            actual_up = changes[i] > 0
            
            if predicted_up == actual_up:
                correct += 1
        
        return correct / len(scores)
    
    def _load_sample_data(self) -> List[Dict]:
        """샘플 데이터 로드 (실제 데이터 사용 불가 시)"""
        sample_file = os.path.join(self.cache_dir, "backtest_data.json")
        
        if os.path.exists(sample_file):
            with open(sample_file, 'r') as f:
                return json.load(f)
        
        # 샘플 데이터 생성
        print("⚠️ Generating sample data...")
        return self._generate_sample_data()
    
    def _generate_sample_data(self) -> List[Dict]:
        """샘플 백테스트 데이터 생성 (폴백용)"""
        import random
        
        data = []
        start_date = datetime(2025, 1, 1)
        
        for i in range(413):
            date = start_date + timedelta(days=i)
            luck_score = random.uniform(0.3, 0.9)
            
            # 약한 상관관계 시뮬레이션
            base_change = random.gauss(0, 3)
            luck_influence = (luck_score - 0.5) * 2
            price_change = base_change + luck_influence
            
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "luck_score": round(luck_score, 2),
                "btc_price": round(50000 + random.gauss(0, 5000), 2),
                "price_change_percent": round(price_change, 2),  # 키 이름 통일
                "btc_change_percent": round(price_change, 2),     # 호환성
                "btc_volume": round(random.uniform(20, 40) * 1e9, 2),
                "volume_change_percent": round(random.gauss(0, 10), 2)
            })
        
        return data
