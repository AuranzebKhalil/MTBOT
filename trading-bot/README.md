# 🛡️ MTBOT | Advanced Algorithmic Trading Suite

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-MetaTrader%205-orange.svg)

**MTBOT** is a professional-grade, institutional-inspired algorithmic trading platform. It combines a high-performance Python backend with a stunning, modern Next.js dashboard to provide real-time market analysis, automated trade execution, and comprehensive strategy management.

---

## ✨ Key Features

### 🤖 Intelligent Trading Engine
- **Hybrid Strategy Logic:** Optimized (April 2026) to prioritize high-probability structural setups (SMC) while excluding noisy M1 reversals and fakeouts.
- **Advanced Indicator Suite:** Integrated custom indicators including LYRO RS, Bollinger Bands, RSI, and Multi-Timeframe Volume Analysis.
- **Support for High Probability:** For detailed setup criteria and refinement history, see [STRATEGIES.md](file:///c:/Users/Auranzeb%20Khalil/OneDrive/Desktop/My%20project/trading-bot/STRATEGIES.md).
- **Risk Management:** Institutional-grade risk filters, including ADR-based stop losses, partial profit-taking (staged execution), and post-loss cooldown periods.

### 📊 Professional Dashboard
- **Glassmorphic UI:** A premium, dark-mode interface built with high-fidelity aesthetics.
- **Real-Time Monitoring:** Live tracking of bot status, active positions, and AI confidence levels.
- **Strategy Analytics:** Detailed performance breakdown of different strategy families.

### 🛡️ Secure Infrastructure
- **Role-Based Access:** Multi-level user access (User, Admin, Superadmin).
- **Database Flexibility:** Developed with SQLite for zero-config local setup, fully compatible with PostgreSQL for cloud scale.
- **Support System:** Integrated ticketing system for enterprise-level user management.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 14, React, Tailwind CSS, Lucide Icons |
| **Backend** | FastAPI, Python 3.10+, SQLAlchemy |
| **Database** | SQLite (Local) / PostgreSQL (Production) |
| **Execution** | MetaTrader 5 Python Integration |
| **Analytics** | Pandas, NumPy, Scikit-learn, TensorFlow |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- MetaTrader 5 Terminal (installed and running on Windows)

### 1. Backend Setup
```bash
cd trading-bot/backend
python -m venv venv
source venv/bin/scripts/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
python start.py
```

### 2. Frontend Setup
```bash
cd trading-bot/frontend
npm install
npm run dev
```

### 3. Environment Configuration
Create a `.env` file in the `backend` directory:
```env
DATABASE_URL=sqlite:///./alertli.db
SECRET_KEY=your_secure_random_key
MT5_LOGIN=your_mt5_account
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
```

---

## 📈 Deployment

For production deployment, we recommend the following free-tier stack:
- **Backend:** [Render](https://render.com) (Python Web Service)
- **Frontend:** [Vercel](https://vercel.com) (Next.js)
- **Database:** [Neon.tech](https://neon.tech) (PostgreSQL)

> [!IMPORTANT]
> Since this bot uses the official `MetaTrader5` library, it must be hosted on a **Windows-based server** (VPS) to communicate with the MT5 terminal.

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License.

---

Developed with ❤️ by **Auranzeb Khalil**
