# VPS 배포 단계별 가이드 🚀

## 📋 배포 전 준비사항

### 1. 로컬 환경 확인 ✅
- [x] 모든 코드 작성 완료
- [x] 테스트 통과 (7/7)
- [x] 환경 변수 설정
- [x] .gitignore 확인

### 2. VPS 선택
추천 옵션 (가격 순):

| 서비스 | 가격 | 스펙 | 추천도 |
|--------|------|------|--------|
| AWS Lightsail | $5/월 | 512MB RAM, 1 vCPU | ⭐⭐⭐⭐⭐ |
| Vultr | $5/월 | 1GB RAM, 1 vCPU | ⭐⭐⭐⭐ |
| DigitalOcean | $6/월 | 1GB RAM, 1 vCPU | ⭐⭐⭐⭐ |
| Oracle Cloud | 무료 | 1GB RAM, 1 vCPU | ⭐⭐⭐ (설정 복잡) |

**권장**: AWS Lightsail (간단하고 안정적)

---

## 🎯 Step 1: AWS Lightsail 서버 생성

### 1.1 AWS 계정 생성
1. https://aws.amazon.com/lightsail/ 접속
2. "무료로 시작하기" 클릭
3. 이메일/비밀번호 입력
4. 결제 정보 입력 (첫 3개월 무료 크레딧)

### 1.2 인스턴스 생성
```
1. Lightsail 콘솔 접속
2. "인스턴스 생성" 클릭
3. 설정:
   - 플랫폼: Linux/Unix
   - 블루프린트: Ubuntu 22.04 LTS
   - 요금제: $5/월 (512MB RAM)
   - 인스턴스 이름: trinity-acp-agent
4. "인스턴스 생성" 클릭
```

### 1.3 고정 IP 할당 (무료)
```
1. "네트워킹" 탭 클릭
2. "고정 IP 생성" 클릭
3. 인스턴스 선택: trinity-acp-agent
4. 이름: trinity-acp-ip
5. "생성" 클릭
```

### 1.4 방화벽 설정
```
1. 인스턴스 클릭
2. "네트워킹" 탭
3. "규칙 추가":
   - 애플리케이션: Custom
   - 프로토콜: TCP
   - 포트: 8000
   - 저장
```

---

## 🔧 Step 2: 서버 접속 및 환경 설정

### 2.1 SSH 접속
```bash
# Mac/Linux
ssh -i LightsailDefaultKey-ap-northeast-2.pem ubuntu@YOUR_IP

# Windows (PuTTY)
# 1. PuTTY 설치
# 2. .pem → .ppk 변환 (PuTTYgen)
# 3. PuTTY로 접속
```

### 2.2 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Python 및 필수 도구 설치
```bash
# Python 3 확인
python3 --version  # 3.10+ 필요

# pip 설치
sudo apt install python3-pip python3-venv -y

# Git 설치
sudo apt install git -y
```

---

## 📦 Step 3: 코드 배포

### 3.1 GitHub 저장소 생성 (권장)

#### 로컬에서 작업
```bash
cd /Users/pochoco/Desktop/acp-gridcore

# Git 초기화
git init

# .gitignore 확인 (.env가 포함되어 있는지)
cat .gitignore

# 커밋
git add .
git commit -m "Initial commit: Trinity ACP Agent v1.0"

# GitHub 저장소 생성 후
git remote add origin https://github.com/YOUR_USERNAME/trinity-acp-agent.git
git branch -M main
git push -u origin main
```

#### 서버에서 클론
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/trinity-acp-agent.git
cd trinity-acp-agent
```

### 3.2 직접 업로드 (대안)
```bash
# 로컬에서 실행
scp -i key.pem -r /Users/pochoco/Desktop/acp-gridcore ubuntu@YOUR_IP:~/trinity-acp-agent
```

---

## ⚙️ Step 4: 서버 설정

### 4.1 가상 환경 생성
```bash
cd ~/trinity-acp-agent
python3 -m venv venv
source venv/bin/activate
```

### 4.2 의존성 설치
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env
nano .env

# 내용 입력:
GAME_API_KEY=apt-a842d80e4cf1024d250f08c8a1445211
BASE_PRIVATE_KEY=your_private_key_here  # 필요시
CACHE_TTL_SECONDS=3600
MAX_RESPONSE_TIME=2.0

# 저장: Ctrl+X, Y, Enter
```

### 4.4 테스트 실행
```bash
# 서버 테스트
python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000

# 다른 터미널에서 테스트
curl http://YOUR_IP:8000/health

# 잘 작동하면 Ctrl+C로 종료
```

---

## 🔄 Step 5: systemd 서비스 설정 (자동 재시작)

### 5.1 서비스 파일 생성
```bash
sudo nano /etc/systemd/system/trinity-acp.service
```

### 5.2 서비스 파일 내용
```ini
[Unit]
Description=Trinity ACP Agent API Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trinity-acp-agent
Environment="PATH=/home/ubuntu/trinity-acp-agent/venv/bin"
ExecStart=/home/ubuntu/trinity-acp-agent/venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/trinity-acp-agent/api_server.log
StandardError=append:/home/ubuntu/trinity-acp-agent/api_server.log

[Install]
WantedBy=multi-user.target
```

