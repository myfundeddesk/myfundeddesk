import time
import os
import random
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import httpx
from .options_engine import calculate_option_price_live

# Global in-memory notifications queue for super admin alerts
admin_notifications = []

INSTRUMENTS: Dict[str, Dict[str, Any]] = {
    "NIFTY50": {
        "name": "NIFTY 50 (NSE)",
        "category": "Indices",
        "base_price": 24080.40,
        "spread": 1.5,
        "digits": 2,
        "pip_size": 0.05,
        "contract_size": 50,
        "volatility": 15.0,
    },
    "BANKNIFTY": {
        "name": "BANK NIFTY (NSE)",
        "category": "Indices",
        "base_price": 58025.00,
        "spread": 2.5,
        "digits": 2,
        "pip_size": 0.05,
        "contract_size": 15,
        "volatility": 35.0,
    },
    "SENSEX": {
        "name": "BSE SENSEX (BSE)",
        "category": "Indices",
        "base_price": 76957.00,
        "spread": 5.0,
        "digits": 2,
        "pip_size": 0.05,
        "contract_size": 10,
        "volatility": 50.0,
    },
    "FINNIFTY": {
        "name": "NIFTY FINANCIAL (NSE)",
        "category": "Indices",
        "base_price": 26293.00,
        "spread": 1.2,
        "digits": 2,
        "pip_size": 0.05,
        "contract_size": 25,
        "volatility": 18.0,
    },
    "MIDCPNIFTY": {
        "name": "NIFTY MIDCAP SELECT (NSE)",
        "category": "Indices",
        "base_price": 18491.00,
        "spread": 1.0,
        "digits": 2,
        "pip_size": 0.05,
        "contract_size": 50,
        "volatility": 12.0,
    },
    "RELIANCE": {
        "name": "Reliance Industries (NSE)",
        "category": "Equities",
        "base_price": 1277.0,
        "spread": 0.5,
        "digits": 2,
        "pip_size": 0.05,
        "contract_size": 250,
        "volatility": 1.5,
    },
    "HDFCBANK": {
        "name": "HDFC Bank Ltd (NSE)",
        "category": "Equities",
        "base_price": 709.0,
        "spread": 0.3,
        "digits": 2,
        "pip_size": 0.05,
        "contract_size": 550,
        "volatility": 1.0,
    }
}

YAHOO_MAP = {
    "NIFTY50":    "^NSEI",
    "BANKNIFTY":  "^NSEBANK",
    "SENSEX":     "^BSESN",
    "FINNIFTY":   "NIFTY_FIN_SERVICE.NS",
    "MIDCPNIFTY": "^NSEMDCP50",
    "RELIANCE":   "RELIANCE.NS",
    "HDFCBANK":   "HDFCBANK.NS",
}

