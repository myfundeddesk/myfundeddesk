import random
import time
import threading
import httpx
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from app.engine.options_engine import calculate_option_price_live

# Institutional Market Instruments
INSTRUMENTS = {
    "NIFTY50": {
        "name": "NIFTY 50 Index (NSE)",
        "category": "Indices",
        "base_price": 24200.0,
        "spread": 1.5,
        "digits": 2,
        "pip_size": 1.0,
        "contract_size": 25,  # Lot size for Nifty
        "volatility": 1.5,
    },
    "BANKNIFTY": {
        "name": "NIFTY BANK Index (NSE)",
        "category": "Indices",
        "base_price": 57500.0,
        "spread": 2.5,
        "digits": 2,
        "pip_size": 1.0,
        "contract_size": 15,  # Lot size for BankNifty
        "volatility": 3.0,
    },
    "SENSEX": {
        "name": "BSE SENSEX Index",
        "category": "Indices",
        "base_price": 80500.0,
        "spread": 5.0,
        "digits": 2,
        "pip_size": 1.0,
        "contract_size": 10,
        "volatility": 4.0,
    },
    "FINNIFTY": {
        "name": "NIFTY FIN SERVICE (NSE)",
        "category": "Indices",
        "base_price": 22500.0,
        "spread": 1.2,
        "digits": 2,
        "pip_size": 1.0,
        "contract_size": 25,
        "volatility": 1.2,
    },
    "MIDCPNIFTY": {
        "name": "NIFTY MIDCAP SELECT",
        "category": "Indices",
        "base_price": 12500.0,
        "spread": 1.0,
        "digits": 2,
        "pip_size": 1.0,
        "contract_size": 50,
        "volatility": 1.0,
    },
    "RELIANCE": {
        "name": "Reliance Industries (NSE)",
        "category": "Equities",
        "base_price": 2950.0,
        "spread": 0.5,
        "digits": 2,
        "pip_size": 0.05,
        "contract_size": 250,
        "volatility": 0.5,
    },
    "HDFCBANK": {
        "name": "HDFC Bank Ltd (NSE)",
        "category": "Equities",
        "base_price": 1650.0,
        "spread": 0.3,
        "digits": 2,
        "pip_size": 0.05,
        "contract_size": 550,
        "volatility": 10.0,
    }
}

