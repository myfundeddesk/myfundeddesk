import urllib.request
import json
url = 'https://symbol-search.tradingview.com/symbol_search/v3/?text=NSEIX&hl=1&lang=en&domain=production'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Origin': 'https://www.tradingview.com', 'Referer': 'https://www.tradingview.com/'})
try:
    with urllib.request.urlopen(req) as response:
        content = response.read().decode()
        data = json.loads(content)
        for d in data.get('symbols', []):
            if d.get('exchange') == 'NSEIX':
                print(f"{d.get('exchange')}:{d.get('symbol').replace('<em>', '').replace('</em>', '')}")
except Exception as e:
    pass
