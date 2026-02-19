"""
Trinity ACP Agent - FastAPI REST API Server
독립적인 REST API 제공 + GAME SDK 통합
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional
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
    description="AI-powered trading luck calculator based on Saju metaphysics",
    version="1.0.1",
    docs_url="/docs",
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

# Routes
@app.get("/", tags=["Root"])
def root():
    """API root endpoint"""
    return {
        "name": "Trinity ACP Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
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
                "dominant_element": res["favorable_sectors"],  # 오행 정보 포함
                "keyword": res["keyword"],
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
                "target_date": request.target_date,
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

# 서버 실행
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Trinity ACP Agent API Server...")
    logger.info("Swagger UI: http://localhost:8000/docs")
    logger.info("ReDoc: http://localhost:8000/redoc")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
