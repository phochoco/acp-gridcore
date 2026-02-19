"""
Trinity Oracle — B2A Data Feed Agent
포트: 8001 | 경로: trinity-protocol.com/oracle/

서비스:
  - sectorFeed   ($0.005) : CoinGecko × Trinity 실시간 섹터 신호
  - dailySignal  ($0.01)  : 오늘의 매수/매도 신호 (BFF → :8000)
  - deepSignal   ($0.50)  : 에이전트 사주 심층 분석 (BFF → :8000)
  - agentMatch   ($1.00~) : 에이전트 궁합 분석 (n≤5)

포지셔닝: Survival Intelligence for Autonomous Agents
"""
import os
import time
import asyncio
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import json
import secrets

import httpx
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

TRINITY_API_URL = "http://localhost:8000"  # 내부 Trinity Agent API
COINGECKO_API   = "https://api.coingecko.com/api/v3"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "1629086047")

# ===== 인메모리 API Key 크레딧 스토어 =====
# 실제 운영 시 Redis 또는 DB로 교체
_api_keys: Dict[str, float] = {}  # key → credit balance (USDC)

def _generate_api_key() -> str:
    return "trk_" + secrets.token_hex(16)

# ===== TTL 캐시 (sectorFeed용) =====
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}
CACHE_TTL = 300  # 5분

def _get_cache(key: str):
    if key in _cache and time.time() - _cache_ts.get(key, 0) < CACHE_TTL:
        return _cache[key]
    return None

def _set_cache(key: str, value: Any):
    _cache[key] = value
    _cache_ts[key] = time.time()

# ===== 결제 검증 미들웨어 =====
SERVICE_PRICES = {
    "sectorFeed":  0.005,
    "dailySignal": 0.01,
    "deepSignal":  0.50,
    "agentMatch":  1.00,  # 기본 2개, 추가당 +$0.50
}

async def verify_payment(request: Request, service: str, extra_cost: float = 0.0):
    """API Key 기반 결제 검증 — 크레딧 차감"""
    api_key = request.headers.get("X-Oracle-Key", "")
    if not api_key:
        raise HTTPException(status_code=401, detail="X-Oracle-Key header required")

    required = SERVICE_PRICES.get(service, 0) + extra_cost
    balance = _api_keys.get(api_key, 0.0)

    if balance < required:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credit. Required: ${required:.3f}, Balance: ${balance:.3f}"
        )
    _api_keys[api_key] -= required
    return {"api_key": api_key, "charged": required, "remaining": _api_keys[api_key]}

# ===== FastAPI 앱 =====
app = FastAPI(
    title="Trinity Oracle",
    description=(
        "Survival Intelligence for Autonomous Agents.\n\n"
        "⚡ A wrong partner = lost USDC = server bill unpaid = DEATH.\n"
        "Trinity Oracle maximizes your agent's survival probability."
    ),
    version="1.0.0",
    openapi_url="/oracle/openapi.json",
    docs_url="/oracle/docs",
    redoc_url=None,
)

# ===== Pydantic 모델 =====
class DailySignalRequest(BaseModel):
    target_date: str = Field(default_factory=lambda: date.today().strftime("%Y-%m-%d"),
                             description="Date to analyze (YYYY-MM-DD)")
    agent_birth: Optional[str] = Field(None, description="Agent creation date as birth data (YYYY-MM-DD HH:MM)")

class DeepSignalRequest(BaseModel):
    agent_birth_date: str = Field(..., description="Agent genesis date (YYYY-MM-DD). Use deployment timestamp.")
    agent_birth_time: str = Field(default="12:00", description="Agent creation time (HH:MM)")
    target_date: str = Field(default_factory=lambda: date.today().strftime("%Y-%m-%d"))
    gender: str = Field(default="M", description="M or F (agent polarity)")

class AgentMatchRequest(BaseModel):
    agents: List[Dict[str, str]] = Field(
        ...,
        description="List of agents with 'name' and 'birth_date'. Max 5.",
        example=[
            {"name": "AgentA", "birth_date": "2024-03-15"},
            {"name": "AgentB", "birth_date": "2025-01-20"},
        ]
    )
    target_date: str = Field(default_factory=lambda: date.today().strftime("%Y-%m-%d"))

class TopupRequest(BaseModel):
    amount: float = Field(..., description="Amount in USDC to add to credit")
    tx_hash: Optional[str] = Field(None, description="On-chain payment TX hash for verification")

# ===== 유틸 =====
async def _send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
            )
    except Exception:
        pass

# ===== 엔드포인트 =====

