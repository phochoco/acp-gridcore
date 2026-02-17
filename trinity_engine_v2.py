"""
Trinity Engine v2 - Enhanced Version
정교한 대운/세운 계산 로직 포함
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
class YongsinData:
    """용신 데이터"""
    yongsin: str  # 용신 (用神) - 필요한 오행
    heesin: str   # 희신 (喜神) - 보조 오행
    strong: bool  # 신강/신약


@dataclass
class DaewoonInfo:
    """대운 정보"""
    gan: str
    ji: str
    ganZhi: str
    start_age: int
    end_age: int
    start_year: int


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
    
    # 용신 데이터
    yongsin_data: Optional[YongsinData] = None


@dataclass
class TrinityScore:
    """Trinity 점수 결과"""
    total_score: int  # 10-95
    daewoon_score: float  # 대운 점수
    seun_score: float  # 세운 점수
    interaction_score: int  # 상호작용 점수
    keyword: str  # 키워드
    breakdown: List[str]  # 점수 산출 근거


# ===== 상수 정의 =====

# 천간 (天干) - 10개 (한글)
HEAVENLY_STEMS_KO = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]

# 지지 (地支) - 12개 (한글)
EARTHLY_BRANCHES_KO = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

# 천간 (天干) - 10개 (한자)
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 지지 (地支) - 12개 (한자)
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 한글 → 한자 매핑
KO_TO_HANJA_GAN = dict(zip(HEAVENLY_STEMS_KO, HEAVENLY_STEMS))
KO_TO_HANJA_ZHI = dict(zip(EARTHLY_BRANCHES_KO, EARTHLY_BRANCHES))

# 오행 매핑 (한글) - 천간/지지 분리
STEM_ELEMENT_MAP_KO = {
    "갑": "목", "을": "목",
    "병": "화", "정": "화",
    "무": "토", "기": "토",
    "경": "금", "신": "금",  # 천간 신(辛)
    "임": "수", "계": "수"
}

BRANCH_ELEMENT_MAP_KO = {
    "인": "목", "묘": "목",
    "사": "화", "오": "화",
    "진": "토", "술": "토", "축": "토", "미": "토",
    "신": "금", "유": "금",  # 지지 신(申)
    "자": "수", "해": "수"
}

# 오행 매핑 (한자)
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

# 오행 상극 관계
CONTROL_MAP = {
    "목": "토",  # 木克土
    "화": "금",  # 火克金
    "토": "수",  # 土克水
    "금": "목",  # 金克木
    "수": "화"   # 水克火
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


# ===== 유틸리티 함수 =====

def get_element(gan_or_ji: str) -> str:
    """간지에서 오행 추출"""
    # 천간 먼저 확인
    if gan_or_ji in STEM_ELEMENT_MAP_KO:
        return STEM_ELEMENT_MAP_KO[gan_or_ji]
    # 지지 확인
    if gan_or_ji in BRANCH_ELEMENT_MAP_KO:
        return BRANCH_ELEMENT_MAP_KO[gan_or_ji]
    # 기본값
    return "토"


def controls_element(from_elem: str, to_elem: str) -> bool:
    """오행 상극 체크"""
    return CONTROL_MAP.get(from_elem) == to_elem


def evaluate_element(gan_or_ji: str, yongsin: str, heesin: str) -> float:
    """
    오행 평가 함수
    용신: +30, 희신: +15, 기신: -20, 중립: 0
    """
    element = get_element(gan_or_ji)
    
    # 용신 일치
    if element == yongsin:
        return 30.0
    
    # 희신 일치
    if element == heesin:
        return 15.0
    
    # 기신 (용신을 극하는 오행)
    if controls_element(element, yongsin):
        return -20.0
    
    # 중립
    return 0.0


def get_ganzi_for_year(year: int) -> Dict[str, str]:
    """
    60갑자 순환 계산
    2024년 = 갑진(甲辰)을 기준으로 계산
    """
    # 2024년 = 갑(0) + 진(4)
    stem_index = (year - 2024 + 0 + 10) % 10
    branch_index = (year - 2024 + 4 + 12) % 12
    
    gan = HEAVENLY_STEMS_KO[stem_index]
    ji = EARTHLY_BRANCHES_KO[branch_index]
    
    return {
        "gan": gan,
        "ji": ji,
        "ganZhi": gan + ji
    }


# ===== Trinity Engine v2 클래스 =====

class TrinityEngineV2:
    """정교한 대운/세운 계산이 포함된 Trinity Engine"""
    
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
            크립토 네이티브 용어로 변환된 결과
        """
        # 입력 검증
        self._validate_inputs(birth_date, birth_time, target_date, gender)
        
        # 1. 사주 계산
        saju = self._calculate_saju(birth_date, birth_time, gender)
        
        # 2. 목표 날짜의 연도 추출
        target_year = datetime.strptime(target_date, "%Y-%m-%d").year
        
        # 3. Trinity 점수 계산 (정교한 버전)
        trinity_score = self._calculate_trinity_score_v2(saju, target_year)
        
        # 4. 크립토 네이티브 용어로 변환
        crypto_result = self._map_to_crypto_terms(trinity_score, saju)
        
        return crypto_result
    
    def _validate_inputs(self, birth_date: str, birth_time: str, target_date: str, gender: str):
        """입력 검증"""
        # 날짜 형식 검증
        try:
            datetime.strptime(birth_date, "%Y-%m-%d")
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format (expected YYYY-MM-DD): {e}")
        
        # 시간 형식 검증
        if ":" not in birth_time:
            raise ValueError(f"Invalid time format (expected HH:MM): {birth_time}")
        
        try:
            parts = birth_time.split(":")
            hour = int(parts[0])
            if not (0 <= hour <= 23):
                raise ValueError(f"Hour must be 0-23: {hour}")
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid time format: {birth_time}")
        
        # 성별 검증
        if gender not in ["M", "F"]:
            raise ValueError(f"Gender must be 'M' or 'F': {gender}")
    
    def _calculate_saju(self, birth_date: str, birth_time: str, gender: str) -> SajuData:
        """
        사주팔자 계산 (간단한 버전)
        """
        birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
        
        # 간단한 만세력 계산
        year_gan_idx = (birth_dt.year - 4) % 10
        year_zhi_idx = (birth_dt.year - 4) % 12
        
        month_gan_idx = (birth_dt.month - 1) % 10
        month_zhi_idx = (birth_dt.month - 1) % 12
        
        day_gan_idx = (birth_dt.day - 1) % 10
        day_zhi_idx = (birth_dt.day - 1) % 12
        
        # 시간 파싱 (이미 검증됨)
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
        
        # 용신 계산
        yongsin_data = self._calculate_yongsin(elements)
        
        return SajuData(
            pillars=pillars,
            birth_date=birth_dt.date(),
            birth_time=birth_time,
            gender=gender,
            elements=elements,
            clash_count=clash_count,
            harmony_count=harmony_count,
            yongsin_data=yongsin_data
        )
    
    def _calculate_elements(self, pillars: SajuPillar) -> Dict[str, int]:
        """오행(五行) 개수 계산"""
        elements = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        
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
    
    def _calculate_yongsin(self, elements: Dict[str, int]) -> YongsinData:
        """
        용신 계산 (간단한 버전)
        가장 약한 오행을 용신으로, 용신을 생하는 오행을 희신으로
        """
        # 가장 약한 오행 찾기
        yongsin_hanja = min(elements, key=elements.get)
        
        # 한자 → 한글 변환
        hanja_to_ko = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
        yongsin = hanja_to_ko[yongsin_hanja]
        
        # 희신 계산 (용신을 생하는 오행)
        # 목생화, 화생토, 토생금, 금생수, 수생목
        sheng_map = {"목": "수", "화": "목", "토": "화", "금": "토", "수": "금"}
        heesin = sheng_map[yongsin]
        
        # 신강/신약 판정 (일간 오행 개수로 간단히 판정)
        total_elements = sum(elements.values())
        strong = elements[yongsin_hanja] > (total_elements / 5) if total_elements > 0 else False
        
        return YongsinData(
            yongsin=yongsin,
            heesin=heesin,
            strong=strong
        )
    
    def _calculate_trinity_score_v2(self, saju: SajuData, target_year: int) -> TrinityScore:
        """
        Trinity 점수 계산 v2 (정교한 대운/세운 로직)
        """
        score = 50.0  # 기본 점수
        breakdown = []
        
        # 1. 대운 점수 (±30점, 천간 30% + 지지 70%)
        daewoon_score = self._calculate_daewoon_score_v2(saju, target_year)
        score += daewoon_score
        breakdown.append(f"대운: {daewoon_score:+.1f}점")
        
        # 2. 세운 점수 (±20점, 대운의 2/3 영향력)
        seun_score = self._calculate_seun_score_v2(saju, target_year)
        score += seun_score
        breakdown.append(f"세운: {seun_score:+.1f}점")
        
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
            daewoon_score=daewoon_score,
            seun_score=seun_score,
            interaction_score=interaction_score,
            keyword=keyword,
            breakdown=breakdown
        )
    
    def _get_current_daewoon(self, saju: SajuData, target_year: int) -> DaewoonInfo:
        """
        현재 대운 추출 (10년 주기)
        """
        birth_year = saju.birth_date.year
        age = target_year - birth_year + 1
        
        # 대운 시작 나이 계산 (간단한 버전: 남자 양년생/여자 음년생 = 순행)
        # 실제로는 더 복잡하지만, MVP에서는 단순화
        start_offset = 3  # 기본 3세부터 시작
        
        # 현재 대운 주기 계산
        daewoon_cycle = (age - start_offset) // 10
        start_age = start_offset + (daewoon_cycle * 10)
        end_age = start_age + 10
        
        # 대운 간지 계산 (월주 기준으로 순행)
        month_gan_idx = HEAVENLY_STEMS.index(saju.pillars.month.gan)
        month_zhi_idx = EARTHLY_BRANCHES.index(saju.pillars.month.zhi)
        
        daewoon_gan_idx = (month_gan_idx + daewoon_cycle + 1) % 10
        daewoon_zhi_idx = (month_zhi_idx + daewoon_cycle + 1) % 12
        
        gan_ko = HEAVENLY_STEMS_KO[daewoon_gan_idx]
        ji_ko = EARTHLY_BRANCHES_KO[daewoon_zhi_idx]
        
        return DaewoonInfo(
            gan=gan_ko,
            ji=ji_ko,
            ganZhi=gan_ko + ji_ko,
            start_age=start_age,
            end_age=end_age,
            start_year=birth_year + start_age - 1
        )
    
    def _calculate_daewoon_score_v2(self, saju: SajuData, target_year: int) -> float:
        """
        대운 점수 계산 v2 (용신 기반, 천간 30% + 지지 70%)
        """
        if not saju.yongsin_data:
            return 0.0
        
        daewoon = self._get_current_daewoon(saju, target_year)
        yongsin_data = saju.yongsin_data
        
        # 천간 평가
        gan_score = evaluate_element(daewoon.gan, yongsin_data.yongsin, yongsin_data.heesin)
        
        # 지지 평가
        ji_score = evaluate_element(daewoon.ji, yongsin_data.yongsin, yongsin_data.heesin)
        
        # 가중 평균 (천간 30% + 지지 70%)
        total_score = gan_score * 0.3 + ji_score * 0.7
        
        return total_score
    
    def _calculate_seun_score_v2(self, saju: SajuData, target_year: int) -> float:
        """
        세운 점수 계산 v2 (용신 기반, 대운의 2/3 영향력)
        """
        if not saju.yongsin_data:
            return 0.0
        
        # 연도의 간지 계산
        seun = get_ganzi_for_year(target_year)
        yongsin_data = saju.yongsin_data
        
        # 천간 평가
        gan_score = evaluate_element(seun["gan"], yongsin_data.yongsin, yongsin_data.heesin)
        
        # 지지 평가
        ji_score = evaluate_element(seun["ji"], yongsin_data.yongsin, yongsin_data.heesin)
        
        # 가중 평균 (천간 30% + 지지 70%)
        # 세운은 대운의 2/3 영향력
        total_score = (gan_score * 0.3 + ji_score * 0.7) * 0.67
        
        return total_score
    
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
    engine = TrinityEngineV2()
    
    # 테스트
    result = engine.calculate_daily_luck(
        birth_date="1990-05-15",
        birth_time="14:30",
        target_date="2026-02-20"
    )
    
    print("=== Trinity Trading Luck Score v2 ===")
    print(f"Score: {result['trading_luck_score']}")
    print(f"Raw Score: {result['raw_score']}/95")
    print(f"Favorable Sectors: {', '.join(result['favorable_sectors'])}")
    print(f"Volatility Index: {result['volatility_index']}")
    print(f"Market Sentiment: {result['market_sentiment']}")
    print(f"Wealth Opportunity: {result['wealth_opportunity']}")
    print(f"\nBreakdown:")
    for item in result['breakdown']:
        print(f"  - {item}")
