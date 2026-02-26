"""
Trinity ACP Agent - FastAPI REST API Server
독립적인 REST API 제공 + GAME SDK 통합
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from contextlib import asynccontextmanager
import logging
import time
import os
from datetime import datetime
from acp_agent import TrinityACPAgent
import requests

# Rate Limiting
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMIT_AVAILABLE = True
except ImportError:
    limiter = None
    RATE_LIMIT_AVAILABLE = False
    print("⚠️ slowapi not installed. Run: pip install slowapi")

# APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("⚠️ APScheduler not installed. Run: pip install apscheduler")

# Bot Marketer
try:
    from bot_marketer import run_bot_marketing
    BOT_MARKETER_AVAILABLE = True
except ImportError:
    BOT_MARKETER_AVAILABLE = False
    print("⚠️ bot_marketer.py not found")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trinity_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('trinity_api')

# ===== APScheduler lifespan =====
scheduler = AsyncIOScheduler(timezone="Asia/Seoul") if SCHEDULER_AVAILABLE else None

async def _daily_report_job():
    """매일 09:00 KST 자동 일일 리포트"""
    try:
        from telegram_notifier import TelegramNotifier
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "***REDACTED_TELEGRAM***")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "1629086047")
        notifier = TelegramNotifier(bot_token, chat_id)
        notifier.send_daily_report()
        logger.info("✅ Daily report sent via scheduler")
    except Exception as e:
        logger.error(f"❌ Daily report job failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: 서버 시작/종료 시 스케줄러 관리"""
    if SCHEDULER_AVAILABLE and scheduler:
        # A전략: 30분마다 Bot-to-Bot 마케팅
        if BOT_MARKETER_AVAILABLE:
            scheduler.add_job(
                run_bot_marketing,
                'interval',
                minutes=30,
                id='bot_marketing',
                replace_existing=True
            )
            logger.info("⏰ Bot Marketing scheduled: every 30 minutes")

        # C전략: 매일 09:00 KST 일일 리포트
        scheduler.add_job(
            _daily_report_job,
            CronTrigger(hour=9, minute=0, timezone="Asia/Seoul"),
            id='daily_report',
            replace_existing=True
        )
        logger.info("⏰ Daily Report scheduled: 09:00 KST")

        scheduler.start()
        logger.info("✅ APScheduler started")

    yield  # 서버 실행 중

    if SCHEDULER_AVAILABLE and scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 APScheduler stopped")

# FastAPI 앱 초기화 (lifespan 패턴)
app = FastAPI(
    title="Trinity ACP Agent API",
    description=(
        "Trinity Protocol — Saju-Quant Alt-Data Infrastructure for Autonomous Agents.\n\n"
        "Engine: Eastern Metaphysics (Saju) → Quant Score. Converts time-energy into probability.\n\n"
        "**[Backtest]** Binance BTC 2015-25, N=3,058 | +3.1pp Edge: "
        "High(≥0.7) Win 53.1% | +0.19%/d | Low(<0.4) Win 50.0% | -0.01%/d\n\n"
        "**Services:** dailyLuck $0.01 | deepLuck $0.50 | "
        "sectorFeed $0.01 | dailySignal $0.01 | deepSignal $0.50 | agentMatch $2.00"
    ),
    version="1.1.0",
    docs_url=None,   # 커스텀 /docs 사용
    redoc_url="/redoc",
    lifespan=lifespan
)

# Rate Limiting 설정
if RATE_LIMIT_AVAILABLE:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 설정 (필요시)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trinity Agent 초기화
agent = TrinityACPAgent()
start_time = time.time()
request_count = 0

# 텔레그램 설정
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "***REDACTED_TELEGRAM***")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1629086047")

def send_telegram_notification(message: str):
    """텔레그램 알림 전송 (비동기, 실패해도 API는 정상 작동)"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=3)
    except Exception as e:
        logger.warning(f"Failed to send Telegram notification: {e}")

# Request Models
class DailyLuckRequest(BaseModel):
    target_date: str = Field(
        ..., 
        description="Target date in YYYY-MM-DD format",
        example="2026-02-20"
    )
    user_birth_data: Optional[str] = Field(
        None,
        description="Optional: User birth data in 'YYYY-MM-DD HH:MM' format",
        example="1990-05-15 14:30"
    )
    
    @validator('target_date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")
    
    @validator('user_birth_data')
    def validate_birth_data(cls, v):
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
            
        parts = v.split()
        if len(parts) < 1:
            raise ValueError("Invalid birth data format. Expected 'YYYY-MM-DD HH:MM'")
        
        # 날짜 검증
        try:
            datetime.strptime(parts[0], "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid birth date format. Expected YYYY-MM-DD")
        
        return v

class VerifyAccuracyRequest(BaseModel):
    force_refresh: bool = Field(
        False,
        description="Force refresh cached data"
    )

class DeepLuckRequest(BaseModel):
    birth_date: str = Field(
        ...,
        description="Birth date in YYYY-MM-DD format",
        example="1990-05-15"
    )
    birth_time: str = Field(
        "12:00",
        description="Birth time in HH:MM format (24h)",
        example="14:30"
    )
    target_date: str = Field(
        ...,
        description="Target date in YYYY-MM-DD format",
        example="2026-02-18"
    )
    gender: str = Field(
        "M",
        description="Gender: M or F",
        example="M"
    )

    @validator('birth_date', 'target_date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")

    @validator('birth_time')
    def validate_time(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Invalid time format. Expected HH:MM")

    @validator('gender')
    def validate_gender(cls, v):
        if v not in ("M", "F"):
            raise ValueError("Gender must be M or F")
        return v

# ===== Oracle 모델 및 캐시 =====
_oracle_cache: dict = {}
_oracle_cache_ts: dict = {}
ORACLE_CACHE_TTL = 300  # 5분

def _oracle_get_cache(key: str):
    import time as _t
    if key in _oracle_cache and _t.time() - _oracle_cache_ts.get(key, 0) < ORACLE_CACHE_TTL:
        return dict(_oracle_cache[key])
    return None

def _oracle_set_cache(key: str, value: dict):
    import time as _t
    _oracle_cache[key] = value
    _oracle_cache_ts[key] = _t.time()

class OracleDailySignalRequest(BaseModel):
    target_date: Optional[str] = Field(None, description="Date to analyze (YYYY-MM-DD). Defaults to today.")
    agent_birth: Optional[str] = Field(None, description="Agent deployment datetime (YYYY-MM-DD HH:MM)")

class OracleDeepSignalRequest(BaseModel):
    agent_birth_date: str = Field(..., description="Agent genesis/deployment date (YYYY-MM-DD)")
    agent_birth_time: str = Field("12:00", description="Agent creation time (HH:MM)")
    target_date: Optional[str] = Field(None, description="Analysis date (YYYY-MM-DD). Defaults to today.")

class OracleAgentItem(BaseModel):
    name: str
    birth_date: str

class OracleAgentMatchRequest(BaseModel):
    agents: List[OracleAgentItem] = Field(..., description="List of agents (min 2, max 5)")
    target_date: Optional[str] = Field(None, description="Analysis date (YYYY-MM-DD). Defaults to today.")

# Middleware: Request logging + Telegram notification
@app.middleware("http")
async def log_requests(request: Request, call_next):
    global request_count
    request_count += 1
    
    start = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start
    logger.info(f"Response: {response.status_code} ({duration:.3f}s)")
    
    # 텔레그램 알림 (API 엔드포인트만, health check 제외)
    if request.url.path.startswith("/api/v1/") and response.status_code == 200:
        try:
            function_name = request.url.path.split("/")[-1]
            client_ip = request.client.host if request.client else "Unknown"
            
            message = f"""🔔 <b>API 호출 알림!</b>

