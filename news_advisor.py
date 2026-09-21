import re
from datetime import datetime


class NewsSentimentRiskAdvisor:
    """
    Dedicated AI & NLP Risk Advisor class that evaluates:
    1. Overall News Direction: Whether breaking news is leaning heavily BULLISH or BEARISH (with percentage ratio).
    2. News Volatility & TA Safety Gatekeeper: Answers whether unexpected news / crazy volatility
       could disrupt and invalidate your Technical Analysis (TA), or whether it is SAFE to execute your TA setups.
    """

    def __init__(self):
        self.bullish_keywords = {
            "high": ["etf approved", "etf inflow", "rate cut", "all-time high", "institutional buy", "record inflow", "adoption"],
            "medium": ["surge", "rally", "breakout", "accumulate", "soar", "partnership", "upgrade", "bullish", "expansion", "growth"],
            "low": ["gain", "rise", "positive", "green", "up", "recovery"]
        }
        self.bearish_keywords = {
            "high": ["sec lawsuit", "doj", "hack", "exploit", "fraud", "rate hike", "ban", "stolen", "liquidation cascade"],
            "medium": ["crash", "dump", "plunge", "investigation", "subpoena", "outflow", "bearish", "crackdown", "delisting"],
            "low": ["drop", "fall", "red", "slip", "down", "struggle", "loss"]
        }
        self.macro_danger_keywords = [
            "cpi", "fomc", "federal reserve", "fed interest rate", "powell", "non-farm payroll", "nfp", "unemployment rate"
        ]

    def evaluate_news_and_risk(self, news_articles: list, macro_events: list, crypto_events: list = None) -> dict:
        """
        Synthesizes all breaking news and economic calendar releases to answer:
        1. Is news pointing towards Bullish or Bearish?
        2. Could news volatility ruin/invert your technical analysis setups, or is it safe to trade your TA?
        """
        crypto_events = crypto_events or []
        bull_score = 0.0
        bear_score = 0.0
        
        bullish_headlines = []
        bearish_headlines = []

        # 1. Analyze every single news headline across all 12 platforms
        for art in news_articles:
            text = (art.get("title", "") + " " + art.get("summary", "")).lower()
            art_bull = 0.0
            art_bear = 0.0

            # Score Bullish
            for w in self.bullish_keywords["high"]:
                if w in text:
                    art_bull += 3.0
            for w in self.bullish_keywords["medium"]:
                if w in text:
                    art_bull += 1.5
            for w in self.bullish_keywords["low"]:
                if w in text:
                    art_bull += 0.8

            # Score Bearish
            for w in self.bearish_keywords["high"]:
                if w in text:
                    art_bear += 3.0
            for w in self.bearish_keywords["medium"]:
                if w in text:
                    art_bear += 1.5
            for w in self.bearish_keywords["low"]:
                if w in text:
                    art_bear += 0.8

            bull_score += art_bull
            bear_score += art_bear

            if art_bull > art_bear and art_bull >= 1.5:
                bullish_headlines.append({
                    "title": art.get("title"),
                    "source": art.get("source"),
                    "link": art.get("link"),
                    "strength": "High" if art_bull >= 3.0 else "Medium"
                })
            elif art_bear > art_bull and art_bear >= 1.5:
                bearish_headlines.append({
                    "title": art.get("title"),
                    "source": art.get("source"),
                    "link": art.get("link"),
                    "strength": "High" if art_bear >= 3.0 else "Medium"
                })

        # Calculate exact percentages
        total_score = bull_score + bear_score
        if total_score > 0:
            bull_pct = int(round((bull_score / total_score) * 100))
            bear_pct = 100 - bull_pct
        else:
            bull_pct = 50
            bear_pct = 50

        # QUESTION 1: News Leaning
        if bull_pct >= 62:
            news_bias = "STRONGLY BULLISH"
            news_leaning = "BULLISH"
            bias_summary = f"News is heavily pointing towards BULLISH momentum ({bull_pct}% Bullish vs {bear_pct}% Bearish). Institutional adoption, inflows, and positive catalysts dominate."
        elif bear_pct >= 62:
            news_bias = "STRONGLY BEARISH"
            news_leaning = "BEARISH"
            bias_summary = f"News is heavily pointing towards BEARISH pressure ({bear_pct}% Bearish vs {bull_pct}% Bullish). Negative catalysts, regulatory threats, or dumps dominate."
        elif bull_pct > bear_pct:
            news_bias = "MODERATELY BULLISH"
            news_leaning = "BULLISH"
            bias_summary = f"News slightly leans BULLISH ({bull_pct}% Bullish vs {bear_pct}% Bearish), but momentum is not yet overwhelmingly one-sided."
        elif bear_pct > bull_pct:
            news_bias = "MODERATELY BEARISH"
            news_leaning = "BEARISH"
            bias_summary = f"News slightly leans BEARISH ({bear_pct}% Bearish vs {bull_pct}% Bullish), showing caution among market participants."
        else:
            news_bias = "NEUTRAL / BALANCED"
            news_leaning = "NEUTRAL"
            bias_summary = "News is evenly split between positive and negative factors (50% - 50%). Market is in equilibrium."

        # QUESTION 2: TECHNICAL ANALYSIS THREAT & VOLATILITY GATEKEEPER
        # "Will unpredictable news spoil/invert your Technical Analysis, or is it safe to trade your TA?"
        risk_reasons = []
        is_ta_threatened = False

        # Current date string (MM-DD-YYYY or YYYY-MM-DD)
        now_dt = datetime.now()
        today_str_mmdd = now_dt.strftime("%m-%d-%Y")

        # 1. Check Macro Danger (ForexFactory)
        for event in macro_events:
            title_l = event.get("title", "").lower()
            impact_l = event.get("impact", "").lower()
            event_date = event.get("date", "").strip()
            
            # Check if high-impact or macro shock keyword
            is_shock = impact_l == "high" or any(m in title_l for m in self.macro_danger_keywords)
            if is_shock and event_date == today_str_mmdd:
                is_ta_threatened = True
                risk_reasons.append(f"ForexFactory High-Impact Catalyst TODAY: '{event.get('title')}' at {event.get('time')}. High risk of sudden news spikes breaking technical supports/resistances.")
                break

        # 2. Check major black swan / emergency exploit headlines in latest news
        for art in news_articles[:12]:
            title_l = art.get("title", "").lower()
            if any(k in title_l for k in ["sec lawsuit", "indictment", "arrested", "hacked $", "exploit $", "stolen $", "emergency rate"]):
                risk_reasons.append(f"Black Swan Legal/Security Headline: '{art.get('title')}' ({art.get('source')}). Unexpected downside shock hazard.")
                is_ta_threatened = True
                break

        # 3. Final Verdict for Question 2
        if is_ta_threatened:
            trade_verdict = "DANGER: AVOID TRADING (NEWS MIGHT SPOIL YOUR TA)"
            verdict_badge = "HIGH VOLATILITY HAZARD"
            verdict_color = "#f85149"
            advice = "The market is vulnerable to sudden news volatility. High-impact announcements or black-swan catalysts can cause massive whipsaws, invalidating your technical support/resistance levels and hitting stop-losses. AVOID taking fresh trades right now until the news event passes and the market calms down."
            ta_status = "TA AT RISK (DO NOT TRADE)"
        else:
            trade_verdict = "SAFE: NO SPOILER NEWS (PROCEED WITH YOUR TECHNICAL ANALYSIS)"
            verdict_badge = "SAFE TRADING ENVIRONMENT"
            verdict_color = "#3fb950"
            advice = "No imminent high-impact macro shocks or crazy news volatility detected across all 12 websites. The news environment is stable and will not spoil your technical setups. You can safely execute your Technical Analysis (TA) trades with standard risk management."
            ta_status = "TA FULLY RELIABLE (SAFE TO TRADE)"

        return {
            "news_bias": news_bias,
            "news_leaning": news_leaning,
            "bull_percentage": bull_pct,
            "bear_percentage": bear_pct,
            "bias_summary": bias_summary,
            "total_articles_evaluated": len(news_articles),
            "top_bullish_headlines": bullish_headlines[:5],
            "top_bearish_headlines": bearish_headlines[:5],
            
            # The TA Safety Gatekeeper
            "trade_verdict": trade_verdict,
            "verdict_badge": verdict_badge,
            "verdict_color": verdict_color,
            "is_dangerous": is_ta_threatened,
            "ta_status": ta_status,
            "advice": advice,
            "risk_reasons": risk_reasons
        }
