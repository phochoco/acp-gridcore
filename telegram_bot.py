"""
Trinity Telegram Command Bot — 양방향 텔레그램 봇
trinity-seller 스레드로 통합 실행
지원 명령어: /sales, /last, /status, /help
"""
import os
import json
import time
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "***REDACTED_TELEGRAM***")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1629086047")
SALES_LOG_PATH = os.path.join(os.path.dirname(__file__), "sales_log.json")

# sales_log.json 동시 접근 보호
_sales_lock = threading.Lock()


# ===== sales_log.json 유틸 =====

def load_sales_log() -> dict:
    with _sales_lock:
        try:
            if os.path.exists(SALES_LOG_PATH):
                with open(SALES_LOG_PATH, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"total_sales": 0, "total_revenue_usdc": 0.0, "sales": []}


def save_sale(job_id, service: str, buyer: str, revenue: float):
    """판매 1건 기록 (thread-safe)"""
    with _sales_lock:
        try:
            log = load_sales_log_unsafe()
            log["total_sales"] += 1
            log["total_revenue_usdc"] = round(log["total_revenue_usdc"] + revenue, 4)
            log["sales"].append({
                "job_id": job_id,
                "service": service,
                "buyer": buyer,
                "revenue": revenue,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            })
            with open(SALES_LOG_PATH, "w") as f:
                json.dump(log, f, indent=2)
        except Exception as e:
            print(f"[TelegramBot] save_sale error: {e}")


def load_sales_log_unsafe() -> dict:
    """Lock 없이 읽기 (내부 전용 — 이미 lock 보유 시)"""
    try:
        if os.path.exists(SALES_LOG_PATH):
            with open(SALES_LOG_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {"total_sales": 0, "total_revenue_usdc": 0.0, "sales": []}


def get_buyer_purchase_count(buyer_address: str) -> int:
    """특정 지갑의 구매 횟수"""
    log = load_sales_log()
    return sum(1 for s in log.get("sales", [])
               if s.get("buyer", "").lower() == buyer_address.lower())


# ===== 텔레그램 API =====

def _send(chat_id: str, text: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=5
        )
    except Exception:
        pass


def _get_updates(offset: int) -> list:
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
            params={"offset": offset, "timeout": 10, "allowed_updates": ["message"]},
            timeout=15
        )
        data = r.json()
        return data.get("result", [])
    except Exception:
        return []


# ===== 명령어 핸들러 =====

def _cmd_sales(chat_id: str):
    log = load_sales_log()
    total = log.get("total_sales", 0)
    revenue = log.get("total_revenue_usdc", 0.0)
    sales = log.get("sales", [])

    # 서비스별 집계
    daily_count = sum(1 for s in sales if s.get("service") == "dailyLuck")
    deep_count = sum(1 for s in sales if s.get("service") == "deepLuck")

    _send(chat_id,
        f"💰 <b>Trinity Sales Report</b>\n\n"
        f"📊 Total Sales: <b>{total}</b>\n"
        f"💵 Total Revenue: <b>${revenue:.4f} USDC</b>\n\n"
        f"• dailyLuck ($0.01): {daily_count}건\n"
        f"• deepLuck ($0.50): {deep_count}건\n\n"
        f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )


def _cmd_last(chat_id: str):
    log = load_sales_log()
    sales = log.get("sales", [])
    if not sales:
        _send(chat_id, "📭 아직 판매 내역이 없습니다.")
        return
    last = sales[-1]
    buyer = last.get("buyer", "Unknown")
    count = get_buyer_purchase_count(buyer)
    _send(chat_id,
        f"🕵️ <b>Last Buyer</b>\n\n"
        f"<b>Service:</b> {last.get('service')}\n"
        f"<b>Revenue:</b> ${last.get('revenue')} USDC\n"
        f"<b>Wallet:</b> <code>{buyer[:16]}...</code>\n"
        f"<b>This buyer's total purchases:</b> {count}회\n"
        f"<b>Time:</b> {last.get('timestamp')}\n\n"
        f"<a href='https://basescan.org/address/{buyer}'>🔗 BaseScan</a>"
    )


def _cmd_status(chat_id: str):
    log = load_sales_log()
    _send(chat_id,
        f"🟢 <b>Trinity Seller Status</b>\n\n"
        f"• ACP Polling: <b>ACTIVE</b> (30s interval)\n"
        f"• Telegram Bot: <b>ACTIVE</b>\n"
        f"• Buyer Profiler: <b>ACTIVE</b>\n"
        f"• Total Sales: {log.get('total_sales', 0)}\n"
        f"• Revenue: ${log.get('total_revenue_usdc', 0.0):.4f} USDC\n\n"
        f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )


def _cmd_help(chat_id: str):
    _send(chat_id,
        "🤖 <b>Trinity Bot Commands</b>\n\n"
        "/sales — 전체 판매 내역 및 수익\n"
        "/last — 마지막 구매자 정보\n"
        "/status — 서비스 상태 확인\n"
        "/help — 이 메시지"
    )


COMMANDS = {
    "/sales":  _cmd_sales,
    "/last":   _cmd_last,
    "/status": _cmd_status,
    "/help":   _cmd_help,
}


# ===== 폴링 루프 =====

def run_telegram_bot():
    """
    텔레그램 봇 롱폴링 루프.
    acp_seller.py에서 daemon 스레드로 실행.
    """
    print("[TelegramBot] Starting command bot polling...")
    offset = 0
    while True:
        try:
            updates = _get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "").strip().split("@")[0]  # @botname 제거

                # 허용된 채팅만 처리
                if chat_id != TELEGRAM_CHAT_ID:
                    continue

                handler = COMMANDS.get(text)
                if handler:
                    print(f"[TelegramBot] Command: {text}")
                    handler(chat_id)
                elif text.startswith("/"):
                    _send(chat_id, f"❓ 알 수 없는 명령어: {text}\n/help 를 입력하세요.")
        except Exception as e:
            print(f"[TelegramBot] Polling error: {e}")
            time.sleep(5)
