"""
Trinity Engine v1 vs v2 비교 테스트
"""
from trinity_engine import TrinityEngine
from trinity_engine_v2 import TrinityEngineV2
from datetime import datetime

def compare_engines():
    """두 엔진의 결과 비교"""
    
    # 테스트 케이스
    test_cases = [
        {
            "name": "Test Case 1",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "target_date": "2026-02-20"
        },
        {
            "name": "Test Case 2",
            "birth_date": "1985-11-23",
            "birth_time": "09:15",
            "target_date": "2026-03-15"
        },
        {
            "name": "Test Case 3",
            "birth_date": "1995-08-07",
            "birth_time": "18:45",
            "target_date": "2026-06-01"
        }
    ]
    
    engine_v1 = TrinityEngine()
    engine_v2 = TrinityEngineV2()
    
    print("=" * 80)
    print("Trinity Engine v1 vs v2 비교 테스트")
    print("=" * 80)
    
    for test in test_cases:
        print(f"\n### {test['name']}")
        print(f"생년월일: {test['birth_date']} {test['birth_time']}")
        print(f"분석 날짜: {test['target_date']}")
        print("-" * 80)
        
        # v1 실행
        result_v1 = engine_v1.calculate_daily_luck(
            birth_date=test['birth_date'],
            birth_time=test['birth_time'],
            target_date=test['target_date']
        )
        
        # v2 실행
        result_v2 = engine_v2.calculate_daily_luck(
            birth_date=test['birth_date'],
            birth_time=test['birth_time'],
            target_date=test['target_date']
        )
        
        # 비교 출력
        print(f"\n[v1 - 기본 로직]")
        print(f"  Score: {result_v1['trading_luck_score']} (Raw: {result_v1['raw_score']}/95)")
        print(f"  Sectors: {', '.join(result_v1['favorable_sectors'])}")
        print(f"  Breakdown: {' | '.join(result_v1['breakdown'])}")
        
        print(f"\n[v2 - 정교한 대운/세운]")
        print(f"  Score: {result_v2['trading_luck_score']} (Raw: {result_v2['raw_score']}/95)")
        print(f"  Sectors: {', '.join(result_v2['favorable_sectors'])}")
        print(f"  Breakdown: {' | '.join(result_v2['breakdown'])}")
        
        # 차이 분석
        score_diff = result_v2['raw_score'] - result_v1['raw_score']
        print(f"\n[차이 분석]")
        print(f"  점수 차이: {score_diff:+d}점")
        print(f"  개선율: {(score_diff / result_v1['raw_score'] * 100):+.1f}%")
        
        if result_v1['favorable_sectors'] != result_v2['favorable_sectors']:
            print(f"  ⚠️ 추천 섹터 변경됨!")
        else:
            print(f"  ✅ 추천 섹터 동일")
    
    print("\n" + "=" * 80)
    print("비교 완료")
    print("=" * 80)


if __name__ == "__main__":
    compare_engines()
