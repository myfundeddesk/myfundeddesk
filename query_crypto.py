import urllib.request
import json
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
payload = b'{"symbols":{"tickers":["BINGX:NIFTY50USDT","BINGX:NIFTY50USDT.P"],"query":{"types":[]}}}'
req = urllib.request.Request('https://scanner.tradingview.com/crypto/scan', data=payload, headers={'User-Agent': 'Mozilla', 'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, context=ctx) as response:
        print(response.read().decode())
except Exception as e:
    print(e)

