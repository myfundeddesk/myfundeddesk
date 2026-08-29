with open('old_admin2.html', 'r', encoding='utf-16') as f:
    text = f.read()

def extract_tab(tab_id):
    start = text.find(f'<div id="{tab_id}"')
    if start == -1: return ""
    end = text.find('<div id="tab-', start + 10)
    if end == -1: end = text.find('</main>')
    return text[start:end]

for tab in ['tab-packages', 'tab-trades', 'tab-settings']:
    with open(f'{tab.replace("-", "_")}.html', 'w', encoding='utf-8') as out:
        out.write(extract_tab(tab))
