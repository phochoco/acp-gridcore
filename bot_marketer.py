"""
Trinity ACP Agent — Bot-to-Bot Marketing Module
Type A: 30분마다 무료 핑 (HTTP 요청, 로그 존재감)
Type B: 6시간마다 실제 ACP 온체인 결제 (virtuals-acp SDK)
"""
import os
import json
import random
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


# ===== 타겟 에이전트 설정 (targets.json에서 동적 로드) =====
def _load_targets():
    """targets.json에서 에이전트/토큰 목록 로드 (없으면 기본값 사용)"""
    targets_path = os.path.join(os.path.dirname(__file__), "targets.json")
    try:
        with open(targets_path, "r") as f:
            data = json.load(f)
            agents = data.get("agents", [])
            tokens = data.get("tokens", [])
            if agents and tokens:
                print(f"[Config] Loaded {len(agents)} agents, {len(tokens)} tokens from targets.json")
                return agents, tokens
    except Exception as e:
        print(f"[Config] targets.json load failed: {e}, using defaults")

    # 기본값 (targets.json 없을 때)
    return [
        {"name": "Otto AI", "project_id": "788", "service": "trading", "description": "Trading agent"},
        {"name": "BigBugAi", "project_id": "157", "service": "market_scan", "description": "Market scanner"},
    ], [
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    ]

TARGET_AGENTS, SAMPLE_TOKENS = _load_targets()

BASE_API_URL = "http://15.165.210.0:8000"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "***REDACTED_TELEGRAM***")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1629086047")

# Type B 결제 주기 (6시간마다)
TYPE_B_INTERVAL_HOURS = 6
_last_type_b_time: Optional[datetime] = None


def _send_telegram(message: str):
    """텔레그램 알림"""
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


# ===== TYPE A: 무료 핑 (기존 방식) =====
def _call_target_agent_free(agent: Dict, token_address: str) -> Optional[Dict]:
    """
    Type A: 타겟 에이전트 무료 핑
    ACP API에 HTTP 요청 → 상대방 서버 로그에 Trinity 기록
    """
    try:
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
            print(f"✅ [Type A] Agent ping success: HTTP {response.status_code}")
            try:
                return response.json() if response.text else {"status": "success", "http_code": response.status_code}
            except:
                return {"status": "success", "http_code": response.status_code}
        else:
            print(f"⚠️ [Type A] Agent ping failed: {response.status_code} — {response.text[:100]}")
            return None

    except Exception as e:
        print(f"⚠️ [Type A] Error calling {agent['name']}: {e}")
        return None


