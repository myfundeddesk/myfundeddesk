import urllib.request, json
try:
    req = urllib.request.Request("https://symbol-search.tradingview.com/symbol_search/v3/?text=INDIA50&hl=1&exchange=CAPITALCOM&lang=en", headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req).read().decode('utf-8')
    print(res)
except Exception as e:
    print(e)