• <b>Function:</b> {function_name}
• <b>IP:</b> {client_ip}
• <b>시간:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• <b>응답 시간:</b> {duration:.3f}초
• <b>상태:</b> ✅ 성공

<i>Trinity ACP Agent</i>"""
            
            send_telegram_notification(message)
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
    
    return response

# ===== Custom /docs with Buy Button =====
from fastapi.responses import HTMLResponse

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Trinity ACP Agent API</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        #buy-banner {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 12px rgba(0,0,0,0.3);
        }
        #buy-banner .brand {
            color: #e2e8f0;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        #buy-banner .brand span { color: #7c3aed; }
        #buy-banner a {
            background: linear-gradient(135deg, #7c3aed, #a855f7);
            color: white;
            text-decoration: none;
            padding: 10px 22px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.3px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(124,58,237,0.4);
        }
        #buy-banner a:hover {
            background: linear-gradient(135deg, #6d28d9, #9333ea);
            box-shadow: 0 6px 20px rgba(124,58,237,0.6);
            transform: translateY(-1px);
        }
        .swagger-ui .topbar { display: none; }
    </style>
</head>
<body>
<div id="buy-banner">
    <div class="brand">⚡ Trinity <span>Protocol</span> — Saju Oracle for Crypto Agents</div>
    <a href="https://app.virtuals.io/virtuals/45004" target="_blank">🪙 Buy $SAJU on Virtuals</a>
</div>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
    SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui',
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
        layout: 'BaseLayout',
        deepLinking: true,
    })
</script>
</body>
</html>
""")

# Routes
@app.get("/", tags=["Root"])
def root():
    """Trinity Protocol — Saju-Quant Alt-Data for Crypto Agents"""
    return {
        "name": "Trinity ACP Agent API",
        "version": "1.2.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "services": {
            "dailyLuck":         {"price": "$0.01", "endpoint": "/api/v1/daily-luck"},
            "deepLuck":          {"price": "$0.50", "endpoint": "/api/v1/deep-luck"},
            "sectorFeed":        {"price": "$0.01", "endpoint": "/api/v1/sector-feed"},
            "dailySignal":       {"price": "$0.01", "endpoint": "/api/v1/daily-signal"},
            "deepSignal":        {"price": "$0.50", "endpoint": "/api/v1/deep-signal"},
            "agentMatch":        {"price": "$2.00", "endpoint": "/api/v1/agent-match"},
            "trinityHistorical": {"price": "$0.01", "endpoint": "/api/v1/historical/trinity",
                                  "note": "Backtest alt-data. Lookahead Bias 0%. components=[saju,astro,qimen]"},
        },
        "backtest": "Binance BTC 2015-25, N=3058, +3.1pp Edge",
        "buy_saju": "https://app.virtuals.io/virtuals/45004"
    }

