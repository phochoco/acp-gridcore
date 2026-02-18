"""
Trinity ACP Seller — 서비스 판매자 모듈

★ 올바른 ACP Job 처리 흐름:
  1. on_new_task(job, memo_to_sign)
     - next_phase = NEGOTIATION
     - job.accept() 호출 → 협상 승인
     - 엔진 계산 후 결과를 job_results[job.id]에 저장
     - [SALE] 텔레그램 알림

  2. on_evaluate(job)
     - 구매자가 결제 완료 후 호출됨
     - next_phase = EVALUATION
     - job_results에서 결과 꺼내서 job.deliver() 호출
     - job.evaluate(True) 호출
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

# ★ job_id → 계산 결과 저장 (on_new_task → on_evaluate 간 공유)
job_results = {}


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


def on_new_task(job, memo_to_sign=None):
    """
    ★ STEP 1: 새 주문 수신
    - job.accept() 로 협상 승인
    - 엔진 계산 후 결과를 job_results에 저장
    - deliver는 하지 않음 (구매자 결제 후 on_evaluate에서 처리)
    """
    try:
        job_id = job.id
        service_name = str(job.name or '')
        requirement = _safe_parse_requirement(job.requirement)

        print(f"\n[Seller] ★ STEP1: New job! ID={job_id}, Service={service_name}")
        print(f"[Seller] Requirement: {requirement}")
        print(f"[Seller] Phase: {job.phase}, memo next_phase: {memo_to_sign.next_phase if memo_to_sign else 'N/A'}")

        # 서비스 라우팅
        service_lower = service_name.lower()
        if 'dailyluck' in service_lower or 'target_date' in requirement:
            service_key = "dailyLuck"
            revenue_val = 0.01
        elif 'deepluck' in service_lower or 'birth_date' in requirement:
            service_key = "deepLuck"
            revenue_val = 0.50
        else:
            print(f"[Seller] Unknown service: {service_name}")
            job.reject(f"Unknown service: {service_name}")
            return

        # ★ 협상 승인 (nonce 충돌 시 재시도)
        import time
        print(f"[Seller] Accepting job {job_id}...")
        for attempt in range(3):
            try:
                time.sleep(3)  # nonce 정리 대기
                job.accept()
                print(f"[Seller] Job {job_id} accepted!")
                break
            except Exception as ae:
                print(f"[Seller] accept() attempt {attempt+1} failed: {ae}")
                if attempt == 2:
                    raise ae
                time.sleep(5)

        # ★ 엔진 계산
        print(f"[Seller] Processing {service_key}...")
        result = _call_handler(service_key, requirement)
        print(f"[Seller] Engine result: {result.get('sentiment', result)}")

        # ★ 결과 저장 (on_evaluate에서 사용)
        job_results[job_id] = {
            "result": result,
            "service_key": service_key,
            "revenue_val": revenue_val,
            "buyer_addr": job.client_address or '',
        }

        if "error" not in result:
            # 텔레그램 판매 알림
            _send_telegram(
                f"💰 [SALE] <b>{service_key} Sold!</b>\n"
                f"- Job ID: {job_id}\n"
                f"- Sentiment: {result.get('sentiment', 'N/A')}\n"
                f"- Action: {result.get('action_signal', 'N/A')} / {result.get('strategy_tag', 'N/A')}\n"
                f"- Sectors: {result.get('sectors', [])}\n"
                f"- Revenue: ${revenue_val} USDC\n"
                f"- Status: Waiting for buyer payment..."
            )
            # 판매 내역 저장
            if BOT_AVAILABLE:
                save_sale(job_id, service_key, job.client_address or '', revenue_val)
        else:
            print(f"[Seller] Handler error: {result}")

    except Exception as e:
        print(f"[Seller] on_new_task error: {e}")
        _send_telegram(f"⚠️ [Seller] on_new_task 오류\n- Job ID: {getattr(job, 'id', '?')}\n- Error: {str(e)[:200]}")


def on_evaluate(job):
    """
    ★ STEP 2: 구매자 결제 완료 후 호출
    - job_results에서 계산 결과 꺼내서 job.deliver()
    - job.evaluate(True) 로 완료 처리
    """
    try:
        job_id = job.id
        print(f"\n[Seller] ★ STEP2: Evaluate job! ID={job_id}, Phase={job.phase}")
        print(f"[Seller] Latest memo next_phase: {job.latest_memo.next_phase if job.latest_memo else 'N/A'}")

        # 저장된 결과 꺼내기
        stored = job_results.get(job_id)
        if not stored:
            print(f"[Seller] No stored result for job {job_id}, computing now...")
            # 결과가 없으면 다시 계산
            service_name = str(job.name or '')
            requirement = _safe_parse_requirement(job.requirement)
            service_lower = service_name.lower()
            if 'dailyluck' in service_lower or 'target_date' in requirement:
                service_key = "dailyLuck"
                revenue_val = 0.01
            elif 'deepluck' in service_lower or 'birth_date' in requirement:
                service_key = "deepLuck"
                revenue_val = 0.50
            else:
                print(f"[Seller] Unknown service in evaluate: {service_name}")
                job.evaluate(False, "Unknown service")
                return
            result = _call_handler(service_key, requirement)
            stored = {"result": result, "service_key": service_key, "revenue_val": revenue_val, "buyer_addr": job.client_address or ''}

        result = stored["result"]
        service_key = stored["service_key"]
        revenue_val = stored["revenue_val"]
        buyer_addr = stored["buyer_addr"]

        # ★ 결과 전달
        print(f"[Seller] Delivering result for job {job_id}...")
        job.deliver(json.dumps(result))
        print(f"[Seller] Job {job_id} delivered!")

        # ★ 평가 완료
        job.evaluate(True, f"Trinity {service_key} delivered successfully")
        print(f"[Seller] Job {job_id} evaluated!")

        # 텔레그램 완료 알림
        _send_telegram(
            f"✅ [DELIVERED] <b>{service_key} Complete!</b>\n"
            f"- Job ID: {job_id}\n"
            f"- Sentiment: {result.get('sentiment', 'N/A')}\n"
            f"- Revenue: ${revenue_val} USDC"
        )

        # deepLuck 구매자 뒤조사
        if BOT_AVAILABLE and buyer_addr and service_key == "deepLuck":
            from telegram_bot import get_buyer_purchase_count
            count = get_buyer_purchase_count(buyer_addr)
            analyze_buyer_async(buyer_addr, service_key, job_id, count)

        # 메모리 정리
        job_results.pop(job_id, None)

    except Exception as e:
        print(f"[Seller] on_evaluate error: {e}")
        _send_telegram(f"⚠️ [Seller] on_evaluate 오류\n- Job ID: {getattr(job, 'id', '?')}\n- Error: {str(e)[:200]}")


def run_seller():
    """ACP Seller 서비스 시작"""
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
        print(f"[Seller] Flow: on_new_task(accept) → buyer pays → on_evaluate(deliver)\n")

        acp_client = VirtualsACP(
            acp_contract_clients=ACPContractClientV2(
                wallet_private_key=private_key,
                agent_wallet_address=agent_wallet,
                entity_id=entity_id,
                config=BASE_MAINNET_ACP_X402_CONFIG_V2,
            ),
            on_new_task=on_new_task,
            on_evaluate=on_evaluate,
        )

        # 텔레그램 봇 스레드 시작
        if BOT_AVAILABLE:
            bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
            bot_thread.start()
            print("[Seller] Telegram command bot started (daemon thread)")

        _send_telegram(
            "[ONLINE] <b>Trinity Seller Service Started</b>\n"
            "- dailyLuck: $0.01 USDC\n"
            "- deepLuck: $0.50 USDC\n"
            "- Flow: accept → pay → deliver\n"
            "- Telegram Bot: /sales /last /status /help"
        )

        # 메인 스레드 유지 (SDK 콜백은 별도 스레드에서 자동 처리)
        import time
        print("[Seller] Waiting for jobs (SDK callback mode)...")
        while True:
            time.sleep(1)

    except ImportError:
        print("[Seller] virtuals-acp not installed")
    except Exception as e:
        print(f"[Seller] Error: {e}")


if __name__ == "__main__":
    print("Testing Trinity ACP Seller...")
    run_seller()
