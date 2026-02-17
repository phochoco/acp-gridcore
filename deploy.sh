#!/bin/bash
# Trinity ACP Agent - 자동 배포 스크립트
# VPS 서버에서 실행

set -e  # 에러 발생 시 중단

echo "🚀 Trinity ACP Agent 배포 시작..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 시스템 업데이트
echo -e "${YELLOW}[1/8] 시스템 업데이트...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. 필수 도구 설치
echo -e "${YELLOW}[2/8] 필수 도구 설치...${NC}"
sudo apt install -y python3-pip python3-venv git

# 3. 프로젝트 디렉토리 생성
echo -e "${YELLOW}[3/8] 프로젝트 디렉토리 설정...${NC}"
cd ~
if [ -d "trinity-acp-agent" ]; then
    echo "기존 디렉토리 발견. 백업 중..."
    mv trinity-acp-agent trinity-acp-agent.backup.$(date +%Y%m%d_%H%M%S)
fi

# GitHub에서 클론 (또는 수동 업로드)
# git clone https://github.com/YOUR_USERNAME/trinity-acp-agent.git
# cd trinity-acp-agent

# 4. 가상 환경 생성
echo -e "${YELLOW}[4/8] 가상 환경 생성...${NC}"
python3 -m venv venv
source venv/bin/activate

# 5. 의존성 설치
echo -e "${YELLOW}[5/8] 의존성 설치...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 6. 환경 변수 설정
echo -e "${YELLOW}[6/8] 환경 변수 설정...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  .env 파일을 편집하여 API 키를 입력하세요:"
    echo "   nano .env"
    read -p "Enter를 눌러 계속..."
fi

# 7. systemd 서비스 설정
echo -e "${YELLOW}[7/8] systemd 서비스 설정...${NC}"
sudo cp trinity-acp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trinity-acp.service
sudo systemctl start trinity-acp.service

# 8. 상태 확인
echo -e "${YELLOW}[8/8] 서비스 상태 확인...${NC}"
sleep 3
sudo systemctl status trinity-acp.service --no-pager

# 헬스체크
echo -e "\n${YELLOW}헬스체크 테스트...${NC}"
sleep 2
curl -s http://localhost:8000/health | python3 -m json.tool || echo "⚠️  서버가 아직 시작 중입니다. 잠시 후 다시 시도하세요."

echo -e "\n${GREEN}✅ 배포 완료!${NC}"
echo -e "\n📊 서비스 정보:"
echo "  - 상태 확인: sudo systemctl status trinity-acp.service"
echo "  - 로그 확인: sudo journalctl -u trinity-acp.service -f"
echo "  - API 테스트: curl http://localhost:8000/health"
echo "  - Swagger UI: http://YOUR_IP:8000/docs"
echo ""
echo "🎉 Trinity ACP Agent가 실행 중입니다!"
