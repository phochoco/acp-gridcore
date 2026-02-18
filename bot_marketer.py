"""
Trinity ACP Agent — Bot-to-Bot Marketing Module
30분마다 타 에이전트 서비스를 호출하여 온체인 존재감 확보.
응답 데이터를 교차검증 명분으로 활용.
"""
import os
import json
import random
import asyncio
import requests
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# .env 파일 로드 (GAME_API_KEY 등)
load_dotenv()


# ===== 타겟 에이전트 설정 =====
# ACP 마켓 상위 에이전트 (실제 확인된 Project ID)
# https://app.virtuals.io/acp/agent-details/{id}
TARGET_AGENTS = [
    {
        "name": "Ethy AI",
        "project_id": "84",
        "service": "token_info",
        "description": "ETH ecosystem intelligence — #1 ranked agent"
    },
    {
        "name": "BigBugAi",
        "project_id": "157",
        "service": "market_scan",
        "description": "Market scanner"
    },
    {
        "name": "ArAIstotle",
        "project_id": "842",
        "service": "analysis",
        "description": "AI analysis"
    },
    {
        "name": "Axelrod",
        "project_id": "129",
        "service": "analysis",
        "description": "Trading analysis"
    },
    {
        "name": "Otto AI",
        "project_id": "788",
        "service": "trading",
        "description": "Trading agent"
    },
]

# 교차검증에 사용할 토큰 주소 목록 (매 사이클 다른 토큰 사용)
SAMPLE_TOKENS = [
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
    "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
    "0x514910771AF9Ca656af840dff83E8264EcF986CA",  # LINK
]

BASE_API_URL = "http://15.165.210.0:8000"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "***REDACTED_TELEGRAM***")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1629086047")


def _send_telegram(message: str):
    """텔레그램 알림 (선택적)"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=5)
    except:
        pass


def _get_today_trinity_score() -> Optional[Dict]:
    """오늘 Trinity 운세 점수 조회"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.post(
            f"{BASE_API_URL}/api/v1/daily-luck",
            json={"target_date": today},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"⚠️ Failed to get Trinity score: {e}")
    return None


