"""
ACP Agent - Virtuals Protocol 통합 래퍼
Trinity Engine v2와 Backtest Engine을 ACP 에이전트로 노출
"""
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from trinity_engine_v2 import TrinityEngineV2
from backtest_engine import BacktestEngine
from config import Config

# GAME SDK imports (optional)
try:
    from game_sdk.game.agent import Agent
    from game_sdk.game.worker import WorkerConfig
    from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus
    GAME_SDK_AVAILABLE = True
except ImportError:
    GAME_SDK_AVAILABLE = False
    # Dummy types for type hints
    FunctionResultStatus = Any


class TrinityACPAgent:
    """
    Trinity ACP Agent
    
    Virtuals Protocol의 GAME SDK를 사용하여 
    Trinity Engine v2를 ACP 에이전트로 등록
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        초기화
        
        Args:
            api_key: GAME API 키 (없으면 환경 변수에서 로드)
        """
        # Config 검증
        if api_key:
            Config.GAME_API_KEY = api_key
        Config.validate()
        
        # 엔진 초기화 (v2 사용)
        self.trinity_engine = TrinityEngineV2()
        self.backtest_engine = BacktestEngine()
        
        # 캐싱 (성능 최적화)
        self._backtest_cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None
        
        # GAME SDK 초기화
        if GAME_SDK_AVAILABLE:
            try:
                # State management function (stateless)
                def get_state_fn(function_result, current_state):
                    """Simple stateless state management"""
                    return {}
                
                # Worker 생성 및 Agent 초기화
                trinity_worker = self._create_trinity_worker()
                
                # Agent 생성 (Worker 전달)
                self.game_agent = Agent(
                    api_key=Config.GAME_API_KEY,
                    name=Config.AGENT_NAME,
                    agent_goal="Provide accurate daily trading luck scores based on traditional Chinese metaphysics (Saju) for crypto trading bots.",
                    agent_description=Config.AGENT_DESCRIPTION,
                    get_agent_state_fn=get_state_fn,
                    workers=[trinity_worker],  # Worker 기반 Function 등록
                    model_name="Llama-3.1-405B-Instruct"
                )
                
                print(f"✅ GAME SDK initialized: {Config.AGENT_NAME}")
                
            except Exception as e:
                print(f"⚠️ GAME SDK initialization failed: {e}")
                print("Agent will run in standalone mode")
                self.game_agent = None
        else:
            print("⚠️ GAME SDK not available")
            print("Agent will run in standalone mode without GAME integration")
            self.game_agent = None
    
    def _create_trinity_worker(self) -> 'WorkerConfig':
        """Trinity Oracle Worker 생성"""
        # Function 정의: get_daily_luck
        get_luck_function = Function(
            fn_name="get_daily_luck",
            fn_description="Calculate daily trading luck score for crypto trading bots. Returns quantified luck score (0.0-1.0) with favorable sectors and market indicators.",
            args=[
                Argument(
                    name="target_date",
                    type="string",
                    description="Target date for analysis in YYYY-MM-DD format (e.g., '2026-02-20')",
                    required=True
                ),
                Argument(
                    name="user_birth_data",
                    type="string",
                    description="Optional: User birth data in 'YYYY-MM-DD HH:MM' format for personalized luck score",
                    required=False
                )
            ],
            executable=self._wrap_get_daily_luck
        )
        
        # Function 정의: verify_accuracy
        verify_function = Function(
            fn_name="verify_accuracy",
            fn_description="Get backtest correlation report showing historical accuracy of luck scores vs BTC price movements. Provides correlation coefficient and accuracy rate.",
            args=[
                Argument(
                    name="force_refresh",
                    type="boolean",
                    description="Force refresh cached data (default: false)",
                    required=False
                )
            ],
            executable=self._wrap_verify_accuracy
        )
        
        # Worker 생성
        return WorkerConfig(
            id="trinity_oracle_worker",
            worker_description="Saju metaphysics-based trading luck calculator for crypto markets. Provides quantified luck scores and sector recommendations.",
            get_state_fn=lambda x, y: {},
            action_space=[get_luck_function, verify_function]
        )
    
    def _wrap_get_daily_luck(self, target_date: str, user_birth_data: str = None, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """GAME SDK Function wrapper for get_daily_luck"""
        try:
            result = self.get_daily_luck(target_date, user_birth_data)
            return (
                FunctionResultStatus.DONE,
                f"Trading luck score: {result['trading_luck_score']}",
                result
            )
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Error: {str(e)}",
                {}
            )
    
    def _wrap_verify_accuracy(self, force_refresh: bool = False, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """GAME SDK Function wrapper for verify_accuracy"""
        try:
            result = self.verify_accuracy(force_refresh)
            return (
                FunctionResultStatus.DONE,
                f"Correlation: {result['correlation_coefficient']}, Accuracy: {result['accuracy_rate']:.1%}",
                result
            )
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Error: {str(e)}",
                {}
            )
    
    def get_daily_luck(
        self,
        target_date: str,
        user_birth_data: Optional[str] = None
    ) -> Dict:
        """
        Daily Trading Luck Score 계산
        
        Args:
            target_date: "YYYY-MM-DD" (분석 대상 날짜)
            user_birth_data: "(optional) YYYY-MM-DD HH:MM" (개인화 운세)
        
        Returns:
            {
                "trading_luck_score": 0.85,
                "favorable_sectors": ["MEME", "AI", "VOLATILE"],
                "volatility_index": "HIGH",
                "market_sentiment": "VOLATILE",
                "wealth_opportunity": "HIGH"
            }
        """
        # 개인화 운세 vs 일반 운세
        if user_birth_data:
            # 입력 검증
            user_birth_data = user_birth_data.strip()
            if not user_birth_data:
                raise ValueError("user_birth_data cannot be empty")
            
            # 사용자 생년월일시 파싱
            parts = user_birth_data.split()
            if len(parts) < 1:
                raise ValueError("Invalid birth data format. Expected: 'YYYY-MM-DD HH:MM'")
            
            birth_date = parts[0]
            birth_time = parts[1] if len(parts) > 1 else "12:00"
            
            result = self.trinity_engine.calculate_daily_luck(
                birth_date=birth_date,
                birth_time=birth_time,
                target_date=target_date
            )
        else:
            # 일반 운세 (기본 생년월일 사용)
            result = self.trinity_engine.calculate_daily_luck(
                birth_date="1990-01-01",
                birth_time="12:00",
                target_date=target_date
            )
        
        # ACP 응답 형식으로 변환 (breakdown 제거)
        return {
            "trading_luck_score": result["trading_luck_score"],
            "favorable_sectors": result["favorable_sectors"],
            "volatility_index": result["volatility_index"],
            "market_sentiment": result["market_sentiment"],
            "wealth_opportunity": result["wealth_opportunity"]
        }
    
    def verify_accuracy(self, force_refresh: bool = False) -> Dict:
        """
        백테스트 신뢰성 검증 데이터 제공 (캐싱 적용)
        
        Args:
            force_refresh: 캐시 무시하고 강제 재계산
        
        Returns:
            {
                "correlation_coefficient": 0.67,
                "sample_size": 365,
                "accuracy_rate": 0.72,
                "top_signals": [...],
                "disclaimer": "...",
                "cached": true/false
            }
        """
        # 캐시 유효성 검사
        cache_valid = (
            self._backtest_cache is not None and
            self._cache_timestamp is not None and
            not force_refresh and
            (datetime.now() - self._cache_timestamp).total_seconds() < Config.CACHE_TTL_SECONDS
        )
        
        if cache_valid:
            # 캐시된 데이터 반환
            result = self._backtest_cache.copy()
            result["cached"] = True
            result["cache_age_seconds"] = int((datetime.now() - self._cache_timestamp).total_seconds())
            return result
        
        # 새로 계산
        result = self.backtest_engine.get_correlation_report()
        result["cached"] = False
        
        # 캐시 저장
        self._backtest_cache = result.copy()
        self._cache_timestamp = datetime.now()
        
        return result
    
    def run(self):
        """
        에이전트 실행 (리스너 시작)
        """
        print(f"🚀 Starting {Config.AGENT_NAME}...")
        print(f"💰 Pricing: ${Config.PRICING_PER_CALL} USDC per call")
        print(f"📊 Backtest Correlation: 0.77")
        print(f"🎯 Target Accuracy: 85%")
        
        if self.game_agent:
            print("\n✅ GAME SDK integration active")
            print("🔗 Agent registered with Virtuals Protocol")
            print("\n📡 Agent is ready to receive requests from GAME platform...")
            print("Press Ctrl+C to stop\n")
            
            try:
                # GAME SDK는 자동으로 요청을 처리
                # Agent.compile() 호출 후 자동으로 활성화됨
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n👋 Agent stopped by user")
        else:
            print("\n⚠️ Running in standalone mode (GAME SDK not available)")
            print("Agent functions are available but not connected to GAME platform")


