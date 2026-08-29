from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from app.config import APP_NAME, APP_TAGLINE
from app.database import get_db
from app.models import ChallengePackage
from app.security import get_optional_user

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request, user = Depends(get_optional_user), db: Session = Depends(get_db)):
    packages = db.query(ChallengePackage).order_by(ChallengePackage.price.asc()).all()
    
    
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

    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context={
            "app_name": APP_NAME,
            "app_tagline": APP_TAGLINE,
            "user": user,
            "packages": packages,
            "landing_data": landing_data
        }
    )

from app.models import DynamicPage, AppSetting
@router.get('/page/{slug}', response_class=HTMLResponse)
async def dynamic_page_view(request: Request, slug: str, db: Session = Depends(get_db)):
    page = db.query(DynamicPage).filter(DynamicPage.slug == slug, DynamicPage.is_published == True).first()
    if not page:
        return HTMLResponse('Page not found', status_code=404)
    return templates.TemplateResponse(request=request, name='dynamic_page.html', context={'page': page, 'app_name': APP_NAME})

