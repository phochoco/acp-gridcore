"""
Trinity ACP Handlers — 서비스 로직 라우터 v2
dailyLuck / deepLuck 요청을 trinity_engine_v2에 라우팅하여 처리

JSON 응답 스키마 v2:
- meta 블록 분리 (provider, version, timestamp)
- 핵심 필드 root 레벨 평탄화 (Flat is better than nested)
- Enum 표준화: sentiment(BULLISH/BEARISH/NEUTRAL), action_signal(BUY/SELL/HOLD)
- breakdown 제거, metrics 블록에 수치만
- base_score 명시로 raw_score 정합성 확보
"""
import json
from datetime import datetime, timezone
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


# ===== Enum 매핑 상수 =====

# keyword → sentiment (BULLISH/BEARISH/NEUTRAL)
KEYWORD_TO_SENTIMENT = {
    "STRONG_BULLISH": "BULLISH",
    "BULLISH":        "BULLISH",
    "NEUTRAL":        "NEUTRAL",
    "BEARISH":        "BEARISH",
    "STRONG_BEARISH": "BEARISH",
}

# keyword → action_signal (BUY/SELL/HOLD)
KEYWORD_TO_ACTION = {
    "STRONG_BULLISH": "BUY",
    "BULLISH":        "BUY",
    "NEUTRAL":        "HOLD",
    "BEARISH":        "SELL",
    "STRONG_BEARISH": "SELL",
}

# keyword → strategy_tag (DIPS/BREAKOUT/MOMENTUM/DEFENSIVE/WAIT)
KEYWORD_TO_STRATEGY = {
    "STRONG_BULLISH": "MOMENTUM",
    "BULLISH":        "DIPS",
    "NEUTRAL":        "WAIT",
    "BEARISH":        "DEFENSIVE",
    "STRONG_BEARISH": "DEFENSIVE",
}

# volatility_index → volatility Enum (LOW/HIGH)
VOLATILITY_MAP = {
    "LOW":  "LOW",
    "HIGH": "HIGH",
}

# luck_score → risk_level Enum (LOW_RISK/MED_RISK/HIGH_RISK)
def _score_to_risk(luck_score: float) -> str:
    if luck_score >= 0.65:
        return "LOW_RISK"
    elif luck_score >= 0.40:
        return "MED_RISK"
    else:
        return "HIGH_RISK"

# 오행(Five Elements) → 크립토 섹터 (참고용)
ELEMENT_TO_SECTOR = {
    "木": ["NFT", "GAMEFI", "NEW_LISTING"],
    "火": ["AI", "MEME", "VOLATILE_TECH"],
    "土": ["INFRA", "L1", "BTC"],
    "金": ["RWA", "STABLECOIN", "POW"],
    "水": ["DEFI", "L2", "LIQUIDITY"],
}


def _parse_requirement(requirement: Union[dict, str]) -> dict:
    """requirement를 dict로 파싱"""
    if isinstance(requirement, str):
        try:
            return json.loads(requirement)
        except Exception:
            return {}
    return requirement or {}


def _build_response(engine_result: dict, input_echo: dict) -> dict:
    """
    엔진 결과를 표준 스키마 v2로 변환.
    - meta 분리
    - 핵심 필드 root 레벨 평탄화
    - Enum 표준화
    - breakdown 제거, metrics 수치만
    """
    keyword = engine_result.get("keyword", "NEUTRAL")
    luck_score = engine_result.get("trading_luck_score", 0.5)
    raw_score = engine_result.get("raw_score", 50)

    # breakdown에서 수치 추출 (문자열 파싱 대신 TrinityScore 직접 접근은 불가 → 추정값 사용)
    # raw_score = base(50) + daewoon + seun + interaction
    # metrics는 엔진 내부 계산값을 breakdown string에서 추출
    metrics = _extract_metrics(engine_result.get("breakdown", []))

    return {
        "meta": {
            "provider": "Trinity Agent",
            "version": "v2.0",
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "note": "birth_time interpreted as provided (no timezone conversion)"
        },
        "input_echo": input_echo,
        # === 핵심 지표 (root 레벨 평탄화) ===
        "sentiment":     KEYWORD_TO_SENTIMENT.get(keyword, "NEUTRAL"),
        "volatility":    VOLATILITY_MAP.get(engine_result.get("volatility_index", "LOW"), "LOW"),
        "risk_level":    _score_to_risk(luck_score),
        "action_signal": KEYWORD_TO_ACTION.get(keyword, "HOLD"),
        "strategy_tag":  KEYWORD_TO_STRATEGY.get(keyword, "WAIT"),
        # === 수치 데이터 ===
        "luck_score":  luck_score,
        "raw_score":   raw_score,
        "base_score":  50,
        "sectors":     engine_result.get("favorable_sectors", []),
        # === 세부 수치 (옵션) ===
        "metrics": metrics,
    }


