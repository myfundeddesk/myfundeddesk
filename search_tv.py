import urllib.request
import json
url = 'https://symbol-search.tradingview.com/symbol_search/v3/?text=India&hl=1&lang=en&domain=production'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        content = response.read().decode()
        data = json.loads(content)
        for d in data.get('symbols', []):
            if d.get('type') == 'cfd':
                print(f"{d.get('exchange')}:{d.get('symbol').replace('<em>', '').replace('</em>', '')} ({d.get('type')})")
except Exception as e:
    pass
