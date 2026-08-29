with open("app/routers/admin_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

customizer_api = """
@router.post('/admin/api/customize')
async def save_customizer(
    request: Request,
    hero_title_1: str = Form(...),
    hero_title_2: str = Form(...),
    hero_subtitle: str = Form(...),
    primary_color: str = Form(...),
    announcement_text: str = Form(...),
    db: Session = Depends(get_db)
):
    require_super_admin(request)
    
    settings = {
        'landing_hero_title_1': hero_title_1,
        'landing_hero_title_2': hero_title_2,
        'landing_hero_subtitle': hero_subtitle,
        'landing_primary_color': primary_color,
        'landing_announcement': announcement_text
    }
    
    for key, value in settings.items():
        db_setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        if db_setting:
            db_setting.value = value
        else:
            db_setting = AppSetting(key=key, value=value)
            db.add(db_setting)
            
    db.commit()
    return RedirectResponse(url='/admin?updated=true', status_code=303)
"""

if "save_customizer" not in text:
    text += "\n" + customizer_api
    with open("app/routers/admin_dashboard.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Added customizer API!")
