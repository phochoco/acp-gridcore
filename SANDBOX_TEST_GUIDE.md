# Sandbox 테스트 가이드

## 🎯 목표
Virtuals Platform Sandbox에서 Trinity ACP Agent를 테스트합니다.

## 📋 사전 준비

### 1. 로컬 에이전트 실행 확인
```bash
cd /Users/pochoco/Desktop/acp-gridcore
python3 -c "from acp_agent import TrinityACPAgent; agent = TrinityACPAgent()"
```

**예상 출력**:
```
✅ GAME SDK initialized: Trinity ACP Agent
```

### 2. 환경 변수 확인
```bash
cat .env
```

**필수 변수**:
- `GAME_API_KEY`: apt-a842d80e4cf1024d250f08c8a1445211 ✅

---

## 🧪 Sandbox 테스트 단계

### Step 1: Virtuals Console 접속
1. 브라우저에서 https://console.game.virtuals.io/ 접속
2. API 키로 로그인: `apt-a842d80e4cf1024d250f08c8a1445211`

### Step 2: Agent 확인
1. Dashboard → Agents 메뉴
2. "Trinity ACP Agent" 확인
3. Status: Active 확인

### Step 3: Function 테스트

#### Test 1: get_daily_luck
**입력**:
```json
{
  "target_date": "2026-02-20",
  "user_birth_data": "1990-05-15 14:30"
}
```

**예상 출력**:
```json
{
  "trading_luck_score": 0.75,
  "favorable_sectors": ["INFRASTRUCTURE", "LAYER1", "BTC"],
  "volatility_index": "LOW",
  "market_sentiment": "STABLE",
  "wealth_opportunity": "HIGH"
}
```

#### Test 2: verify_accuracy
**입력**:
```json
{
  "force_refresh": false
}
```

**예상 출력**:
```json
{
  "correlation_coefficient": 0.77,
  "sample_size": 413,
  "accuracy_rate": 0.85,
  "cached": false,
  "top_signals": [...]
}
```

### Step 4: 성능 테스트
1. **응답 시간**: <2초 확인
2. **캐싱**: 두 번째 호출 시 `cached: true` 확인
3. **에러 핸들링**: 잘못된 입력 테스트

---

## 🔍 테스트 체크리스트

### 기능 테스트
- [ ] Agent가 Console에 표시됨
- [ ] `get_daily_luck` 정상 작동
- [ ] `verify_accuracy` 정상 작동
- [ ] 캐싱 작동 (두 번째 호출)
- [ ] 에러 메시지 명확함

### 성능 테스트
- [ ] 응답 시간 <2초
- [ ] 캐시 적용 시 <0.2ms
- [ ] 동시 요청 처리

### 보안 테스트
- [ ] 잘못된 날짜 형식 거부
- [ ] 빈 문자열 거부
- [ ] SQL Injection 방어

---

## 🐛 문제 해결

### Issue 1: Agent가 Console에 표시되지 않음
**해결책**:
```bash
# Agent 재컴파일
python3 -c "
from acp_agent import TrinityACPAgent
agent = TrinityACPAgent()
if agent.game_agent:
    agent.game_agent.compile()
    print('✅ Agent recompiled')
"
```

### Issue 2: Function 호출 실패
**확인사항**:
1. Function 파라미터 이름 확인 (`fn_name`, `fn_description`, `args`)
2. Argument 타입 확인 (`string`, `boolean`)
3. Wrapper 함수 반환값 확인 (`Tuple[FunctionResultStatus, str, dict]`)

### Issue 3: 응답 시간 >2초
**확인사항**:
1. 캐싱 작동 여부
2. 네트워크 지연
3. Trinity Engine 계산 시간

---

## 📊 성공 기준

### ✅ 필수 조건
1. Agent가 Console에 등록됨
2. 두 Function 모두 정상 작동
3. 응답 시간 <2초
4. 에러 핸들링 정상

### 🎯 추가 목표
1. 캐싱으로 응답 시간 <0.2ms
2. 동시 요청 10개 처리
3. 24시간 안정성 테스트

---

## 🚀 다음 단계

### Sandbox 테스트 성공 시
1. **프로덕션 배포**
   - Base Chain 지갑 설정
   - `BASE_PRIVATE_KEY` 추가
   - 실제 트레이딩 봇 연동

2. **마케팅**
   - 백테스트 데이터 강조
   - 크립토 네이티브 매핑 홍보
   - 가격 경쟁력 ($0.01/call)

### Sandbox 테스트 실패 시
1. 로그 확인
2. Function 파라미터 재검토
3. SDK 버전 확인
4. Support 문의

---

## 📞 지원

- **GAME SDK 문서**: https://github.com/game-by-virtuals/game-python
- **Virtuals Console**: https://console.game.virtuals.io/
- **API 키**: apt-a842d80e4cf1024d250f08c8a1445211
