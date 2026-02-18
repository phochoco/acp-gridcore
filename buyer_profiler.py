"""
Trinity Buyer Profiler — 구매자 뒷조사 모듈
판매 성공 시 구매자 지갑을 BaseScan API로 조회하고
Gemini Flash로 1줄 프로파일링 후 텔레그램 전송
"""
import os
import json
import requests
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "***REDACTED_TELEGRAM***")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1629086047")

BASESCAN_BASE = "https://api.basescan.org/api"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"


def _send_telegram(message: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=5
        )
    except Exception:
        pass


def _get_wallet_transactions(address: str, limit: int = 20) -> list:
    """BaseScan API로 지갑 최근 거래 조회"""
    try:
        params = {
            "module": "account",
            "action": "tokentx",       # ERC-20 토큰 거래
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": BASESCAN_API_KEY
        }
        r = requests.get(BASESCAN_BASE, params=params, timeout=10)
        data = r.json()
        if data.get("status") == "1":
            return data.get("result", [])
        return []
    except Exception as e:
        print(f"[Profiler] BaseScan error: {e}")
        return []


def _get_wallet_info(address: str) -> dict:
    """지갑 ETH 잔액 조회"""
    try:
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": BASESCAN_API_KEY
        }
        r = requests.get(BASESCAN_BASE, params=params, timeout=10)
        data = r.json()
        if data.get("status") == "1":
            balance_wei = int(data.get("result", 0))
            balance_eth = balance_wei / 1e18
            return {"balance_eth": round(balance_eth, 4)}
        return {"balance_eth": 0}
    except Exception as e:
        print(f"[Profiler] Balance error: {e}")
        return {"balance_eth": 0}


def _build_profile_prompt(address: str, txs: list, wallet_info: dict,
                           service: str, purchase_count: int) -> str:
    """Gemini에게 보낼 프로파일링 프롬프트 생성"""
    # 최근 거래한 토큰 목록 추출
    tokens = list(set([tx.get("tokenSymbol", "?") for tx in txs[:20]]))[:10]
    token_list = ", ".join(tokens) if tokens else "Unknown"

    # 거래 상대방 주소 (자주 거래한 DEX/프로토콜)
    to_addrs = [tx.get("to", "")[:10] for tx in txs[:5]]

    prompt = f"""You are a crypto intelligence analyst. Analyze this wallet and give a ONE-LINE profile in English.

Wallet: {address[:10]}...
ETH Balance: {wallet_info.get('balance_eth', 0)} ETH
Recent tokens traded: {token_list}
Service purchased: {service} (x{purchase_count} times)
Recent tx count: {len(txs)}

Rules:
- One sentence only (max 20 words)
- Focus on trading style and purpose
- Be specific, not generic
- Example: "Meme coin sniper bot that uses fortune data for entry timing"

Profile:"""
    return prompt


def _call_gemini(prompt: str) -> str:
    """Gemini Flash API 호출"""
    try:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 100
            }
        }
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except Exception as e:
        print(f"[Profiler] Gemini error: {e}")
        return "Profile analysis unavailable"


def analyze_buyer(buyer_address: str, service: str, job_id: int,
                  purchase_count: int = 1):
    """
    구매자 뒷조사 메인 함수 (별도 스레드에서 실행)
    판매 성공 후 비동기로 호출
    """
    try:
        print(f"[Profiler] Analyzing buyer: {buyer_address[:10]}...")

        # 1. 데이터 수집
        txs = _get_wallet_transactions(buyer_address)
        wallet_info = _get_wallet_info(buyer_address)

        # 2. Gemini 프로파일링
        prompt = _build_profile_prompt(
            buyer_address, txs, wallet_info, service, purchase_count
        )
        profile = _call_gemini(prompt)

        # 3. 토큰 목록
        tokens = list(set([tx.get("tokenSymbol", "?") for tx in txs[:20]]))[:8]
        token_str = ", ".join(tokens) if tokens else "No token activity"

        # 4. 텔레그램 전송
        message = (
            f"🕵️ <b>Buyer Intelligence Report</b>\n\n"
            f"<b>Job ID:</b> {job_id}\n"
            f"<b>Service:</b> {service} (x{purchase_count})\n"
            f"<b>Wallet:</b> <code>{buyer_address[:16]}...</code>\n"
            f"<b>Balance:</b> {wallet_info.get('balance_eth', 0)} ETH\n"
            f"<b>Recent Tokens:</b> {token_str}\n\n"
            f"🤖 <b>AI Profile:</b>\n"
            f"<i>{profile}</i>\n\n"
            f"<a href='https://basescan.org/address/{buyer_address}'>🔗 View on BaseScan</a>"
        )
        _send_telegram(message)
        print(f"[Profiler] Analysis complete for {buyer_address[:10]}")

    except Exception as e:
        print(f"[Profiler] Analysis failed: {e}")


def analyze_buyer_async(buyer_address: str, service: str, job_id: int,
                        purchase_count: int = 1):
    """비동기 실행 래퍼 — 메인 폴링 루프를 블로킹하지 않음"""
    t = threading.Thread(
        target=analyze_buyer,
        args=(buyer_address, service, job_id, purchase_count),
        daemon=True
    )
    t.start()
