"""
Configuration for Trinity ACP Agent
"""
import os
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """환경 변수 및 설정 관리"""
    
    # Virtuals Protocol
    GAME_API_KEY: Optional[str] = os.getenv("GAME_API_KEY")
    
    # Base Chain Wallet (CRITICAL: Never hardcode!)
    BASE_PRIVATE_KEY: Optional[str] = os.getenv("BASE_PRIVATE_KEY")
    
    # Agent 설정
    AGENT_NAME: str = "Trinity_Alpha_Oracle"
    AGENT_DESCRIPTION: str = "Provides quantitative luck scores for algorithmic trading bots based on metaphysics"
    
    # 가격 정책
    PRICING_PER_CALL: float = 0.01  # USDC
    
    # 성능 목표
    MAX_RESPONSE_TIME: float = float(os.getenv("MAX_RESPONSE_TIME", "2.0"))
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    
    # 백테스트 데이터 경로
    BACKTEST_DATA_PATH: str = os.path.join(os.path.dirname(__file__), "data", "backtest_data.json")
    
    @classmethod
    def validate(cls) -> bool:
        """필수 환경 변수 검증"""
        if not cls.GAME_API_KEY:
            raise ValueError("GAME_API_KEY environment variable is required")
        
        # 프로덕션 환경에서는 Private Key도 필수
        if os.getenv("ENV") == "production" and not cls.BASE_PRIVATE_KEY:
            raise ValueError("BASE_PRIVATE_KEY is required in production environment")
        
        return True
    
    @classmethod
    def is_production(cls) -> bool:
        """프로덕션 환경 여부"""
        return os.getenv("ENV") == "production"
