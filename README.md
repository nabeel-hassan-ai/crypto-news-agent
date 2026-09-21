# ⚡ Crypto News Trading AI Agent & Intelligence Dashboard

An institutional-grade crypto news trading assistant and market intelligence dashboard. It aggregates macro economic catalysts and breaking crypto news from all 12 key sources (ForexFactory, CryptoCraft, CoinMarketCal, WatcherGuru, CoinDesk, Cointelegraph, CryptoSlate, CryptoPotato, Binance News, etc.), analyzes market impact, flags dangerous volatility zones, and provides clear directional bias (Long/Short/Wait) with actionable risk management rules.

---

## 🚀 How to Run in Visual Studio Code (VS Code)

### Step 1: Open the Project in VS Code
1. Open **Visual Studio Code**.
2. Click **File** -> **Open Folder...** (یا شارٹ کٹ `Ctrl + K, Ctrl + O`).
3. اس فولڈر کے پاتھ کو سلیکٹ کریں:
   ```
   C:\Users\Nabeel\.gemini\antigravity\scratch\crypto_news_trading_agent
   ```
4. Click **Select Folder**.

---

### Step 2: Open Terminal in VS Code
1. VS Code کے اوپر مینو سے **Terminal** -> **New Terminal** پر کلک کریں (یا کی بورڈ سے دبایں: `` Ctrl + ` ``).
2. ٹرمینل میں چیک کریں کہ آپ اسی فولڈر میں موجود ہیں۔

---

### Step 3: Verify Dependencies (Already installed on your system)
تمام بنیادی لائبریریز پہلے سے انسٹال ہیں، لیکن اگر دوبارہ چیک کرنا چاہیں تو ٹرمینل میں یہ کمانڈ چلائیں:
```bash
pip install -r requirements.txt
```

---

### Step 4: Run the AI Agent Dashboard
ٹرمینل میں بس یہ کمانڈ انٹر کریں:
```bash
python -m streamlit run app.py
```

چند سیکنڈز میں آپ کا براؤزر خودکار طور پر کھل جائے گا اور لوکل ایڈریس پر ڈیش بورڈ نظر آئے گا:
```
http://localhost:8501
```

---

## 🔑 AI Reasoning Mode (Gemini API - Optional)
- **Built-in Offline Rule Engine**: اگر آپ کوئی API key نہیں ڈالتے، تب بھی سسٹم ہائی امپیکٹ ایونٹس، کی ورڈز اور میکرو ڈیٹا کی بنیاد پر مکمل رپورٹ جنریٹ کرے گا۔
- **Google Gemini Integration**: گہری نیورل اینالسس کے لیے آپ [Google AI Studio](https://aistudio.google.com/) سے فری API Key حاصل کر کے ڈیش بورڈ کی سائڈ بار میں پیسٹ کر سکتے ہیں۔

---

## 🎯 How to Use
1. اوپر دائیں جانب موجود بڑے بٹن **"⚡ Run Deep Market & News Research"** پر کلک کریں۔
2. چند سیکنڈز میں سسٹم تمام 12 ویب سائٹس اسکین کر کے یہ چیزیں فراہم کرے گا:
   - **Directional Bias**: BULLISH (LONG) / BEARISH (SHORT) / VOLATILE (WAIT).
   - **Risk Alert**: اگر CPI یا FOMC کا کوئی ہائی امپیکٹ ایونٹ قریب ہے تو نو-ٹریڈ زون کی وارننگ۔
   - **Execution Playbook**: انٹری کب لینی ہے، کون سی کینڈل کلوز کا انتظار کرنا ہے، اور کتنا لیوریج رکھنا ہے۔
   - **Macro Calendar Table**: ForexFactory اور CryptoCraft کا شیڈول۔
   - **Breaking News Wire**: تمام ویب سائٹس کی فلٹر شدہ خبریں اور لنکس۔
