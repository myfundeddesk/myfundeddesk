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
        'hero_subtitle': settings.get('landing_hero_subtitle', 'We provide up to ₹1,00,00,000 in real capital. You keep 90% of the profits. No hidden rules. No excuses. Just pure trading.'),
        'announcement_text': settings.get('landing_announcement', '🚀 Update 2.0: 100k Instant account'),
        'step1_title': settings.get('landing_step1_title', '1. Choose Your Challenge'),
        'step1_desc': settings.get('landing_step1_desc', 'Select a funding package that suits your trading style and risk appetite.'),
        'step2_title': settings.get('landing_step2_title', '2. Prove Your Skills'),
        'step2_desc': settings.get('landing_step2_desc', 'Trade securely on our proprietary terminal and meet the profit targets.'),
        'step3_title': settings.get('landing_step3_title', '3. Get Funded & Payouts'),
        'step3_desc': settings.get('landing_step3_desc', 'Once you pass, trade our capital and request payouts up to 90% profit split.')
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
@router.get('/{slug}', response_class=HTMLResponse)
async def dynamic_page_view(request: Request, slug: str, db: Session = Depends(get_db)):
    page = db.query(DynamicPage).filter(DynamicPage.slug == slug, DynamicPage.is_published == True).first()
    if not page:
        return HTMLResponse('Page not found', status_code=404)
    return templates.TemplateResponse(request=request, name='dynamic_page.html', context={'page': page, 'app_name': APP_NAME})


from pydantic import BaseModel
class ContactForm(BaseModel):
    name: str
    email: str
    subject: str
    message: str

@router.post('/api/contact')
async def submit_contact(data: ContactForm, db: Session = Depends(get_db)):
    try:
        # Save to DB
        from app.models import ContactMessage
        msg = ContactMessage(name=data.name, email=data.email, subject=data.subject, message=data.message)
        db.add(msg)
        db.commit()
        
        # Send Email to myfundeddesk@gmail.com
        from app.email_service import send_activity_email
        send_activity_email(
            'myfundeddesk@gmail.com',
            subject=f"New Contact from {data.name}: {data.subject}",
            headline="New Support Request",
            message=data.message,
            request_info={"Sender Name": data.name, "Sender Email": data.email}
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

from fastapi.responses import RedirectResponse
@router.get('/page/{slug}')
async def redirect_old_page(slug: str):
    return RedirectResponse(url=f'/{slug}', status_code=301)
