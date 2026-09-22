import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from config import SOURCES_CONFIG, REQUEST_HEADERS

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and clean up whitespace."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = ' '.join(clean.split())
    return clean[:350]


# In-memory cache for calendars to avoid 429 rate-limiting
_CALENDAR_CACHE = {
    "forex_factory": {"data": [], "timestamp": 0},
    "crypto_craft": {"data": [], "timestamp": 0}
}


def fetch_forex_factory_calendar(url: str = None) -> list:
    """Fetch high and medium impact macro events from ForexFactory XML feed with caching."""
    global _CALENDAR_CACHE
    now = time.time()
    # If cached within last 10 minutes and not empty, use cache
    if _CALENDAR_CACHE["forex_factory"]["data"] and (now - _CALENDAR_CACHE["forex_factory"]["timestamp"] < 600):
        return _CALENDAR_CACHE["forex_factory"]["data"]

    url = url or SOURCES_CONFIG["ForexFactory"]["url"]
    events = []
    try:
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as response:
            content = response.read()
            root = ET.fromstring(content)
            for event in root.findall("event"):
                title = event.find("title").text if event.find("title") is not None else "Untitled"
                country = event.find("country").text if event.find("country") is not None else ""
                impact = event.find("impact").text if event.find("impact") is not None else "Low"
                date = event.find("date").text if event.find("date") is not None else ""
                time_val = event.find("time").text if event.find("time") is not None else ""
                forecast = event.find("forecast").text if event.find("forecast") is not None else "N/A"
                previous = event.find("previous").text if event.find("previous") is not None else "N/A"

                if country in ["USD", "ALL", "EUR"] or impact in ["High", "Medium"]:
                    events.append({
                        "source": "ForexFactory",
                        "title": title.strip(),
                        "country": country.strip(),
                        "impact": impact.strip(),
                        "date": date.strip(),
                        "time": time_val.strip(),
                        "forecast": (forecast or "N/A").strip(),
                        "previous": (previous or "N/A").strip(),
                        "is_high_impact": impact.strip().lower() == "high" or "cpi" in title.lower() or "fomc" in title.lower() or "fed" in title.lower()
                    })
            if events:
                _CALENDAR_CACHE["forex_factory"] = {"data": events, "timestamp": now}
    except Exception as e:
        print(f"ForexFactory notice: {e} (using fallback cache if available)")
        if _CALENDAR_CACHE["forex_factory"]["data"]:
            return _CALENDAR_CACHE["forex_factory"]["data"]
    return events or _CALENDAR_CACHE["forex_factory"]["data"]


def fetch_crypto_craft_calendar(url: str = None) -> list:
    """Fetch crypto-specific economic calendar events from CryptoCraft XML feed with caching."""
    global _CALENDAR_CACHE
    now = time.time()
    if _CALENDAR_CACHE["crypto_craft"]["data"] and (now - _CALENDAR_CACHE["crypto_craft"]["timestamp"] < 600):
        return _CALENDAR_CACHE["crypto_craft"]["data"]

    url = url or SOURCES_CONFIG["CryptoCraft"]["url"]
    events = []
    try:
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as response:
            content = response.read()
            root = ET.fromstring(content)
            for event in root.findall("event"):
                title = event.find("title").text if event.find("title") is not None else "Untitled"
                impact = event.find("impact").text if event.find("impact") is not None else "Low"
                date = event.find("date").text if event.find("date") is not None else ""
                time_val = event.find("time").text if event.find("time") is not None else ""
                currency = event.find("currency").text if event.find("currency") is not None else "CRYPTO"
                forecast = event.find("forecast").text if event.find("forecast") is not None else "N/A"
                previous = event.find("previous").text if event.find("previous") is not None else "N/A"

                events.append({
                    "source": "CryptoCraft",
                    "title": title.strip(),
                    "country": currency.strip() if currency else "CRYPTO",
                    "impact": impact.strip(),
                    "date": date.strip(),
                    "time": time_val.strip(),
                    "forecast": (forecast or "N/A").strip(),
                    "previous": (previous or "N/A").strip(),
                    "is_high_impact": impact.strip().lower() in ["high", "medium"]
                })
            if events:
                _CALENDAR_CACHE["crypto_craft"] = {"data": events, "timestamp": now}
    except Exception as e:
        print(f"CryptoCraft notice: {e} (using fallback cache if available)")
        if _CALENDAR_CACHE["crypto_craft"]["data"]:
            return _CALENDAR_CACHE["crypto_craft"]["data"]
    return events or _CALENDAR_CACHE["crypto_craft"]["data"]


