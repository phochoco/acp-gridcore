#!/bin/bash

# Trinity ACP Agent - systemd 서비스 설치 스크립트

echo "🚀 Installing Trinity ACP systemd services..."

# 1. API 서버 서비스 설치
echo "📦 Installing API Server service..."
sudo cp trinity-acp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trinity-acp.service
echo "✅ API Server service installed"

# 2. Virtuals Agent 서비스 설치
echo "📦 Installing Virtuals Agent service..."
sudo cp trinity-acp-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trinity-acp-agent.service
echo "✅ Virtuals Agent service installed"

# 3. 서비스 시작
echo ""
echo "🎯 Starting services..."
sudo systemctl start trinity-acp.service
sudo systemctl start trinity-acp-agent.service

# 4. 상태 확인
echo ""
echo "📊 Service Status:"
echo ""
echo "=== API Server ==="
sudo systemctl status trinity-acp.service --no-pager -l
echo ""
echo "=== Virtuals Agent ==="
sudo systemctl status trinity-acp-agent.service --no-pager -l

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Useful commands:"
echo "  - Check API Server: sudo systemctl status trinity-acp"
echo "  - Check Agent: sudo systemctl status trinity-acp-agent"
echo "  - View API logs: sudo journalctl -u trinity-acp -f"
echo "  - View Agent logs: sudo journalctl -u trinity-acp-agent -f"
echo "  - Restart API: sudo systemctl restart trinity-acp"
echo "  - Restart Agent: sudo systemctl restart trinity-acp-agent"
