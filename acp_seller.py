"""
Trinity ACP Seller — 서비스 판매자 모듈
다른 에이전트가 dailyLuck / deepLuck 서비스를 구매하면 자동 처리
virtuals-acp SDK 폴링 방식 + handlers.py 직접 호출
"""
import os
import json
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "***REDACTED_TELEGRAM***")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1629086047")

# handlers.py 직접 import (Trinity 엔진 직접 호출)
try:
    import handlers as _handlers
    HANDLERS_AVAILABLE = True
    print("[Seller] handlers.py loaded successfully")
except Exception as e:
    HANDLERS_AVAILABLE = False
    print(f"[Seller] handlers.py load failed: {e}")

# 텔레그램 봇 + 뒤조사 모듈 import
try:
    from telegram_bot import run_telegram_bot, save_sale
    from buyer_profiler import analyze_buyer_async
    BOT_AVAILABLE = True
    print("[Seller] telegram_bot + buyer_profiler loaded")
except Exception as e:
    BOT_AVAILABLE = False
    print(f"[Seller] Bot/Profiler load failed: {e}")


def _send_telegram(message: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=5
        )
    except:
        pass


def _call_handler(service: str, requirement: dict) -> dict:
    """handlers.py를 통해 Trinity 엔진 직접 호출"""
    try:
        if not HANDLERS_AVAILABLE:
            return {"error": "handlers.py not available"}
        if service == "dailyLuck":
            result_str = _handlers.handle_daily_luck(requirement)
        elif service == "deepLuck":
            result_str = _handlers.handle_deep_luck(requirement)
        else:
            return {"error": f"Unknown service: {service}"}
        return json.loads(result_str)
    except Exception as e:
        print(f"[Seller] Handler error: {e}")
        return {"error": str(e)}


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

        # ===== 서비스 라우팅 =====
        if 'dailyLuck' in str(service_name) or 'target_date' in str(requirement):
            service_key = "dailyLuck"
            revenue = "$0.01 USDC"
        elif 'deepLuck' in str(service_name) or 'birth_date' in str(requirement):
            service_key = "deepLuck"
            revenue = "$0.50 USDC"
        else:
            print(f"[Seller] Unknown service: {service_name}")
            return json.dumps({"error": f"Unknown service: {service_name}"})

        print(f"[Seller] Processing {service_key}...")
        result = _call_handler(service_key, requirement)

        if "error" not in result:
            buyer_addr = getattr(task, 'client_address', '') or getattr(task, 'buyer_address', '')
            revenue_val = 0.01 if service_key == "dailyLuck" else 0.50

            # 1. 판매 내역 저장
            if BOT_AVAILABLE:
                save_sale(job_id, service_key, buyer_addr, revenue_val)

            # 2. 텔레그램 판매 알림
            _send_telegram(
                f"💰 [SALE] <b>{service_key} Sold!</b>\n"
                f"- Job ID: {job_id}\n"
                f"- Sentiment: {result.get('sentiment', 'N/A')}\n"
                f"- Action: {result.get('action_signal', 'N/A')} / {result.get('strategy_tag', 'N/A')}\n"
                f"- Sectors: {result.get('sectors', [])}\n"
                f"- Revenue: ${revenue_val} USDC"
            )

            # 3. 구매자 뒤조사 (비동기 실행 — deepLuck만)
            if BOT_AVAILABLE and buyer_addr and service_key == "deepLuck":
                from telegram_bot import get_buyer_purchase_count
                count = get_buyer_purchase_count(buyer_addr)
                analyze_buyer_async(buyer_addr, service_key, job_id, count)

            print(f"[Seller] {service_key} delivered! Sentiment: {result.get('sentiment')}")
        else:
            print(f"[Seller] Handler returned error: {result}")

        return json.dumps(result)

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

        # 텔레그램 봇 스레드 먼저 시작 (daemon=True)
        if BOT_AVAILABLE:
            bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
            bot_thread.start()
            print("[Seller] Telegram command bot started (daemon thread)")

        _send_telegram(
            "[ONLINE] <b>Trinity Seller Service Started</b>\n"
            "- dailyLuck: $0.01 USDC\n"
            "- deepLuck: $0.50 USDC\n"
            "- Buyer Profiler: ACTIVE\n"
            "- Telegram Bot: /sales /last /status /help\n"
            "- Polling every 30s..."
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
                            _send_telegram(
                                f"⚠️ [Seller] Job 처리 오류\n"
                                f"- Job ID: {getattr(job, 'id', 'unknown')}\n"
                                f"- Error: {str(je)[:200]}"
                            )
                else:
                    print(f"[Seller] No pending jobs at {datetime.now().strftime('%H:%M:%S')}")
            except Exception as pe:
                print(f"[Seller] Polling error: {pe}")
                _send_telegram(f"⚠️ [Seller] 폴링 오류 발생\n- Error: {str(pe)[:200]}")
            time.sleep(30)


    except ImportError:
        print("[Seller] virtuals-acp not installed")
    except Exception as e:
        print(f"[Seller] Error: {e}")


if __name__ == "__main__":
    print("Testing Trinity ACP Seller...")
    run_seller()