@app.get("/oracle/health")
async def health():
    return {"status": "alive", "service": "Trinity Oracle", "timestamp": datetime.now().isoformat()}

@app.post("/oracle/api-key")
async def create_api_key(body: TopupRequest):
    """
    API Key 발급 (크레딧 선충전 방식).
    실제 운영 시 tx_hash 온체인 검증 로직 추가 필요.
    """
    key = _generate_api_key()
    _api_keys[key] = body.amount
    return {
        "api_key": key,
        "credit": body.amount,
        "message": "Store this key. It cannot be recovered."
    }

@app.get("/oracle/balance")
async def check_balance(request: Request):
    """크레딧 잔액 조회"""
    api_key = request.headers.get("X-Oracle-Key", "")
    if not api_key or api_key not in _api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"api_key": api_key[:12] + "...", "balance_usdc": _api_keys[api_key]}

# ─── sectorFeed ───────────────────────────────────────────
@app.get("/oracle/sector-feed")
async def sector_feed(request: Request):
    """
    [sectorFeed $0.005] Real-time market sector signal.
    CoinGecko top movers × Trinity daily score.
    Cached 5 minutes to prevent rate limit.
    """
    payment = await verify_payment(request, "sectorFeed")

    cached = _get_cache("sector_feed")
    if cached:
        cached["cached"] = True
        return cached

    # Trinity 일일 점수 조회
    trinity_score = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{TRINITY_API_URL}/api/v1/daily-luck",
                json={"target_date": date.today().strftime("%Y-%m-%d")}
            )
            if r.status_code == 200:
                trinity_score = r.json()
    except Exception:
        pass

    # CoinGecko 상위 코인 조회
    top_coins = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{COINGECKO_API}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "volume_desc",
                    "per_page": 20,
                    "page": 1,
                    "sparkline": False,
                    "price_change_percentage": "24h"
                }
            )
            if r.status_code == 200:
                coins = r.json()
                top_coins = [
                    {
                        "symbol": c["symbol"].upper(),
                        "name": c["name"],
                        "price_usd": c["current_price"],
                        "change_24h_pct": round(c.get("price_change_percentage_24h", 0), 2),
                        "volume_usd": c.get("total_volume", 0),
                    }
                    for c in coins[:10]
                ]
    except Exception:
        pass

    # Trinity 섹터와 교차 분석
    favorable_sectors = []
    signal = "NEUTRAL"
    if trinity_score:
        favorable_sectors = trinity_score.get("favorable_sectors", [])
        score = trinity_score.get("trading_luck_score", 0.5)
        signal = "BUY" if score >= 0.65 else ("CAUTION" if score < 0.4 else "NEUTRAL")

    result = {
        "timestamp": datetime.now().isoformat(),
        "trinity_score": trinity_score.get("trading_luck_score") if trinity_score else None,
        "signal": signal,
        "favorable_sectors": favorable_sectors,
        "top_coins": top_coins,
        "cached": False,
        "credit_charged": payment["charged"],
    }

    _set_cache("sector_feed", result)

    await _send_telegram(
        f"📡 [Oracle] sectorFeed 호출\n"
        f"- Signal: {signal}\n"
        f"- Sectors: {favorable_sectors}\n"
        f"- Credit: ${payment['charged']}"
    )

    return result

# ─── dailySignal (BFF → :8000) ────────────────────────────
@app.post("/oracle/daily-signal")
async def daily_signal(request: Request, body: DailySignalRequest):
    """
    [dailySignal $0.01] Today's crypto trading signal.
    Agents: pass your creation date as agent_birth for personalized signal.
    """
    payment = await verify_payment(request, "dailySignal")

    async with httpx.AsyncClient(timeout=15) as client:
        payload = {"target_date": body.target_date}
        if body.agent_birth:
            payload["user_birth_data"] = body.agent_birth
        r = await client.post(f"{TRINITY_API_URL}/api/v1/daily-luck", json=payload)

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Upstream Trinity API error")

    result = r.json()
    result["oracle_credit_charged"] = payment["charged"]
    return result

# ─── deepSignal (BFF → :8000) ─────────────────────────────
@app.post("/oracle/deep-signal")
async def deep_signal(request: Request, body: DeepSignalRequest):
    """
    [deepSignal $0.50] 24-hour hourly signal for your agent.
    Use agent_birth_date = your deployment date for entity-level Saju analysis.
    Wrong partners cost you everything. Know your destiny first.
    """
    payment = await verify_payment(request, "deepSignal")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{TRINITY_API_URL}/api/v1/deep-luck",
            json={
                "birth_date": body.agent_birth_date,
                "birth_time": body.agent_birth_time,
                "target_date": body.target_date,
                "gender": body.gender,
            }
        )

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Upstream Trinity API error")

    result = r.json()
    result["oracle_credit_charged"] = payment["charged"]
    return result

