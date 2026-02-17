# Trinity ACP Agent 배포 가이드 🚀

## 📖 구조 이해

### Virtuals Protocol = 메뉴판 (On-Chain)
- **역할**: 에이전트 등록 정보만 저장
- **내용**: 이름, 가격, 지갑 주소, 설명
- **코드**: ❌ 업로드하지 않음

### 내 서버 = 주방 (Off-Chain Worker)
- **역할**: 실제 코드 실행
- **내용**: `acp_agent.py` 24시간 실행
- **작동**: Virtuals 네트워크 감시 → 요청 수신 → 계산 → 결과 반환

💡 **비유**: 배달의민족(Virtuals)에 식당 이름은 올라가지만, 실제 음식(결과)은 사장님 주방(서버)에서 만들어야 함

---

## 🎯 배포 방법 비교

### ❌ 방법 A: 집 PC 켜두기 (비추천)
**장점**:
- 비용 $0

**단점**:
- ⚠️ 정전 시 중단
- ⚠️ 인터넷 끊김 시 중단
- ⚠️ Windows 업데이트 재부팅
- ⚠️ 신뢰도 낮음 (트레이딩 봇에 치명적)

### ✅ 방법 B: 클라우드 VPS (강력 추천)
**장점**:
- ✅ 24시간 365일 안정적
- ✅ 자동 재시작
- ✅ 고정 IP
- ✅ 전문 인프라

**비용**:
- **AWS Lightsail**: $3.5~$5/월 (₩4,500~₩6,500)
- **Vultr**: $5/월 (₩6,500)
- **DigitalOcean**: $6/월 (₩7,800)

---

## 🛠️ VPS 배포 가이드 (AWS Lightsail)

### Step 1: 서버 생성

1. **AWS Lightsail 접속**
   - https://lightsail.aws.amazon.com/

2. **인스턴스 생성**
   - 플랫폼: `Linux/Unix`
   - 블루프린트: `Ubuntu 22.04 LTS`
   - 요금제: `$5/월` (512MB RAM, 1 vCPU)
   - 인스턴스 이름: `trinity-acp-agent`

3. **생성 완료!**
   - 고정 IP 할당 (무료)
   - SSH 키 다운로드

---

### Step 2: 서버 접속

```bash
# Mac/Linux
ssh -i LightsailDefaultKey-ap-northeast-2.pem ubuntu@YOUR_IP

# Windows (PuTTY 사용)
# 1. PuTTY 설치
# 2. .pem → .ppk 변환 (PuTTYgen)
# 3. PuTTY로 접속
```

---

### Step 3: 환경 설정

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. Python 3 설치 확인
python3 --version  # Python 3.10+ 필요

# 3. pip 설치
sudo apt install python3-pip -y

# 4. Git 설치
sudo apt install git -y
```

---

### Step 4: 코드 배포

#### Option A: GitHub 사용 (권장)
```bash
# 1. 로컬에서 GitHub에 푸시
cd /Users/pochoco/Desktop/acp-gridcore
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/trinity-acp-agent.git
git push -u origin main

# 2. 서버에서 클론
cd ~
git clone https://github.com/YOUR_USERNAME/trinity-acp-agent.git
cd trinity-acp-agent
```

#### Option B: 직접 업로드
```bash
# FileZilla 또는 scp 사용
scp -i key.pem -r /Users/pochoco/Desktop/acp-gridcore ubuntu@YOUR_IP:~/
```

---

### Step 5: 의존성 설치

```bash
# 1. 가상 환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
cp .env.example .env
nano .env  # GAME_API_KEY 입력
```

---

### Step 6: 백그라운드 실행

#### Option A: nohup (간단)
```bash
# 백그라운드 실행
nohup python3 acp_agent.py > output.log 2>&1 &

# 프로세스 확인
ps aux | grep acp_agent

# 로그 확인
tail -f output.log

# 종료
pkill -f acp_agent.py
```

#### Option B: systemd (권장 - 자동 재시작)
```bash
# 1. 서비스 파일 생성
sudo nano /etc/systemd/system/trinity-acp.service
```

**파일 내용**:
```ini
[Unit]
Description=Trinity ACP Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trinity-acp-agent
Environment="PATH=/home/ubuntu/trinity-acp-agent/venv/bin"
ExecStart=/home/ubuntu/trinity-acp-agent/venv/bin/python3 acp_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 2. 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable trinity-acp.service
sudo systemctl start trinity-acp.service

