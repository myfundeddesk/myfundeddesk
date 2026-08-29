with open('app/templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

tabs_html = ""
for tab in ['tab_packages.html', 'tab_trades.html', 'tab_settings.html']:
    with open(tab, 'r', encoding='utf-8') as f:
        tabs_html += f.read() + "\n\n"

target = '<!-- TAB: USERS -->'
if target in text:
    if "id=\"tab-packages\"" not in text:
        text = text.replace(target, tabs_html + target)
        with open('app/templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Injected missing tabs!")
    else:
        print("Tabs already exist.")
else:
    print("Could not find target block.")