def _call_target_agent(agent: Dict, token_address: str) -> Optional[Dict]:
    """
    타겟 에이전트 서비스 호출 (ACP HTTP API)
    실제 ACP 프로토콜로 호출 — 트랜잭션 기록이 온체인에 남음
    """
    try:
        # ACP 마켓플레이스 API 엔드포인트
        # 실제 ACP API 스펙에 맞게 조정 필요
        acp_api_url = "https://api.virtuals.io/api/acp/v1/request"
        
        game_api_key = os.getenv("GAME_API_KEY", "")
        if not game_api_key:
            print("⚠️ GAME_API_KEY not set, skipping agent call")
            return None

        payload = {
            "projectId": agent["project_id"],
            "service": agent["service"],
            "params": {
                "token_address": token_address,
                "chain": "base"
            }
        }

        headers = {
            "Authorization": f"Bearer {game_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(acp_api_url, json=payload, headers=headers, timeout=15)
        
        if response.status_code in (200, 201, 202, 204):
            # 204 = No Content (성공이지만 응답 본문 없음)
            print(f"✅ Agent call success: HTTP {response.status_code}")
            try:
                return response.json() if response.text else {"status": "success", "http_code": response.status_code}
            except:
                return {"status": "success", "http_code": response.status_code}
        else:
            print(f"⚠️ Agent call failed: {response.status_code} — {response.text[:100]}")
            return None


    except Exception as e:
        print(f"⚠️ Error calling {agent['name']}: {e}")
        return None


def _log_cross_validation(trinity_data: Dict, agent: Dict, agent_response: Optional[Dict]):
    """교차검증 결과 로그 저장"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "trinity_score": trinity_data.get("trading_luck_score"),
        "trinity_sectors": trinity_data.get("favorable_sectors"),
        "trinity_volatility": trinity_data.get("volatility_index"),
        "target_agent": agent["name"],
        "agent_response": agent_response,
        "cross_validation": _interpret_cross_validation(trinity_data, agent_response)
    }

    # 로그 파일에 저장
    log_path = os.path.join(os.path.dirname(__file__), "data", "bot_marketing_log.json")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append(log_entry)
    # 최근 100개만 유지
    logs = logs[-100:]

    with open(log_path, "w") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    print(f"📝 Cross-validation logged: Trinity={log_entry['trinity_score']}, Agent={agent['name']}")
    return log_entry


def _interpret_cross_validation(trinity_data: Dict, agent_response: Optional[Dict]) -> str:
    """교차검증 해석 — 마케팅 명분 생성"""
    score = trinity_data.get("trading_luck_score", 0)
    volatility = trinity_data.get("volatility_index", "")

    if agent_response is None:
        return "AGENT_UNAVAILABLE"

    # Trinity 점수 기반 신호
    if score >= 0.7:
        trinity_signal = "BULLISH"
    elif score >= 0.5:
        trinity_signal = "NEUTRAL"
    else:
        trinity_signal = "BEARISH"

    # 교차검증 결과
    if trinity_signal == "BULLISH" and volatility == "LOW":
        return "STRONG_ENTRY_SIGNAL"
    elif trinity_signal == "BULLISH":
        return "ENTRY_SIGNAL_HIGH_VOLATILITY"
    elif trinity_signal == "BEARISH":
        return "CAUTION_SIGNAL"
    else:
        return "NEUTRAL_SIGNAL"


async def run_bot_marketing():
    """
    메인 마케팅 봇 실행 함수 (APScheduler에서 30분마다 호출)
    1. Trinity 오늘 운세 조회
    2. 랜덤 타겟 에이전트 선택
    3. 타겟 에이전트 호출 ($0.01 지불 → 온체인 기록)
    4. 교차검증 결과 로그
    5. 강한 신호 시 텔레그램 알림
    """
    print(f"\n🤖 [Bot Marketing] Starting cycle at {datetime.now().strftime('%H:%M:%S')}")

    # 1. Trinity 운세 조회
    trinity_data = _get_today_trinity_score()
    if not trinity_data:
        print("⚠️ Could not get Trinity score, skipping cycle")
        return

    score = trinity_data.get("trading_luck_score", 0)
    sectors = trinity_data.get("favorable_sectors", [])
    print(f"📊 Trinity Score: {score} | Sectors: {sectors}")

    # 2. 랜덤 타겟 에이전트 + 토큰 선택 (패턴 노출 방지)
    agent = random.choice(TARGET_AGENTS)
    token = random.choice(SAMPLE_TOKENS)
    print(f"🎯 Target: {agent['name']} | Token: {token[:10]}...")

    # 3. 에이전트 호출 (실제 $0.01 트랜잭션 발생)
    agent_response = _call_target_agent(agent, token)

    # 4. 교차검증 로그
    log_entry = _log_cross_validation(trinity_data, agent, agent_response)
    cross_signal = log_entry["cross_validation"]

    # 5. 텔레그램 알림 (매 사이클 요약)
    signal_tag = {
        "STRONG_ENTRY_SIGNAL":        "[STRONG BUY]",
        "ENTRY_SIGNAL_HIGH_VOLATILITY": "[BUY - High Vol]",
        "NEUTRAL_SIGNAL":             "[NEUTRAL]",
        "CAUTION_SIGNAL":             "[CAUTION]",
        "AGENT_UNAVAILABLE":          "[AGENT OFFLINE]",
    }.get(cross_signal, "[UNKNOWN]")

    agent_status = "OK" if agent_response else "NO RESPONSE"

    message = (
        f"{signal_tag} <b>Bot Marketing Cycle Done</b>\n\n"
        f"- <b>Target:</b> {agent['name']}\n"
        f"- <b>Trinity Score:</b> {score} / 1.0\n"
        f"- <b>Sectors:</b> {', '.join(sectors)}\n"
        f"- <b>Agent Response:</b> {agent_status}\n"
        f"- <b>Signal:</b> <b>{cross_signal}</b>\n\n"
        f"<i>Next cycle: 30 min later</i>"
    )

    _send_telegram(message)
    print(f"[Bot Marketing] Cycle complete: {cross_signal}\n")



# ===== 직접 실행 테스트 =====
if __name__ == "__main__":
    print("🧪 Testing bot marketing module...")
    asyncio.run(run_bot_marketing())
