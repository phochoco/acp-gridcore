"""
Trinity Engine - 사주 기반 운세 점수 계산 엔진
기존 TypeScript 코드를 Python으로 포팅
"""
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import calendar


# ===== 데이터 구조 =====

@dataclass
class GanZhi:
    """천간지지 (天干地支)"""
    gan: str  # 천간 (天干)
    zhi: str  # 지지 (地支)
    
    def __str__(self) -> str:
        return f"{self.gan}{self.zhi}"


@dataclass
class SajuPillar:
    """사주 기둥 (년/월/일/시)"""
    year: GanZhi
    month: GanZhi
    day: GanZhi
    hour: GanZhi


@dataclass
class SajuData:
    """사주 데이터"""
    pillars: SajuPillar
    birth_date: date
    birth_time: str
    gender: str  # "M" or "F"
    
    # 오행 균형
    elements: Dict[str, int]  # {"木": 2, "火": 1, ...}
    
    # 상호작용
    clash_count: int  # 충(沖) 개수
    harmony_count: int  # 합(合) 개수


@dataclass
class TrinityScore:
    """Trinity 점수 결과"""
    total_score: int  # 10-95
    daewoon_score: int  # 대운 점수
    seun_score: int  # 세운 점수
    interaction_score: int  # 상호작용 점수
    keyword: str  # 키워드
    breakdown: List[str]  # 점수 산출 근거


# ===== 상수 정의 =====

# 천간 (天干) - 10개
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 지지 (地支) - 12개
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 오행 매핑
STEM_ELEMENTS = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}

BRANCH_ELEMENTS = {
    "子": "水", "亥": "水",
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "辰": "土", "戌": "土", "丑": "土", "未": "土"
}

# 충(沖) 관계 - 정반대 위치
CLASH_PAIRS = [
    ("子", "午"), ("丑", "未"), ("寅", "申"),
    ("卯", "酉"), ("辰", "戌"), ("巳", "亥")
]

# 합(合) 관계
HARMONY_PAIRS = [
    ("子", "丑"), ("寅", "亥"), ("卯", "戌"),
    ("辰", "酉"), ("巳", "申"), ("午", "未")
]


# ===== Trinity Engine 클래스 =====