def fetch_rss_feed(source_key: str, config: dict, limit: int = 10) -> list:
    """Fetch and parse RSS feeds for CoinDesk, Cointelegraph, WatcherGuru, CryptoSlate, CryptoPotato, CryptoNews."""
    articles = []
    url = config["url"]
    name = config["name"]
    try:
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
            try:
                root = ET.fromstring(xml_data)
                items = root.findall(".//item")
                for item in items[:limit]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    pub_elem = item.find("pubDate")
                    desc_elem = item.find("description")

                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                    pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                    description = clean_html(desc_elem.text) if desc_elem is not None and desc_elem.text else ""

                    if title:
                        articles.append({
                            "source": name,
                            "source_key": source_key,
                            "title": title,
                            "link": link,
                            "pub_date": pub_date,
                            "summary": description
                        })
            except ET.ParseError:
                soup = BeautifulSoup(xml_data, "html.parser")
                for item in soup.find_all("item")[:limit]:
                    title = item.find("title").get_text(strip=True) if item.find("title") else ""
                    link = item.find("link").get_text(strip=True) if item.find("link") else ""
                    pub_date = item.find("pubdate").get_text(strip=True) if item.find("pubdate") else ""
                    desc = item.find("description").get_text(strip=True) if item.find("description") else ""

                    if title:
                        articles.append({
                            "source": name,
                            "source_key": source_key,
                            "title": title,
                            "link": link,
                            "pub_date": pub_date,
                            "summary": clean_html(desc)
                        })
    except Exception as e:
        print(f"Error fetching {name} ({url}): {e}")
    return articles


def fetch_binance_square_news(limit: int = 8) -> list:
    """Fetch latest announcements and news from Binance API."""
    articles = []
    url = SOURCES_CONFIG["BinanceSquare"]["url"]
    try:
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("success") and "data" in data and "articles" in data["data"]:
                for item in data["data"]["articles"][:limit]:
                    title = item.get("title", "")
                    code = item.get("code", "")
                    release_date = item.get("releaseDate", "")
                    link = f"https://www.binance.com/en/support/announcement/{code}" if code else "https://www.binance.com"
                    
                    if title:
                        articles.append({
                            "source": "Binance Square",
                            "source_key": "BinanceSquare",
                            "title": title,
                            "link": link,
                            "pub_date": str(datetime.fromtimestamp(release_date / 1000.0)) if release_date else "",
                            "summary": clean_html(item.get("body", ""))
                        })
    except Exception as e:
        print(f"Error fetching Binance news: {e}")
    return articles


def fetch_coinmarketcal_catalysts(limit: int = 6) -> list:
    """Fetch upcoming crypto catalysts (token unlocks, listings, hardforks) using CoinMarketCal discovery."""
    catalysts = []
    if DDGS is None:
        return catalysts
    try:
        ddgs = DDGS()
        results = ddgs.text("CoinMarketCal upcoming crypto events token unlock hardfork 2026", max_results=limit)
        for r in results:
            catalysts.append({
                "source": "CoinMarketCal Catalyst",
                "title": r.get("title", ""),
                "link": r.get("href", "https://coinmarketcal.com"),
                "summary": r.get("body", "")
            })
    except Exception as e:
        print(f"Error discovering CoinMarketCal catalysts: {e}")
    return catalysts


def fetch_live_market_context() -> dict:
    """Fetch current prices, 24h change, and trending coins from CoinGecko public endpoints."""
    market_data = {
        "prices": {},
        "trending": []
    }
    try:
        price_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,pax-gold,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        req = urllib.request.Request(price_url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=6) as response:
            raw_prices = json.loads(response.read().decode("utf-8"))
            if "pax-gold" in raw_prices:
                raw_prices["gold (xau)"] = raw_prices.pop("pax-gold")
            market_data["prices"] = raw_prices
    except Exception as e:
        print(f"Error fetching prices: {e}")

    try:
        trend_url = "https://api.coingecko.com/api/v3/search/trending"
        req = urllib.request.Request(trend_url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=6) as response:
            trend_data = json.loads(response.read().decode("utf-8"))
            if "coins" in trend_data:
                market_data["trending"] = [
                    {"name": c["item"]["name"], "symbol": c["item"]["symbol"], "rank": c["item"]["market_cap_rank"]}
                    for c in trend_data["coins"][:6]
                ]
    except Exception as e:
        print(f"Error fetching trending: {e}")

    return market_data


