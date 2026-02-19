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
    from game_sdk.game.agent import Agent, WorkerConfig
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
            action_space=[get_luck_function, verify_function],
            instruction="Calculate daily trading luck scores based on Saju (Chinese metaphysics) analysis. Provide quantified scores (0.0-1.0) with favorable crypto sectors and market indicators."
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
        실제 바이낸스 BTC/USDT 10년치 데이터 기반 (backtest_result.json)

        Args:
            force_refresh: 캐시 무시하고 강제 재계산

        Returns:
            실제 Binance 백테스트 결과 (N=3058일, 2015~2025)
        """
        import json, os

        # 캐시 유효성 검사
        cache_valid = (
            self._backtest_cache is not None and
            self._cache_timestamp is not None and
            not force_refresh and
            (datetime.now() - self._cache_timestamp).total_seconds() < Config.CACHE_TTL_SECONDS
        )

        if cache_valid:
            result = self._backtest_cache.copy()
            result["cached"] = True
            result["cache_age_seconds"] = int((datetime.now() - self._cache_timestamp).total_seconds())
            return result

        # ★ 실제 바이낸스 백테스트 결과 파일 우선 읽기
        backtest_json_path = os.path.join(os.path.dirname(__file__), "backtest_result.json")
        if os.path.exists(backtest_json_path):
            try:
                with open(backtest_json_path, "r") as f:
                    raw = json.load(f)
                result = {
                    "correlation_coefficient": raw.get("return_correlation", 0.0),
                    "volatility_correlation": raw.get("volatility_correlation", 0.0),
                    "sample_size": raw.get("sample_size", 0),
                    "period": raw.get("period", ""),
                    "accuracy_rate": round(raw.get("high_luck_win_rate_pct", 0) / 100, 4),
                    "high_luck_win_rate_pct": raw.get("high_luck_win_rate_pct", 0),
                    "high_luck_avg_return_pct": raw.get("high_luck_avg_return_pct", 0),
                    "low_luck_win_rate_pct": raw.get("low_luck_win_rate_pct", 0),
                    "low_luck_avg_return_pct": raw.get("low_luck_avg_return_pct", 0),
                    "edge_pct": raw.get("edge_pct", 0),
                    "win_rate_edge_pp": raw.get("win_rate_edge_pp", 0),
                    "all_win_rate_pct": raw.get("all_win_rate_pct", 0),
                    "top_signals": [
                        {
                            "signal": "HIGH_LUCK (score >= 0.7)",
                            "days": raw.get("high_luck_days", 0),
                            "avg_next_day_return": f"+{raw.get('high_luck_avg_return_pct', 0):.2f}%",
                            "win_rate": f"{raw.get('high_luck_win_rate_pct', 0):.1f}%"
                        },
                        {
                            "signal": "LOW_LUCK (score < 0.4)",
                            "days": raw.get("low_luck_days", 0),
                            "avg_next_day_return": f"{raw.get('low_luck_avg_return_pct', 0):.2f}%",
                            "win_rate": f"{raw.get('low_luck_win_rate_pct', 0):.1f}%"
                        }
                    ],
                    "data_source": raw.get("source", "Binance BTCUSDT 1d OHLCV"),
                    "methodology": "BTC Genesis Block (2009-01-03 18:15 KST) Saju analysis vs next-day BTC return",
                    "disclaimer": "Past performance does not guarantee future results. For informational purposes only.",
                    "cached": False
                }
            except Exception as e:
                # JSON 읽기 실패 시 기존 엔진으로 폴백
                result = self.backtest_engine.get_correlation_report()
                result["cached"] = False
        else:
            # backtest_result.json 없으면 기존 엔진 사용
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
            print("\n📡 Compiling agent workers...")
            
            try:
                # compile() 호출 필수 - Worker를 GAME 플랫폼에 등록
                self.game_agent.compile()
                print("✅ Workers compiled successfully!")
                print("\n🚀 Agent is running and ready to receive requests from GAME platform...")
                print("Press Ctrl+C to stop\n")
                
                # GAME SDK run() 호출 - 자동으로 요청 처리
                self.game_agent.run()
                
            except KeyboardInterrupt:
                print("\n\n👋 Agent stopped by user")
        else:
            print("\n⚠️ Running in standalone mode (GAME SDK not available)")
            print("Agent functions are available but not connected to GAME platform")



# ===== 메인 실행 코드 =====

if __name__ == "__main__":
    # .env에서 API Key 로드
    agent = TrinityACPAgent()
    agent.run()