class MarketDataEngine:
    def __init__(self):
        self.prices: Dict[str, Dict[str, float]] = {}
        self.candle_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.lock = threading.Lock()
        self._initialize_prices()
        self._sync_live_prices()

    def _initialize_prices(self):
        for symbol, cfg in INSTRUMENTS.items():
            mid = cfg["base_price"]
            spread = cfg["spread"]
            self.prices[symbol] = {
                "bid": round(mid - spread / 2, cfg["digits"]),
                "ask": round(mid + spread / 2, cfg["digits"]),
                "mid": mid,
                "change_24h": round(random.uniform(-1.2, 2.5), 2),
                "high_24h": round(mid * 1.018, cfg["digits"]),
                "low_24h": round(mid * 0.982, cfg["digits"]),
            }
            self.candle_cache[symbol] = self._generate_initial_candles(symbol, count=120)

    def _sync_live_prices(self):
        """Fetch REAL live Indian market prices from Yahoo Finance every 5 seconds."""
        # Yahoo Finance symbol mapping for NSE indices & stocks
        YAHOO_MAP = {
            "NIFTY50":    "^NSEI",
            "BANKNIFTY":  "^NSEBANK",
            "SENSEX":     "^BSESN",
            "FINNIFTY":   "NIFTY_FIN_SERVICE.NS",
            "MIDCPNIFTY": "^NSEMDCP50",
            "RELIANCE":   "RELIANCE.NS",
            "HDFCBANK":   "HDFCBANK.NS",
        }

        def fetch_worker():
            while True:
                try:
                    import yfinance as yf
                    tickers = list(YAHOO_MAP.values())
                    data = yf.download(tickers, period="1d", interval="1m", progress=False, threads=True)
                    
                    if data is not None and not data.empty:
                        close_data = data["Close"] if "Close" in data.columns else None
                        if close_data is not None:
                            with self.lock:
                                for sym, yticker in YAHOO_MAP.items():
                                    if sym not in INSTRUMENTS:
                                        continue
                                    try:
                                        cfg = INSTRUMENTS[sym]
                                        
                                        if yticker in data["Close"].columns:
                                            series_close = data["Close"][yticker].dropna()
                                            series_open = data["Open"][yticker].dropna()
                                            series_high = data["High"][yticker].dropna()
                                            series_low = data["Low"][yticker].dropna()
                                        else:
                                            series_close = data["Close"].dropna()
                                            series_open = data["Open"].dropna()
                                            series_high = data["High"].dropna()
                                            series_low = data["Low"].dropna()
                                        
                                        if len(series_close) == 0:
                                            continue
                                        
                                        last_p = float(series_close.iloc[-1])
                                        if last_p <= 0:
                                            continue
                                        
                                        spread = cfg["spread"]
                                        self.prices[sym]["mid"] = round(last_p, cfg["digits"])
                                        self.prices[sym]["bid"] = round(last_p - spread / 2, cfg["digits"])
                                        self.prices[sym]["ask"] = round(last_p + spread / 2, cfg["digits"])
                                        
                                        # Overwrite candle cache with REAL historical data
                                        real_candles = []
                                        for ts, close_val in series_close.items():
                                            if ts in series_open and ts in series_high and ts in series_low:
                                                real_candles.append({
                                                    "time": int(ts.timestamp()),
                                                    "open": round(float(series_open[ts]), cfg["digits"]),
                                                    "high": round(float(series_high[ts]), cfg["digits"]),
                                                    "low": round(float(series_low[ts]), cfg["digits"]),
                                                    "close": round(float(close_val), cfg["digits"]),
                                                    "volume": 100
                                                })
                                        
                                        if real_candles:
                                            self.candle_cache[sym] = real_candles
                                        if len(self.candle_cache[sym]) > 500:
                                            self.candle_cache[sym].pop(0)
                                    except Exception:
                                        pass
                except Exception:
                    pass  # Silently fall back to stochastic generation if offline
                
                time.sleep(5)  # Refresh every 5 seconds

        t = threading.Thread(target=fetch_worker, daemon=True)
        t.start()


    def _generate_initial_candles(self, symbol: str, count: int = 120) -> List[Dict[str, Any]]:
        is_option = symbol.endswith("CE") or symbol.endswith("PE")
        candles = []
        now = datetime.now(timezone.utc)
        
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
            # Get underlying candles
            if underlying not in self.candle_cache:
                self.candle_cache[underlying] = self._generate_initial_candles(underlying, count)
            
            from .options_engine import calculate_option_price_live
            
            underlying_candles = self.candle_cache[underlying][-count:]
            for uc in underlying_candles:
                base_p = calculate_option_price_live(symbol, uc["close"])
                if base_p is None: base_p = 150.0
                
                # Mock high/low around base_p
                vol = base_p * 0.05
                candles.append({
                    "time": uc["time"],
                    "open": round(base_p + random.uniform(-vol, vol), 2),
                    "high": round(base_p + vol + random.uniform(0, vol), 2),
                    "low": round(max(0.05, base_p - vol - random.uniform(0, vol)), 2),
                    "close": round(base_p, 2),
                    "volume": random.randint(100, 1000)
                })
        else:
            cfg = INSTRUMENTS.get(symbol, {"base_price": 100.0, "volatility": 1.0, "digits": 2})
            current_p = cfg.get("base_price", 100.0)
            
            for i in range(count, 0, -1):
                t = now - timedelta(minutes=i * 5)
                timestamp = int(t.timestamp())
                
                volatility = cfg.get("volatility", 1.0)
                change = random.uniform(-volatility, volatility)
                
                o = current_p
                c = current_p + change
                h = max(o, c) + random.uniform(0, volatility * 0.5)
                l = min(o, c) - random.uniform(0, volatility * 0.5)
                
                candles.append({
                    "time": timestamp,
                    "open": round(o, cfg.get("digits", 2)),
                    "high": round(h, cfg.get("digits", 2)),
                    "low": round(l, cfg.get("digits", 2)),
                    "close": round(c, cfg.get("digits", 2)),
                    "volume": random.randint(100, 1000)
                })
                current_p = c
                
        return candles

    def tick(self, symbol: str = None) -> Dict[str, Any]:
        """Advance price ticks dynamically"""
        symbols_to_tick = [symbol] if symbol and symbol in INSTRUMENTS else list(INSTRUMENTS.keys())
        updated = {}

        with self.lock:
            for sym in symbols_to_tick:
                cfg = INSTRUMENTS[sym]
                cur_mid = self.prices[sym]["mid"]
                vol = cfg["volatility"] * random.uniform(0.4, 1.6)
                step = random.gauss(0, vol)
                
                new_mid = max(cfg["base_price"] * 0.4, cur_mid + step)
                new_bid = round(new_mid - cfg["spread"] / 2, cfg["digits"])
                new_ask = round(new_mid + cfg["spread"] / 2, cfg["digits"])
                
                self.prices[sym]["mid"] = round(new_mid, cfg["digits"])
                self.prices[sym]["bid"] = new_bid
                self.prices[sym]["ask"] = new_ask

                if sym in self.candle_cache and self.candle_cache[sym]:
                    last_c = self.candle_cache[sym][-1]
                    now_ts = int(time.time())
                    if now_ts - last_c["time"] < 300:
                        last_c["close"] = round(new_mid, cfg["digits"])
                        last_c["high"] = max(last_c["high"], round(new_mid, cfg["digits"]))
                        last_c["low"] = min(last_c["low"], round(new_mid, cfg["digits"]))
                        last_c["volume"] += 1
                    else:
                        self.candle_cache[sym].append({
                            "time": now_ts,
                            "open": round(new_mid, cfg["digits"]),
                            "high": round(new_mid, cfg["digits"]),
                            "low": round(new_mid, cfg["digits"]),
                            "close": round(new_mid, cfg["digits"]),
                            "volume": 1
                        })
                        if len(self.candle_cache[sym]) > 500:
                            self.candle_cache[sym].pop(0)

                updated[sym] = {
                    "symbol": sym,
                    "name": cfg["name"],
                    "category": cfg["category"],
                    "bid": new_bid,
                    "ask": new_ask,
                    "mid": round(new_mid, cfg["digits"]),
                    "spread_pips": round(cfg["spread"] / cfg["pip_size"], 1),
                    "digits": cfg["digits"],
                    "change_24h": self.prices[sym]["change_24h"]
                }

        return updated

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

    def get_candles(self, symbol: str) -> List[Dict[str, Any]]:
        with self.lock:
            is_option = symbol.endswith("CE") or symbol.endswith("PE")
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
                    
                if underlying not in self.candle_cache:
                    self.candle_cache[underlying] = self._generate_initial_candles(underlying)
                    
                from .options_engine import calculate_option_price_live
                import random
                
                underlying_candles = self.candle_cache[underlying]
                option_candles = []
                for uc in underlying_candles:
                    base_p = calculate_option_price_live(symbol, uc["close"])
                    if base_p is None: base_p = 150.0
                    vol = base_p * 0.05
                    option_candles.append({
                        "time": uc["time"],
                        "open": round(base_p + random.uniform(-vol, vol), 2),
                        "high": round(base_p + vol + random.uniform(0, vol), 2),
                        "low": round(max(0.05, base_p - vol - random.uniform(0, vol)), 2),
                        "close": round(base_p, 2),
                        "volume": random.randint(100, 1000)
                    })
                return option_candles
            else:
                if symbol not in self.candle_cache:
                    self.candle_cache[symbol] = self._generate_initial_candles(symbol)
                return list(self.candle_cache[symbol])

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
            underlying_spot = self.prices[underlying]["mid"]
            opt_price = calculate_option_price_live(symbol, underlying_spot)
            if opt_price is None: opt_price = open_price
            
            # Options spread logic
            bid = opt_price - 0.25
            ask = opt_price + 0.25
            
            current_exit_price = bid if order_type == "BUY" else ask
            diff = current_exit_price - open_price if order_type == "BUY" else open_price - current_exit_price
            
            pips = diff
            if "BANKNIFTY" in symbol:
                contract_size = 15
            elif "FINNIFTY" in symbol:
                contract_size = 40
            elif "MIDCPNIFTY" in symbol:
                contract_size = 75
            elif "SENSEX" in symbol:
                contract_size = 10
            elif "NIFTY" in symbol:
                contract_size = 25
            else:
                contract_size = 25
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

        if "JPY" in symbol:
            pnl = pnl / cur_p["mid"]

        return round(pnl, 2), round(current_exit_price, cfg["digits"]), round(pips, 1)

# Global engine instance
market_engine = MarketDataEngine()

# Global notifications store
admin_notifications = {}
