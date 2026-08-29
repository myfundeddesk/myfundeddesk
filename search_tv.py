import urllib.request
import json
def search_tv(query):
    url = f'https://symbol-search.tradingview.com/symbol_search/v3/?text={query}&hl=1&exchange=&lang=en&domain=production'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f'Search for {query}:')
            for item in data[:3]:
                print(f"  {item.get('exchange')}:{item.get('symbol')} ({item.get('description')})")
    except Exception as e:
        print(e)
search_tv('NIFTY')
search_tv('BANKNIFTY')
search_tv('FINNIFTY')
search_tv('SENSEX')
search_tv('RELIANCE')
search_tv('HDFCBANK')

