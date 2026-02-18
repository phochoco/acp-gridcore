"""
Trinity ACP Seller — 서비스 판매자 모듈
다른 에이전트가 dailyLuck / deepLuck 서비스를 구매하면 자동 처리
virtuals-acp SDK on_new_task 콜백 기반
"""
import os
import json
import asyncio
import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_API_URL = os.getenv("BASE_API_URL", "http://15.165.210.0:8000")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "***REDACTED_TELEGRAM***")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1629086047")


def _send_telegram(message: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=5
        )
    except:
        pass


def _call_daily_luck(target_date: str) -> dict:
    """Trinity API에서 dailyLuck 데이터 조회"""
    try:
        r = requests.post(
            f"{BASE_API_URL}/api/v1/daily-luck",
            json={"target_date": target_date},
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[Seller] dailyLuck API error: {e}")
    return {}


def _call_deep_luck(birth_date: str, birth_time: str) -> dict:
    """Trinity API에서 deepLuck 데이터 조회"""
    try:
        r = requests.post(
            f"{BASE_API_URL}/api/v1/deep-luck",
            json={
                "birth_date": birth_date,
                "birth_time": birth_time,
                "target_date": datetime.now().strftime("%Y-%m-%d")
            },
            timeout=15
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[Seller] deepLuck API error: {e}")
    return {}


def on_new_task(task) -> str:
    """
    ACP 새 주문 수신 콜백
    다른 에이전트가 Trinity 서비스를 구매하면 자동 호출됨
    """
    try:
        job_id = getattr(task, 'id', 'unknown')
        service_name = getattr(task, 'service_name', '') or getattr(task, 'name', '')
        requirement = getattr(task, 'requirement', {}) or {}

        print(f"\n[Seller] New job received! ID: {job_id}, Service: {service_name}")
        print(f"[Seller] Requirement: {requirement}")

        # ===== dailyLuck 처리 =====
        if 'dailyLuck' in str(service_name) or 'target_date' in str(requirement):
            target_date = requirement.get('target_date', datetime.now().strftime('%Y-%m-%d'))
            print(f"[Seller] Processing dailyLuck for date: {target_date}")

            result = _call_daily_luck(target_date)

            if result:
                deliverable = json.dumps({
                    "lucky_report": json.dumps({
                        "trading_luck_score": result.get("trading_luck_score", 0),
                        "favorable_sectors": result.get("favorable_sectors", []),
                        "volatility_index": result.get("volatility_index", "UNKNOWN"),
                        "market_sentiment": result.get("market_sentiment", "NEUTRAL"),
                        "wealth_opportunity": result.get("wealth_opportunity", "LOW"),
                        "analysis_date": target_date,
                        "provider": "Trinity Agent - Eastern Metaphysics"
                    })
                })
            else:
                deliverable = json.dumps({"lucky_report": json.dumps({"error": "Service temporarily unavailable"})})

            _send_telegram(
                f"[SALE] <b>dailyLuck Sold!</b>\n"
                f"- Job ID: {job_id}\n"
                f"- Date: {target_date}\n"
                f"- Score: {result.get('trading_luck_score', 'N/A')}\n"
                f"- Revenue: $0.01 USDC"
            )
            print(f"[Seller] dailyLuck delivered! Score: {result.get('trading_luck_score')}")
            return deliverable

        # ===== deepLuck 처리 =====
        elif 'deepLuck' in str(service_name) or 'birth_date' in str(requirement):
            birth_date = requirement.get('birth_date', '1990-01-01')
            birth_time = requirement.get('birth_time', '12:00')
            print(f"[Seller] Processing deepLuck for: {birth_date} {birth_time}")

            result = _call_deep_luck(birth_date, birth_time)

            if result:
                deliverable = json.dumps({
                    "deep_report": json.dumps({
                        "luck_score": result.get("trading_luck_score", 0),
                        "favorable_sectors": result.get("favorable_sectors", []),
                        "risk_level": result.get("volatility_index", "UNKNOWN"),
                        "strategy": result.get("market_sentiment", "NEUTRAL"),
                        "wealth_opportunity": result.get("wealth_opportunity", "LOW"),
                        "birth_date": birth_date,
                        "birth_time": birth_time,
                        "provider": "Trinity Agent - Saju Eastern Metaphysics"
                    })
                })
            else:
                deliverable = json.dumps({"deep_report": json.dumps({"error": "Service temporarily unavailable"})})

            _send_telegram(
                f"[SALE] <b>deepLuck Sold!</b>\n"
                f"- Job ID: {job_id}\n"
                f"- Birth: {birth_date} {birth_time}\n"
                f"- Score: {result.get('trading_luck_score', 'N/A')}\n"
                f"- Revenue: $0.50 USDC"
            )
            print(f"[Seller] deepLuck delivered!")
            return deliverable

        else:
            print(f"[Seller] Unknown service: {service_name}")
            return json.dumps({"error": f"Unknown service: {service_name}"})

    except Exception as e:
        print(f"[Seller] Error processing task: {e}")
        return json.dumps({"error": str(e)})


def run_seller():
    """
    ACP Seller 서비스 시작
    다른 에이전트의 구매 요청을 대기하며 자동 처리
    """
    try:
        from virtuals_acp.client import VirtualsACP
        from virtuals_acp.contract_clients.contract_client_v2 import ACPContractClientV2
        from virtuals_acp.configs.configs import BASE_MAINNET_ACP_X402_CONFIG_V2

        private_key = os.getenv("WHITELISTED_WALLET_PRIVATE_KEY", "")
        agent_wallet = os.getenv("BUYER_AGENT_WALLET_ADDRESS", "")
        entity_id = int(os.getenv("BUYER_ENTITY_ID", "2"))

        if not private_key or not agent_wallet:
            print("[Seller] Missing ACP credentials in .env")
            return

        print(f"\n[Seller] Starting Trinity ACP Seller Service...")
        print(f"[Seller] Agent Wallet: {agent_wallet}")
        print(f"[Seller] Services: dailyLuck ($0.01), deepLuck ($0.50)")
        print(f"[Seller] Waiting for purchase requests...\n")

        acp_client = VirtualsACP(
            acp_contract_clients=ACPContractClientV2(
                wallet_private_key=private_key,
                agent_wallet_address=agent_wallet,
                entity_id=entity_id,
                config=BASE_MAINNET_ACP_X402_CONFIG_V2,
            ),
            on_new_task=on_new_task  # 주문 수신 콜백
        )

        _send_telegram(
            "[ONLINE] <b>Trinity Seller Service Started</b>\n"
            "- dailyLuck: $0.01 USDC\n"
            "- deepLuck: $0.50 USDC\n"
            "- Polling for purchase requests every 30s..."
        )

        # 폴링 루프 — 30초마다 미처리 주문 확인
        import time
        print("[Seller] Polling loop started (every 30s)...")
        while True:
            try:
                pending = acp_client.get_pending_memo_jobs()
                if pending:
                    print(f"[Seller] Found {len(pending)} pending job(s)!")
                    for job in pending:
                        try:
                            job_id = getattr(job, 'id', 'unknown')
                            job_name = getattr(job, 'name', '') or ''
                            requirement = getattr(job, 'requirement', {}) or {}
                            phase = str(getattr(job, 'phase', ''))
                            client_addr = getattr(job, 'client_address', '')

                            print(f"[Seller] Job {job_id}: name={job_name}, phase={phase}")
                            print(f"[Seller] Requirement: {requirement}")

                            # 자기 자신이 보낸 job (buyer==evaluator)은 스킵
                            if client_addr.lower() == agent_wallet.lower():
                                print(f"[Seller] Skipping own job {job_id}")
                                continue

                            # 주문 수락
                            job.accept()
                            print(f"[Seller] Job {job_id} accepted!")

                            # 서비스 처리 및 결과 전달
                            deliverable = on_new_task(job)
                            job.deliver(deliverable)
                            print(f"[Seller] Job {job_id} delivered!")

                        except Exception as je:
                            print(f"[Seller] Job handling error: {je}")
                else:
                    print(f"[Seller] No pending jobs at {datetime.now().strftime('%H:%M:%S')}")
            except Exception as pe:
                print(f"[Seller] Polling error: {pe}")
            time.sleep(30)


    except ImportError:
        print("[Seller] virtuals-acp not installed")
    except Exception as e:
        print(f"[Seller] Error: {e}")


if __name__ == "__main__":
    print("Testing Trinity ACP Seller...")
    run_seller()
