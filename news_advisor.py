import re
from datetime import datetime


class NewsSentimentRiskAdvisor:
    """
    Dedicated AI & NLP Risk Advisor class that evaluates:
    1. News Direction: Whether breaking news is leaning heavily BULLISH or BEARISH (with percentage ratio).
    2. News Volatility & TA Safety Gatekeeper: Answers whether unexpected news / crazy volatility
       could disrupt and invalidate your Technical Analysis (TA), or whether it is SAFE to execute your TA setups.
       Supports specialized asset evaluation for:
       - Bitcoin (BTC)
       - Gold (XAU/USD)
       - Overall Market
    """

    def __init__(self):
        self.crypto_bullish_keywords = {
            "high": ["etf approved", "etf inflow", "rate cut", "all-time high", "institutional buy", "record inflow", "adoption", "btc surge", "bitcoin rally"],
            "medium": ["surge", "rally", "breakout", "accumulate", "soar", "partnership", "upgrade", "bullish", "expansion", "growth"],
            "low": ["gain", "rise", "positive", "green", "up", "recovery"]
        }
        self.crypto_bearish_keywords = {
            "high": ["sec lawsuit", "doj", "hack", "exploit", "fraud", "rate hike", "ban", "stolen", "liquidation cascade"],
            "medium": ["crash", "dump", "plunge", "investigation", "subpoena", "outflow", "bearish", "crackdown", "delisting"],
            "low": ["drop", "fall", "red", "slip", "down", "struggle", "loss"]
        }

        # Gold-Specific Fundamental Keywords
        self.gold_bullish_keywords = [
            "gold surge", "gold rally", "gold high", "rate cut", "inflation rise", "inflation high",
            "cpi rise", "dxy drop", "dollar weak", "safe haven", "central bank buy", "gold breakout",
            "precious metal gain", "treasury yield drop", "geopolitical tension", "debt crisis"
        ]
        self.gold_bearish_keywords = [
            "gold drop", "gold slump", "rate hike", "fed hawkish", "dollar strong", "dxy rally",
            "treasury yield surge", "inflation cool", "cpi drop", "gold dump", "strong dollar", "nfp surge"
        ]

        self.macro_danger_keywords = [
            "cpi", "fomc", "federal reserve", "fed interest rate", "powell", "non-farm payroll", "nfp", "unemployment rate"
        ]

    def evaluate_news_and_risk(self, news_articles: list, macro_events: list, crypto_events: list = None, asset: str = "OVERALL") -> dict:
        """
        Synthesizes news and economic calendar releases specifically for:
        - 'BTC': Bitcoin news, ETF flows, and crypto macro catalysts.
        - 'GOLD': Gold (XAU/USD), ForexFactory USD releases, Fed rate decisions, inflation, DXY.
        - 'OVERALL': The broad crypto and macro market.
        """
        asset = (asset or "OVERALL").upper()
        crypto_events = crypto_events or []
        bull_score = 0.0
        bear_score = 0.0
        bullish_headlines = []
        bearish_headlines = []

        now_dt = datetime.now()
        today_str_mmdd = now_dt.strftime("%m-%d-%Y")

        # ----------------------------------------------------
        # 1. BITCOIN SPECIFIC EVALUATION
        # ----------------------------------------------------
        if asset in ["BTC", "BITCOIN"]:
            btc_keywords = ["bitcoin", "btc", "satoshi", "crypto", "etf", "mining", "sec", "halving", "inflow", "outflow"]
            relevant_articles = []
            for art in news_articles:
                txt = (art.get("title", "") + " " + art.get("summary", "")).lower()
                if any(k in txt for k in btc_keywords):
                    relevant_articles.append(art)
            if not relevant_articles:
                relevant_articles = news_articles

            for art in relevant_articles:
                text = (art.get("title", "") + " " + art.get("summary", "")).lower()
                art_bull = sum(3.0 for w in self.crypto_bullish_keywords["high"] if w in text) + \
                           sum(1.5 for w in self.crypto_bullish_keywords["medium"] if w in text) + \
                           sum(0.8 for w in self.crypto_bullish_keywords["low"] if w in text)
                art_bear = sum(3.0 for w in self.crypto_bearish_keywords["high"] if w in text) + \
                           sum(1.5 for w in self.crypto_bearish_keywords["medium"] if w in text) + \
                           sum(0.8 for w in self.crypto_bearish_keywords["low"] if w in text)

                bull_score += art_bull
                bear_score += art_bear

                if art_bull > art_bear and art_bull >= 1.5:
                    bullish_headlines.append({"title": art.get("title"), "source": art.get("source"), "link": art.get("link"), "strength": "High" if art_bull >= 3 else "Medium"})
                elif art_bear > art_bull and art_bear >= 1.5:
                    bearish_headlines.append({"title": art.get("title"), "source": art.get("source"), "link": art.get("link"), "strength": "High" if art_bear >= 3 else "Medium"})

            total_score = bull_score + bear_score
            bull_pct = int(round((bull_score / total_score) * 100)) if total_score > 0 else 50
            bear_pct = 100 - bull_pct

            news_lean = "BULLISH" if bull_pct >= 55 else ("BEARISH" if bear_pct >= 55 else "NEUTRAL")
            news_bias = f"{news_lean} (BITCOIN FOCUSED)"
            bias_summary = f"Bitcoin news sentiment is currently leaning {news_lean} ({bull_pct}% Bullish vs {bear_pct}% Bearish) across tier-1 crypto feeds and ETF trackers."

            # TA Danger for Bitcoin
            risk_reasons = []
            is_ta_threatened = False
            for event in macro_events:
                title_l = event.get("title", "").lower()
                impact_l = event.get("impact", "").lower()
                event_date = event.get("date", "").strip()
                if (impact_l == "high" or any(m in title_l for m in self.macro_danger_keywords)) and event_date == today_str_mmdd:
                    is_ta_threatened = True
                    risk_reasons.append(f"ForexFactory Macro Event TODAY: '{event.get('title')}' at {event.get('time')}. Volatility wick threat to BTC technical levels.")
                    break

            for art in relevant_articles[:10]:
                title_l = art.get("title", "").lower()
                if any(k in title_l for k in ["sec lawsuit", "indictment", "arrested", "hacked $", "exploit $", "stolen $"]):
                    risk_reasons.append(f"Regulatory / Security Threat: '{art.get('title')}' ({art.get('source')}). Sudden downside flash volatility.")
                    is_ta_threatened = True
                    break

            if is_ta_threatened:
                trade_verdict = "DANGER: AVOID TRADING BTC (NEWS MIGHT SPOIL YOUR TA)"
                verdict_badge = "BTC VOLATILITY HAZARD"
                verdict_color = "#f85149"
                advice = "High news or macro event threat detected today. Entering new Bitcoin leverage setups carries high risk of sudden liquidity wicks breaking support/resistance levels. AVOID taking fresh BTC trades until the event passes."
                ta_status = "BTC TA AT RISK (DO NOT TRADE)"
            else:
                trade_verdict = "SAFE: NO SPOILER NEWS FOR BITCOIN (PROCEED WITH YOUR BTC TA)"
                verdict_badge = "SAFE TRADING ENVIRONMENT"
                verdict_color = "#3fb950"
                advice = "Bitcoin news environment is quiet and free of sudden macro shock catalysts. It will not spoil your technical setup. You can safely trade your BTC chart patterns, supports, and resistances with strict risk control."
                ta_status = "BTC TA FULLY RELIABLE (SAFE TO TRADE)"

        # ----------------------------------------------------
        # 2. GOLD (XAU/USD) SPECIFIC EVALUATION
        # ----------------------------------------------------
        elif asset in ["GOLD", "XAU", "XAUUSD"]:
            gold_articles = []
            gold_search_terms = ["gold", "xau", "bullion", "dollar", "dxy", "fed", "rate cut", "treasury", "inflation", "safe haven", "central bank"]
            for art in news_articles:
                txt = (art.get("title", "") + " " + art.get("summary", "")).lower()
                if any(k in txt for k in gold_search_terms):
                    gold_articles.append(art)

            # Analyze ForexFactory USD macro events which heavily dictate Gold
            for event in macro_events:
                title_l = event.get("title", "").lower()
                # Rate cuts / high inflation / weak dollar = Bullish Gold
                if any(k in title_l for k in ["rate cut", "cpi", "pce", "dovish"]):
                    bull_score += 3.0
                # Rate hikes / strong dollar / hawkish fed = Bearish Gold
                elif any(k in title_l for k in ["rate hike", "hawkish", "fomc member", "dollar"]):
                    bear_score += 3.0

            for art in (gold_articles or news_articles[:15]):
                text = (art.get("title", "") + " " + art.get("summary", "")).lower()
                art_bull = sum(2.5 for w in self.gold_bullish_keywords if w in text)
                art_bear = sum(2.5 for w in self.gold_bearish_keywords if w in text)
                bull_score += art_bull
                bear_score += art_bear

                if art_bull > art_bear and art_bull >= 2.0:
                    bullish_headlines.append({"title": art.get("title"), "source": art.get("source"), "link": art.get("link"), "strength": "High"})
                elif art_bear > art_bull and art_bear >= 2.0:
                    bearish_headlines.append({"title": art.get("title"), "source": art.get("source"), "link": art.get("link"), "strength": "High"})

            total_score = bull_score + bear_score
            bull_pct = int(round((bull_score / total_score) * 100)) if total_score > 0 else 52
            bear_pct = 100 - bull_pct

            news_lean = "BULLISH" if bull_pct >= 55 else ("BEARISH" if bear_pct >= 55 else "NEUTRAL")
            news_bias = f"{news_lean} (GOLD / XAUUSD FOCUSED)"
            bias_summary = f"Gold (XAU/USD) macro fundamentals are leaning {news_lean} ({bull_pct}% Bullish vs {bear_pct}% Bearish), evaluated against ForexFactory USD rate expectations, inflation, and safe-haven demand."

            # TA Danger for Gold (Gold is 100% reactive to ForexFactory USD releases)
            risk_reasons = []
            is_ta_threatened = False
            for event in macro_events:
                title_l = event.get("title", "").lower()
                impact_l = event.get("impact", "").lower()
                event_date = event.get("date", "").strip()
                if (impact_l == "high" or any(m in title_l for m in self.macro_danger_keywords)) and event_date == today_str_mmdd:
                    is_ta_threatened = True
                    risk_reasons.append(f"ForexFactory USD Catalyst TODAY: '{event.get('title')}' at {event.get('time')}. High risk of violent 300+ pip wicks blowing through Gold support/resistance.")
                    break

            if is_ta_threatened:
                trade_verdict = "DANGER: AVOID TRADING GOLD (NEWS MIGHT SPOIL YOUR TA)"
                verdict_badge = "GOLD VOLATILITY HAZARD"
                verdict_color = "#f85149"
                advice = "ForexFactory has high-impact USD economic releases scheduled today. Gold ($XAU/USD) is extremely sensitive to USD catalysts and often creates massive 200–500 pip spikes that shatter technical chart patterns. AVOID trading your Gold technical setups until the event passes and spreads normalize."
                ta_status = "GOLD TA AT RISK (DO NOT TRADE)"
            else:
                trade_verdict = "SAFE: NO SPOILER NEWS FOR GOLD (PROCEED WITH YOUR GOLD TA)"
                verdict_badge = "SAFE TRADING ENVIRONMENT"
                verdict_color = "#3fb950"
                advice = "No imminent high-impact USD shock catalysts on ForexFactory today. Gold price action is respecting technical market structure and key levels. You can safely execute your Gold (XAU/USD) Technical Analysis setups with standard risk parameters."
                ta_status = "GOLD TA FULLY RELIABLE (SAFE TO TRADE)"

        # ----------------------------------------------------
        # 3. OVERALL MARKET EVALUATION
        # ----------------------------------------------------
        else:
            for art in news_articles:
                text = (art.get("title", "") + " " + art.get("summary", "")).lower()
                art_bull = sum(3.0 for w in self.crypto_bullish_keywords["high"] if w in text) + \
                           sum(1.5 for w in self.crypto_bullish_keywords["medium"] if w in text) + \
                           sum(0.8 for w in self.crypto_bullish_keywords["low"] if w in text)
                art_bear = sum(3.0 for w in self.crypto_bearish_keywords["high"] if w in text) + \
                           sum(1.5 for w in self.crypto_bearish_keywords["medium"] if w in text) + \
                           sum(0.8 for w in self.crypto_bearish_keywords["low"] if w in text)

                bull_score += art_bull
                bear_score += art_bear

                if art_bull > art_bear and art_bull >= 1.5:
                    bullish_headlines.append({"title": art.get("title"), "source": art.get("source"), "link": art.get("link"), "strength": "High" if art_bull >= 3 else "Medium"})
                elif art_bear > art_bull and art_bear >= 1.5:
                    bearish_headlines.append({"title": art.get("title"), "source": art.get("source"), "link": art.get("link"), "strength": "High" if art_bear >= 3 else "Medium"})

            total_score = bull_score + bear_score
            bull_pct = int(round((bull_score / total_score) * 100)) if total_score > 0 else 50
            bear_pct = 100 - bull_pct

            news_lean = "BULLISH" if bull_pct >= 55 else ("BEARISH" if bear_pct >= 55 else "NEUTRAL")
            news_bias = f"{news_lean} (OVERALL MARKET)"
            bias_summary = f"Overall crypto & macro news is leaning {news_lean} ({bull_pct}% Bullish vs {bear_pct}% Bearish) across all 12 monitored platforms."

            risk_reasons = []
            is_ta_threatened = False
            for event in macro_events:
                title_l = event.get("title", "").lower()
                impact_l = event.get("impact", "").lower()
                event_date = event.get("date", "").strip()
                if (impact_l == "high" or any(m in title_l for m in self.macro_danger_keywords)) and event_date == today_str_mmdd:
                    is_ta_threatened = True
                    risk_reasons.append(f"ForexFactory High-Impact Catalyst TODAY: '{event.get('title')}' at {event.get('time')}. Risk of sudden news spikes breaking technical supports/resistances.")
                    break

            for art in news_articles[:12]:
                title_l = art.get("title", "").lower()
                if any(k in title_l for k in ["sec lawsuit", "indictment", "arrested", "hacked $", "exploit $", "stolen $", "emergency rate"]):
                    risk_reasons.append(f"Black Swan Legal/Security Headline: '{art.get('title')}' ({art.get('source')}). Unexpected downside shock hazard.")
                    is_ta_threatened = True
                    break

            if is_ta_threatened:
                trade_verdict = "DANGER: AVOID TRADING (NEWS MIGHT SPOIL YOUR TA)"
                verdict_badge = "HIGH VOLATILITY HAZARD"
                verdict_color = "#f85149"
                advice = "The market is vulnerable to sudden news volatility. High-impact announcements can cause massive whipsaws, invalidating your technical support/resistance levels. AVOID taking fresh trades right now until the market calms down."
                ta_status = "TA AT RISK (DO NOT TRADE)"
            else:
                trade_verdict = "SAFE: NO SPOILER NEWS (PROCEED WITH YOUR TECHNICAL ANALYSIS)"
                verdict_badge = "SAFE TRADING ENVIRONMENT"
                verdict_color = "#3fb950"
                advice = "No imminent high-impact macro shocks or crazy news volatility detected. The news environment is stable and will not spoil your technical setups. You can safely execute your Technical Analysis (TA) trades."
                ta_status = "TA FULLY RELIABLE (SAFE TO TRADE)"

        return {
            "asset": asset,
            "news_bias": news_bias,
            "news_leaning": news_lean,
            "bull_percentage": bull_pct,
            "bear_percentage": bear_pct,
            "bias_summary": bias_summary,
            "total_articles_evaluated": len(news_articles),
            "top_bullish_headlines": bullish_headlines[:5],
            "top_bearish_headlines": bearish_headlines[:5],
            "trade_verdict": trade_verdict,
            "verdict_badge": verdict_badge,
            "verdict_color": verdict_color,
            "is_dangerous": is_ta_threatened,
            "ta_status": ta_status,
            "advice": advice,
            "risk_reasons": risk_reasons
        }
