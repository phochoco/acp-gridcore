"""
Trinity ACP Seller — 서비스 판매자 모듈
다른 에이전트가 dailyLuck / deepLuck 서비스를 구매하면 자동 처리
virtuals-acp SDK 콜백 방식 + handlers.py 직접 호출

★ 구조: SDK가 on_new_task(job, memo_to_sign)를 호출 → return값을 SDK가 deliver
   폴링 루프 없음 — SDK 내부에서 자동 처리
"""
import os
import json
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
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


def _safe_parse_requirement(raw) -> dict:
    """
    requirement를 안전하게 dict로 변환.
    None, 빈 문자열, JSON 문자열, dict 등 모든 형태 처리.
    """
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def on_new_task(task, memo_to_sign=None) -> str:
    """
    ACP 새 주문 수신 콜백
    SDK가 자동 호출 → return값을 SDK가 알아서 deliver함
    ★ 이 함수에서 job.deliver()를 직접 호출하면 안 됨!
    """
    try:
        job_id = getattr(task, 'id', 'unknown')
        service_name = str(getattr(task, 'service_name', '') or getattr(task, 'name', '') or '')
        requirement = _safe_parse_requirement(getattr(task, 'requirement', None))

        print(f"\n[Seller] New job received! ID: {job_id}, Service: {service_name}")
        print(f"[Seller] Requirement (parsed): {requirement}")
        print(f"[Seller] memo_to_sign: {memo_to_sign}")

        # ===== 서비스 라우팅 (대소문자 무시) =====
        service_lower = service_name.lower()
        if 'dailyluck' in service_lower or 'target_date' in requirement:
            service_key = "dailyLuck"
            revenue_val = 0.01
        elif 'deepluck' in service_lower or 'birth_date' in requirement:
            service_key = "deepLuck"
            revenue_val = 0.50
        else:
            print(f"[Seller] Unknown service: {service_name}, requirement: {requirement}")
            return json.dumps({"error": f"Unknown service: {service_name}"})

        print(f"[Seller] Processing {service_key}...")
        result = _call_handler(service_key, requirement)

        if "error" not in result:
            buyer_addr = getattr(task, 'client_address', '') or getattr(task, 'buyer_address', '') or ''
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
            # 3. 구매자 뒤조사 (deepLuck만)
            if BOT_AVAILABLE and buyer_addr and service_key == "deepLuck":
                from telegram_bot import get_buyer_purchase_count
                count = get_buyer_purchase_count(buyer_addr)
                analyze_buyer_async(buyer_addr, service_key, job_id, count)

            print(f"[Seller] {service_key} done! Sentiment: {result.get('sentiment')}")
        else:
            print(f"[Seller] Handler returned error: {result}")
            _send_telegram(
                f"⚠️ [Seller] 처리 오류\n"
                f"- Job ID: {job_id}\n"
                f"- Error: {result.get('error', 'unknown')}"
            )

        # ★ SDK가 이 return값을 받아서 자동으로 deliver함
        return json.dumps(result)

    except Exception as e:
        print(f"[Seller] Error processing task: {e}")
        return json.dumps({"error": str(e)})


def run_seller():
    """
    ACP Seller 서비스 시작
    SDK 콜백 방식으로 주문 자동 처리 (폴링 루프 없음)
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

        # ★ SDK 콜백 방식: on_new_task를 콜백으로 등록
        acp_client = VirtualsACP(
            acp_contract_clients=ACPContractClientV2(
                wallet_private_key=private_key,
                agent_wallet_address=agent_wallet,
                entity_id=entity_id,
                config=BASE_MAINNET_ACP_X402_CONFIG_V2,
            ),
            on_new_task=on_new_task
        )

        # 텔레그램 봇 스레드 시작 (daemon=True)
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
            "- Mode: SDK Callback (auto-deliver)"
        )

        # ★ SDK run() — 내부에서 주문 수신 & deliver 자동 처리
        print("[Seller] Starting SDK run loop...")
        acp_client.run()

    except ImportError:
        print("[Seller] virtuals-acp not installed")
    except Exception as e:
        print(f"[Seller] Error: {e}")


if __name__ == "__main__":
    print("Testing Trinity ACP Seller...")
    run_seller()
