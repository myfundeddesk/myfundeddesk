import urllib.request, json
try:
    req = urllib.request.Request("https://symbol-search.tradingview.com/symbol_search/v3/?text=SENSEX&hl=1&exchange=TVC&lang=en", headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req).read().decode('utf-8')
    data = json.loads(res)
    print("TVC SENSEX:", [s['symbol'] for s in data])
except Exception as e:
    print(e)