class TrinityEngine:
    """사주 기반 운세 점수 계산 엔진"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def calculate_daily_luck(
        self, 
        birth_date: str, 
        birth_time: str,
        target_date: str,
        gender: str = "M"
    ) -> Dict:
        """
        특정 날짜의 트레이딩 운 점수 계산
        
        Args:
            birth_date: "YYYY-MM-DD" (양력)
            birth_time: "HH:MM" (24시간 형식)
            target_date: "YYYY-MM-DD" (분석 대상 날짜)
            gender: "M" or "F"
        
        Returns:
            {
                "trading_luck_score": 0.85,
                "favorable_sectors": ["MEME", "AI", "VOLATILE"],
                "volatility_index": "HIGH",
                "market_sentiment": "VOLATILE",
                "wealth_opportunity": "HIGH",
                "raw_score": 85,  # 10-95 범위
                "breakdown": ["대운: +20점", "세운: +15점", ...]
            }
        """
        # 1. 사주 계산
        saju = self._calculate_saju(birth_date, birth_time, gender)
        
        # 2. 목표 날짜의 연도 추출
        target_year = datetime.strptime(target_date, "%Y-%m-%d").year
        
        # 3. Trinity 점수 계산
        trinity_score = self._calculate_trinity_score(saju, target_year)
        
        # 4. 크립토 네이티브 용어로 변환
        crypto_result = self._map_to_crypto_terms(trinity_score, saju)
        
        return crypto_result
    
    def _calculate_saju(self, birth_date: str, birth_time: str, gender: str) -> SajuData:
        """
        사주팔자 계산
        
        Note: 현재는 간단한 구현. 실제로는 korean-lunar-calendar 사용
        """
        birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
        
        # 간단한 만세력 계산 (실제로는 더 복잡함)
        year_gan_idx = (birth_dt.year - 4) % 10
        year_zhi_idx = (birth_dt.year - 4) % 12
        
        month_gan_idx = (birth_dt.month - 1) % 10
        month_zhi_idx = (birth_dt.month - 1) % 12
        
        day_gan_idx = (birth_dt.day - 1) % 10
        day_zhi_idx = (birth_dt.day - 1) % 12
        
        hour = int(birth_time.split(":")[0])
        hour_zhi_idx = ((hour + 1) // 2) % 12
        hour_gan_idx = (day_gan_idx * 2 + hour_zhi_idx) % 10
        
        pillars = SajuPillar(
            year=GanZhi(HEAVENLY_STEMS[year_gan_idx], EARTHLY_BRANCHES[year_zhi_idx]),
            month=GanZhi(HEAVENLY_STEMS[month_gan_idx], EARTHLY_BRANCHES[month_zhi_idx]),
            day=GanZhi(HEAVENLY_STEMS[day_gan_idx], EARTHLY_BRANCHES[day_zhi_idx]),
            hour=GanZhi(HEAVENLY_STEMS[hour_gan_idx], EARTHLY_BRANCHES[hour_zhi_idx])
        )
        
        # 오행 계산
        elements = self._calculate_elements(pillars)
        
        # 충/합 계산
        clash_count = self._count_clashes(pillars)
        harmony_count = self._count_harmonies(pillars)
        
        return SajuData(
            pillars=pillars,
            birth_date=birth_dt.date(),
            birth_time=birth_time,
            gender=gender,
            elements=elements,
            clash_count=clash_count,
            harmony_count=harmony_count
        )
    
    def _calculate_elements(self, pillars: SajuPillar) -> Dict[str, int]:
        """오행(五行) 개수 계산"""
        elements = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        
        # 천간 오행
        for pillar in [pillars.year, pillars.month, pillars.day, pillars.hour]:
            elements[STEM_ELEMENTS[pillar.gan]] += 1
            elements[BRANCH_ELEMENTS[pillar.zhi]] += 1
        
        return elements
    
    def _count_clashes(self, pillars: SajuPillar) -> int:
        """충(沖) 개수 계산"""
        branches = [p.zhi for p in [pillars.year, pillars.month, pillars.day, pillars.hour]]
        clash_count = 0
        
        for i, b1 in enumerate(branches):
            for b2 in branches[i+1:]:
                if (b1, b2) in CLASH_PAIRS or (b2, b1) in CLASH_PAIRS:
                    clash_count += 1
        
        return clash_count
    
    def _count_harmonies(self, pillars: SajuPillar) -> int:
        """합(合) 개수 계산"""
        branches = [p.zhi for p in [pillars.year, pillars.month, pillars.day, pillars.hour]]
        harmony_count = 0
        
        for i, b1 in enumerate(branches):
            for b2 in branches[i+1:]:
                if (b1, b2) in HARMONY_PAIRS or (b2, b1) in HARMONY_PAIRS:
                    harmony_count += 1
        
        return harmony_count
    
    def _calculate_trinity_score(self, saju: SajuData, target_year: int) -> TrinityScore:
        """
        Trinity 점수 계산 (기존 TypeScript 로직 포팅)
        """
        score = 50  # 기본 점수
        breakdown = []
        
        # 1. 대운 점수 (±30점)
        daewoon_score = self._calculate_daewoon_score(saju, target_year)
        score += daewoon_score
        breakdown.append(f"대운: {int(daewoon_score):+d}점")
        
        # 2. 세운 점수 (±20점)
        seun_score = self._calculate_seun_score(saju, target_year)
        score += seun_score
        breakdown.append(f"세운: {int(seun_score):+d}점")
        
        # 3. 상호작용 점수 (±10점)
        interaction_score = self._calculate_interaction_score(saju)
        score += interaction_score
        if interaction_score != 0:
            breakdown.append(f"상호작용: {interaction_score:+d}점")
        
        # 최종 점수 (10-95 범위)
        final_score = max(10, min(95, round(score)))
        
        # 키워드 결정
        keyword = self._determine_keyword(final_score)
        
        return TrinityScore(
            total_score=final_score,
            daewoon_score=round(daewoon_score),
            seun_score=round(seun_score),
            interaction_score=interaction_score,
            keyword=keyword,
            breakdown=breakdown
        )
    
    def _calculate_daewoon_score(self, saju: SajuData, target_year: int) -> float:
        """대운 점수 계산 (간단한 구현)"""
        # 실제로는 복잡한 대운 계산 필요
        # 현재는 오행 균형 기반으로 간단히 계산
        dominant_element = max(saju.elements, key=saju.elements.get)
        element_strength = saju.elements[dominant_element]
        
        # 오행이 균형잡혀 있으면 긍정적
        if 2 <= element_strength <= 3:
            return 20.0
        elif element_strength >= 4:
            return -10.0
        else:
            return 0.0
    
    def _calculate_seun_score(self, saju: SajuData, target_year: int) -> float:
        """세운 점수 계산"""
        # 연도의 천간지지 계산
        year_gan_idx = (target_year - 4) % 10
        year_zhi_idx = (target_year - 4) % 12
        
        year_gan = HEAVENLY_STEMS[year_gan_idx]
        year_zhi = EARTHLY_BRANCHES[year_zhi_idx]
        
        # 일간과의 관계 분석
        day_gan = saju.pillars.day.gan
        
        # 간단한 점수 계산 (실제로는 더 복잡)
        if STEM_ELEMENTS[year_gan] == STEM_ELEMENTS[day_gan]:
            return 15.0  # 같은 오행
        else:
            return -5.0
    
    def _calculate_interaction_score(self, saju: SajuData) -> int:
        """상호작용 점수 (충/합)"""
        score = 0
        
        # 합이 많으면 긍정적
        score += saju.harmony_count * 5
        
        # 충이 많으면 부정적
        score -= saju.clash_count * 5
        
        return score
    
    def _determine_keyword(self, score: int) -> str:
        """점수 기반 키워드 결정"""
        if score >= 80:
            return "STRONG_BULLISH"
        elif score >= 65:
            return "BULLISH"
        elif score >= 45:
            return "NEUTRAL"
        elif score >= 30:
            return "BEARISH"
        else:
            return "STRONG_BEARISH"
    
    def _map_to_crypto_terms(self, trinity_score: TrinityScore, saju: SajuData) -> Dict:
        """Trinity 점수를 크립토 네이티브 용어로 변환"""
        # 점수 정규화 (10-95 → 0.0-1.0)
        normalized_score = (trinity_score.total_score - 10) / 85
        
        # 주도 오행 판정
        dominant_element = max(saju.elements, key=saju.elements.get)
        
        # 오행 → 크립토 섹터 매핑
        element_to_sector = {
            "火": ["MEME", "AI", "VOLATILE"],
            "土": ["INFRASTRUCTURE", "LAYER1", "BTC"],
            "水": ["DEFI", "EXCHANGE", "LIQUIDITY"],
            "金": ["RWA", "STABLECOIN"],
            "木": ["NEW_LISTING", "GAMEFI", "NFT"]
        }
        
        favorable_sectors = element_to_sector[dominant_element]
        
        # 변동성 지수
        volatility_index = "HIGH" if saju.clash_count > 2 else "LOW"
        
        # 시장 심리
        market_sentiment = "STABLE" if saju.harmony_count > 1 else "VOLATILE"
        
        # 재물 기회
        wealth_opportunity = "HIGH" if trinity_score.total_score >= 70 else \
                           "MEDIUM" if trinity_score.total_score >= 50 else "LOW"
        
        return {
            "trading_luck_score": round(normalized_score, 2),
            "favorable_sectors": favorable_sectors,
            "volatility_index": volatility_index,
            "market_sentiment": market_sentiment,
            "wealth_opportunity": wealth_opportunity,
            "raw_score": trinity_score.total_score,
            "breakdown": trinity_score.breakdown,
            "keyword": trinity_score.keyword
        }


# ===== 테스트 코드 =====

if __name__ == "__main__":
    engine = TrinityEngine()
    
    # 테스트
    result = engine.calculate_daily_luck(
        birth_date="1990-05-15",
        birth_time="14:30",
        target_date="2026-02-20"
    )
    
    print("=== Trinity Trading Luck Score ===")
    print(f"Score: {result['trading_luck_score']}")
    print(f"Raw Score: {result['raw_score']}/95")
    print(f"Favorable Sectors: {', '.join(result['favorable_sectors'])}")
    print(f"Volatility Index: {result['volatility_index']}")
    print(f"Market Sentiment: {result['market_sentiment']}")
    print(f"Wealth Opportunity: {result['wealth_opportunity']}")
    print(f"\nBreakdown:")
    for item in result['breakdown']:
        print(f"  - {item}")
