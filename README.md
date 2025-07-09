# CreditPulse 💳📈
![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/creditpulse?color=blueviolet)
![GitHub license](https://img.shields.io/github/license/yourusername/creditpulse?color=success)
![Flutter](https://img.shields.io/badge/Flutter-3.13-blue?logo=flutter)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)

**Transform email/SMS financial data into actionable insights**  
*A smart financial assistant that automatically analyzes credit card statements and payment reminders*

---

## ✨ Features

<div style="display: flex; flex-wrap: wrap; gap: 10px;">
  <div>
    <h4>🔍 Automated Tracking</h4>
    <ul>
      <li>Gmail API integration</li>
      <li>SMS payment parsing</li>
    </ul>
  </div>
  <div>
    <h4>📊 Smart Dashboard</h4>
    <ul>
      <li>Spending categorization</li>
      <li>Credit utilization charts</li>
    </ul>
  </div>
  <div>
    <h4>⏰ Proactive Alerts</h4>
    <ul>
      <li>Payment reminders</li>
      <li>Unusual spending detection</li>
    </ul>
  </div>
</div>

---
<div style="display: flex; gap: 10px; overflow-x: auto;"> <img src="screenshots/dashboard.png" width="200" alt="Dashboard"> <img src="screenshots/analysis.png" width="200" alt="Spending Analysis"> <img src="screenshots/alerts.png" width="200" alt="Payment Alerts"> </div>

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Flutter 3.13+
- Google Cloud Platform account (for Gmail API
  
graph TD
    A[User Device] --> B[Gmail API]
    A --> C[SMS Manager]
    B --> D[Local Processing]
    C --> D
    D --> E[Encrypted Storage]
  
### Installation

Frontend (Flutter)
cd credit-pulse
flutter pub get

# For Android
flutter build apk --release

# For iOS
flutter build ios --release

#### Backend (Python)
```bash
cd backend
pip install -r requirements.txt
python main.py
