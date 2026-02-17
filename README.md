# Trinity ACP Agent

**AI-powered trading luck calculator based on Saju metaphysics**

Virtuals Protocol의 ACP(Agent Commerce Protocol) 기반 트레이딩 운세 점수 제공 에이전트

---

## 🎯 개요

Trinity ACP Agent는 사주명리학 기반의 정량화된 "운(Luck)" 점수를 트레이딩 봇에게 제공하는 독립형 API 서버입니다.

### 핵심 기능

- **Daily Trading Luck Score**: 0.0~1.0 범위의 정규화된 운세 점수
- **Crypto-Native Sectors**: 오행(五行) 기반 크립토 섹터 추천
- **Volatility Index**: 사주 패턴 기반 변동성 지수
- **Backtest Verification**: 과거 1년간 BTC 등락폭과의 상관관계 (0.77)
- **REST API**: FastAPI 기반 HTTP API 제공
- **Swagger UI**: 자동 API 문서 생성

### 성능 지표

- **상관계수**: 0.77
- **정확도**: 85%
- **응답 속도**: <2초 (목표), ~0.2ms (캐싱)
- **처리량**: 7,500+ req/hour

---

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/trinity-acp-agent.git
cd trinity-acp-agent

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 GAME_API_KEY 설정
```

### 2. 서버 실행

```bash
# 개발 모드 (자동 재시작)
uvicorn api_server:app --reload

# 프로덕션 모드
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. API 테스트

```bash
# Swagger UI 접속
open http://localhost:8000/docs

# 헬스체크
curl http://localhost:8000/health

# 일일 운세 조회
curl -X POST http://localhost:8000/api/v1/daily-luck \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-02-20"}'
```

---

## 📡 API 엔드포인트

### POST /api/v1/daily-luck
일일 트레이딩 운세 점수 계산

**Request**:
```json
{
  "target_date": "2026-02-20",
  "user_birth_data": "1990-05-15 14:30"  // Optional
}
```

**Response**:
```json
{
  "trading_luck_score": 0.75,
  "favorable_sectors": ["INFRASTRUCTURE", "LAYER1", "BTC"],
  "volatility_index": "LOW",
  "market_sentiment": "STABLE",
  "wealth_opportunity": "HIGH"
}
```

### POST /api/v1/verify-accuracy
백테스트 신뢰성 검증

**Response**:
```json
{
  "correlation_coefficient": 0.77,
  "sample_size": 413,
  "accuracy_rate": 0.85,
  "cached": false
}
```

**전체 API 문서**: [API_GUIDE.md](API_GUIDE.md)

---

## 🏗️ 프로젝트 구조

```
acp-gridcore/
├── api_server.py               # FastAPI REST API 서버
├── acp_agent.py                # GAME SDK 통합
├── trinity_engine_v2.py        # 사주 계산 엔진 (600줄)
├── backtest_engine.py          # 백테스트 엔진 (200줄)
├── config.py                   # 환경 설정
├── health_check.py             # 헬스체크 스크립트
├── test_api.py                 # API 통합 테스트
├── deploy.sh                   # 자동 배포 스크립트
├── trinity-acp.service         # systemd 서비스 파일
├── requirements.txt            # 의존성
├── .env.example                # 환경 변수 템플릿
├── data/
│   └── backtest_data.json      # 백테스트 데이터
└── docs/
    ├── API_GUIDE.md            # API 사용 가이드
    ├── DEPLOYMENT_GUIDE.md     # 일반 배포 가이드
    ├── VPS_DEPLOYMENT_GUIDE.md # VPS 배포 가이드
    └── SECURITY_REVIEW.md      # 보안 검토
```

---

## 🧪 테스트

### 자동 테스트
```bash
# API 서버 시작
uvicorn api_server:app --host 0.0.0.0 --port 8000 &

# 통합 테스트 실행
python3 test_api.py

# 결과: 7/7 tests passed ✅
```

