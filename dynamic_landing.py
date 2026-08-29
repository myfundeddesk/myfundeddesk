with open("app/routers/landing.py", "r", encoding="utf-8") as f:
    text = f.read()

# Add get_settings to pass to landing.html
import_injection = "from app.models import DynamicPage, AppSetting"

if "AppSetting" not in text:
    text = text.replace("from app.models import DynamicPage", import_injection)

# Get settings in landing_page
settings_logic = """
    # Fetch Customizer Settings
    settings_db = db.query(AppSetting).all()
    settings = {s.key: s.value for s in settings_db}
    
    # Defaults
    landing_data = {
        'hero_title_1': settings.get('landing_hero_title_1', 'Built for Traders.'),
        'hero_title_2': settings.get('landing_hero_title_2', 'Funded by Us.'),
        'hero_subtitle': settings.get('landing_hero_subtitle', 'We provide up to ?1,00,00,000 in real capital. You keep 90% of the profits. No hidden rules. No excuses. Just pure trading.'),
        'announcement_text': settings.get('landing_announcement', '?? Update 2.0: 100k Instant account')
    }
"""

if "landing_data" not in text:
    # insert inside landing_page before return
    insert_pos = text.find('return templates.TemplateResponse')
    text = text[:insert_pos] + settings_logic + "\n    " + text[insert_pos:]
    
    # Update context
    text = text.replace('"packages": packages', '"packages": packages,\n            "landing_data": landing_data')
    
    with open("app/routers/landing.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Injected customizer logic into landing.py")
else:
    print("Already injected.")
