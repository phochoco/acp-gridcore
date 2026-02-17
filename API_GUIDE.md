# FastAPI 서버 사용 가이드

## 🚀 빠른 시작

### 1. 서버 실행
```bash
cd /Users/pochoco/Desktop/acp-gridcore

# 개발 모드 (자동 재시작)
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Swagger UI 접속
브라우저에서 열기:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📡 API 엔드포인트

### 1. 루트 (/)
```bash
curl http://localhost:8000/
```

**응답**:
```json
{
  "name": "Trinity ACP Agent API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health"
}
```

---

### 2. 헬스체크 (/health)
```bash
curl http://localhost:8000/health
```

**응답**:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600.5,
  "uptime_hours": 1.0,
  "total_requests": 150,
  "timestamp": "2026-02-18T02:35:00"
}
```

---

### 3. 일일 운세 (POST /api/v1/daily-luck)

#### 개인화된 운세
```bash
curl -X POST http://localhost:8000/api/v1/daily-luck \
  -H "Content-Type: application/json" \
  -d '{
    "target_date": "2026-02-20",
    "user_birth_data": "1990-05-15 14:30"
  }'
```

#### 일반 운세
```bash
curl -X POST http://localhost:8000/api/v1/daily-luck \
  -H "Content-Type: application/json" \
  -d '{
    "target_date": "2026-02-20"
  }'
```

**응답**:
```json
{
  "trading_luck_score": 0.75,
  "favorable_sectors": ["INFRASTRUCTURE", "LAYER1", "BTC"],
  "volatility_index": "LOW",
  "market_sentiment": "STABLE",
  "wealth_opportunity": "HIGH",
  "raw_score": 73,
  "breakdown": {
    "daewoon_score": 25,
    "seun_score": 30,
    "yongsin_score": 18
  },
  "keyword": "안정적 성장"
}
```

---

### 4. 정확도 검증 (POST /api/v1/verify-accuracy)
```bash
curl -X POST http://localhost:8000/api/v1/verify-accuracy \
  -H "Content-Type: application/json" \
  -d '{
    "force_refresh": false
  }'
```

**응답**:
```json
{
  "correlation_coefficient": 0.77,
  "sample_size": 413,
  "accuracy_rate": 0.85,
  "top_signals": [...],
  "cached": false,
  "disclaimer": "Past performance does not guarantee future results."
}
```

---

### 5. 통계 (GET /api/v1/stats)
```bash
curl http://localhost:8000/api/v1/stats
```

**응답**:
```json
{
  "uptime_seconds": 7200.5,
  "total_requests": 500,
  "requests_per_hour": 250.0,
  "agent_name": "Trinity ACP Agent",
  "version": "1.0.0"
}
```

---

## 🧪 테스트

### 자동 테스트 실행
```bash
# 서버 시작 (백그라운드)
uvicorn api_server:app --host 0.0.0.0 --port 8000 &

# 테스트 실행
python3 test_api.py

# 서버 종료
pkill -f "uvicorn api_server"
```

### 수동 테스트 (Swagger UI)
1. http://localhost:8000/docs 접속
2. 각 엔드포인트 클릭
3. "Try it out" 버튼 클릭
4. 파라미터 입력
5. "Execute" 버튼 클릭

---

## 🔧 프로덕션 배포

### systemd 서비스 설정
```ini
[Unit]
Description=Trinity ACP Agent API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trinity-acp-agent
Environment="PATH=/home/ubuntu/trinity-acp-agent/venv/bin"
ExecStart=/home/ubuntu/trinity-acp-agent/venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx 리버스 프록시 (선택)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 📊 모니터링

### 헬스체크 (Cron)
```bash
# /etc/crontab에 추가
*/5 * * * * /path/to/venv/bin/python /path/to/health_check.py http://localhost:8000/health
```

### 로그 확인
```bash
# API 로그
tail -f trinity_api.log

# systemd 로그
sudo journalctl -u trinity-api.service -f
```

---

## 🎯 사용 예제

### Python
```python
import requests

# 일일 운세 조회
response = requests.post(
    "http://localhost:8000/api/v1/daily-luck",
    json={
        "target_date": "2026-02-20",
        "user_birth_data": "1990-05-15 14:30"
    }
)

data = response.json()
print(f"Score: {data['trading_luck_score']}")
print(f"Sectors: {data['favorable_sectors']}")
```

### JavaScript
```javascript
// 일일 운세 조회
fetch('http://localhost:8000/api/v1/daily-luck', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        target_date: '2026-02-20',
        user_birth_data: '1990-05-15 14:30'
    })
})
.then(res => res.json())
.then(data => {
    console.log(`Score: ${data.trading_luck_score}`);
    console.log(`Sectors: ${data.favorable_sectors}`);
});
```

### cURL
```bash
# 일일 운세 조회
curl -X POST http://localhost:8000/api/v1/daily-luck \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-02-20"}'
```

---

## 🔒 보안

### CORS 설정 (프로덕션)
`api_server.py`에서 수정:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### API 키 인증 (선택)
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.post("/api/v1/daily-luck", dependencies=[Depends(verify_api_key)])
def get_daily_luck(...):
    ...
```

---

## ✅ 체크리스트

### 개발 환경
- [ ] 서버 실행 확인
- [ ] Swagger UI 접속 확인
- [ ] 모든 엔드포인트 테스트
- [ ] 로그 확인

### 프로덕션 환경
- [ ] systemd 서비스 등록
- [ ] Nginx 리버스 프록시 설정 (선택)
- [ ] 헬스체크 Cron 설정
- [ ] CORS 설정 확인
- [ ] 로그 로테이션 설정
