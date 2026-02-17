"""
Trinity ACP Agent - Health Check Script
서버 상태를 확인하는 스크립트 (Cron 등에서 사용)
"""
import requests
import sys
import time

def check_health(url="http://localhost:8000/health", timeout=5, retries=3):
    """
    서버 헬스체크
    
    Args:
        url: 헬스체크 엔드포인트 URL
        timeout: 타임아웃 (초)
        retries: 재시도 횟수
    
    Returns:
        0: 정상
        1: 실패
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service is healthy")
                print(f"   Uptime: {data.get('uptime_hours', 0):.2f} hours")
                print(f"   Total requests: {data.get('total_requests', 0)}")
                return 0
            else:
                print(f"⚠️ Service returned status code {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(2)
                
        except requests.exceptions.Timeout:
            print(f"❌ Request timeout (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return 1
    
    print(f"❌ Health check failed after {retries} attempts")
    return 1

if __name__ == '__main__':
    # 커맨드라인 인자로 URL 받기
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/health"
    sys.exit(check_health(url))