# 3. 상태 확인
sudo systemctl status trinity-acp.service

# 4. 로그 확인
sudo journalctl -u trinity-acp.service -f
```

---

### Step 7: 방화벽 설정 (선택)

```bash
# 필요한 포트만 열기
sudo ufw allow ssh
sudo ufw allow 8000/tcp  # API 포트 (FastAPI 사용 시)
sudo ufw enable
```

---

## 🔧 모니터링 및 유지보수

### 로그 확인
```bash
# systemd 사용 시
sudo journalctl -u trinity-acp.service -f

# nohup 사용 시
tail -f output.log
```

### 서비스 재시작
```bash
# systemd
sudo systemctl restart trinity-acp.service

# nohup
pkill -f acp_agent.py
nohup python3 acp_agent.py > output.log 2>&1 &
```

### 코드 업데이트
```bash
# GitHub 사용 시
cd ~/trinity-acp-agent
git pull
sudo systemctl restart trinity-acp.service
```

---

## 💰 비용 최적화

### AWS Lightsail 무료 체험
- **첫 3개월**: $5 크레딧 제공
- **실제 비용**: 3개월 후부터 $5/월

### 더 저렴한 대안
1. **Oracle Cloud Free Tier**: 영구 무료 (제한적)
2. **Google Cloud Free Tier**: $300 크레딧 (90일)
3. **Vultr**: $5/월 (신규 가입 시 $100 크레딧)

---

## 🚀 FastAPI로 API 서버 만들기 (선택)

현재 `acp_agent.py`는 GAME SDK 리스너입니다. 독립 API 서버로도 사용하려면:

```python
# api_server.py
from fastapi import FastAPI
from acp_agent import TrinityACPAgent

app = FastAPI()
agent = TrinityACPAgent()

@app.get("/api/daily-luck")
def get_daily_luck(date: str, birth_data: str = None):
    return agent.get_daily_luck(date, birth_data)

@app.get("/api/verify-accuracy")
def verify_accuracy(force_refresh: bool = False):
    return agent.verify_accuracy(force_refresh)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```bash
# 실행
pip install fastapi uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

---

## ✅ 배포 체크리스트

### 배포 전
- [ ] 로컬에서 테스트 완료
- [ ] `.env` 파일 준비 (API 키)
- [ ] `requirements.txt` 확인
- [ ] GitHub 저장소 생성 (선택)

### 서버 설정
- [ ] VPS 생성 (AWS Lightsail 등)
- [ ] SSH 접속 확인
- [ ] Python 3.10+ 설치
- [ ] 코드 업로드 (Git 또는 SCP)

### 실행
- [ ] 의존성 설치
- [ ] 환경 변수 설정
- [ ] systemd 서비스 등록
- [ ] 서비스 시작 및 확인

### 모니터링
- [ ] 로그 확인
- [ ] 에러 없는지 확인
- [ ] 메모리/CPU 사용량 확인

---

## 🎯 최종 권장사항

### 즉시 시작 (로컬 테스트)
```bash
cd /Users/pochoco/Desktop/acp-gridcore
python3 acp_agent.py
```

### 프로덕션 배포 (VPS)
1. **AWS Lightsail** $5/월 서버 생성
2. **systemd**로 자동 재시작 설정
3. **GitHub**로 코드 관리
4. **CloudWatch** 또는 **Uptime Robot**으로 모니터링

### 비용 예상
- **서버**: $5/월 (₩6,500)
- **도메인**: $10/년 (선택)
- **총**: **월 ₩6,500** 🎉

---

## 📞 문제 해결

### 서비스가 시작되지 않음
```bash
# 로그 확인
sudo journalctl -u trinity-acp.service -n 50

# 권한 확인
ls -la /home/ubuntu/trinity-acp-agent

# 수동 실행 테스트
cd ~/trinity-acp-agent
source venv/bin/activate
python3 acp_agent.py
```

### 메모리 부족
```bash
# 메모리 사용량 확인
free -h

# swap 추가 (1GB)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 🎉 완료!

이제 Trinity ACP Agent가 24시간 안정적으로 작동합니다!

**다음 단계**:
1. Virtuals Console에서 지갑 연결
2. Agent 등록 (이름, 가격, 서버 주소)
3. 마케팅 시작!
