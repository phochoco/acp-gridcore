# Trinity ACP Agent

**AI-powered trading luck calculator based on Eastern Metaphysics (Saju)**

> *"Powered by Math, Guided by Philosophy."*

An independent API server providing quantified "Trading Luck" scores for crypto trading bots, built on the Virtuals Protocol (Agent Commerce Protocol).

[🇰🇷 한국어 README](README_KR.md)

---

## 🎯 Overview

Trinity ACP Agent is a quantitative oracle that translates traditional Eastern metaphysics into actionable data. It provides a normalized "Luck Score" (0.0 - 1.0) to help trading bots manage risk and select sectors.

### Key Features

- **Daily Trading Luck Score**: Normalized score (0.0~1.0) indicating the day's energy
- **Crypto-Native Sectors**: Sector recommendations based on the Five Elements (Wood, Fire, Earth, Metal, Water)
- **Volatility Index**: Market volatility prediction based on metaphysical patterns
- **Backtest Verification**: Correlation verified with 412 days of real BTC market data
- **REST API**: Fast & Lightweight HTTP API (FastAPI)
- **Swagger UI**: Auto-generated API documentation at `/docs`

### Performance Matrix

| Metric | Value | Methodology |
|--------|-------|-------------|
| **Volatility Correlation** | **0.108** | Yahoo Finance (N=412 days), Pearson |
| **Statistical Significance** | **p < 0.05** | Orthogonal Alpha (Uncorrelated with RSI/MACD) |
| **Latency** | ~10ms | FastAPI + Caching |
| **Data Source** | Yahoo Finance | Free, no API key required |

---

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/phochoco/acp-gridcore.git
cd acp-gridcore

pip install -r requirements.txt

cp .env.example .env
# Set GAME_API_KEY in .env
```

### 2. Run Server

```bash
# Development
uvicorn api_server:app --reload

# Production
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 1
```

### 3. Test API

```bash
# Swagger UI
open http://localhost:8000/docs

# Health Check
curl http://localhost:8000/health

# Daily Luck
curl -X POST http://localhost:8000/api/v1/daily-luck \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-02-20"}'
```

---

## 📡 API Endpoints

### POST /api/v1/daily-luck

**Request:**
```json
{
  "target_date": "2026-02-20",
  "user_birth_data": "1990-05-15 14:30"
}
```

**Response:**
```json
{
  "trading_luck_score": 0.71,
  "favorable_sectors": ["NEW_LISTING", "GAMEFI", "NFT"],
  "volatility_index": "HIGH",
  "market_sentiment": "VOLATILE",
  "wealth_opportunity": "HIGH"
}
```

### POST /api/v1/verify-accuracy

**Response:**
```json
{
  "correlation_volatility": 0.108,
  "correlation_price": 0.066,
  "sample_size": 412,
  "data_source": "Yahoo Finance (yfinance)"
}
```

**Full API Docs**: [API_GUIDE.md](API_GUIDE.md)

> 💡 **Pro Tip**: Need precise entry timing? Use `/api/v1/deep-luck` ($0.50).
> It analyzes the full 24-hour cycle to find the **"Golden Time"** for max alpha.
> Basic gives you the day's weather. Pro gives you the exact hour of the storm.

### POST /api/v1/deep-luck ⭐ Pro Plan ($0.50)

**Full Four Pillars (사주팔자) analysis** — Hour pillar included for precise entry timing.

**Request:**
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "target_date": "2026-02-18",
  "gender": "M"
}
```

**Response:**
```json
{
  "meta": {
    "target_date": "2026-02-18",
    "algorithm": "Gridcore_Saju_Hourly_V1",
    "process_time_ms": 2
  },
  "strategy": {
    "action": "WAIT_UNTIL_1300",
    "best_window": "13:00~15:00",
    "max_score": 0.75,
    "pro_tip": "Golden Cross at 13:00. Low clash risk + peak luck. Ideal entry."
  },
  "hourly_analysis": {
    "max_score": 0.75,
    "min_score": 0.31,
    "spread": 0.44,
    "volatility_warning": "00:00~02:00 (Score 0.31, Clash detected ⚠️)"
  },
  "hourly_forecast": [
    {
      "time": "13:00",
      "score": 0.75,
      "element": "Wood",
      "signal": "STRONG_BUY",
      "reason": "Growth energy aligns with market expansion.",
      "is_golden": true
    },
    {
      "time": "00:00",
      "score": 0.31,
      "element": "Earth",
      "signal": "AVOID",
      "reason": "Clash detected (충) — High volatility and reversal risk.",
      "is_golden": false
    }
  ]
}
```

| Signal | Score Range | Action |
|--------|-------------|--------|
| `STRONG_BUY` | ≥ 0.80 | Full position |
| `BUY` | 0.65~0.79 | Normal entry |
| `NEUTRAL` | 0.50~0.64 | Wait & watch |
| `CAUTION` | 0.40~0.49 | Reduce size |
| `AVOID` | < 0.40 | No trade |
| `DO_NOT_TRADE` | All < 0.60 | Rest today |

---

## 🔬 Engine Philosophy: Science + Art

```
                    ⭐ Bitcoin Genesis
                  (2009-01-04 03:15 KST)
                     The Origin Point

         🌳 Wood                  🔥 Fire
      NEW_LISTING               MEME / AI
        GAMEFI                  VOLATILE
          NFT
                  ┌───────────┐
                  │  🔬 ENGINE  │
  💧 Water        │  Volatility │    ⛰️ Earth
  DEFI / DEX     │  corr=0.108 │  INFRA / L1 / BTC
  LIQUIDITY      │  N=412 days │
                  └───────────┘
                        🪙 Metal
                    RWA / STABLECOIN

  ←──────── 🎨 ART (Heuristic) ────────→
  ←──────── 🔬 SCIENCE (Backtested) ───→
```