def fetch_technical_indicators(symbol: str = "BTCUSDT") -> dict:
    """Fetch 1h klines from Binance and calculate RSI, EMAs, Support & Resistance."""
    default_price = 2650.0 if "PAXG" in symbol or "GOLD" in symbol else (85000.0 if "BTC" in symbol else 2700.0)
    result = {
        "symbol": symbol,
        "price": default_price,
        "rsi": 50.0,
        "ema9": default_price * 0.99,
        "ema21": default_price * 0.98,
        "ema50": default_price * 0.97,
        "support": default_price * 0.96,
        "resistance": default_price * 1.04,
        "trend": "NEUTRAL",
        "rsi_status": "NEUTRAL"
    }
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=60"
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            klines = json.loads(resp.read().decode("utf-8"))

        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]

        current_price = closes[-1]
        result["price"] = current_price

        # RSI (14)
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))

        avg_gain = sum(gains[-14:]) / 14.0
        avg_loss = sum(losses[-14:]) / 14.0
        rs = avg_gain / (avg_loss if avg_loss != 0 else 0.0001)
        rsi = 100 - (100 / (1 + rs))
        result["rsi"] = round(rsi, 2)

        if rsi >= 75:
            result["rsi_status"] = "OVERBOUGHT (Watch for Pullback / Exhaustion)"
        elif rsi <= 30:
            result["rsi_status"] = "OVERSOLD (Rebound / Discount Zone)"
        else:
            result["rsi_status"] = "NEUTRAL / BALANCED"

        # EMA helper
        def calc_ema(series, period):
            k = 2 / (period + 1)
            e = series[0]
            for val in series[1:]:
                e = (val * k) + (e * (1 - k))
            return e

        result["ema9"] = round(calc_ema(closes, 9), 2)
        result["ema21"] = round(calc_ema(closes, 21), 2)
        result["ema50"] = round(calc_ema(closes, 50), 2)

        # Support & Resistance (24-hour range)
        result["support"] = round(min(lows[-24:]), 2)
        result["resistance"] = round(max(highs[-24:]), 2)

        # Trend Determination
        if current_price > result["ema9"] > result["ema21"]:
            result["trend"] = "BULLISH (Upward Momentum)"
        elif current_price < result["ema9"] < result["ema21"]:
            result["trend"] = "BEARISH (Downward Pressure)"
        else:
            result["trend"] = "CONSOLIDATING / CHOPPY"

    except Exception as e:
        print(f"Error computing technicals for {symbol}: {e}")

    return result


def collect_all_data(active_sources: list = None) -> dict:
    """Collect macro calendar, crypto calendar, breaking news, market context, and technical analysis concurrently."""
    if active_sources is None:
        active_sources = list(SOURCES_CONFIG.keys())

    results = {
        "macro_events": [],
        "crypto_calendar_events": [],
        "news_articles": [],
        "catalysts": [],
        "market_context": {},
        "technicals": {},
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}

        if "ForexFactory" in active_sources:
            futures[executor.submit(fetch_forex_factory_calendar)] = "forex_factory"
        if "CryptoCraft" in active_sources:
            futures[executor.submit(fetch_crypto_craft_calendar)] = "crypto_craft"
        if "BinanceSquare" in active_sources:
            futures[executor.submit(fetch_binance_square_news)] = "binance"
        
        # CoinMarketCal
        futures[executor.submit(fetch_coinmarketcal_catalysts)] = "coinmarketcal"
        
        # Live prices
        futures[executor.submit(fetch_live_market_context)] = "market_context"

        # Technical Indicators for Bitcoin, Gold, and Top Coins
        futures[executor.submit(fetch_technical_indicators, "BTCUSDT")] = "tech_btc"
        futures[executor.submit(fetch_technical_indicators, "PAXGUSDT")] = "tech_gold"
        futures[executor.submit(fetch_technical_indicators, "ETHUSDT")] = "tech_eth"
        futures[executor.submit(fetch_technical_indicators, "SOLUSDT")] = "tech_sol"

        # RSS News Sources
        for key, conf in SOURCES_CONFIG.items():
            if key in active_sources and conf.get("type") == "rss":
                futures[executor.submit(fetch_rss_feed, key, conf)] = f"rss_{key}"

        for future in as_completed(futures):
            job_name = futures[future]
            try:
                res = future.result()
                if job_name == "forex_factory":
                    results["macro_events"] = res
                elif job_name == "crypto_craft":
                    results["crypto_calendar_events"] = res
                elif job_name == "binance":
                    results["news_articles"].extend(res)
                elif job_name == "coinmarketcal":
                    results["catalysts"] = res
                elif job_name == "market_context":
                    results["market_context"] = res
                elif job_name == "tech_btc":
                    results["technicals"]["BTCUSDT"] = res
                elif job_name == "tech_gold":
                    results["technicals"]["PAXGUSDT"] = res
                elif job_name == "tech_eth":
                    results["technicals"]["ETHUSDT"] = res
                elif job_name == "tech_sol":
                    results["technicals"]["SOLUSDT"] = res
                elif job_name.startswith("rss_"):
                    results["news_articles"].extend(res)
            except Exception as e:
                print(f"Task {job_name} failed: {e}")

    # Deduplicate news articles by title
    seen_titles = set()
    deduped_news = []
    for art in results["news_articles"]:
        t = art.get("title", "").strip().lower()
        if t and t not in seen_titles:
            seen_titles.add(t)
            deduped_news.append(art)
    results["news_articles"] = deduped_news

    return results


if __name__ == "__main__":
    print("Testing data collectors...")
    data = collect_all_data()
    print(f"Collected {len(data['macro_events'])} macro events (ForexFactory)")
    print(f"Collected {len(data['crypto_calendar_events'])} crypto calendar events (CryptoCraft)")
    print(f"Collected {len(data['news_articles'])} news articles across all outlets")
    print(f"Collected {len(data['catalysts'])} CoinMarketCal catalysts")
    print("Market Context:", data["market_context"].get("prices", {}))
