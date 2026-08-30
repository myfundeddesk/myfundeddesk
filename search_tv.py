import urllib.request, json
url = 'https://symbol-search.tradingview.com/symbol_search/v3/?text=NIFTY&hl=1&lang=en&domain=production'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for d in data.get('symbols', []):
            if d.get('type') == 'cfd' or d.get('exchange') not in ['NSE', 'BSE', 'NSEIX']:
                print(f"{d.get('exchange')}:{d.get('symbol').replace('<em>', '').replace('</em>', '')} ({d.get('type')})")
except Exception as e:
    print(e)
