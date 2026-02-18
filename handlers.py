"""
Trinity ACP Handlers — 서비스 로직 라우터
dailyLuck / deepLuck 요청을 trinity_engine_v2에 라우팅하여 처리
"""
import json
from datetime import datetime
from typing import Union

# Trinity 엔진 import
try:
    from trinity_engine_v2 import TrinityEngineV2
    _engine = TrinityEngineV2()
    ENGINE_AVAILABLE = True
    print("[Handlers] TrinityEngineV2 loaded successfully")
except Exception as e:
    ENGINE_AVAILABLE = False
    _engine = None
    print(f"[Handlers] TrinityEngineV2 load failed: {e}")

# ===== 매핑 상수 (Rosetta Stone) =====
# 오행(Five Elements) → 크립토 섹터
ELEMENT_TO_SECTOR = {
    "木": ["NFT", "GameFi", "New Listings"],
    "火": ["AI", "Meme Coin", "Volatile Tech"],
    "土": ["RWA", "Infrastructure", "Exchange Tokens"],
    "金": ["Bitcoin (BTC)", "PoW Coins", "Store of Value"],
    "水": ["DeFi", "Layer 2", "Liquidity Providers"]
}

# 관계(Relation) → 리스크 레벨
RELATION_TO_RISK = {
    "Clash":   "HIGH_RISK (Sell/Avoid)",
    "Grudge":  "HIGH_VOLATILITY (Wait)",
    "Harmony": "LOW_RISK (Buy/Hold)",
    "Support": "VERY_LOW_RISK (Strong Buy)",
    "Same":    "NEUTRAL (Range Trade)"
}

# 키워드 → 전략 매핑
KEYWORD_TO_STRATEGY = {
    "STRONG_BULLISH": "Aggressive Entry — Strong Buy Signal",
    "BULLISH":        "Moderate Entry — Buy on Dips",
    "NEUTRAL":        "Range Trade — Wait for Breakout",
    "BEARISH":        "Reduce Position — Defensive Mode",
    "STRONG_BEARISH": "Exit Position — Capital Preservation"
}


def _parse_requirement(requirement: Union[dict, str]) -> dict:
    """requirement를 dict로 파싱"""
    if isinstance(requirement, str):
        try:
            return json.loads(requirement)
        except Exception:
            return {}
    return requirement or {}


def handle_daily_luck(requirement: Union[dict, str]) -> str:
    """
    [서비스] $0.01 dailyLuck
    입력: {"target_date": "2026-02-18"}
    출력: 시장 전체 운세 JSON
    """
    try:
        data = _parse_requirement(requirement)
        target_date = data.get("target_date", datetime.now().strftime("%Y-%m-%d"))
        # dailyLuck은 날짜 기반 시장 운세 — birth_date 없으면 기준일 사용
        birth_date = data.get("birth_date", "1990-01-01")
        birth_time = data.get("birth_time", "12:00")
        gender = data.get("gender", "M")

        print(f"[Handlers] dailyLuck: target={target_date}")

        if ENGINE_AVAILABLE and _engine:
            result = _engine.calculate_daily_luck(
                birth_date=birth_date,
                birth_time=birth_time,
                target_date=target_date,
                gender=gender
            )
            # 엔진 결과에 전략 추가
            keyword = result.get("keyword", "NEUTRAL")
            result["strategy"] = KEYWORD_TO_STRATEGY.get(keyword, "Hold Position")
            result["provider"] = "Trinity Agent — Eastern Metaphysics"
            result["analysis_date"] = target_date
            return json.dumps(result)
        else:
            # 엔진 없을 때 폴백
            return json.dumps({
                "trading_luck_score": 0.5,
                "favorable_sectors": ["DeFi", "Layer 2"],
                "volatility_index": "MEDIUM",
                "market_sentiment": "NEUTRAL",
                "wealth_opportunity": "MEDIUM",
                "strategy": "Hold Position",
                "provider": "Trinity Agent (Fallback Mode)",
                "analysis_date": target_date
            })

    except Exception as e:
        print(f"[Handlers] dailyLuck error: {e}")
        return json.dumps({"error": str(e), "trading_luck_score": 0.5})


def handle_deep_luck(requirement: Union[dict, str]) -> str:
    """
    [서비스] $0.50 deepLuck
    입력: {"birth_date": "1990-05-15", "birth_time": "14:30"}
    출력: 개인 정밀 운세 JSON
    """
    try:
        data = _parse_requirement(requirement)
        birth_date = data.get("birth_date")
        birth_time = data.get("birth_time", "12:00")
        target_date = data.get("target_date", datetime.now().strftime("%Y-%m-%d"))
        gender = data.get("gender", "M")

        if not birth_date:
            return json.dumps({"error": "birth_date is required for deepLuck service"})

        print(f"[Handlers] deepLuck: birth={birth_date} {birth_time}, target={target_date}")

        if ENGINE_AVAILABLE and _engine:
            result = _engine.calculate_daily_luck(
                birth_date=birth_date,
                birth_time=birth_time,
                target_date=target_date,
                gender=gender
            )
            # deepLuck 전용 필드 추가
            keyword = result.get("keyword", "NEUTRAL")
            result["strategy"] = KEYWORD_TO_STRATEGY.get(keyword, "Hold Position")
            result["risk_level"] = RELATION_TO_RISK.get(
                "Harmony" if result.get("trading_luck_score", 0) > 0.6 else "Clash",
                "NEUTRAL"
            )
            result["birth_date"] = birth_date
            result["birth_time"] = birth_time
            result["provider"] = "Trinity Agent — Saju Eastern Metaphysics"
            result["analysis_date"] = target_date
            return json.dumps(result)
        else:
            return json.dumps({
                "error": "Engine unavailable",
                "birth_date": birth_date,
                "birth_time": birth_time
            })

    except Exception as e:
        print(f"[Handlers] deepLuck error: {e}")
        return json.dumps({"error": str(e)})
