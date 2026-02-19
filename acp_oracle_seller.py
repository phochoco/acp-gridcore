"""
Trinity Oracle — ACP Seller 로직
/oracle/ 엔드포인트 서비스를 ACP 마켓플레이스에 등록하고 판매
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

AGENT_WALLET   = os.getenv("BUYER_AGENT_WALLET_ADDRESS", "").lower()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "1629086047")

# Oracle 서버 주소 (내부 호출)
ORACLE_BASE = "http://localhost:8001"

import requests

def _send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=5
        )
    except Exception:
        pass

def _safe_parse(requirement) -> dict:
    if isinstance(requirement, dict):
        return requirement
    try:
        return json.loads(requirement)
    except Exception:
        return {"raw": str(requirement)}


def on_new_task(job, memo_to_sign=None):
    """
    ACP 신규 작업 처리 — Oracle 서비스 라우팅
    """
    try:
        job_id = job.id
        service_name = str(job.name or '').lower()
        requirement = _safe_parse(job.requirement)

        # 자기 자신이 보낸 job 스킵
        client_addr = str(getattr(job, 'client_address', '') or '').lower()
        provider_addr = str(getattr(job, 'provider_address', '') or '').lower()
        if AGENT_WALLET and client_addr == AGENT_WALLET:
            print(f"[Oracle Seller] SKIP Job {job_id} — self-sent")
            return
        if AGENT_WALLET and provider_addr and provider_addr != AGENT_WALLET:
            print(f"[Oracle Seller] SKIP Job {job_id} — not our provider")
            return

        print(f"\n[Oracle Seller] New job! ID={job_id}, Service={service_name}")

        # Accept
        if memo_to_sign:
            memo_to_sign.sign(True, f"Trinity Oracle accepted: {service_name}")
            print(f"[Oracle Seller] Accepted job {job_id}")

        # 서비스 라우팅
        result = None
        if 'sectorfeed' in service_name or 'sector' in service_name:
            result = _handle_sector_feed(requirement)
        elif 'dailysignal' in service_name or 'daily' in service_name:
            result = _handle_daily_signal(requirement)
        elif 'deepsignal' in service_name or 'deep' in service_name:
            result = _handle_deep_signal(requirement)
        elif 'agentmatch' in service_name or 'match' in service_name:
            result = _handle_agent_match(requirement)
        else:
            result = {"error": f"Unknown service: {service_name}"}

        print(f"[Oracle Seller] Job {job_id} processed: {str(result)[:100]}")
        _send_telegram(
            f"🔮 <b>[Oracle Seller] Job 완료</b>\n"
            f"- Job ID: {job_id}\n"
            f"- Service: {service_name}\n"
            f"- Result: {str(result)[:80]}..."
        )

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        print(f"[Oracle Seller] Error: {e}")
        return json.dumps({"error": str(e)})


def _handle_sector_feed(req: dict) -> dict:
    """Internal sectorFeed 호출 (결제 검증 없이 내부 직접 호출)"""
    target_date = req.get("target_date", datetime.now().strftime("%Y-%m-%d"))
    try:
        r = requests.get(f"{ORACLE_BASE}/oracle/sector-feed",
                         headers={"X-Oracle-Key": _get_internal_key()}, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        pass
    return {"error": "sectorFeed unavailable"}


def _handle_daily_signal(req: dict) -> dict:
    target_date = req.get("target_date", datetime.now().strftime("%Y-%m-%d"))
    agent_birth = req.get("agent_birth", req.get("user_birth_data", None))
    payload = {"target_date": target_date}
    if agent_birth:
        payload["agent_birth"] = agent_birth
    try:
        r = requests.post(f"{ORACLE_BASE}/oracle/daily-signal",
                          json=payload,
                          headers={"X-Oracle-Key": _get_internal_key()}, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        pass
    return {"error": "dailySignal unavailable"}


def _handle_deep_signal(req: dict) -> dict:
    payload = {
        "agent_birth_date": req.get("birth_date", req.get("agent_birth_date", "2024-01-01")),
        "agent_birth_time": req.get("birth_time", "12:00"),
        "target_date": req.get("target_date", datetime.now().strftime("%Y-%m-%d")),
        "gender": req.get("gender", "M"),
    }
    try:
        r = requests.post(f"{ORACLE_BASE}/oracle/deep-signal",
                          json=payload,
                          headers={"X-Oracle-Key": _get_internal_key()}, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        pass
    return {"error": "deepSignal unavailable"}


def _handle_agent_match(req: dict) -> dict:
    agents = req.get("agents", [])
    if not agents:
        return {"error": "agents list required"}
    payload = {
        "agents": agents,
        "target_date": req.get("target_date", datetime.now().strftime("%Y-%m-%d"))
    }
    try:
        r = requests.post(f"{ORACLE_BASE}/oracle/agent-match",
                          json=payload,
                          headers={"X-Oracle-Key": _get_internal_key()}, timeout=60)
        if r.status_code == 200:
            return r.json()
        return {"error": f"agentMatch error: {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# 내부 요청용 마스터 키 (서버 기동 시 한 번 생성)
_internal_key: Optional[str] = None

def _get_internal_key() -> str:
    """내부 서비스용 무제한 크레딧 키 조회 / 생성"""
    global _internal_key
    if _internal_key:
        return _internal_key
    try:
        r = requests.post(f"{ORACLE_BASE}/oracle/api-key",
                          json={"amount": 9999.0, "tx_hash": "internal"},
                          timeout=5)
        if r.status_code == 200:
            _internal_key = r.json()["api_key"]
            return _internal_key
    except Exception:
        pass
    return "internal-fallback-key"


def on_evaluate(job, is_accepted: bool, memo_to_sign=None):
    """결제 완료 후 최종 deliver"""
    try:
        job_id = job.id
        print(f"[Oracle Seller] on_evaluate: job={job_id}, accepted={is_accepted}")
        if is_accepted and memo_to_sign:
            memo_to_sign.sign(True, "Trinity Oracle delivery confirmed")
            print(f"[Oracle Seller] Job {job_id} delivered.")
            _send_telegram(f"✅ [Oracle] Job {job_id} delivered successfully!")
    except Exception as e:
        print(f"[Oracle Seller] on_evaluate error: {e}")


def run_oracle_seller():
    """Oracle ACP Seller 서비스 시작"""
    from virtuals_acp.client import VirtualsACP
    from virtuals_acp.contract_clients.contract_client_v2 import ACPContractClientV2
    from virtuals_acp.configs.configs import BASE_MAINNET_ACP_X402_CONFIG_V2

    private_key  = os.getenv("WHITELISTED_WALLET_PRIVATE_KEY", "")
    agent_wallet = os.getenv("BUYER_AGENT_WALLET_ADDRESS", "")
    entity_id    = int(os.getenv("ORACLE_ENTITY_ID", os.getenv("BUYER_ENTITY_ID", "2")))

    if not private_key or not agent_wallet:
        print("[Oracle Seller] Missing ACP credentials in .env")
        return

    print(f"\n[Oracle Seller] Starting Trinity Oracle ACP Seller...")
    print(f"[Oracle Seller] Entity ID: {entity_id}")

    acp_client = VirtualsACP(
        acp_contract_clients=ACPContractClientV2(
            wallet_private_key=private_key,
            agent_wallet_address=agent_wallet,
            entity_id=entity_id,
            config=BASE_MAINNET_ACP_X402_CONFIG_V2,
        )
    )
    acp_client.set_on_new_task(on_new_task)
    acp_client.set_on_evaluate(on_evaluate)

    _send_telegram("🔮 [Trinity Oracle] ACP Seller 서비스 시작!")
    acp_client.start()


if __name__ == "__main__":
    run_oracle_seller()