# ─── agentMatch ───────────────────────────────────────────
@app.post("/oracle/agent-match")
async def agent_match(request: Request, body: AgentMatchRequest):
    """
    [agentMatch $1.00~$2.50] Agent compatibility survival analysis.

    ⚡ SURVIVAL WARNING: A wrong trading partner = USDC loss = server bill unpaid = DEATH.
    Check compatibility BEFORE committing resources.

    Max 5 agents. Pricing:
    - 2 agents: $1.00
    - 3 agents: $1.50
    - 4 agents: $2.00
    - 5 agents: $2.50
    """
    n = len(body.agents)
    if n < 2:
        raise HTTPException(status_code=422, detail="Minimum 2 agents required for match analysis")
    if n > 5:
        raise HTTPException(
            status_code=422,
            detail="Maximum 5 agents allowed for survival analysis"
        )

    # 가격: 2개=$1.00, 이후 +$0.50/에이전트
    price = 1.00 + (n - 2) * 0.50
    extra_cost = price - SERVICE_PRICES["agentMatch"]  # 기본 $1.00 초과분
    payment = await verify_payment(request, "agentMatch", extra_cost=max(0, extra_cost))

    target_date = body.target_date
    pairs = []

    async def _get_score(client: httpx.AsyncClient, birth_date: str) -> float:
        """에이전트 사주 점수 조회"""
        try:
            r = await client.post(
                f"{TRINITY_API_URL}/api/v1/daily-luck",
                json={"target_date": target_date, "user_birth_data": birth_date + " 12:00"}
            )
            if r.status_code == 200:
                return r.json().get("trading_luck_score", 0.5)
        except Exception:
            pass
        return 0.5

    agents = body.agents
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                a = agents[i]
                b = agents[j]

                score_a = await _get_score(client, a.get("birth_date", "2024-01-01"))
                score_b = await _get_score(client, b.get("birth_date", "2024-01-01"))

                # 궁합 점수: 조화 평균 - 차이 패널티
                diff_penalty = abs(score_a - score_b)
                harmony = round((score_a + score_b) / 2 - diff_penalty * 0.3, 3)
                harmony = max(0.0, min(1.0, harmony))

                verdict = (
                    "SYNERGY"    if harmony >= 0.7  else
                    "COMPATIBLE" if harmony >= 0.5  else
                    "CAUTION"    if harmony >= 0.35 else
                    "AVOID"
                )

                pairs.append({
                    "agent_a": a.get("name", "AgentA"),
                    "agent_b": b.get("name", "AgentB"),
                    "score_a": round(score_a, 3),
                    "score_b": round(score_b, 3),
                    "harmony_score": harmony,
                    "verdict": verdict,
                    "recommendation": (
                        "✅ Strong synergy — ideal collaboration pair."    if verdict == "SYNERGY"    else
                        "🟡 Compatible — proceed with caution."            if verdict == "COMPATIBLE" else
                        "⚠️ Risky — verify alignment before committing."   if verdict == "CAUTION"    else
                        "❌ Avoid — incompatible energies, high loss risk."
                    )
                })

    # 최적 / 최악 파트너
    best  = max(pairs, key=lambda x: x["harmony_score"])
    worst = min(pairs, key=lambda x: x["harmony_score"])

    result = {
        "timestamp": datetime.now().isoformat(),
        "agents_analyzed": n,
        "pairs_checked": len(pairs),
        "pairs": pairs,
        "best_match":  {"pair": f"{best['agent_a']} ↔ {best['agent_b']}",  "score": best["harmony_score"]},
        "worst_match": {"pair": f"{worst['agent_a']} ↔ {worst['agent_b']}", "score": worst["harmony_score"]},
        "survival_advisory": (
            f"Best collaboration: {best['agent_a']} ↔ {best['agent_b']} (harmony {best['harmony_score']}). "
            f"Avoid: {worst['agent_a']} ↔ {worst['agent_b']} (harmony {worst['harmony_score']})."
        ),
        "oracle_credit_charged": payment["charged"],
    }

    await _send_telegram(
        f"🔮 [Oracle] agentMatch 호출\n"
        f"- 에이전트: {n}개 / {len(pairs)}쌍\n"
        f"- Best: {best['agent_a']} ↔ {best['agent_b']} ({best['harmony_score']})\n"
        f"- Credit: ${payment['charged']:.2f}"
    )

    return result

# ===== 실행 =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("oracle_server:app", host="0.0.0.0", port=8001, reload=False)
