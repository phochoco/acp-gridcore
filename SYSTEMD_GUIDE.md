# systemd 서비스 설치 가이드

## 🎯 목표
Trinity ACP Agent를 systemd 서비스로 등록하여 24시간 자동 실행 및 재부팅 시 자동 시작

---

## 📋 준비사항

VPS 터미널에서 현재 실행 중인 Agent를 종료합니다:

```bash
# 현재 실행 중인 Agent 종료 (Ctrl+C)
# 또는 다른 터미널에서:
pkill -f acp_agent.py
pkill -f api_server.py
```

---

## 🚀 설치 방법

### 1. GitHub에서 최신 코드 받기

```bash
cd ~/acp-gridcore
git pull
```

### 2. 자동 설치 스크립트 실행

```bash
chmod +x install_services.sh
./install_services.sh
```

이 스크립트는 다음을 수행합니다:
- ✅ API 서버 서비스 설치 (`trinity-acp.service`)
- ✅ Virtuals Agent 서비스 설치 (`trinity-acp-agent.service`)
- ✅ 서비스 자동 시작 설정
- ✅ 서비스 시작

---

## 📊 서비스 상태 확인

### API 서버 상태
```bash
sudo systemctl status trinity-acp
```

### Virtuals Agent 상태
```bash
sudo systemctl status trinity-acp-agent
```

### 로그 확인 (실시간)
```bash
# API 서버 로그
sudo journalctl -u trinity-acp -f

# Virtuals Agent 로그
sudo journalctl -u trinity-acp-agent -f
```

---

## 🔧 서비스 관리 명령어

### 서비스 시작
```bash
sudo systemctl start trinity-acp          # API 서버
sudo systemctl start trinity-acp-agent    # Virtuals Agent
```

### 서비스 중지
```bash
sudo systemctl stop trinity-acp
sudo systemctl stop trinity-acp-agent
```

### 서비스 재시작
```bash
sudo systemctl restart trinity-acp
sudo systemctl restart trinity-acp-agent
```

### 자동 시작 활성화/비활성화
```bash
# 활성화 (재부팅 시 자동 시작)
sudo systemctl enable trinity-acp
sudo systemctl enable trinity-acp-agent

# 비활성화
sudo systemctl disable trinity-acp
sudo systemctl disable trinity-acp-agent
```

---

## 📝 로그 파일 위치

- **API 서버**: `~/acp-gridcore/api_server.log`
- **Virtuals Agent**: `~/acp-gridcore/agent.log`

```bash
# 로그 파일 확인
tail -f ~/acp-gridcore/api_server.log
tail -f ~/acp-gridcore/agent.log
```

---

## ✅ 설치 확인

### 1. 서비스 상태 확인
```bash
sudo systemctl status trinity-acp trinity-acp-agent
```

**예상 출력**:
```
● trinity-acp.service - Trinity ACP Agent API Server
   Loaded: loaded (/etc/systemd/system/trinity-acp.service; enabled)
   Active: active (running) since ...

● trinity-acp-agent.service - Trinity ACP Virtuals Agent
   Loaded: loaded (/etc/systemd/system/trinity-acp-agent.service; enabled)
   Active: active (running) since ...
```

### 2. API 엔드포인트 테스트
```bash
curl http://localhost:8000/health
```

**예상 출력**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-18T04:55:00"
}
```

### 3. Virtuals Agent 연결 확인
```bash
sudo journalctl -u trinity-acp-agent -n 20
```

**예상 출력**:
```
✅ GAME SDK initialized: Trinity_Alpha_Oracle
✅ Agent registered with Virtuals Protocol
✅ Agent is ready to receive requests from GAME platform...
```

---

## 🎉 완료!

이제 Trinity ACP Agent가 24시간 자동으로 실행됩니다:
- ✅ 재부팅 시 자동 시작
- ✅ 에러 발생 시 자동 재시작 (10초 후)
- ✅ 백그라운드 실행
- ✅ 로그 자동 저장

---

## 🔍 문제 해결

### 서비스가 시작되지 않을 때

1. **로그 확인**:
```bash
sudo journalctl -u trinity-acp-agent -n 50
```

2. **권한 확인**:
```bash
ls -la ~/acp-gridcore/acp_agent.py
```

3. **가상환경 확인**:
```bash
ls -la ~/acp-gridcore/venv/bin/python3
```

4. **수동 실행 테스트**:
```bash
cd ~/acp-gridcore
source venv/bin/activate
python3 acp_agent.py
```

### 포트 충돌

API 서버가 시작되지 않으면 포트 8000이 이미 사용 중일 수 있습니다:

```bash
# 포트 사용 확인
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 <PID>
```

---

## 📞 지원

문제가 발생하면 로그를 확인하고 GitHub Issues에 보고해주세요.
