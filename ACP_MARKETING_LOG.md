# Trinity ACP Agent — 하이브리드 마케팅 구현 로그

> 작성일: 2026-02-18  
> 작성자: Antigravity AI  
> 목적: ACP 하이브리드 마케팅 전체 구현 과정 기록

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [구현 체크리스트](#2-구현-체크리스트)
3. [오류 및 해결 과정](#3-오류-및-해결-과정)
4. [최종 시스템 구조](#4-최종-시스템-구조)
5. [환경 변수](#5-환경-변수)
6. [서비스 등록 정보](#6-서비스-등록-정보)
7. [향후 과제](#7-향후-과제)

---

## 1. 프로젝트 개요

Trinity ACP Agent를 ACP(Agent Commerce Protocol) 마켓에서 **구매자(Buyer)** 이자 **판매자(Seller)** 로 운영하는 하이브리드 마케팅 전략 구현.

### 전략 구조

| 타입 | 방식 | 주기 | 비용 |
|------|------|------|------|
| **Type A** | 무료 HTTP 핑 (존재감 노출) | 30분마다 | $0 |
| **Type B** | 실제 온체인 결제 (ACP 트랜잭션) | 6시간마다 | $0.01~$0.02 |
| **Seller** | 다른 에이전트 구매 요청 자동 처리 | 30초 폴링 | 수익 발생 |

---

## 2. 구현 체크리스트

### Phase 1: 환경 설정
- [x] VPS에 `virtuals-acp` SDK 설치 (`pip install virtuals-acp`)
- [x] `.env` 파일에 ACP 자격증명 추가
  - `BUYER_ENTITY_ID=2`
  - `BUYER_AGENT_WALLET_ADDRESS=0xaC44D4C2De4d3b49844ac4B3500Ab49ad57b2dEB`
  - `WHITELISTED_WALLET_PRIVATE_KEY=...`
- [x] Burner Wallet 화이트리스트 등록 완료
- [x] ACP 지갑에 USDC $2 이체

### Phase 2: Type A 마케팅 (무료 핑)
- [x] `bot_marketer.py` 에 HTTP POST 요청 구현
- [x] 30분마다 랜덤 타겟 에이전트 선택
- [x] 교차검증 로그 저장 (`data/bot_marketing_log.json`)
- [x] 텔레그램 알림 연동

### Phase 3: Type B 마케팅 (온체인 결제)
- [x] `virtuals-acp` SDK import 경로 수정
  - `ACPContractClientV2`: `virtuals_acp.contract_clients.contract_client_v2`
  - `BASE_MAINNET_ACP_X402_CONFIG_V2`: `virtuals_acp.configs.configs`
- [x] `job_offerings` 속성명 수정 (`offerings` → `job_offerings`)
- [x] `service_requirement` JSON 객체 자동 생성 구현
  - `job_offering.requirement` 속성에서 스키마 자동 읽기
  - `required` 필드를 타입에 맞게 자동 채우기
- [x] **첫 온체인 트랜잭션 성공!** Job ID: `1002049392` (Otto AI)
- [x] 6시간마다 자동 실행

### Phase 4: 서비스 판매자 등록
- [x] ACP Service Registry UI 등록 (`app.virtuals.io/acp/join`)
  - `dailyLuck` ($0.01, SLA 5분)
  - `deepLuck` ($0.50, SLA 10분)
- [x] `acp_seller.py` 구현
  - `get_pending_memo_jobs()` 폴링 방식
  - `job.accept()` → `job.deliver()` 패턴
  - 자기 자신이 보낸 job 스킵 로직
- [x] `trinity-seller` systemd 서비스 등록 (24/7 자동 실행)

### Phase 5: API 검증
- [x] `/api/v1/daily-luck` 엔드포인트 정상 응답 확인
- [x] `/api/v1/deep-luck` 엔드포인트 정상 응답 확인

---

## 3. 오류 및 해결 과정

### 오류 1: Import 경로 오류
```
ImportError: cannot import name 'ACPContractClientV2' from 'virtuals_acp'
```
**원인**: 잘못된 import 경로  
**해결**: VPS에서 SDK 패키지 구조 직접 확인 후 수정
```python
# 수정 전
from virtuals_acp import ACPContractClientV2

# 수정 후
from virtuals_acp.contract_clients.contract_client_v2 import ACPContractClientV2
from virtuals_acp.configs.configs import BASE_MAINNET_ACP_X402_CONFIG_V2
```

---

### 오류 2: offerings 속성명 오류
```
AttributeError: 'IACPAgent' object has no attribute 'offerings'
```
**원인**: 속성명 불일치  
**해결**: `offerings` → `job_offerings` 로 수정

---

### 오류 3: service_requirement 타입 오류
```
Invalid service requirement: 'Trinity Agent cross-validation...' is not of type 'object'
Failed validating 'type' in schema: {'type': 'object', 'required': ['chain'], ...}
```
**원인**: `service_requirement`를 문자열로 전달했으나 에이전트가 JSON 객체를 요구  
**해결 과정**:
1. `job_offering` 객체 속성 확인 → `requirement` 속성에 스키마 존재 확인
2. `getattr(chosen_offering, 'requirement', None)` 으로 스키마 읽기
3. `required` 필드를 타입별로 자동 채우는 로직 구현

```python
schema = getattr(chosen_offering, 'requirement', None)
if schema and isinstance(schema, dict):
    required_fields = schema.get('required', [])
    props = schema.get('properties', {})
    service_requirement = {}
    for field in required_fields:
        field_type = props.get(field, {}).get('type', 'string')
        if field_type == 'string':
            service_requirement[field] = f"trinity-cross-validation-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        elif field_type == 'number':
            service_requirement[field] = 0
        elif field_type == 'boolean':
            service_requirement[field] = True
        else:
            service_requirement[field] = "trinity-request"
```

---

### 오류 4: VirtualsACP.start() 없음
```
[Seller] Error: 'VirtualsACP' object has no attribute 'start'
```
**원인**: SDK에 `start()` 메서드 없음  
**해결**: `dir(VirtualsACP)` 로 실제 메서드 확인 후 폴링 방식으로 변경
```python
# 수정 전
acp_client.start()

# 수정 후 (30초 폴링)
while True:
    pending = acp_client.get_pending_memo_jobs()
    for job in pending:
        job.accept()
        deliverable = on_new_task(job)
        job.deliver(deliverable)
    time.sleep(30)
```

---

### 오류 5: ACPJob.get() 없음
```
[Seller] Job handling error: 'ACPJob' object has no attribute 'get'
```
**원인**: `handle_new_task(job)` 내부에서 dict 메서드 호출 시도  
**해결**: `handle_new_task()` 제거, 직접 `job.accept()` → `job.deliver()` 패턴 사용  
**추가**: 자기 자신이 보낸 job(`client_address == agent_wallet`) 스킵 로직 추가

---

## 4. 최종 시스템 구조

```
Trinity ACP Agent (VPS: 15.165.210.0)
├── trinity-acp.service          # FastAPI API 서버 (포트 8000)
│   ├── /api/v1/daily-luck       # 일일 운세 API
│   └── /api/v1/deep-luck        # 심층 운세 API
│
├── trinity-acp-agent.service    # 마케팅 봇
│   └── bot_marketer.py
│       ├── Type A: 30분마다 HTTP 핑
│       └── Type B: 6시간마다 온체인 결제
│
└── trinity-seller.service       # 판매자 서비스
    └── acp_seller.py
        ├── 30초마다 pending jobs 폴링
        ├── dailyLuck 주문 처리 → Trinity API 호출 → deliver()
        └── deepLuck 주문 처리 → Trinity API 호출 → deliver()
```

### 주요 파일

| 파일 | 역할 |
|------|------|
| `bot_marketer.py` | Type A/B 하이브리드 마케팅 |
| `acp_seller.py` | ACP 판매자 서비스 |
| `acp_agent.py` | GAME SDK 기반 에이전트 (레거시) |
| `api_server.py` | FastAPI 서버 |
| `trinity_engine_v2.py` | 사주 엔진 |

---

## 5. 환경 변수

```env
# Trinity API
GAME_API_KEY=...
TELEGRAM_BOT_TOKEN=***REDACTED_TELEGRAM***
TELEGRAM_CHAT_ID=1629086047

# ACP Type B 결제
BUYER_ENTITY_ID=2
BUYER_AGENT_WALLET_ADDRESS=0xaC44D4C2De4d3b49844ac4B3500Ab49ad57b2dEB
WHITELISTED_WALLET_PRIVATE_KEY=<비공개>

# API 서버
BASE_API_URL=http://15.165.210.0:8000
```

---

## 6. 서비스 등록 정보

### ACP Service Registry
- **에이전트명**: Trinity Agent (Hybrid)
- **지갑**: `0xaC44D4C2De4d3b49844ac4B3500Ab49ad57b2dEB`
- **Entity ID**: 2
- **등록 URL**: https://app.virtuals.io/acp/join

### 등록된 서비스 오퍼링

#### dailyLuck
```json
{
  "name": "dailyLuck",
  "price": 0.01,
  "slaMinutes": 5,
  "requirement": {
    "type": "object",
    "required": ["target_date"],
    "properties": {
      "target_date": {"type": "string", "description": "Date in YYYY-MM-DD format"}
    }
  },
  "deliverable": "JSON with trading_luck_score, favorable_sectors, volatility_index"
}
```

#### deepLuck
```json
{
  "name": "deepLuck",
  "price": 0.50,
  "slaMinutes": 10,
  "requirement": {
    "type": "object",
    "required": ["birth_date", "birth_time"],
    "properties": {
      "birth_date": {"type": "string", "description": "Birth date YYYY-MM-DD"},
      "birth_time": {"type": "string", "description": "Birth time HH:MM (24h)"}
    }
  },
  "deliverable": "Comprehensive JSON with luck_score, sectors, risk_level, strategy"
}
```

### 타겟 에이전트 (Type B 마케팅 대상)

| 에이전트 | Project ID | 서비스 |
|---------|-----------|--------|
| Ethy AI | 84 | token_info |
| BigBugAi | 157 | market_scan |
| Otto AI | 193 | twitter_alpha |
| ArAIstotle | 201 | philosophy |
| Meme Factory | 312 | meme_gen |

### 첫 온체인 트랜잭션
- **Job ID**: `1002049392`
- **대상**: Otto AI (twitter_alpha 서비스)
- **금액**: $0.02 USDC
- **날짜**: 2026-02-18
- **체인**: Base Mainnet

---

## 7. 향후 과제

### 단기 (1주일 내)
- [ ] USDC 잔액 모니터링 자동화 (잔액 $0.50 이하 시 텔레그램 알림)
- [ ] `deep-luck` API 엔드포인트 실제 사주 엔진 연동 확인
- [ ] 첫 판매 발생 시 텔레그램 알림 확인

### 중기 (1개월 내)
- [ ] 타겟 에이전트 목록 확장 (현재 5개 → 20개)
- [ ] Type B 결제 주기 조정 (6시간 → 에이전트별 최적화)
- [ ] 판매 수익 대시보드 구현

### 장기
- [ ] Trinity 토큰 발행 후 ACP 마켓 연동
- [ ] 다국어 운세 서비스 추가 (영어, 일본어)
- [ ] 프리미엄 서비스 추가 (`weeklyLuck`, `monthlyLuck`)

### 모니터링 명령어
```bash
# 서비스 상태 확인
sudo systemctl status trinity-acp trinity-acp-agent trinity-seller

# 실시간 로그
sudo journalctl -u trinity-seller -f
sudo journalctl -u trinity-acp-agent -f

# API 테스트
curl http://localhost:8000/api/v1/daily-luck -X POST \
  -H "Content-Type: application/json" \
  -d '{"target_date":"2026-02-18"}'

# 서비스 재시작
sudo systemctl restart trinity-acp trinity-acp-agent trinity-seller
```

---

*마지막 업데이트: 2026-02-18 16:05 KST*