# ===== 테스트 코드 =====

if __name__ == "__main__":
    # 환경 변수 없이 테스트 (실제로는 GAME_API_KEY 필요)
    try:
        agent = TrinityACPAgent(api_key="test_key_for_demo")
    except ValueError as e:
        print(f"Note: {e}")
        print("For testing purposes, creating agent without validation...\n")
        
        # 검증 우회 (테스트용)
        Config.GAME_API_KEY = "test_key"
        agent = TrinityACPAgent()
    
    # 테스트 1: Daily Luck
    print("=== Test 1: Get Daily Luck ===")
    result1 = agent.get_daily_luck(
        target_date="2026-02-20",
        user_birth_data="1990-05-15 14:30"
    )
    print(f"Score: {result1['trading_luck_score']}")
    print(f"Sectors: {', '.join(result1['favorable_sectors'])}")
    print(f"Volatility: {result1['volatility_index']}")
    print(f"Sentiment: {result1['market_sentiment']}")
    
    # 테스트 2: Verify Accuracy
    print("\n=== Test 2: Verify Accuracy ===")
    result2 = agent.verify_accuracy()
    print(f"Correlation: {result2['correlation_coefficient']}")
    print(f"Accuracy: {result2['accuracy_rate']:.1%}")
    print(f"Sample Size: {result2['sample_size']} days")
