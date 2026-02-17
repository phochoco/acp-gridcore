# 텔레그램 알림 시스템 사용 가이드

## 🤖 개요

Trinity ACP Agent의 24/7 운영 상태를 텔레그램으로 실시간 모니터링하는 시스템입니다.

---

## 📋 기능

### 1. 신입 확인 알림 🦁
- Agent 상태 확인
- 백테스트 결과 요약
- API 서버 상태
- Virtuals Agent 연결 상태

### 2. 일일 리포트 📊
- 매일 오전 9시 자동 전송
- 서비스 가동 시간
- 백테스트 성능
- 오늘의 추천 전략

### 3. 에러 알림 🚨
- 서비스 다운 감지
- API 응답 실패
- 즉시 알림 전송

---

## 🚀 사용 방법

### 로컬에서 테스트

```bash
cd ~/Desktop/acp-gridcore
python3 telegram_notifier.py
```

### VPS에서 설정

#### 1. 파일 업로드
```bash
# GitHub에서 최신 코드 받기
cd ~/acp-gridcore
git pull
```

#### 2. cron 작업 설정
```bash
crontab -e
```

**추가할 내용**:
```bash
# 매일 오전 9시에 일일 리포트
0 9 * * * cd /home/ubuntu/acp-gridcore && /home/ubuntu/acp-gridcore/venv/bin/python3 telegram_notifier.py

# 매 시간마다 상태 체크
0 * * * * cd /home/ubuntu/acp-gridcore && /home/ubuntu/acp-gridcore/venv/bin/python3 -c "from telegram_notifier import TelegramNotifier; n = TelegramNotifier('***REDACTED_TELEGRAM***', '1629086047'); import requests; r = requests.get('http://localhost:8000/health'); n.send_error_alert('Health Check', 'API Down') if r.status_code != 200 else None"
```

---

## 📱 메시지 예시

### 신입 확인 알림
```
🦁 신입 확인 알림!

구매자 정보:
• 컨트랙트 타입: Trinity ACP Agent
• 생성일: 2026년 2월 18일
• ACP 프로필: 독립적으로 운영 중

📊 백테스트 결과:
• Price Correlation: -0.0638 (역매매 전략)
• Volatility Correlation: 0.1054 (변동성 예측)

🌐 서비스 상태:
• API Server: ✅ 정상
• Virtuals Agent: ✅ 연결됨
```

---

## 🔧 커스터마이징

### 알림 빈도 조정
- 일일 리포트: `0 9 * * *` (매일 오전 9시)
- 시간별 체크: `0 * * * *` (매 시간)
- 30분마다: `*/30 * * * *`

### 메시지 내용 수정
`telegram_notifier.py` 파일의 메시지 템플릿 수정

---

## ✅ 확인 사항

1. **텔레그램 봇 토큰**: `***REDACTED_TELEGRAM***`
2. **Chat ID**: `1629086047`
3. **API 엔드포인트**: `http://15.165.210.0:8000/health`

---

## 🎯 다음 단계

1. VPS에서 cron 작업 설정
2. 첫 알림 수신 확인
3. 필요시 메시지 커스터마이징