# ===== TYPE B: 실제 ACP 온체인 결제 (virtuals-acp SDK) =====
def _call_target_agent_paid(agent: Dict) -> Optional[Dict]:
    """
    Type B: 실제 ACP 온체인 결제
    virtuals-acp SDK로 타겟 에이전트에게 $0.01 USDC 결제
    6시간마다 1회 실행
    """
    try:
        from virtuals_acp.client import VirtualsACP
        from virtuals_acp.contract_clients.contract_client_v2 import ACPContractClientV2
        from virtuals_acp.configs.configs import BASE_MAINNET_ACP_X402_CONFIG_V2

        private_key = os.getenv("WHITELISTED_WALLET_PRIVATE_KEY", "")
        agent_wallet = os.getenv("BUYER_AGENT_WALLET_ADDRESS", "")
        entity_id = int(os.getenv("BUYER_ENTITY_ID", "2"))

        if not private_key or not agent_wallet:
            print("⚠️ [Type B] Missing ACP credentials in .env")
            return None

        print(f"💳 [Type B] Initiating paid job with {agent['name']}...")

        # ACP 클라이언트 초기화
        acp_client = VirtualsACP(
            acp_contract_clients=ACPContractClientV2(
                wallet_private_key=private_key,
                agent_wallet_address=agent_wallet,
                entity_id=entity_id,
                config=BASE_MAINNET_ACP_X402_CONFIG_V2,
            )
        )

        # 타겟 에이전트 검색
        today_str = datetime.now().strftime("%Y-%m-%d")
        service_requirement = (
            f"Trinity Agent requesting {agent['service']} analysis. "
            f"Date: {today_str}. "
            f"Cross-validation with Eastern Metaphysics trading signals."
        )

        # 에이전트 검색 후 job 시작
        relevant_agents = acp_client.browse_agents(agent["name"])

        if not relevant_agents:
            print(f"[Type B] Agent '{agent['name']}' not found in ACP marketplace")
            return None

        chosen_agent = relevant_agents[0]

        if not chosen_agent.job_offerings:
            print(f"[Type B] No offerings"); return None
        chosen_offering = min(chosen_agent.job_offerings, key=lambda x: getattr(x, 'price', float('inf')))

        # 스키마에서 required 필드 자동 추출하여 JSON 객체 생성
        schema = getattr(chosen_offering, 'requirement', None)
        if schema and isinstance(schema, dict):
            required_fields = schema.get('required', [])
            props = schema.get('properties', {})
            service_requirement = {}
            for field in required_fields:
                field_type = props.get(field, {}).get('type', 'string')
                if field_type == 'string':
                    service_requirement[field] = f"trinity-cross-validation-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                elif field_type == 'number':
                    service_requirement[field] = 0
                elif field_type == 'boolean':
                    service_requirement[field] = True
                else:
                    service_requirement[field] = "trinity-request"
            print(f"[Type B] Schema detected, using: {service_requirement}")
        else:
            # 스키마 없으면 기본 문자열
            service_requirement = f"Trinity Agent cross-validation: {agent['service']} analysis {datetime.now().strftime('%Y-%m-%d')}"
            print(f"[Type B] No schema, using string requirement")

        # Job 시작 (온체인 트랜잭션 발생!)
        job_id = chosen_offering.initiate_job(
            service_requirement=service_requirement,
            evaluator_address=agent_wallet,
        )


        print(f"✅ [Type B] Job initiated! Job ID: {job_id}")
        print(f"   Agent: {agent['name']} | Offering: {getattr(chosen_offering, 'name', 'N/A')}")

        return {
            "status": "paid_job_initiated",
            "job_id": str(job_id),
            "agent": agent["name"],
            "type": "TYPE_B_ONCHAIN"
        }

    except ImportError:
        print("⚠️ [Type B] virtuals-acp not installed. Run: pip install virtuals-acp")
        return None
    except Exception as e:
        print(f"⚠️ [Type B] Error: {e}")
        return None


def _should_run_type_b() -> bool:
    """Type B 실행 여부 판단 (6시간마다)"""
    global _last_type_b_time
    now = datetime.now()
    if _last_type_b_time is None:
        return True
    return (now - _last_type_b_time).total_seconds() >= TYPE_B_INTERVAL_HOURS * 3600


