import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = "gemini-2.5-flash"

# Feeds & Data Sources
SOURCES_CONFIG = {
    # Macro & Economic Calendars
    "ForexFactory": {
        "name": "ForexFactory (Macro Calendar)",
        "url": "https://nfs.faireconomy.media/ff_calendar_thisweek.xml",
        "type": "macro_calendar",
        "description": "High-impact USD releases (CPI, FOMC, NFP, Fed interest rates)",
        "enabled": True
    },
    "CryptoCraft": {
        "name": "CryptoCraft (Crypto Calendar)",
        "url": "https://nfs.faireconomy.media/cc_calendar_thisweek.xml",
        "type": "crypto_calendar",
        "description": "Crypto-specific economic calendar and policy events",
        "enabled": True
    },
    
    # Major Crypto Outlets (from user bookmark list)
    "CoinDesk": {
        "name": "CoinDesk",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "type": "rss",
        "description": "Institutional, regulatory, and macro crypto news",
        "enabled": True
    },
    "Cointelegraph": {
        "name": "Cointelegraph",
        "url": "https://cointelegraph.com/rss",
        "type": "rss",
        "description": "Breaking crypto news and market analysis",
        "enabled": True
    },
    "WatcherGuru": {
        "name": "WatcherGuru",
        "url": "https://watcher.guru/news/feed",
        "type": "rss",
        "description": "Breaking alerts, whale moves, ETF flows, and memecoins",
        "enabled": True
    },
    "CryptoSlate": {
        "name": "CryptoSlate",
        "url": "https://cryptoslate.com/feed/",
        "type": "rss",
        "description": "On-chain data, tokenomics, and deep market insights",
        "enabled": True
    },
    "CryptoPotato": {
        "name": "CryptoPotato",
        "url": "https://cryptopotato.com/feed/",
        "type": "rss",
        "description": "Altcoin analysis, trading setups, and market updates",
        "enabled": True
    },
    "CryptoNews": {
        "name": "CryptoNews.com",
        "url": "https://cryptonews.com/news/feed/",
        "type": "rss",
        "description": "Fast global crypto news wire",
        "enabled": True
    },
    "BinanceSquare": {
        "name": "Binance Square / News",
        "url": "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query?catalogId=48&pageNo=1&pageSize=10",
        "type": "binance_json",
        "description": "Exchange listings, announcements, and market sentiment",
        "enabled": True
    }
}

# Standard Request Headers
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}