| Component | Type | Methodology | Role |
|-----------|------|-------------|------|
| Volatility | 🔬 Science | N=412, p<0.05 | "When to enter?" (Timing / Risk) |
| Sectors | 🎨 Art | Five Elements Logic | "What to buy?" (Selection) |

> **Risk management is Science. Sector selection is Art.**
> We provide mathematically verified volatility signals and logic-based sector rotation.

---

## 📊 Sector Mapping (Five Elements)

| Element | Crypto Sectors | Characteristics | Logic |
|---------|---------------|-----------------|-------|
| 🔥 Fire | MEME, AI, VOLATILE | Explosive, Fast | Fire = speed and heat |
| ⛰️ Earth | INFRA, LAYER1, BTC | Foundation, Stable | Earth = center and base |
| 💧 Water | DEFI, EXCHANGE, LIQUIDITY | Liquidity, Flow | Water = flow and circulation |
| 🪙 Metal | RWA, STABLECOIN | Store of Value | Metal = hardness and value |
| 🌳 Wood | NEW_LISTING, GAMEFI, NFT | Growth, New | Wood = sprouts and beginning |

> ⚠️ **Transparency**: Sector mapping is a **Logic-based Heuristic** grounded in Five Elements theory.
> The Volatility Correlation (0.108) is statistically verified. Sector performance backtests are scheduled for **V2**.

---

## 🎯 Integration Examples

### 🚀 [Recommended] Virtuals GAME SDK (No server setup required)

```python
# Connect using Project ID only
# Project ID: e8d1733f-9769-4590-bab0-776115e715a7
# Find Trinity_Alpha_Oracle on the Virtuals marketplace and send a request
```

### 🔌 Direct REST API (Python)

```python
import requests

BASE_URL = "http://YOUR_SERVER_IP:8000"  # or use the hosted endpoint

response = requests.post(
    f"{BASE_URL}/api/v1/daily-luck",
    json={"target_date": "2026-02-20"}
)
data = response.json()

# Simple bot logic (one if-statement integration)
if data["trading_luck_score"] >= 0.7:
    # Sector filter (Five Elements logic)
    if "NEW_LISTING" in data["favorable_sectors"]:
        bet_size = 1000  # High confidence: 2x normal size
    else:
        bet_size = 500

    # Volatility risk adjustment
    if data["volatility_index"] == "HIGH":
        bet_size = bet_size * 0.5  # Reduce leverage on high volatility days

    execute_trade(bet_size)
```

### JavaScript

```javascript
const BASE_URL = "http://YOUR_SERVER_IP:8000";

fetch(`${BASE_URL}/api/v1/daily-luck`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({target_date: '2026-02-20'})
})
.then(res => res.json())
.then(data => {
    if (data.trading_luck_score >= 0.7) {
        console.log('✅ Entry Signal! Sectors:', data.favorable_sectors);
    }
});
```

### cURL

```bash
curl -X POST http://YOUR_SERVER_IP:8000/api/v1/daily-luck \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-02-20"}'
```

---

## 🏗️ Project Structure

```
acp-gridcore/
├── api_server.py               # FastAPI REST API server
├── acp_agent.py                # GAME SDK integration
├── trinity_engine_v2.py        # Saju calculation engine
├── backtest_engine.py          # Backtest engine (Yahoo Finance)
├── telegram_notifier.py        # Telegram alert system
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── .env.example                # Environment variable template
└── docs/
    ├── API_GUIDE.md
    ├── VPS_DEPLOYMENT_GUIDE.md
    └── SECURITY_REVIEW.md
```

---

## 📈 Roadmap

### ✅ V1 (Current — Live)
- [x] Trinity Engine V2 (Saju calculation)
- [x] Volatility Backtest — Yahoo Finance, N=412, corr=0.108, p<0.05
- [x] GAME SDK Integration (Trinity_Alpha_Oracle)
- [x] FastAPI REST API Server
- [x] VPS 24/7 Deployment (systemd + Swap)
- [x] HEAD /health support (monitoring bot compatible)

### 🔜 V2 (Upcoming)
- [ ] **Sector Backtest**: Verify "Wood days" vs. NFT/GameFi outperformance
- [ ] Granular scoring (hourly / monthly resolution)
- [ ] Official listing on Virtuals Marketplace
- [ ] Webhook support (push instead of poll)
- [ ] Personalized API (birth date-based custom luck scores)

---

## 💰 Pricing

| Plan | Price | Details |
|------|-------|---------|
| **Direct API** | Free | Self-hosted / Rate limited |
| **Per Call** | $0.01 / call | Paid via Virtuals Protocol |

> **Affordable Alpha**: Independent signals uncorrelated with RSI/MACD — for just $0.01 per call.

---

## 🔒 Security

- ✅ API keys managed via environment variables
- ✅ Sensitive files excluded via `.gitignore`
- ✅ Input validation (Pydantic)
- ✅ Path traversal protection
- ✅ Division by zero protection

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License

MIT License

---

## ⚠️ Disclaimer

This agent provides data for **informational purposes only** and does not constitute financial advice. Past performance does not guarantee future results. Always do your own research (DYOR).

---

## 📞 Support

- **Docs**: [API_GUIDE.md](API_GUIDE.md)
- **Issues**: GitHub Issues
- **Virtuals Protocol**: https://virtuals.io/