### 5.3 서비스 활성화
```bash
# 서비스 등록
sudo systemctl daemon-reload
sudo systemctl enable trinity-acp.service

# 서비스 시작
sudo systemctl start trinity-acp.service

# 상태 확인
sudo systemctl status trinity-acp.service

# 로그 확인
sudo journalctl -u trinity-acp.service -f
```

---

## 🔍 Step 6: 모니터링 설정

### 6.1 헬스체크 Cron 설정
```bash
# Cron 편집
crontab -e

# 5분마다 헬스체크 (선택 1번 에디터)
*/5 * * * * /home/ubuntu/trinity-acp-agent/venv/bin/python /home/ubuntu/trinity-acp-agent/health_check.py http://localhost:8000/health >> /home/ubuntu/health_check.log 2>&1
```

### 6.2 Uptime Robot 설정 (무료)
```
1. https://uptimerobot.com/ 가입
2. "Add New Monitor" 클릭
3. 설정:
   - Monitor Type: HTTP(s)
   - Friendly Name: Trinity ACP Agent
   - URL: http://YOUR_IP:8000/health
   - Monitoring Interval: 5 minutes
4. 알림 이메일 설정
5. "Create Monitor" 클릭
```

---

## 🌐 Step 7: 도메인 연결 (선택)

### 7.1 도메인 구매
- Namecheap: $10/년
- GoDaddy: $12/년
- Cloudflare: $9/년

### 7.2 DNS 설정
```
A 레코드 추가:
- Name: api (또는 @)
- Value: YOUR_IP
- TTL: 자동
```

### 7.3 Nginx 리버스 프록시 (선택)
```bash
# Nginx 설치
sudo apt install nginx -y

# 설정 파일 생성
sudo nano /etc/nginx/sites-available/trinity-acp
```

**설정 내용**:
```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/trinity-acp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## ✅ Step 8: 최종 검증

### 8.1 API 테스트
```bash
# 헬스체크
curl http://YOUR_IP:8000/health

# 일일 운세
curl -X POST http://YOUR_IP:8000/api/v1/daily-luck \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-02-20"}'

# Swagger UI 접속
# http://YOUR_IP:8000/docs
```

### 8.2 서비스 상태 확인
```bash
# 서비스 상태
sudo systemctl status trinity-acp.service

# 로그 확인
tail -f ~/trinity-acp-agent/api_server.log

# 프로세스 확인
ps aux | grep uvicorn
```

---

## 🎯 배포 완료 체크리스트

### 서버 설정
- [ ] AWS Lightsail 인스턴스 생성
- [ ] 고정 IP 할당
- [ ] 방화벽 포트 8000 열기
- [ ] SSH 접속 확인

### 코드 배포
- [ ] GitHub 저장소 생성
- [ ] 코드 클론 또는 업로드
- [ ] 가상 환경 생성
- [ ] 의존성 설치
- [ ] 환경 변수 설정

### 서비스 설정
- [ ] systemd 서비스 파일 생성
- [ ] 서비스 활성화
- [ ] 서비스 시작
- [ ] 자동 재시작 확인

### 모니터링
- [ ] 헬스체크 Cron 설정
- [ ] Uptime Robot 설정 (선택)
- [ ] 로그 확인

### 최종 검증
- [ ] API 엔드포인트 테스트
- [ ] Swagger UI 접속
- [ ] 24시간 안정성 확인

---

## 🔧 유지보수

### 코드 업데이트
```bash
# 서버 접속
ssh ubuntu@YOUR_IP

# 코드 업데이트
cd ~/trinity-acp-agent
git pull

# 서비스 재시작
sudo systemctl restart trinity-acp.service

# 상태 확인
sudo systemctl status trinity-acp.service
```

### 로그 확인
```bash
# API 로그
tail -f ~/trinity-acp-agent/api_server.log

# systemd 로그
sudo journalctl -u trinity-acp.service -f

# 헬스체크 로그
tail -f ~/health_check.log
```

### 문제 해결
```bash
# 서비스 재시작
sudo systemctl restart trinity-acp.service

# 서비스 중지
sudo systemctl stop trinity-acp.service

# 서비스 시작
sudo systemctl start trinity-acp.service

# 로그 확인
sudo journalctl -u trinity-acp.service -n 100
```

---

## 💰 비용 정리

| 항목 | 비용 | 비고 |
|------|------|------|
| AWS Lightsail | $5/월 | 첫 3개월 무료 크레딧 |
| 도메인 (선택) | $10/년 | Namecheap 기준 |
| **총계** | **₩6,500/월** | 도메인 제외 |

---

## 🎉 완료!

축하합니다! Trinity ACP Agent가 24시간 안정적으로 작동합니다!

**다음 단계**:
1. Virtuals Console에서 Agent 등록
2. 마케팅 시작
3. 수익 창출!