class MarketDataEngine:
    def __init__(self):
        self.prices: Dict[str, Dict[str, float]] = {}
        self.candle_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.lock = threading.Lock()
        
        # 1. Base initialize prices & fallback candles
        self._initialize_prices()
        
        # 2. Fetch real historical 1m candles immediately so charts look 100% authentic
        self._fetch_real_history_sync()
        
        # 3. Start background live sync workers
        self._sync_live_prices()

    def _initialize_prices(self):
        for symbol, cfg in INSTRUMENTS.items():
            mid = cfg["base_price"]
            spread = cfg["spread"]
            self.prices[symbol] = {
                "bid": round(mid - spread / 2, cfg["digits"]),
                "ask": round(mid + spread / 2, cfg["digits"]),
                "mid": mid,
                "change_24h": round(random.uniform(-0.5, 0.8), 2),
                "high_24h": round(mid * 1.008, cfg["digits"]),
                "low_24h": round(mid * 0.992, cfg["digits"]),
            }
            self.candle_cache[symbol] = self._generate_realistic_fallback_candles(symbol, mid, count=300)

    def _fetch_real_history_sync(self):
        """Synchronously pull real 1-minute historical candles from Yahoo Finance at startup."""
        try:
            import yfinance as yf
            tickers = list(YAHOO_MAP.values())
            data = yf.download(tickers, period="2d", interval="1m", progress=False, timeout=10)
            if data is not None and not data.empty:
                with self.lock:
                    self._parse_and_store_yahoo_data(data)
                print("Successfully loaded real 1-minute historical candles from market feed.")
        except Exception as e:
            print(f"Historical market backfill notice: {e}")

    def _parse_and_store_yahoo_data(self, data):
        """Parse multi-ticker dataframe into continuous 1-minute OHLCV candle lists."""
        for sym, yticker in YAHOO_MAP.items():
            if sym not in INSTRUMENTS:
                continue
            cfg = INSTRUMENTS[sym]
            try:
                if yticker in data["Close"].columns:
                    s_close = data["Close"][yticker].dropna()
                    s_open = data["Open"][yticker].dropna()
                    s_high = data["High"][yticker].dropna()
                    s_low = data["Low"][yticker].dropna()
                    s_vol = data["Volume"][yticker].dropna() if "Volume" in data else None
                else:
                    s_close = data["Close"].dropna()
                    s_open = data["Open"].dropna()
                    s_high = data["High"].dropna()
                    s_low = data["Low"].dropna()
                    s_vol = data["Volume"].dropna() if "Volume" in data else None

                if len(s_close) == 0:
                    continue

                real_candles = []
                for ts, c_val in s_close.items():
                    if ts in s_open and ts in s_high and ts in s_low:
                        o_val = float(s_open[ts])
                        h_val = float(s_high[ts])
                        l_val = float(s_low[ts])
                        vol = int(s_vol[ts]) if s_vol is not None and ts in s_vol else 100
                        real_candles.append({
                            "time": int(ts.timestamp()),
                            "open": round(o_val, cfg["digits"]),
                            "high": round(h_val, cfg["digits"]),
                            "low": round(l_val, cfg["digits"]),
                            "close": round(float(c_val), cfg["digits"]),
                            "volume": max(vol, 10)
                        })

                if real_candles:
                    self.candle_cache[sym] = real_candles
                    last_c = real_candles[-1]
                    spread = cfg["spread"]
                    self.prices[sym]["mid"] = last_c["close"]
                    self.prices[sym]["bid"] = round(last_c["close"] - spread / 2, cfg["digits"])
                    self.prices[sym]["ask"] = round(last_c["close"] + spread / 2, cfg["digits"])
            except Exception as ex:
                pass

    def _sync_live_prices(self):
        """Live price feed: Angel One 1s WebSocket/REST polling + periodic Yahoo backfill."""
        def angel_one_worker():
            import pyotp
            import os
            from SmartApi import SmartConnect
            
            ANGEL_MAP = {
                "NIFTY50":    ("NSE", "26000"),
                "BANKNIFTY":  ("NSE", "26009"),
                "FINNIFTY":   ("NSE", "26037"),
                "MIDCPNIFTY": ("NSE", "26074"),
                "RELIANCE":   ("NSE", "2885"),
                "HDFCBANK":   ("NSE", "1333"),
                "SENSEX":     ("BSE", "99919000"),
            }
            
            api_key = os.getenv("ANGEL_API_KEY", "3EWlZO4e")
            client_code = os.getenv("ANGEL_CLIENT_CODE", "G140240")
            pin = os.getenv("ANGEL_PIN", "5012")
            totp_key = os.getenv("ANGEL_TOTP_KEY", "FMKOE2BD2DHDRUPAI4AV3BWNKU")
            
            obj = SmartConnect(api_key=api_key)
            try:
                totp = pyotp.TOTP(totp_key).now()
                obj.generateSession(client_code, pin, totp)
                print("Angel One Live Data Stream Connected Successfully!")
            except Exception as e:
                print("Failed to authenticate Angel One:", e)
                
            exchangeTokens = {"NSE": [], "BSE": []}
            token_to_sym = {}
            for sym, (exch, token) in ANGEL_MAP.items():
                exchangeTokens[exch].append(token)
                token_to_sym[token] = sym
                
            while True:
                try:
                    res = obj.getMarketData("FULL", exchangeTokens)
                    if res and res.get("status") and res.get("data"):
                        fetched = res["data"].get("fetched", [])
                        with self.lock:
                            for item in fetched:
                                token = item.get("symbolToken")
                                if token in token_to_sym:
                                    sym = token_to_sym[token]
                                    if sym not in INSTRUMENTS:
                                        continue
                                    cfg = INSTRUMENTS[sym]
                                    
                                    last_p = item.get("ltp")
                                    if not last_p or last_p <= 0:
                                        continue
                                        
                                    spread = cfg["spread"]
                                    self.prices[sym]["mid"] = round(last_p, cfg["digits"])
                                    self.prices[sym]["bid"] = round(last_p - spread / 2, cfg["digits"])
                                    self.prices[sym]["ask"] = round(last_p + spread / 2, cfg["digits"])
                                    
                                    now_ts = int(time.time())
                                    if sym in self.candle_cache and len(self.candle_cache[sym]) > 0:
                                        last_c = self.candle_cache[sym][-1]
                                        if now_ts - last_c["time"] < 60: 
                                            last_c["close"] = round(last_p, cfg["digits"])
                                            last_c["high"] = round(max(last_c["high"], last_p), cfg["digits"])
                                            last_c["low"] = round(min(last_c["low"], last_p), cfg["digits"])
                                        else:
                                            new_candle = {
                                                "time": now_ts - (now_ts % 60),
                                                "open": last_c["close"],
                                                "high": max(last_c["close"], last_p),
                                                "low": min(last_c["close"], last_p),
                                                "close": last_p,
                                                "volume": item.get("tradeVolume", 100)
                                            }
                                            self.candle_cache[sym].append(new_candle)
                                            if len(self.candle_cache[sym]) > 1000:
                                                self.candle_cache[sym].pop(0)
                except Exception as e:
                    pass
                time.sleep(1)

        def fetch_worker():
            """Periodic 2-minute history refresher to keep long timeframe charts fresh."""
            import yfinance as yf
            while True:
                time.sleep(120)
                try:
                    tickers = list(YAHOO_MAP.values())
                    data = yf.download(tickers, period="2d", interval="1m", progress=False, timeout=10)
                    if data is not None and not data.empty:
                        with self.lock:
                            self._parse_and_store_yahoo_data(data)
                except Exception:
                    pass

        threading.Thread(target=fetch_worker, daemon=True).start()
        threading.Thread(target=angel_one_worker, daemon=True).start()

    def tick(self, symbol: str = None) -> Dict[str, Any]:
        """Advance price ticks or return current live snapshot."""
        with self.lock:
            return {k: v.copy() for k, v in self.prices.items()}

    def _generate_realistic_fallback_candles(self, symbol: str, current_p: float, count: int = 300) -> List[Dict[str, Any]]:
        """Generates authentic looking 1-minute candles if real API has no response."""
        cfg = INSTRUMENTS.get(symbol, {"base_price": 100.0, "volatility": 1.0, "digits": 2})
        digits = cfg.get("digits", 2)
        candles = []
        now = datetime.now(timezone.utc)
        
        price = current_p * (1.0 - (count * 0.0001))
        for i in range(count, 0, -1):
            t = now - timedelta(minutes=i)
            ts = int(t.timestamp())
            
            pct_move = random.gauss(0, 0.0006)
            open_val = price
            close_val = price * (1.0 + pct_move)
            wick_high = max(open_val, close_val) * (1.0 + abs(random.gauss(0, 0.0004)))
            wick_low = min(open_val, close_val) * (1.0 - abs(random.gauss(0, 0.0004)))
            
            candles.append({
                "time": ts,
                "open": round(open_val, digits),
                "high": round(wick_high, digits),
                "low": round(wick_low, digits),
                "close": round(close_val, digits),
                "volume": random.randint(50, 1500)
            })
            price = close_val
            
        return candles

    def get_candles(self, symbol: str, count: int = 500) -> List[Dict[str, Any]]:
        with self.lock:
            # Handle Options mathematically derived from underlying index
            if symbol.endswith("CE") or symbol.endswith("PE"):
                if "BANKNIFTY" in symbol:
                    underlying = "BANKNIFTY"
                elif "FINNIFTY" in symbol:
                    underlying = "FINNIFTY"
                elif "MIDCPNIFTY" in symbol:
                    underlying = "MIDCPNIFTY"
                elif "SENSEX" in symbol:
                    underlying = "SENSEX"
                else:
                    underlying = "NIFTY50"

                underlying_candles = self.candle_cache.get(underlying, [])[-count:]
                is_call = symbol.endswith("CE")
                
                option_candles = []
                for uc in underlying_candles:
                    base_close = calculate_option_price_live(symbol, uc["close"]) or 150.0
                    base_open = calculate_option_price_live(symbol, uc["open"]) or base_close
                    base_high = calculate_option_price_live(symbol, uc["high"] if is_call else uc["low"]) or max(base_open, base_close)
                    base_low = calculate_option_price_live(symbol, uc["low"] if is_call else uc["high"]) or min(base_open, base_close)
                    
                    option_candles.append({
                        "time": uc["time"],
                        "open": round(base_open, 2),
                        "high": round(max(base_high, base_open, base_close), 2),
                        "low": round(max(0.05, min(base_low, base_open, base_close)), 2),
                        "close": round(base_close, 2),
                        "volume": uc.get("volume", 200)
                    })
                return option_candles

            return self.candle_cache.get(symbol, [])[-count:]

    def get_all_prices(self) -> List[Dict[str, Any]]:
        self.tick()
        with self.lock:
            result = []
            for sym, cfg in INSTRUMENTS.items():
                p = self.prices[sym]
                result.append({
                    "symbol": sym,
                    "name": cfg["name"],
                    "category": cfg["category"],
                    "bid": p["bid"],
                    "ask": p["ask"],
                    "mid": p["mid"],
                    "spread_pips": round(cfg["spread"] / cfg["pip_size"], 1),
                    "digits": cfg["digits"],
                    "change_24h": p["change_24h"],
                    "high_24h": p["high_24h"],
                    "low_24h": p["low_24h"]
                })
            return result

    def get_prices(self) -> Dict[str, Dict[str, float]]:
        with self.lock:
            res = {k: v.copy() for k, v in self.prices.items()}
            return res

    def get_price(self, symbol: str) -> Dict[str, float]:
        with self.lock:
            if symbol in self.prices:
                return self.prices[symbol].copy()
            
            # If Option
            if symbol.endswith("CE") or symbol.endswith("PE"):
                if "BANKNIFTY" in symbol:
                    underlying = "BANKNIFTY"
                elif "FINNIFTY" in symbol:
                    underlying = "FINNIFTY"
                elif "MIDCPNIFTY" in symbol:
                    underlying = "MIDCPNIFTY"
                elif "SENSEX" in symbol:
                    underlying = "SENSEX"
                else:
                    underlying = "NIFTY50"

                u_price = self.prices.get(underlying, {}).get("mid", 24080.0)
                opt_price = calculate_option_price_live(symbol, u_price) or 100.0
                return {
                    "bid": round(opt_price - 0.25, 2),
                    "ask": round(opt_price + 0.25, 2),
                    "mid": round(opt_price, 2),
                    "change_24h": round(random.uniform(-3.5, 5.0), 2),
                    "high_24h": round(opt_price * 1.15, 2),
                    "low_24h": round(opt_price * 0.85, 2)
                }

            return {
                "bid": 100.0,
                "ask": 100.5,
                "mid": 100.25,
                "change_24h": 0.0,
                "high_24h": 105.0,
                "low_24h": 95.0
            }

    def calculate_pnl(self, symbol: str, order_type: str, lots: float, open_price: float) -> tuple[float, float, float]:
        is_option = symbol.endswith("CE") or symbol.endswith("PE")
        
        if not is_option and symbol not in INSTRUMENTS:
            return 0.0, open_price, 0.0
            
        if is_option:
            if "BANKNIFTY" in symbol:
                underlying = "BANKNIFTY"
            elif "FINNIFTY" in symbol:
                underlying = "FINNIFTY"
            elif "MIDCPNIFTY" in symbol:
                underlying = "MIDCPNIFTY"
            elif "SENSEX" in symbol:
                underlying = "SENSEX"
            elif "NIFTY" in symbol:
                underlying = "NIFTY50"
            else:
                underlying = "NIFTY50"
            underlying_spot = self.prices.get(underlying, {}).get("mid", 24080.0)
            opt_price = calculate_option_price_live(symbol, underlying_spot)
            if opt_price is None: opt_price = open_price
            
            # Options spread logic
            bid = opt_price - 0.25
            ask = opt_price + 0.25
            
            current_exit_price = bid if order_type == "BUY" else ask
            diff = current_exit_price - open_price if order_type == "BUY" else open_price - current_exit_price
            
            pips = diff
            pnl = diff * lots
            
            turnover = (open_price + current_exit_price) * lots
            stt_and_charges = turnover * 0.000125
            total_fees = stt_and_charges + 40.0
            pnl -= total_fees
            return round(pnl, 2), round(current_exit_price, 2), round(pips, 1)

        # Standard instruments
        cfg = INSTRUMENTS[symbol]
        cur_p = self.prices[symbol]
        
        if order_type == "BUY":
            current_exit_price = cur_p["bid"]
            diff = current_exit_price - open_price
        else:
            current_exit_price = cur_p["ask"]
            diff = open_price - current_exit_price

        pips = diff / cfg["pip_size"]
        pnl = diff * lots
        
        turnover = (open_price + current_exit_price) * lots
        stt_and_charges = turnover * 0.000125
        total_fees = stt_and_charges + 40.0
        pnl -= total_fees

        return round(pnl, 2), round(current_exit_price, cfg["digits"]), round(pips, 1)

market_engine = MarketDataEngine()
