with open('app/templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()
html = html.replace('<div id="tab-chat" class="tab-content">', '</div>\n<div id="tab-chat" class="tab-content">')
html = html.replace('<div id="tab-content" class="tab-content space-y-6">', '</div>\n<div id="tab-content" class="tab-content space-y-6">')
with open('app/templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

