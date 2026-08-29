import urllib.request
import json
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
def search_tv(query):
    url = f'https://symbol-search.tradingview.com/symbol_search/v3/?text={query}&hl=1&exchange=&lang=en&domain=production'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode())
            print(f'Search for {query}:')
            for item in data[:5]:
                print(f"  {item.get('exchange')}:{item.get('symbol')} ({item.get('description')})")
    except Exception as e:
        print(f'Error searching {query}: {e}')
search_tv('NIFTY')
search_tv('BANKNIFTY')
search_tv('IN50')

