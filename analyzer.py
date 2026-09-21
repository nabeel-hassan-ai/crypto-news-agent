import os
import json
import re
from config import GEMINI_API_KEY, DEFAULT_MODEL

# Try importing Google Generative AI
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class CryptoNewsAnalyzer:
    def __init__(self, api_key: str = None, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name
        self._init_gemini()

    def _init_gemini(self):
        if HAS_GENAI and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.is_active = True
            except Exception as e:
                print(f"Error configuring Gemini: {e}")
                self.is_active = False
        else:
            self.is_active = False

    def analyze(self, collected_data: dict) -> dict:
        """Analyze collected macro, crypto news, and technical analysis."""
        if self.is_active:
            try:
                return self._analyze_with_gemini(collected_data)
            except Exception as e:
                print(f"Gemini analysis error, using rule engine fallback: {e}")
                return self._analyze_heuristically(collected_data, error_note=str(e))
        else:
            return self._analyze_heuristically(collected_data)

    def _analyze_with_gemini(self, data: dict) -> dict:
        """Structured Gemini analysis integrating macro, breaking news, and technical confluence."""
        macro_text = "\n".join([
            f"- [{e.get('country')}] {e.get('date')} {e.get('time')} | Impact: {e.get('impact')} | Event: {e.get('title')} (Forecast: {e.get('forecast')}, Prev: {e.get('previous')})"
            for e in data.get("macro_events", [])[:8]
        ])

        crypto_cal_text = "\n".join([
            f"- [{e.get('country')}] {e.get('date')} {e.get('time')} | Impact: {e.get('impact')} | Event: {e.get('title')}"
            for e in data.get("crypto_calendar_events", [])[:8]
        ])

        news_text = "\n".join([
            f"- [{a.get('source')}] {a.get('title')}: {a.get('summary')[:180]}"
            for a in data.get("news_articles", [])[:18]
        ])

        technicals = data.get("technicals", {})
        tech_text = ""
        for sym, t in technicals.items():
            tech_text += f"- {sym}: Price ${t.get('price', 0):,}, RSI(14) {t.get('rsi')}, EMA9 ${t.get('ema9'):,}, EMA21 ${t.get('ema21'):,}, Support ${t.get('support'):,}, Resistance ${t.get('resistance'):,}, Trend: {t.get('trend')}\n"

        prompt = f"""
You are an institutional Cryptocurrency News Trader, Quantitative Risk Manager, and Technical Analyst.
Evaluate the current market situation by synthesizing real-time Macro Catalysts, Breaking News across 12 tier-1 crypto outlets, and Binance Technical Indicators.

Real-Time Technical Indicators:
{tech_text if tech_text else "N/A"}

High-Impact Macro Releases (ForexFactory - CPI, FOMC, Fed interest rates, NFP):
{macro_text if macro_text else "No immediate high-impact macro releases."}

Upcoming Crypto Calendar Catalysts (CryptoCraft & CoinMarketCal):
{crypto_cal_text if crypto_cal_text else "No major protocol events."}

Breaking Crypto News Headlines:
{news_text if news_text else "No breaking news feeds."}

TASK:
Determine a concrete, actionable Trading Decision (BUY / SELL / WAIT) and technical trade parameters in professional English.

You must return a valid JSON object matching this schema:
{{
  "direct_signal": "BUY NOW (LONG)" | "SELL NOW (SHORT)" | "DO NOT TRADE / WAIT (HIGH RISK)",
  "overall_bias": "BULLISH (LONG)" | "BEARISH (SHORT)" | "VOLATILE / NEUTRAL (WAIT)",
  "confidence_score": 0-100,
  "volatility_risk": "EXTREME RISK (NO-TRADE ZONE)" | "HIGH RISK" | "MODERATE RISK" | "LOW RISK",
  "imminent_danger_warning": "Warning if CPI/FOMC or flash crash event is imminent within 24h, else null",
  "affected_assets": ["BTC", "ETH", "SOL"],
  "signal_summary": "1-2 sentence executive summary of why to BUY, SELL, or WAIT right now.",
  "trade_parameters": {{
    "entry_zone": "e.g., $85,200 - $85,800 or On pullback to EMA21",
    "take_profit_1": "e.g., $87,500",
    "take_profit_2": "e.g., $89,200",
    "stop_loss": "e.g., $84,300 (Below recent 24h swing low)",
    "risk_reward_ratio": "e.g., 1 : 2.5",
    "recommended_leverage": "e.g., Spot or strictly maximum 2x-3x leverage"
  }},
  "technical_confluence": "Detailed analysis of RSI overbought/oversold levels, EMA trend direction, and key Support/Resistance boundaries.",
  "top_news_catalysts": [
    {{
      "headline": "headline",
      "source": "source",
      "impact": "BULLISH" | "BEARISH" | "NEUTRAL",
      "analysis": "trading implication"
    }}
  ],
  "trading_playbook": {{
    "recommended_action": "Clear step-by-step guidance",
    "entry_strategy": "Precise execution trigger",
    "stop_loss_invalidation": "Defensive invalidation rule",
    "whipsaw_alert": "False breakout / liquidity hunt alert"
  }},
  "disclaimer": "Cryptocurrency trading carries substantial financial risk. This is an AI research evaluation and not financial advice."
}}

Respond ONLY with valid JSON.
"""
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    def _analyze_heuristically(self, data: dict, error_note: str = None) -> dict:
        """Heuristic rule-based engine combining News sentiment + Macro Calendar + Binance Technical Indicators."""
        bullish_keywords = [
            "surge", "rally", "record", "soar", "gain", "breakout", "etf approval", "inflow",
            "institutional", "rate cut", "bull", "accumulation", "partnership", "adoption", "upgrade"
        ]
        bearish_keywords = [
            "crash", "plunge", "dump", "ban", "lawsuit", "sec", "investigation", "hack",
            "exploit", "outflow", "bear", "liquidation", "rate hike", "rejection", "stolen", "inflation high"
        ]
        high_volatility_macro = ["cpi", "fomc", "fed rate", "powell", "inflation", "non-farm", "unemployment rate"]

        news_articles = data.get("news_articles", [])
        macro_events = data.get("macro_events", [])
        crypto_events = data.get("crypto_calendar_events", [])
        technicals = data.get("technicals", {})

        bull_count = 0
        bear_count = 0
        detected_catalysts = []

        for art in news_articles:
            title_lower = art.get("title", "").lower() + " " + art.get("summary", "").lower()
            item_bull = sum(1 for w in bullish_keywords if w in title_lower)
            item_bear = sum(1 for w in bearish_keywords if w in title_lower)
            bull_count += item_bull
            bear_count += item_bear

            if item_bull > item_bear and item_bull > 0:
                detected_catalysts.append({
                    "headline": art.get("title"),
                    "source": art.get("source"),
                    "impact": "BULLISH",
                    "analysis": "Positive institutional or narrative catalyst supporting upside momentum."
                })
            elif item_bear > item_bull and item_bear > 0:
                detected_catalysts.append({
                    "headline": art.get("title"),
                    "source": art.get("source"),
                    "impact": "BEARISH",
                    "analysis": "Regulatory, security, or downside catalyst suggesting short/defensive bias."
                })

        # Macro danger check
        high_impact_macro_found = False
        danger_warning = None
        for event in macro_events:
            title_lower = event.get("title", "").lower()
            if event.get("is_high_impact") or any(m in title_lower for m in high_volatility_macro):
                high_impact_macro_found = True
                danger_warning = f"High-Impact Macro Release Detected: '{event.get('title')}' on {event.get('date')} at {event.get('time')}. High risk of sudden price spikes, slippage, and stop-hunts."
                break

        # BTC Technicals reference
        btc_tech = technicals.get("BTCUSDT", {})
        btc_price = btc_tech.get("price", 85000.0)
        btc_rsi = btc_tech.get("rsi", 50.0)
        btc_support = btc_tech.get("support", btc_price * 0.96)
        btc_resistance = btc_tech.get("resistance", btc_price * 1.04)
        btc_trend = btc_tech.get("trend", "NEUTRAL")

        # Confluence logic: News + Macro + Technicals
        if high_impact_macro_found:
            direct_signal = "DO NOT TRADE / WAIT (HIGH RISK)"
            bias = "VOLATILE / NEUTRAL (WAIT)"
            confidence = 70
            risk = "EXTREME RISK (NO-TRADE ZONE)"
            action_desc = "Wait for high-impact macro event to pass. Do not enter fresh leverage positions."
            entry_zone = f"Wait for post-event consolidation near Support (${btc_support:,.0f})"
            tp1 = f"${btc_resistance:,.0f}"
            tp2 = f"${btc_resistance * 1.03:,.0f}"
            sl = f"${btc_support * 0.98:,.0f}"
            rr = "1 : 2.2"
        elif btc_rsi > 80:
            # Overbought warning
            direct_signal = "WAIT FOR PULLBACK (DO NOT FOMO BUY)"
            bias = "BULLISH BUT OVERBOUGHT"
            confidence = 72
            risk = "HIGH RISK (PULLBACK THREAT)"
            action_desc = f"RSI is extreme at {btc_rsi:.1f}. Buying at resistance carries high risk of rejection. Wait for a pullback towards EMA21 (${btc_tech.get('ema21', btc_price * 0.98):,.0f}) before going long."
            entry_zone = f"${btc_tech.get('ema21', btc_price * 0.98):,.0f} - ${btc_tech.get('ema9', btc_price * 0.99):,.0f}"
            tp1 = f"${btc_resistance:,.0f}"
            tp2 = f"${btc_resistance * 1.04:,.0f}"
            sl = f"${btc_support:,.0f}"
            rr = "1 : 2.5"
        elif bull_count > bear_count * 1.2 and "BULLISH" in btc_trend:
            direct_signal = "BUY NOW (LONG)"
            bias = "BULLISH (LONG)"
            confidence = min(88, 65 + (bull_count - bear_count) * 3)
            risk = "MODERATE RISK"
            action_desc = "Strong confluence between bullish news sentiment and upward EMA price action."
            entry_zone = f"${btc_price * 0.995:,.0f} - ${btc_price:,.0f}"
            tp1 = f"${btc_resistance:,.0f}"
            tp2 = f"${btc_resistance * 1.05:,.0f}"
            sl = f"${btc_support:,.0f}"
            rr = "1 : 2.8"
        elif bear_count > bull_count * 1.2 or "BEARISH" in btc_trend:
            direct_signal = "SELL NOW (SHORT)"
            bias = "BEARISH (SHORT)"
            confidence = min(88, 65 + (bear_count - bull_count) * 3)
            risk = "HIGH RISK"
            action_desc = "Bearish news drivers combined with technical resistance rejection."
            entry_zone = f"${btc_price:,.0f} - ${btc_price * 1.005:,.0f}"
            tp1 = f"${btc_support:,.0f}"
            tp2 = f"${btc_support * 0.96:,.0f}"
            sl = f"${btc_resistance:,.0f}"
            rr = "1 : 2.5"
        else:
            direct_signal = "NEUTRAL / WAIT (RANGE-BOUND)"
            bias = "VOLATILE / NEUTRAL (WAIT)"
            confidence = 60
            risk = "MODERATE RISK"
            action_desc = "Mixed news catalysts and range consolidation. Wait for breakout above resistance or bounce off support."
            entry_zone = f"Near Support (${btc_support:,.0f}) or on Breakout above (${btc_resistance:,.0f})"
            tp1 = f"${btc_resistance:,.0f}"
            tp2 = f"${btc_resistance * 1.03:,.0f}"
            sl = f"${btc_support * 0.985:,.0f}"
            rr = "1 : 2.0"

        tech_confluence_desc = f"BTC/USDT is trading at ${btc_price:,.2f} with 1h RSI at {btc_rsi:.1f} ({btc_tech.get('rsi_status', 'Neutral')}). " \
                              f"Trend is currently {btc_trend}. Key 24h Support is at ${btc_support:,.2f} and Resistance is at ${btc_resistance:,.2f}."

        return {
            "direct_signal": direct_signal,
            "overall_bias": bias,
            "confidence_score": confidence,
            "volatility_risk": risk,
            "imminent_danger_warning": danger_warning,
            "affected_assets": ["BTC", "ETH", "SOL", "Major Altcoins"],
            "signal_summary": action_desc,
            "trade_parameters": {
                "entry_zone": entry_zone,
                "take_profit_1": tp1,
                "take_profit_2": tp2,
                "stop_loss": sl,
                "risk_reward_ratio": rr,
                "recommended_leverage": "Spot or strictly 1x-3x leverage max (Protect capital during news trading)"
            },
            "technical_confluence": tech_confluence_desc,
            "macro_impact_summary": f"Scanned {len(macro_events)} ForexFactory macro releases and {len(crypto_events)} CryptoCraft calendar events. " +
                                    ("High volatility events like CPI/FOMC require strict capital preservation." if high_impact_macro_found else "No immediate macro shocks imminent."),
            "top_news_catalysts": detected_catalysts[:6],
            "trading_playbook": {
                "recommended_action": action_desc,
                "entry_strategy": "Wait for 15-minute candle close after headline release to avoid initial liquidation wick traps.",
                "stop_loss_invalidation": f"Hard Stop-Loss at {sl}. Close trade immediately if 1h candle closes beyond invalidation.",
                "recommended_leverage": "Spot or strictly 1x-3x leverage max.",
                "whipsaw_alert": "News candles create aggressive fakeouts in both directions before the real directional move is established."
            },
            "disclaimer": "Cryptocurrency trading and news volatility carry high financial risk. This analysis is an AI-assisted research summary and does not constitute financial or investment advice.",
            "engine_mode": "Heuristic Rule Engine + Live Binance Technical Confluence"
        }
