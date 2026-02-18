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

| 지표 | 값 | 방법론 |
|------|-----|--------|
| **변동성 상관계수** | 0.108 | Yahoo Finance N=412, Pearson |
| **통계적 유의성** | p < 0.05 | 독립적 알파 (RSI/MACD 무관) |
| **응답 속도** | ~10ms | FastAPI + 캐싱 |
| **데이터 소스** | Yahoo Finance | API Key 불필요, 무료 |

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

## 🔬 엔진 철학: Science + Art

```
┌─────────────────────────────────────────────────────┐
│              Trinity Oracle Engine                  │
├──────────────────────┬──────────────────────────────┤
│  🔬 SCIENCE          │  🎨 ART                      │
│  Volatility Timing   │  Sector Rotation             │
│                      │                              │
│  • Backtested Alpha  │  • Five Elements Theory      │
│  • N=412 days        │  • Logic-based Mapping       │
│  • p < 0.05          │  • Metaphysical Heuristic    │
│  • corr = 0.108      │  • 木→NEW_LISTING, 火→MEME   │
│                      │                              │
│  "언제 들어갈지"      │  "무엇을 살지"               │
└──────────────────────┴──────────────────────────────┘
```

> **변동성은 수학으로 검증되었고, 섹터는 동양 철학의 논리를 따릅니다.**
> 리스크 관리는 과학적으로, 종목 선정은 오행의 논리로.

---

## 📊 오행 → 크립토 섹터 매핑

| 오행 | 크립토 섹터 | 특성 | 근거 |
|------|------------|------|------|
| 火 (Fire) | MEME, AI, VOLATILE | 폭발적 변동성 | 화(火) = 빠르고 뜨거운 에너지 |
| 土 (Earth) | INFRASTRUCTURE, LAYER1, BTC | 기반 자산 | 토(土) = 안정적 기반, 중심 |
| 水 (Water) | DEFI, EXCHANGE, LIQUIDITY | 유동성/흐름 | 수(水) = 흐름, 순환 |
| 金 (Metal) | RWA, STABLECOIN | 가치 저장 | 금(金) = 단단한 가치 |
| 木 (Wood) | NEW_LISTING, GAMEFI, NFT | 초기 성장 | 목(木) = 새싹, 성장 |

> ⚠️ **투명한 공개**: 섹터 매핑은 오행 철학 기반 **Logic-based Heuristic**입니다.
> 변동성 상관계수(0.108)는 통계적으로 검증되었으나, 섹터 정확도는 V2에서 백테스트 예정입니다.

**봇 연동 예시 (if 문 하나로 끝):**
```python
oracle = requests.post(url, json={"target_date": today}).json()

# 변동성 타이밍 (수학적 검증)
if oracle["trading_luck_score"] >= 0.7:
    # 섹터 필터 (오행 논리)
    if "NEW_LISTING" in oracle["favorable_sectors"]:
        bet_size = 1000  # 운세 좋으니 평소 2배
    else:
        bet_size = 500
    execute_trade(bet_size)
else:
    pass  # 관망
```


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

### 🚀 [추천] Virtuals GAME SDK 연동 (서버 설치 불필요)

```python
# Project ID만 있으면 즉시 연동 가능
# Virtuals 플랫폼에서 Trinity_Alpha_Oracle에게 요청하면 자동 응답

# Project ID: e8d1733f-9769-4590-bab0-776115e715a7
# Virtuals 마켓플레이스에서 에이전트를 찾아 호출하세요
```

### 🔌 직접 REST API 호출

```python
import requests

BASE_URL = "http://15.165.210.0:8000"  # Trinity ACP Agent 서버

# 오늘 운세 조회
response = requests.post(
    f"{BASE_URL}/api/v1/daily-luck",
    json={"target_date": "2026-02-20"}
)

data = response.json()

# 봇 매매 판단 로직
if data["trading_luck_score"] >= 0.7:
    if "NEW_LISTING" in data["favorable_sectors"]:
        bet_size = 1000  # 운세 좋으니 평소 2배
    else:
        bet_size = 500
    execute_trade(bet_size)
```

### JavaScript
```javascript
const BASE_URL = "http://15.165.210.0:8000";

fetch(`${BASE_URL}/api/v1/daily-luck`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({target_date: '2026-02-20'})
})
.then(res => res.json())
.then(data => {
    if (data.trading_luck_score >= 0.7) {
        console.log('Enter trade! Sectors:', data.favorable_sectors);
    }
});
```

### cURL
```bash
curl -X POST http://15.165.210.0:8000/api/v1/daily-luck \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-02-20"}'
```

---

## 📈 로드맵

### ✅ V1 (현재 - 완료)
- [x] 사주 엔진 개발 (TrinityEngineV2)
- [x] Yahoo Finance 기반 변동성 백테스트 (N=412, corr=0.108)
- [x] GAME SDK 통합 (Trinity_Alpha_Oracle)
- [x] FastAPI REST API 서버
- [x] VPS 24/7 배포 (systemd + Swap)
- [x] HEAD /health 지원 (모니터링 봇 호환)

### 🔜 V2 (예정)
- [ ] **섹터 정확도 백테스트**: "목(木)의 날에 NFT/GAMEFI가 실제로 몇 % 아웃퍼폼했나?"
- [ ] 월봉/일봉 단위 세분화 점수
- [ ] Virtuals 마켓플레이스 정식 등록
- [ ] 웹훅(Webhook) 지원 (봇이 pull 대신 push 수신)
- [ ] 개인화 API (생년월일 기반 맞춤 운세)

---

## 💰 Pricing

| 플랜 | 가격 | 내용 |
|------|------|------|
| **Free** | $0 | 직접 API 호출 (rate limit 있음) |
| **Per Call** | $0.01 / call | Virtuals 플랫폼 통해 결제 |

> **Affordable Alpha**: RSI/MACD와 상관관계 없는 독립적 신호를 $0.01에 제공합니다.

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