def _extract_metrics(breakdown: list) -> dict:
    """
    breakdown 문자열 리스트에서 수치 추출.
    예: "Grand Cycle (Daewoon): +19.5pts" → major_luck: 19.5
    """
    metrics = {"major_luck": 0.0, "annual_luck": 0.0, "harmony": 0.0}
    try:
        for item in breakdown:
            if "Daewoon" in item or "Grand Cycle" in item:
                val = float(item.split(":")[1].replace("pts", "").strip())
                metrics["major_luck"] = val
            elif "Seun" in item or "Annual Cycle" in item:
                val = float(item.split(":")[1].replace("pts", "").strip())
                metrics["annual_luck"] = val
            elif "Interaction" in item or "Clash" in item or "Harmony" in item:
                val = float(item.split(":")[1].replace("pts", "").strip())
                metrics["harmony"] = val
    except Exception:
        pass
    return metrics


def handle_daily_luck(requirement: Union[dict, str]) -> str:
    """
    [서비스] $0.01 dailyLuck
    입력: {"target_date": "2026-02-18"}
    출력: 시장 전체 운세 JSON (스키마 v2)
    """
    try:
        data = _parse_requirement(requirement)
        target_date = data.get("target_date", datetime.now().strftime("%Y-%m-%d"))
        birth_date = data.get("birth_date", "1990-01-01")
        birth_time = data.get("birth_time", "12:00")
        gender = data.get("gender", "M")

        print(f"[Handlers] dailyLuck: target={target_date}")

        input_echo = {
            "target_date": target_date,
            "birth_date": birth_date,
            "birth_time": birth_time,
        }

        if ENGINE_AVAILABLE and _engine:
            engine_result = _engine.calculate_daily_luck(
                birth_date=birth_date,
                birth_time=birth_time,
                target_date=target_date,
                gender=gender
            )
            response = _build_response(engine_result, input_echo)
        else:
            response = {
                "meta": {
                    "provider": "Trinity Agent",
                    "version": "v2.0",
                    "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "note": "Engine unavailable — fallback response"
                },
                "input_echo": input_echo,
                "sentiment": "NEUTRAL",
                "volatility": "LOW",
                "risk_level": "MED_RISK",
                "action_signal": "HOLD",
                "strategy_tag": "WAIT",
                "luck_score": 0.5,
                "raw_score": 50,
                "base_score": 50,
                "sectors": ["DEFI", "L2"],
                "metrics": {"major_luck": 0.0, "annual_luck": 0.0, "harmony": 0.0},
            }

        return json.dumps(response)

    except Exception as e:
        print(f"[Handlers] dailyLuck error: {e}")
        return json.dumps({"error": str(e), "luck_score": 0.5})


def handle_deep_luck(requirement: Union[dict, str]) -> str:
    """
    [서비스] $0.50 deepLuck
    입력: {"birth_date": "1990-05-15", "birth_time": "14:30", "target_date": "2026-02-18"}
    출력: 개인 정밀 운세 JSON (스키마 v2)
    """
    try:
        data = _parse_requirement(requirement)
        birth_date = data.get("birth_date")
        birth_time = data.get("birth_time", "12:00")
        target_date = data.get("target_date", datetime.now().strftime("%Y-%m-%d"))
        gender = data.get("gender", "M")

        if not birth_date:
            return json.dumps({
                "error": "birth_date is required for deepLuck service",
                "example": {"birth_date": "2023-04-14", "birth_time": "12:00", "target_date": "2026-02-18"}
            })

        print(f"[Handlers] deepLuck: birth={birth_date} {birth_time}, target={target_date}")

        input_echo = {
            "genesis_date": birth_date,
            "genesis_time": birth_time,
            "target_date": target_date,
            "note": "birth_time interpreted as provided (no timezone conversion)"
        }

        if ENGINE_AVAILABLE and _engine:
            engine_result = _engine.calculate_daily_luck(
                birth_date=birth_date,
                birth_time=birth_time,
                target_date=target_date,
                gender=gender
            )
            response = _build_response(engine_result, input_echo)
        else:
            return json.dumps({"error": "Engine unavailable", "birth_date": birth_date})

        return json.dumps(response)

    except Exception as e:
        print(f"[Handlers] deepLuck error: {e}")
        return json.dumps({"error": str(e)})