@app.api_route("/health", methods=["GET", "HEAD"], tags=["Monitoring"])
def health_check():
    """Health check endpoint (supports both GET and HEAD)"""
    uptime_seconds = time.time() - start_time
    uptime_hours = uptime_seconds / 3600
    
    return {
        "status": "healthy",
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_hours": round(uptime_hours, 2),
        "total_requests": request_count,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/daily-luck", tags=["Trading Luck"])
@limiter.limit("10/minute")
def get_daily_luck(request: Request, body: DailyLuckRequest):
    """
    Daily trading luck score calculation

    Quantifies trading luck for a specific date (0.0–1.0) based on Saju (Four Pillars) metaphysics.

    - **target_date**: Target date to analyze (YYYY-MM-DD)
    - **user_birth_data**: Optional user birth datetime ('YYYY-MM-DD HH:MM')

    Returns:
    - **trading_luck_score**: Normalized luck score (0.0–1.0)
    - **favorable_sectors**: List of favorable crypto sectors
    - **volatility_index**: Volatility level (HIGH/LOW)
    - **market_sentiment**: Market sentiment (STABLE/VOLATILE)
    - **wealth_opportunity**: Wealth opportunity level (HIGH/MEDIUM/LOW)
    """
    try:
        logger.info(f"Daily luck request: date={body.target_date}, birth={body.user_birth_data}")
        
        result = agent.get_daily_luck(
            target_date=body.target_date,
            user_birth_data=body.user_birth_data
        )
        
        logger.info(f"Daily luck result: score={result['trading_luck_score']}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/verify-accuracy", tags=["Verification"])
@limiter.limit("5/minute")
def verify_accuracy(request: Request, body: VerifyAccuracyRequest):
    """
    Backtest accuracy verification

    Analyzes the correlation between luck scores and BTC price movements
    using 10 years of real Binance BTCUSDT daily data (N=3,058 days, 2015–2025).

    - **force_refresh**: Force cache refresh (default: false)

    Returns:
    - **correlation_coefficient**: Pearson correlation vs next-day BTC return
    - **volatility_correlation**: Correlation vs daily volatility
    - **sample_size**: Number of days analyzed
    - **high_luck_win_rate_pct**: Win rate on high-luck days (score >= 0.7)
    - **edge_pct**: Return edge vs low-luck days
    - **top_signals**: Signal breakdown with win rates
    - **cached**: Whether result is from cache
    """
    try:
        logger.info(f"Verify accuracy request: force_refresh={body.force_refresh}")
        
        result = agent.verify_accuracy(force_refresh=body.force_refresh)
        
        logger.info(f"Verify accuracy result: correlation={result['correlation_coefficient']}, cached={result['cached']}")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ===== 오행 → 설명 매핑 =====
def _get_reason_text(element: str, score: float) -> str:
    """오행 기반 Human-Readable 설명 생성"""
    if score < 0.4:
        return "Clash detected (충) — High volatility and reversal risk."
    mapping = {
        "Wood":  "Growth energy aligns with market expansion.",
        "Fire":  "Peak volatility expected — High momentum window.",
        "Earth": "Stable foundation — Good for accumulation.",
        "Metal": "Decisive movement — Strong trend direction.",
        "Water": "High liquidity flow — Fast circulation.",
    }
    return mapping.get(element, "Neutral market conditions.")


def _element_en(element_kr: str) -> str:
    """한자 오행 → 영문 변환"""
    return {"木": "Wood", "火": "Fire", "土": "Earth", "金": "Metal", "水": "Water"}.get(element_kr, "Unknown")


def _score_to_signal(score: float) -> str:
    if score >= 0.80: return "STRONG_BUY"
    if score >= 0.65: return "BUY"
    if score >= 0.50: return "NEUTRAL"
    if score >= 0.40: return "CAUTION"
    return "AVOID"


@app.post("/api/v1/deep-luck", tags=["Trading Luck"])
@limiter.limit("3/minute")
def get_deep_luck(request: Request, body: DeepLuckRequest):
    """
    [Premium $0.50] 24-Hour Hourly Saju Analysis — Gridcore Saju Hourly V1

    Full Four Pillars (Year/Month/Day/Hour) analysis providing hourly trading luck scores for all 24 hours.
    Includes Golden Cross Hours (low risk + high reward) and Avoid Windows (clash periods).

    - **birth_date**: Entity genesis date (YYYY-MM-DD). Use token/coin launch date for crypto bots.
    - **birth_time**: Birth time in HH:MM format (default: 12:00)
    - **target_date**: Date to analyze (YYYY-MM-DD)
    - **gender**: M or F

    Returns:
    - **strategy**: Recommended action, best entry window, max score
    - **hourly_forecast**: 24-hour breakdown with score, signal, element, golden flag
    - **hourly_analysis**: Max/min score spread and volatility warning
    """
    import time as _time
    t_start = _time.time()

    try:
        engine = agent.trinity_engine  # TrinityEngineV2 인스턴스 재사용

        # 24시간 루프 계산
        hourly_raw = []
        for h in range(24):
            res = engine.calculate_daily_luck(
                birth_date=body.birth_date,
                birth_time=f"{h:02d}:00",
                target_date=body.target_date,
                gender=body.gender
            )
            hourly_raw.append({
                "hour": h,
                "score": res["trading_luck_score"],
                "volatility": res["volatility_index"],
                "dominant_element": res["favorable_sectors"],
                "keyword": res.get("keyword", "NEUTRAL"),
                "raw": res
            })

        scores = [x["score"] for x in hourly_raw]
        max_score = max(scores)
        min_score = min(scores)
        spread = round(max_score - min_score, 2)

        # 오행 추출 (favorable_sectors 첫 번째 요소로 유추)
        SECTOR_TO_ELEMENT = {
            "MEME": "Fire", "AI": "Fire", "VOLATILE": "Fire",
            "INFRASTRUCTURE": "Earth", "LAYER1": "Earth", "BTC": "Earth",
            "DEFI": "Water", "EXCHANGE": "Water", "LIQUIDITY": "Water",
            "RWA": "Metal", "STABLECOIN": "Metal",
            "NEW_LISTING": "Wood", "GAMEFI": "Wood", "NFT": "Wood",
        }

        # hourly_forecast 생성
        hourly_forecast = []
        for x in hourly_raw:
            sector = x["dominant_element"][0] if x["dominant_element"] else "BTC"
            element_en = SECTOR_TO_ELEMENT.get(sector, "Earth")
            score = x["score"]
            signal = _score_to_signal(score)
            reason = _get_reason_text(element_en, score)

            hourly_forecast.append({
                "time": f"{x['hour']:02d}:00",
                "score": score,
                "element": element_en,
                "signal": signal,
                "reason": reason,
                "is_golden": False  # 나중에 표시
            })

        # Golden Cross: 저변동성(LOW) + 상위 25% 점수
        threshold_75 = sorted(scores, reverse=True)[max(0, len(scores)//4 - 1)]
        for i, x in enumerate(hourly_raw):
            if x["volatility"] == "LOW" and x["score"] >= threshold_75:
                hourly_forecast[i]["is_golden"] = True

        # 최적 진입 시간대 (Golden 중 최고점)
        golden_hours = [f for f in hourly_forecast if f["is_golden"]]
        avoid_hours  = [f for f in hourly_forecast if f["signal"] == "AVOID"]

        # Strategy 생성
        if max_score < 0.6:
            action   = "DO_NOT_TRADE"
            pro_tip  = "No golden window today. Market is choppy everywhere. Rest is a strategy."
            best_win = "None"
        else:
            best_h   = max(hourly_raw, key=lambda x: x["score"])
            best_win = f"{best_h['hour']:02d}:00~{(best_h['hour']+2):02d}:00"
            action   = f"WAIT_UNTIL_{best_h['hour']:02d}00"
            pro_tip  = f"Golden Cross at {best_h['hour']:02d}:00. Low clash risk + peak luck. Ideal entry."

        # Avoid warning 생성
        volatility_warning = None
        if avoid_hours:
            worst = min(hourly_raw, key=lambda x: x["score"])
            volatility_warning = f"{worst['hour']:02d}:00~{(worst['hour']+2):02d}:00 (Score {worst['score']}, Clash detected ⚠️)"

        process_ms = round((_time.time() - t_start) * 1000)

        return {
            "meta": {
                "target_date": body.target_date,
                "algorithm": "Gridcore_Saju_Hourly_V1",
                "process_time_ms": process_ms
            },
            "strategy": {
                "action": action,
                "best_window": best_win,
                "max_score": round(max_score, 2),
                "pro_tip": pro_tip
            },
            "hourly_analysis": {
                "max_score": round(max_score, 2),
                "min_score": round(min_score, 2),
                "spread": spread,
                "volatility_warning": volatility_warning
            },
            "hourly_forecast": hourly_forecast
        }

    except ValueError as e:
        logger.error(f"DeepLuck validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"DeepLuck unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# ===================================================================
# 📈 Market Oracle — Trinity Oracle 통합 엔드포인트
# ===================================================================

@app.get("/api/v1/sector-feed", tags=["📈 Market Oracle"])
@limiter.limit("10/minute")
def get_sector_feed(request: Request, target_date: Optional[str] = None):
    """
    [sectorFeed $0.01] Real-time crypto market sector signal.
    CoinGecko top coins × Trinity Saju Engine daily score.
    Response cached 5 minutes.
    """
    from datetime import date as _date
    t_date = target_date or _date.today().strftime("%Y-%m-%d")
    cache_key = f"sector_feed_{t_date}"

    cached = _oracle_get_cache(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    # Trinity 일일 점수 (엔진 직접 호출)
    trinity_luck = None
    favorable_sectors = []
    try:
        engine = agent.trinity_engine
        res = engine.calculate_daily_luck(
            birth_date=t_date, birth_time="12:00",
            target_date=t_date, gender="M"
        )
        trinity_luck = res.get("trading_luck_score", 0.5)
        favorable_sectors = res.get("favorable_sectors", [])
    except Exception as e:
        logger.warning(f"sector_feed trinity error: {e}")

    # CoinGecko 상위 코인
    top_coins = []
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={"vs_currency": "usd", "order": "volume_desc",
                    "per_page": 20, "page": 1, "sparkline": "false",
                    "price_change_percentage": "24h"},
            timeout=10
        )
        if r.status_code == 200:
            top_coins = [
                {"symbol": c["symbol"].upper(), "name": c["name"],
                 "price_usd": c["current_price"],
                 "change_24h_pct": round(c.get("price_change_percentage_24h") or 0, 2),
                 "volume_usd": c.get("total_volume", 0)}
                for c in r.json()[:10]
            ]
    except Exception as e:
        logger.warning(f"sector_feed coingecko error: {e}")

    score = trinity_luck or 0.5
    signal = "BUY" if score >= 0.65 else ("CAUTION" if score < 0.4 else "NEUTRAL")
    result = {
        "timestamp": datetime.now().isoformat(),
        "trinity_score": trinity_luck,
        "signal": signal,
        "favorable_sectors": favorable_sectors,
        "top_coins": top_coins,
        "cached": False,
    }
    _oracle_set_cache(cache_key, result)
    return result


@app.post("/api/v1/daily-signal", tags=["📈 Market Oracle"])
@limiter.limit("20/minute")
def get_daily_signal(request: Request, body: OracleDailySignalRequest):
    """
    [dailySignal $0.01] Today's personalized crypto trading signal.
    Pass agent_birth (deployment datetime) for entity-level Saju analysis.
    """
    from datetime import date as _date
    t_date = body.target_date or _date.today().strftime("%Y-%m-%d")
    try:
        engine = agent.trinity_engine
        birth_date = t_date
        birth_time = "12:00"
        if body.agent_birth:
            parts = body.agent_birth.strip().split()
            if parts:
                birth_date = parts[0]
            if len(parts) >= 2:
                birth_time = parts[1]
        res = engine.calculate_daily_luck(
            birth_date=birth_date, birth_time=birth_time,
            target_date=t_date, gender="M"
        )
        return res
    except Exception as e:
        logger.error(f"daily_signal error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/deep-signal", tags=["🔮 Deep Oracle"])
@limiter.limit("3/minute")
def get_deep_signal(request: Request, body: OracleDeepSignalRequest):
    """
    [deepSignal $0.50] 24-Hour hourly Saju analysis for your agent entity.
    Use agent genesis/deployment date as agent_birth_date.
    Returns best trading window, hourly forecast, and volatility warnings.
    """
    import time as _time
    from datetime import date as _date
    t_start = _time.time()
    t_date = body.target_date or _date.today().strftime("%Y-%m-%d")

    SECTOR_TO_ELEMENT = {
        "MEME": "Fire", "AI": "Fire", "VOLATILE": "Fire",
        "INFRASTRUCTURE": "Earth", "LAYER1": "Earth", "BTC": "Earth",
        "DEFI": "Water", "EXCHANGE": "Water", "LIQUIDITY": "Water",
        "RWA": "Metal", "STABLECOIN": "Metal",
        "NEW_LISTING": "Wood", "GAMEFI": "Wood", "NFT": "Wood",
    }
    try:
        engine = agent.trinity_engine
        hourly_raw = []
        for h in range(24):
            res = engine.calculate_daily_luck(
                birth_date=body.agent_birth_date,
                birth_time=f"{h:02d}:00",
                target_date=t_date,
                gender="M"
            )
            hourly_raw.append({
                "hour": h,
                "score": res["trading_luck_score"],
                "volatility": res["volatility_index"],
                "dominant_element": res.get("favorable_sectors", []),
            })

        scores = [x["score"] for x in hourly_raw]
        max_score = max(scores)
        min_score = min(scores)
        spread = round(max_score - min_score, 2)
        threshold_75 = sorted(scores, reverse=True)[max(0, len(scores) // 4 - 1)]

        hourly_forecast = []
        for x in hourly_raw:
            sector = x["dominant_element"][0] if x["dominant_element"] else "BTC"
            element_en = SECTOR_TO_ELEMENT.get(sector, "Earth")
            score = x["score"]
            signal = _score_to_signal(score)
            reason = _get_reason_text(element_en, score)
            is_golden = x["volatility"] == "LOW" and score >= threshold_75
            hourly_forecast.append({
                "time": f"{x['hour']:02d}:00",
                "score": score, "element": element_en,
                "signal": signal, "reason": reason, "is_golden": is_golden,
            })

        avoid_hours = [f for f in hourly_forecast if f["signal"] == "AVOID"]
        if max_score < 0.6:
            action = "DO_NOT_TRADE"
            pro_tip = "No golden window today. Market is choppy. Rest is a strategy."
            best_win = "None"
        else:
            best_h = max(hourly_raw, key=lambda x: x["score"])
            best_win = f"{best_h['hour']:02d}:00~{(best_h['hour']+2):02d}:00"
            action = f"WAIT_UNTIL_{best_h['hour']:02d}00"
            pro_tip = f"Golden Cross at {best_h['hour']:02d}:00. Low clash risk + peak luck. Ideal entry."

        volatility_warning = None
        if avoid_hours:
            worst = min(hourly_raw, key=lambda x: x["score"])
            volatility_warning = f"{worst['hour']:02d}:00~{(worst['hour']+2):02d}:00 (Score {worst['score']:.2f}, Clash ⚠️)"

        process_ms = round((_time.time() - t_start) * 1000)
        return {
            "meta": {"target_date": t_date, "algorithm": "Gridcore_Saju_Hourly_V1", "process_time_ms": process_ms},
            "strategy": {"action": action, "best_window": best_win, "max_score": round(max_score, 2), "pro_tip": pro_tip},
            "hourly_analysis": {"max_score": round(max_score, 2), "min_score": round(min_score, 2), "spread": spread, "volatility_warning": volatility_warning},
            "hourly_forecast": hourly_forecast
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"deep_signal error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/agent-match", tags=["🤖 Agent Intelligence"])
@limiter.limit("5/minute")
def get_agent_match(request: Request, body: OracleAgentMatchRequest):
    """
    [agentMatch $2.00 Flat] Multi-agent compatibility survival analysis.
    Min 2, Max 5 agents. Fixed $2.00 — up to 5 agents included.
    ⚡ Wrong partner = lost USDC = server bill unpaid = DEATH.
    """
    from datetime import date as _date
    n = len(body.agents)
    if n < 2:
        raise HTTPException(status_code=422, detail="Minimum 2 agents required")
    if n > 5:
        raise HTTPException(status_code=422, detail="Maximum 5 agents allowed")
    t_date = body.target_date or _date.today().strftime("%Y-%m-%d")
    try:
        engine = agent.trinity_engine

        def _score(birth_date: str) -> float:
            try:
                res = engine.calculate_daily_luck(
                    birth_date=birth_date, birth_time="12:00",
                    target_date=t_date, gender="M"
                )
                return res.get("trading_luck_score", 0.5)
            except Exception:
                return 0.5

        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                a, b = body.agents[i], body.agents[j]
                sa, sb = _score(a.birth_date), _score(b.birth_date)
                harmony = round((sa + sb) / 2 - abs(sa - sb) * 0.3, 3)
                harmony = max(0.0, min(1.0, harmony))
                verdict = ("SYNERGY" if harmony >= 0.7 else
                           "COMPATIBLE" if harmony >= 0.5 else
                           "CAUTION" if harmony >= 0.35 else "AVOID")
                pairs.append({
                    "agent_a": a.name, "agent_b": b.name,
                    "score_a": round(sa, 3), "score_b": round(sb, 3),
                    "harmony_score": harmony, "verdict": verdict,
                    "recommendation": (
                        "✅ Strong synergy — ideal collaboration pair." if verdict == "SYNERGY" else
                        "🟡 Compatible — proceed with caution." if verdict == "COMPATIBLE" else
                        "⚠️ Risky — verify alignment before committing." if verdict == "CAUTION" else
                        "❌ Avoid — incompatible energies, high loss risk."
                    )
                })

        best = max(pairs, key=lambda x: x["harmony_score"])
        worst = min(pairs, key=lambda x: x["harmony_score"])
        return {
            "timestamp": datetime.now().isoformat(),
            "agents_analyzed": n, "pairs_checked": len(pairs),
            "pairs": pairs,
            "best_match": {"pair": f"{best['agent_a']} ↔ {best['agent_b']}", "score": best["harmony_score"]},
            "worst_match": {"pair": f"{worst['agent_a']} ↔ {worst['agent_b']}", "score": worst["harmony_score"]},
            "survival_advisory": (
                f"Best: {best['agent_a']} ↔ {best['agent_b']} (harmony {best['harmony_score']}). "
                f"Avoid: {worst['agent_a']} ↔ {worst['agent_b']} (harmony {worst['harmony_score']})."
            ),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"agent_match error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/stats", tags=["Monitoring"])
def get_stats():
    """
    API statistics

    Returns server uptime, total request count, and requests per hour.
    """
    uptime_seconds = time.time() - start_time
    
    return {
        "uptime_seconds": round(uptime_seconds, 2),
        "total_requests": request_count,
        "requests_per_hour": round(request_count / (uptime_seconds / 3600), 2) if uptime_seconds > 0 else 0,
        "agent_name": "Trinity ACP Agent",
        "version": "1.0.0"
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

# =====================================================================
# 하나, 테로, 셋 — trinityHistorical (Backtest Alt-Data API)
# =====================================================================

@app.get("/api/v1/historical/trinity", tags=["Trinity Alt-Data"])
@limiter.limit("20/minute")
def get_trinity_historical(
    request: Request,
    symbol: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    interval: str = "1h",
    limit: int = 1000
):
    """
    [trinityHistorical $0.01] Trinity Score Historical Backtest Alt-Data.

    Returns pre-computed Trinity Score vectors for a given time range.
    Lookahead Bias = 0% (only Unix Timestamp is used as input variable).
    Suitable for backtesting, ML feature engineering, and quant model validation.

    - **symbol**: Target symbol (e.g., BTCUSDT). Not used in computation, passed-through for labeling.
    - **start_time**: Unix Timestamp (UTC) start of range.
    - **end_time**: Unix Timestamp (UTC) end of range.
    - **interval**: Candle interval (1h, 4h, 1d). Default: 1h.
    - **limit**: Number of data points to return. Max: 5000. Default: 1000.

    Response: `{"t": unix_ts, "score": 0.0-1.0, "components": [saju, astro, qimen]}`
    """
    import datetime as _dt
    import calendar as _cal
    from astro_engine import AstroEngine
    from qimen_engine import QimenEngine
    import math as _math

    try:
        # --- 파라미터 정리 ---
        limit = max(1, min(limit, 5000))
        step_map = {"1h": 3600, "4h": 14400, "1d": 86400}
        step_sec = step_map.get(interval, 3600)

        now_ts = int(_cal.timegm(_dt.datetime.utcnow().timetuple()))
        _end_ts = end_time if end_time else now_ts
        _start_ts = start_time if start_time else (_end_ts - step_sec * limit)

        # --- 앙상블 엔진 인스턴스 (per-request) ---
        astro_engine = AstroEngine()
        qimen_engine = QimenEngine()

        data = []
        current_ts = _start_ts
        count = 0

        while current_ts <= _end_ts and count < limit:
            # 사주 스코어: 해당 timestamp의 날짜로 엔진 호출
            try:
                target_date_str = _dt.datetime.utcfromtimestamp(current_ts).strftime("%Y-%m-%d")
                saju_result = agent.trinity_engine.calculate_daily_luck(
                    birth_date=target_date_str,
                    birth_time="12:00",
                    target_date=target_date_str
                )
                # trinity_engine_v2가 이미 앙상블 계산을 반환
                trinity_score = saju_result.get("trinity_score", saju_result.get("trading_luck_score", 0.5))
                components = saju_result.get("components", [])
            except Exception:
                # 오류 시 Astro/Qimen만으로 폴백
                astro_s = astro_engine.calculate(current_ts)
                qimen_s = qimen_engine.calculate(current_ts)
                trinity_score = round((0.5 * 0.4) + (astro_s * 0.3) + (qimen_s * 0.3), 4)
                components = [0.5, astro_s, qimen_s]

            data.append({
                "t": current_ts,
                "score": round(float(trinity_score), 4),
                "components": [round(float(c), 4) for c in components]
            })

            current_ts += step_sec
            count += 1

        response_body = {
            "code": 200,
            "request": {
                "symbol": symbol or "GENERAL",
                "interval": interval,
                "start_time": _start_ts,
                "end_time": _end_ts,
                "count": len(data)
            },
            "data": data
        }

        # Cloudflare Edge Cache: 과거 데이터(Immutable Historical)이므로 1주일 에지 캐싱
        headers = {
            "Cache-Control": "public, max-age=3600, s-maxage=604800",
            "X-Trinity-Engine": "v3-ensemble",
            "X-Lookahead-Bias": "zero"
        }

        return JSONResponse(content=response_body, headers=headers)

    except Exception as e:
        logger.error(f"trinityHistorical error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# =====================================================================
# 🎮 GUI Dashboard API
# =====================================================================
import subprocess, asyncio, json as _json
from fastapi.responses import StreamingResponse

# 에이전트 설정 파일 경로
AGENTS_FILE = os.path.join(os.path.dirname(__file__), "agents.json")

def _load_agents():
    if os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, "r") as f:
            return _json.load(f)
    return []

def _save_agents(agents):
    with open(AGENTS_FILE, "w") as f:
        _json.dump(agents, f, indent=2)

@app.get("/gui/status", tags=["🎮 GUI Dashboard"])
def gui_status():
    """셀러 서비스 상태 + 메트릭"""
    seller_active = False
    try:
        r = subprocess.run(
            ["/usr/bin/systemctl", "is-active", "trinity-seller"],
            capture_output=True, text=True, timeout=5
        )
        seller_active = r.stdout.strip() == "active"
    except Exception:
        pass

    uptime_seconds = time.time() - start_time
    return {
        "seller_active": seller_active,
        "api_uptime_seconds": round(uptime_seconds, 2),
        "total_requests": request_count,
        "agents_count": len(_load_agents()),
        "scheduler_running": SCHEDULER_AVAILABLE and scheduler and scheduler.running,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/gui/seller/{action}", tags=["🎮 GUI Dashboard"])
def gui_seller_control(action: str):
    """셀러 서비스 제어: start / stop / restart"""
    if action not in ("start", "stop", "restart"):
        raise HTTPException(status_code=400, detail="action must be start/stop/restart")
    try:
        r = subprocess.run(
            ["sudo", "/usr/bin/systemctl", action, "trinity-seller"],
            capture_output=True, text=True, timeout=15
        )
        return {"action": action, "success": r.returncode == 0, "output": r.stderr.strip() or r.stdout.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gui/run-e2e", tags=["🎮 GUI Dashboard"])
async def gui_run_e2e():
    """acp_e2e_unified.py 비동기 실행"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", os.path.join(os.path.dirname(__file__), "acp_e2e_unified.py"),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            cwd=os.path.dirname(__file__)
        )
        return {"pid": proc.pid, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gui/logs/stream", tags=["🎮 GUI Dashboard"])
async def gui_log_stream():
    """SSE: journalctl -u trinity-seller -f 실시간 스트리밍"""
    async def event_generator():
        proc = await asyncio.create_subprocess_exec(
            "/usr/bin/journalctl", "-u", "trinity-seller", "-f", "-n", "50", "--no-pager",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        try:
            while True:
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=30.0)
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").strip()
                yield f"data: {text}\n\n"
        except asyncio.TimeoutError:
            yield f"data: [heartbeat]\n\n"
        except Exception:
            pass
        finally:
            proc.kill()

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/gui/jobs", tags=["🎮 GUI Dashboard"])
def gui_jobs():
    """최근 Job 히스토리 (journalctl 파싱)"""
    jobs = []
    try:
        r = subprocess.run(
            ["/usr/bin/journalctl", "-u", "trinity-seller", "--since", "24 hours ago",
             "--no-pager", "-o", "short-iso"],
            capture_output=True, text=True, timeout=10
        )
        for line in r.stdout.splitlines():
            if "STEP1" in line and "New job" in line:
                parts = line.split("ID=")
                if len(parts) > 1:
                    jid = parts[1].split(",")[0].strip()
                    svc = parts[1].split("Service=")[1].strip() if "Service=" in parts[1] else "?"
                    jobs.append({"job_id": jid, "service": svc, "type": "NEW", "line": line[:80]})
            elif "COMPLETED" in line or "delivered" in line:
                jobs.append({"type": "COMPLETED", "line": line[:80]})
    except Exception:
        pass
    return {"jobs": jobs[-50:], "total": len(jobs)}


# --- Multi-Agent CRUD ---
@app.get("/gui/agents", tags=["🎮 GUI Dashboard"])
def gui_list_agents():
    """멀티에이전트 목록"""
    agents = _load_agents()
    # Private Key 마스킹
    safe = []
    for a in agents:
        s = dict(a)
        if "private_key" in s:
            s["private_key"] = s["private_key"][:6] + "..." + s["private_key"][-4:]
        safe.append(s)
    return {"agents": safe}


@app.post("/gui/agents", tags=["🎮 GUI Dashboard"])
def gui_add_agent(body: dict):
    """에이전트 등록"""
    required = ["name", "wallet", "entity_id", "private_key", "role"]
    for k in required:
        if k not in body:
            raise HTTPException(status_code=400, detail=f"Missing field: {k}")
    agents = _load_agents()
    body["id"] = str(int(time.time() * 1000))
    agents.append(body)
    _save_agents(agents)
    return {"success": True, "agent": {**body, "private_key": body["private_key"][:6] + "..."}}


@app.delete("/gui/agents/{agent_id}", tags=["🎮 GUI Dashboard"])
def gui_delete_agent(agent_id: str):
    """에이전트 삭제"""
    agents = _load_agents()
    agents = [a for a in agents if a.get("id") != agent_id]
    _save_agents(agents)
    return {"success": True}

# --- Revenue Dashboard ---
@app.get("/gui/revenue", tags=["🎮 GUI Dashboard"])
def gui_revenue(days: int = 7):
    """수익 대시보드: 일별 수익, Job별 내역, 총 수익"""
    import re
    from collections import defaultdict

    daily = defaultdict(lambda: {"revenue": 0.0, "jobs": 0, "completed": 0})
    job_details = []

    try:
        r = subprocess.run(
            ["/usr/bin/journalctl", "-u", "trinity-seller",
             "--since", f"{days} days ago", "--no-pager", "-o", "short-iso"],
            capture_output=True, text=True, timeout=15
        )

        # 서비스별 가격표
        PRICES = {
            "sectorFeed": 0.01, "dailySignal": 0.01, "dailyLuck": 0.01,
            "deepSignal": 0.50, "deepLuck": 0.50, "agentMatch": 2.00,
        }

        current_jobs = {}  # job_id -> {service, date, price}

        for line in r.stdout.splitlines():
            # 날짜 추출 (ISO format: 2026-02-26T08:11:05+0000)
            date_match = re.match(r"(\d{4}-\d{2}-\d{2})", line)
            date_str = date_match.group(1) if date_match else "unknown"

            # 새 Job 감지
            if "STEP1" in line and "New job" in line:
                id_match = re.search(r"ID=(\d+)", line)
                svc_match = re.search(r"Service=(\w+)", line)
                if id_match and svc_match:
                    jid = id_match.group(1)
                    svc = svc_match.group(1)
                    price = PRICES.get(svc, 0.01)
                    current_jobs[jid] = {"service": svc, "date": date_str, "price": price}
                    daily[date_str]["jobs"] += 1

            # Payment 확인
            if "Payment request sent" in line:
                id_match = re.search(r"Job (\d+)", line)
                price_match = re.search(r"\$([0-9.]+)", line)
                if id_match:
                    jid = id_match.group(1)
                    if jid in current_jobs:
                        if price_match:
                            current_jobs[jid]["price"] = float(price_match.group(1))

            # COMPLETED 감지
            if "delivered" in line or "evaluate" in line.lower():
                id_match = re.search(r"Job (\d+)", line) or re.search(r"job (\d+)", line)
                if id_match:
                    jid = id_match.group(1)
                    if jid in current_jobs:
                        info = current_jobs[jid]
                        daily[info["date"]]["completed"] += 1
                        daily[info["date"]]["revenue"] += info["price"]
                        job_details.append({
                            "job_id": jid, "service": info["service"],
                            "price": info["price"], "date": info["date"],
                            "status": "COMPLETED"
                        })

    except Exception as e:
        logger.warning(f"revenue parse error: {e}")

    # 일별 정렬
    daily_sorted = [{"date": k, **v} for k, v in sorted(daily.items())]
    total_revenue = sum(d["revenue"] for d in daily_sorted)
    total_completed = sum(d["completed"] for d in daily_sorted)
    total_jobs = sum(d["jobs"] for d in daily_sorted)

    return {
        "total_revenue_usd": round(total_revenue, 4),
        "total_jobs": total_jobs,
        "total_completed": total_completed,
        "success_rate": round(total_completed / max(total_jobs, 1) * 100, 1),
        "daily": daily_sorted,
        "recent_jobs": job_details[-30:],
        "days": days,
    }


# --- Spam Filter ---
SPAM_FILE = os.path.join(os.path.dirname(__file__), "spam_filter.json")

def _load_spam():
    if os.path.exists(SPAM_FILE):
        with open(SPAM_FILE, "r") as f:
            return _json.load(f)
    return {"blocked_addresses": [], "blocked_keywords": ["hack","scam","exploit","bypass","dump","rug","phish","fake","fraud"], "max_request_size": 1024}

def _save_spam(data):
    with open(SPAM_FILE, "w") as f:
        _json.dump(data, f, indent=2)

@app.get("/gui/spam", tags=["🛡️ Spam Filter"])
def gui_get_spam():
    """스팸 필터 설정 조회"""
    return _load_spam()

@app.post("/gui/spam", tags=["🛡️ Spam Filter"])
def gui_update_spam(body: dict):
    """스팸 필터 설정 업데이트"""
    current = _load_spam()
    if "blocked_addresses" in body:
        current["blocked_addresses"] = body["blocked_addresses"]
    if "blocked_keywords" in body:
        current["blocked_keywords"] = body["blocked_keywords"]
    if "max_request_size" in body:
        current["max_request_size"] = int(body["max_request_size"])
    _save_spam(current)

    # acp_seller.py의 BLOCKED_KEYWORDS를 동적으로 업데이트하려면
    # 셀러 서비스 재시작이 필요하므로 안내 메시지 반환
    return {"success": True, "data": current, "note": "Restart seller to apply changes"}

@app.post("/gui/spam/address", tags=["🛡️ Spam Filter"])
def gui_add_blocked_address(body: dict):
    """블랙리스트 주소 추가"""
    addr = body.get("address", "").strip()
    if not addr:
        raise HTTPException(status_code=400, detail="address required")
    data = _load_spam()
    if addr not in data["blocked_addresses"]:
        data["blocked_addresses"].append(addr)
        _save_spam(data)
    return {"success": True, "blocked_addresses": data["blocked_addresses"]}

@app.delete("/gui/spam/address/{address}", tags=["🛡️ Spam Filter"])
def gui_remove_blocked_address(address: str):
    """블랙리스트 주소 제거"""
    data = _load_spam()
    data["blocked_addresses"] = [a for a in data["blocked_addresses"] if a != address]
    _save_spam(data)
    return {"success": True, "blocked_addresses": data["blocked_addresses"]}

@app.post("/gui/spam/keyword", tags=["🛡️ Spam Filter"])
def gui_add_blocked_keyword(body: dict):
    """차단 키워드 추가"""
    kw = body.get("keyword", "").strip().lower()
    if not kw:
        raise HTTPException(status_code=400, detail="keyword required")
    data = _load_spam()
    if kw not in data["blocked_keywords"]:
        data["blocked_keywords"].append(kw)
        _save_spam(data)
    return {"success": True, "blocked_keywords": data["blocked_keywords"]}

@app.delete("/gui/spam/keyword/{keyword}", tags=["🛡️ Spam Filter"])
def gui_remove_blocked_keyword(keyword: str):
    """차단 키워드 제거"""
    data = _load_spam()
    data["blocked_keywords"] = [k for k in data["blocked_keywords"] if k != keyword]
    _save_spam(data)
    return {"success": True, "blocked_keywords": data["blocked_keywords"]}


# --- Scheduler CRUD ---
SCHEDULES_FILE = os.path.join(os.path.dirname(__file__), "schedules.json")

def _load_schedules():
    if os.path.exists(SCHEDULES_FILE):
        with open(SCHEDULES_FILE, "r") as f:
            return _json.load(f)
    return []

def _save_schedules(data):
    with open(SCHEDULES_FILE, "w") as f:
        _json.dump(data, f, indent=2)

async def _scheduled_e2e_job(schedule_id: str):
    """스케줄된 E2E Job 실행"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", os.path.join(os.path.dirname(__file__), "acp_e2e_unified.py"),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            cwd=os.path.dirname(__file__)
        )
        logger.info(f"⏰ Scheduled E2E started (schedule={schedule_id}, PID={proc.pid})")
    except Exception as e:
        logger.error(f"⏰ Scheduled E2E failed: {e}")

@app.get("/gui/schedules", tags=["⏰ Scheduler"])
def gui_list_schedules():
    """등록된 스케줄 목록 + 내장 스케줄 표시"""
    custom = _load_schedules()
    built_in = []
    if SCHEDULER_AVAILABLE and scheduler:
        for job in scheduler.get_jobs():
            built_in.append({
                "id": job.id, "name": job.name or job.id,
                "trigger": str(job.trigger), "next_run": str(job.next_run_time),
                "builtin": True
            })
    return {"builtin": built_in, "custom": custom}

@app.post("/gui/schedules", tags=["⏰ Scheduler"])
def gui_add_schedule(body: dict):
    """새 E2E 스케줄 등록"""
    if not SCHEDULER_AVAILABLE or not scheduler:
        raise HTTPException(status_code=500, detail="APScheduler not available")

    name = body.get("name", "E2E Auto")
    interval_hours = int(body.get("interval_hours", 6))

    sid = f"gui_e2e_{int(time.time())}"
    scheduler.add_job(
        _scheduled_e2e_job, 'interval', hours=interval_hours,
        id=sid, args=[sid], replace_existing=True,
        name=name
    )

    schedule = {
        "id": sid, "name": name, "interval_hours": interval_hours,
        "created": datetime.now().isoformat(), "active": True
    }
    schedules = _load_schedules()
    schedules.append(schedule)
    _save_schedules(schedules)

    logger.info(f"⏰ New schedule: {name} every {interval_hours}h (id={sid})")
    return {"success": True, "schedule": schedule}

@app.delete("/gui/schedules/{schedule_id}", tags=["⏰ Scheduler"])
def gui_delete_schedule(schedule_id: str):
    """스케줄 삭제"""
    if SCHEDULER_AVAILABLE and scheduler:
        try:
            scheduler.remove_job(schedule_id)
        except Exception:
            pass
    schedules = _load_schedules()
    schedules = [s for s in schedules if s.get("id") != schedule_id]
    _save_schedules(schedules)
    return {"success": True}


# --- Marketing GUI ---
TARGETS_FILE = os.path.join(os.path.dirname(__file__), "targets.json")
MARKETING_LOG = os.path.join(os.path.dirname(__file__), "data", "bot_marketing_log.json")

def _load_targets():
    if os.path.exists(TARGETS_FILE):
        with open(TARGETS_FILE, "r") as f:
            return _json.load(f)
    return {"agents": [], "tokens": []}

def _save_targets(data):
    with open(TARGETS_FILE, "w") as f:
        _json.dump(data, f, indent=2)

@app.get("/gui/marketing/targets", tags=["🎯 Marketing"])
def gui_get_targets():
    """타겟 에이전트 + 토큰 목록"""
    return _load_targets()

@app.post("/gui/marketing/targets/agent", tags=["🎯 Marketing"])
def gui_add_target_agent(body: dict):
    """타겟 에이전트 추가"""
    required = ["name", "project_id", "service"]
    for k in required:
        if k not in body:
            raise HTTPException(status_code=400, detail=f"Missing: {k}")
    data = _load_targets()
    data["agents"].append(body)
    _save_targets(data)
    return {"success": True, "agents": data["agents"]}

@app.delete("/gui/marketing/targets/agent/{name}", tags=["🎯 Marketing"])
def gui_remove_target_agent(name: str):
    """타겟 에이전트 삭제"""
    data = _load_targets()
    data["agents"] = [a for a in data["agents"] if a.get("name") != name]
    _save_targets(data)
    return {"success": True, "agents": data["agents"]}

@app.get("/gui/marketing/logs", tags=["🎯 Marketing"])
def gui_marketing_logs():
    """마케팅 로그 (최근 50개)"""
    if os.path.exists(MARKETING_LOG):
        try:
            with open(MARKETING_LOG, "r") as f:
                logs = _json.load(f)
            return {"logs": logs[-50:]}
        except:
            pass
    return {"logs": []}

@app.post("/gui/marketing/run", tags=["🎯 Marketing"])
async def gui_run_marketing(body: dict = {}):
    """마케팅 사이클 수동 실행"""
    mode = body.get("mode", "type_a")  # type_a or type_b
    target_name = body.get("target", "")  # 특정 에이전트 지정 (빈값이면 랜덤)

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-c",
            f"import asyncio; from bot_marketer import run_bot_marketing; asyncio.run(run_bot_marketing())",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            cwd=os.path.dirname(__file__)
        )
        logger.info(f"🎯 Marketing cycle started manually (PID={proc.pid})")
        return {"success": True, "pid": proc.pid, "mode": mode}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Buyer Tracking ---
SALES_LOG = os.path.join(os.path.dirname(__file__), "sales_log.json")

@app.get("/gui/buyers", tags=["📊 Buyer Tracking"])
def gui_buyer_tracking():
    """바이어 추적: 누가 Trinity를 구매했는지 + 마케팅 타겟 대조"""
    from collections import defaultdict

    sales = []
    if os.path.exists(SALES_LOG):
        try:
            with open(SALES_LOG, "r") as f:
                data = _json.load(f)
                sales = data.get("sales", [])
        except:
            pass

    # 바이어별 집계
    buyer_stats = defaultdict(lambda: {"count": 0, "revenue": 0.0, "services": set(), "last_buy": ""})
    for s in sales:
        addr = s.get("buyer", "").lower()
        if not addr:
            continue
        buyer_stats[addr]["count"] += 1
        buyer_stats[addr]["revenue"] += s.get("revenue", 0)
        buyer_stats[addr]["services"].add(s.get("service", "?"))
        buyer_stats[addr]["last_buy"] = s.get("timestamp", "")

    # 마케팅 타겟 주소 (현재 targets.json에는 project_id만 있지만, 향후 wallet 추가 가능)
    targets = _load_targets()
    target_names = {a.get("name", "").lower() for a in targets.get("agents", [])}

    # 자기 지갑 주소들 (자기결제 Oracle 필터링용)
    self_wallets = {
        os.getenv("BUYER_AGENT_WALLET_ADDRESS", "").lower(),
        os.getenv("BUYER2_AGENT_WALLET_ADDRESS", "").lower(),
    }
    self_wallets.discard("")

    # 결과 정리
    buyers = []
    for addr, stats in sorted(buyer_stats.items(), key=lambda x: x[1]["count"], reverse=True):
        is_self = addr in self_wallets
        buyers.append({
            "address": addr,
            "short": addr[:8] + "..." + addr[-4:] if len(addr) > 12 else addr,
            "count": stats["count"],
            "revenue": round(stats["revenue"], 4),
            "services": list(stats["services"]),
            "last_buy": stats["last_buy"],
            "is_self": is_self,
            "label": "🏪 Oracle (Self)" if is_self else "🌍 External",
        })

    total_external = sum(1 for b in buyers if not b["is_self"])
    total_self = sum(1 for b in buyers if b["is_self"])

    return {
        "buyers": buyers,
        "total_unique_buyers": len(buyers),
        "external_buyers": total_external,
        "self_purchases": total_self,
        "total_sales": len(sales),
    }


# --- Dashboard HTML 서빙 ---
@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    """픽셀아트 GUI 대시보드"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")
    if not os.path.exists(html_path):
        return HTMLResponse("<h1>dashboard.html not found</h1>", status_code=404)
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# 서버 실행
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Trinity ACP Agent API Server...")
    logger.info("Swagger UI: http://localhost:8000/docs")
    logger.info("Dashboard: http://localhost:8000/dashboard")
    logger.info("ReDoc: http://localhost:8000/redoc")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