def _log_cross_validation(trinity_data: Dict, agent: Dict, agent_response: Optional[Dict], tx_type: str = "TYPE_A"):
    """교차검증 결과 로그 저장"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tx_type": tx_type,
        "trinity_score": trinity_data.get("trading_luck_score"),
        "trinity_sectors": trinity_data.get("favorable_sectors"),
        "trinity_volatility": trinity_data.get("volatility_index"),
        "target_agent": agent["name"],
        "agent_response": agent_response,
        "cross_validation": _interpret_cross_validation(trinity_data, agent_response)
    }

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
    logs = logs[-100:]

    with open(log_path, "w") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    print(f"📝 [{tx_type}] Cross-validation logged: Trinity={log_entry['trinity_score']}, Agent={agent['name']}")
    return log_entry


def _interpret_cross_validation(trinity_data: Dict, agent_response: Optional[Dict]) -> str:
    """교차검증 해석"""
    score = trinity_data.get("trading_luck_score", 0)
    volatility = trinity_data.get("volatility_index", "")

    if agent_response is None:
        return "AGENT_UNAVAILABLE"

    if score >= 0.7:
        trinity_signal = "BULLISH"
    elif score >= 0.5:
        trinity_signal = "NEUTRAL"
    else:
        trinity_signal = "BEARISH"

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
    Type A: 매 사이클 무료 핑
    Type B: 6시간마다 실제 온체인 결제
    """
    global _last_type_b_time
    print(f"\n🤖 [Bot Marketing] Starting cycle at {datetime.now().strftime('%H:%M:%S')}")

    # 1. Trinity 운세 조회
    trinity_data = _get_today_trinity_score()
    if not trinity_data:
        print("⚠️ Could not get Trinity score, skipping cycle")
        return

    score = trinity_data.get("trading_luck_score", 0)
    sectors = trinity_data.get("favorable_sectors", [])
    print(f"📊 Trinity Score: {score} | Sectors: {sectors}")

    # 2. 랜덤 타겟 에이전트 + 토큰 선택
    agent = random.choice(TARGET_AGENTS)
    token = random.choice(SAMPLE_TOKENS)
    print(f"🎯 Target: {agent['name']} | Token: {token[:10]}...")

    # ===== TYPE A: 무료 핑 (매 사이클) =====
    agent_response = _call_target_agent_free(agent, token)
    log_entry = _log_cross_validation(trinity_data, agent, agent_response, "TYPE_A")
    cross_signal = log_entry["cross_validation"]

    # ===== TYPE B: 유료 결제 (6시간마다) =====
    type_b_result = None
    type_b_tag = ""
    if _should_run_type_b():
        print(f"\n💳 [Type B] 6-hour interval reached — initiating paid job...")
        paid_agent = random.choice(TARGET_AGENTS)
        type_b_result = _call_target_agent_paid(paid_agent)
        if type_b_result:
            _last_type_b_time = datetime.now()
            _log_cross_validation(trinity_data, paid_agent, type_b_result, "TYPE_B")
            type_b_tag = f"\n💳 <b>Type B Paid Job:</b> {paid_agent['name']} | Job ID: {type_b_result.get('job_id', 'N/A')}"
            print(f"✅ [Type B] Complete! Next in {TYPE_B_INTERVAL_HOURS}h")

    # 5. 텔레그램 알림
    signal_tag = {
        "STRONG_ENTRY_SIGNAL":          "🟢 [STRONG BUY]",
        "ENTRY_SIGNAL_HIGH_VOLATILITY": "🟡 [BUY - High Vol]",
        "NEUTRAL_SIGNAL":               "⚪ [NEUTRAL]",
        "CAUTION_SIGNAL":               "🔴 [CAUTION]",
        "AGENT_UNAVAILABLE":            "⚫ [AGENT OFFLINE]",
    }.get(cross_signal, "[UNKNOWN]")

    agent_status = "OK" if agent_response else "NO RESPONSE"

    message = (
        f"{signal_tag} <b>Bot Marketing Cycle Done</b>\n\n"
        f"- <b>Type A Target:</b> {agent['name']}\n"
        f"- <b>Trinity Score:</b> {score} / 1.0\n"
        f"- <b>Sectors:</b> {', '.join(sectors)}\n"
        f"- <b>Agent Response:</b> {agent_status}\n"
        f"- <b>Signal:</b> <b>{cross_signal}</b>"
        f"{type_b_tag}\n\n"
        f"<i>Next cycle: 30 min later</i>"
    )

    _send_telegram(message)
    print(f"[Bot Marketing] Cycle complete: {cross_signal}\n")


# ===== 직접 실행 테스트 =====
if __name__ == "__main__":
    import time
    print("🤖 Trinity Bot Marketer started — 30min cycle")
    while True:
        try:
            asyncio.run(run_bot_marketing())
        except Exception as e:
            print(f"⚠️ Cycle error: {e}")
        print("⏳ Sleeping 30 minutes until next cycle...")
        time.sleep(1800)  # 30분
