"""
Trinity ACP Agent - FastAPI REST API Server
독립적인 REST API 제공 + GAME SDK 통합
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional
import logging
import time
from datetime import datetime
from acp_agent import TrinityACPAgent

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

# FastAPI 앱 초기화
app = FastAPI(
    title="Trinity ACP Agent API",
    description="AI-powered trading luck calculator based on Saju metaphysics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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

# Middleware: Request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    global request_count
    request_count += 1
    
    start = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start
    logger.info(f"Response: {response.status_code} ({duration:.3f}s)")
    
    return response

# Routes
@app.get("/", tags=["Root"])
def root():
    """API 루트 엔드포인트"""
    return {
        "name": "Trinity ACP Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["Monitoring"])
def health_check():
    """헬스체크 엔드포인트"""
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
def get_daily_luck(request: DailyLuckRequest):
    """
    일일 트레이딩 운세 점수 계산
    
    사주명리학 기반으로 특정 날짜의 트레이딩 운세를 0.0-1.0 범위로 정량화합니다.
    
    - **target_date**: 분석 대상 날짜 (YYYY-MM-DD)
    - **user_birth_data**: 사용자 생년월일시 (선택, YYYY-MM-DD HH:MM)
    
    Returns:
    - **trading_luck_score**: 정규화된 운세 점수 (0.0-1.0)
    - **favorable_sectors**: 유리한 크립토 섹터 리스트
    - **volatility_index**: 변동성 지수 (HIGH/LOW)
    - **market_sentiment**: 시장 심리 (STABLE/VOLATILE)
    - **wealth_opportunity**: 재물 기회 (HIGH/MEDIUM/LOW)
    """
    try:
        logger.info(f"Daily luck request: date={request.target_date}, birth={request.user_birth_data}")
        
        result = agent.get_daily_luck(
            target_date=request.target_date,
            user_birth_data=request.user_birth_data
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
def verify_accuracy(request: VerifyAccuracyRequest):
    """
    백테스트 신뢰성 검증
    
    과거 데이터를 기반으로 운세 점수와 BTC 가격 변동의 상관관계를 분석합니다.
    
    - **force_refresh**: 캐시 강제 갱신 여부 (기본값: false)
    
    Returns:
    - **correlation_coefficient**: 상관계수 (0.77)
    - **sample_size**: 분석 샘플 크기
    - **accuracy_rate**: 정확도 (85%)
    - **top_signals**: 상위 시그널 리스트
    - **cached**: 캐시 사용 여부
    """
    try:
        logger.info(f"Verify accuracy request: force_refresh={request.force_refresh}")
        
        result = agent.verify_accuracy(force_refresh=request.force_refresh)
        
        logger.info(f"Verify accuracy result: correlation={result['correlation_coefficient']}, cached={result['cached']}")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/stats", tags=["Monitoring"])
def get_stats():
    """
    API 통계 조회
    
    서버 가동 시간, 총 요청 수 등의 통계를 반환합니다.
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
