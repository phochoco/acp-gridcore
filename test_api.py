#!/usr/bin/env python3
"""
Trinity ACP Agent - API 테스트 스크립트
모든 엔드포인트를 테스트합니다
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_root():
    """루트 엔드포인트 테스트"""
    print("\n=== Test 1: Root Endpoint ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ PASSED")

def test_health():
    """헬스체크 엔드포인트 테스트"""
    print("\n=== Test 2: Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    assert response.status_code == 200
    assert data['status'] == 'healthy'
    print("✅ PASSED")

def test_daily_luck():
    """일일 운세 엔드포인트 테스트"""
    print("\n=== Test 3: Daily Luck (Personalized) ===")
    payload = {
        "target_date": "2026-02-20",
        "user_birth_data": "1990-05-15 14:30"
    }
    response = requests.post(f"{BASE_URL}/api/v1/daily-luck", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert 'trading_luck_score' in data
    assert 0.0 <= data['trading_luck_score'] <= 1.0
    print("✅ PASSED")

def test_daily_luck_general():
    """일반 운세 엔드포인트 테스트"""
    print("\n=== Test 4: Daily Luck (General) ===")
    payload = {
        "target_date": "2026-02-20"
    }
    response = requests.post(f"{BASE_URL}/api/v1/daily-luck", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Score: {data['trading_luck_score']}")
    print(f"Sectors: {data['favorable_sectors']}")
    assert response.status_code == 200
    print("✅ PASSED")

def test_verify_accuracy():
    """정확도 검증 엔드포인트 테스트"""
    print("\n=== Test 5: Verify Accuracy ===")
    payload = {
        "force_refresh": False
    }
    response = requests.post(f"{BASE_URL}/api/v1/verify-accuracy", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Correlation: {data['correlation_coefficient']}")
    print(f"Accuracy: {data['accuracy_rate']:.1%}")
    print(f"Cached: {data['cached']}")
    assert response.status_code == 200
    assert 'correlation_coefficient' in data
    print("✅ PASSED")

def test_stats():
    """통계 엔드포인트 테스트"""
    print("\n=== Test 6: Stats ===")
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    assert response.status_code == 200
    print("✅ PASSED")

def test_invalid_date():
    """잘못된 날짜 형식 테스트"""
    print("\n=== Test 7: Invalid Date Format ===")
    payload = {
        "target_date": "invalid-date"
    }
    response = requests.post(f"{BASE_URL}/api/v1/daily-luck", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Error: {response.json()}")
    assert response.status_code == 422  # Validation error
    print("✅ PASSED")

def main():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Trinity ACP Agent API - Integration Tests")
    print("=" * 60)
    
    # 서버가 준비될 때까지 대기
    print("\nWaiting for server to start...")
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/health", timeout=1)
            print("✅ Server is ready!")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            print(f"Waiting... ({i+1}/10)")
    else:
        print("❌ Server did not start in time")
        return 1
    
    try:
        test_root()
        test_health()
        test_daily_luck()
        test_daily_luck_general()
        test_verify_accuracy()
        test_stats()
        test_invalid_date()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