### 수동 테스트
```bash
# Trinity Engine 테스트
python3 trinity_engine_v2.py

# Backtest Engine 테스트
python3 backtest_engine.py

# ACP Agent 테스트
python3 acp_agent.py
```

---

## 🚀 배포

### VPS 배포 (권장)

**상세 가이드**: [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md)

```bash
# 1. AWS Lightsail 서버 생성 ($5/월)
# 2. 코드 배포
git clone https://github.com/YOUR_USERNAME/trinity-acp-agent.git
cd trinity-acp-agent

# 3. 자동 배포 스크립트 실행
chmod +x deploy.sh
./deploy.sh

# 4. 서비스 확인
sudo systemctl status trinity-acp.service
```

**예상 소요 시간**: 50분
**월 운영 비용**: ₩6,500

---

## 📊 오행 → 크립토 섹터 매핑

| 오행 | 크립토 섹터 | 특성 |
|------|------------|------|
| 火 (Fire) | MEME, AI, VOLATILE | 폭발적 변동성 |
| 土 (Earth) | INFRASTRUCTURE, LAYER1, BTC | 기반 자산 |
| 水 (Water) | DEFI, EXCHANGE, LIQUIDITY | 유동성/흐름 |
| 金 (Metal) | RWA, STABLECOIN | 가치 저장 |
| 木 (Wood) | NEW_LISTING, GAMEFI, NFT | 초기 성장 |

---

## 🔒 보안

- ✅ 환경 변수로 API 키 관리
- ✅ .gitignore로 민감 정보 제외
- ✅ 입력 검증 (Pydantic)
- ✅ Path Traversal 방지
- ✅ Division by Zero 방지

**상세 보안 검토**: [SECURITY_REVIEW.md](SECURITY_REVIEW.md)

---

## 📚 문서

| 문서 | 설명 |
|------|------|
| [API_GUIDE.md](API_GUIDE.md) | API 사용 가이드 및 예제 |
| [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md) | VPS 배포 단계별 가이드 |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | 일반 배포 가이드 |
| [SECURITY_REVIEW.md](SECURITY_REVIEW.md) | 보안 검토 및 개선 사항 |

---

## 🎯 사용 예제

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/daily-luck",
    json={"target_date": "2026-02-20"}
)

data = response.json()
print(f"Score: {data['trading_luck_score']}")
print(f"Sectors: {data['favorable_sectors']}")
```

### JavaScript
```javascript
fetch('http://localhost:8000/api/v1/daily-luck', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({target_date: '2026-02-20'})
})
.then(res => res.json())
.then(data => console.log(data));
```

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/daily-luck \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-02-20"}'
```

---

## 📈 로드맵

- [x] Phase 1: 핵심 엔진 개발
- [x] Phase 2: 백테스트 검증
- [x] Phase 3: GAME SDK 통합
- [x] Phase 4: FastAPI 서버 구현
- [ ] Phase 5: VPS 배포
- [ ] Phase 6: Virtuals 마켓플레이스 등록
- [ ] Phase 7: 마케팅 및 사용자 확보

---

## 💰 비즈니스 모델

### 수익 모델
- **API 호출 가격**: $0.01/call
- **월 목표**: 1,000 calls
- **예상 수익**: $10/월 (₩13,000)

### 비용
- **VPS 서버**: $5/월 (₩6,500)
- **순익**: ₩6,500/월

---

## 🤝 기여

이 프로젝트는 오픈소스입니다. 기여를 환영합니다!

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 라이선스

MIT License

---

## ⚠️ 면책 조항

이 에이전트가 제공하는 데이터는 참고용이며, 투자 조언이 아닙니다. 과거 성과가 미래 수익을 보장하지 않습니다.

---

## 📞 지원

- **문서**: [API_GUIDE.md](API_GUIDE.md)
- **이슈**: GitHub Issues
- **Virtuals Protocol**: https://virtuals.io/
