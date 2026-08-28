from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import User, TradingAccount, ChatMessage
from app.security import require_auth, get_current_user_from_request
from app.database import get_db
from app.config import APP_NAME

router = APIRouter()

ADMIN_SESSION_TOKEN = "super_admin_token_secure_9921"

def check_chat_auth(request: Request, db: Session):
    is_admin = request.cookies.get("admin_session") == ADMIN_SESSION_TOKEN
    user = get_current_user_from_request(request, db)
    if not is_admin and not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return is_admin, user

@router.post("/api/chat")
async def send_chat(request: Request, message: str = Form(...), target_user_id: int = Form(None), db: Session = Depends(get_db)):
    if not message.strip():
        return JSONResponse({"success": False})
        
    is_admin, user = check_chat_auth(request, db)
    if is_admin and target_user_id:
        room_user_id = target_user_id
    else:
        room_user_id = user.id if user else 0
    
    msg = ChatMessage(user_id=room_user_id, is_admin=is_admin, message=message.strip())
    db.add(msg)
    db.commit()
    return JSONResponse({"success": True})

@router.post("/api/chat/clear")
async def clear_chat(request: Request, db: Session = Depends(get_db)):
    is_admin, user = check_chat_auth(request, db)
    if not is_admin and user:
        db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
        db.commit()
    return JSONResponse({"success": True})

@router.get("/api/chat")
async def get_chat(request: Request, target_user_id: int = Query(None), db: Session = Depends(get_db)):
    is_admin, user = check_chat_auth(request, db)
    
    if is_admin:
        if target_user_id:
            messages = db.query(ChatMessage).filter(ChatMessage.user_id == target_user_id).order_by(ChatMessage.created_at.desc()).limit(100).all()
        else:
            messages = db.query(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(100).all()
    else:
        messages = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(50).all()
    
    return JSONResponse([
        {"id": m.id, "user_id": m.user_id, "is_admin": m.is_admin, "message": m.message, "created_at": m.created_at.isoformat()}
        for m in reversed(messages)
    ])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


FEATURE_CONTENT = {
    "heatmap": {
        "title": "Market Heatmap",
        "icon": "bar-chart",
        "desc": "Real-time visualization of market movers.",
        "widget": '''<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-crypto-coins-heatmap.js" async>{"dataSource": "Crypto","blockSize": "market_cap_calc","blockColor": "change","locale": "en","symbolUrl": "","colorTheme": "dark","hasTopBar": false,"isDataSetEnabled": false,"isZoomEnabled": true,"hasSymbolTooltip": true,"width": "100%","height": "100%"}</script></div>'''
    },
    "news": {
        "title": "Market News",
        "icon": "newspaper",
        "desc": "Latest fundamental news and economic updates.",
        "widget": '''<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>{"feedMode": "all_symbols","colorTheme": "dark","isTransparent": true,"displayMode": "regular","width": "100%","height": "100%","locale": "en"}</script></div>'''
    },
    "calendar": {
        "title": "Economic Calendar",
        "icon": "calendar",
        "desc": "Track key economic events and data releases.",
        "widget": '''<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"colorTheme": "dark","isTransparent": true,"width": "100%","height": "100%","locale": "en","importanceFilter": "-1,0₹"}</script></div>'''
    },
    "leaderboard": {
        "title": "Leaderboard",
        "icon": "flag",
        "desc": "Top funded traders this month.",
        "widget": '''
        <div class="p-6">
            <div class="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4 flex items-center justify-between mb-6">
                <div>
                    <div class="text-indigo-400 font-bold">Your Global Rank</div>
                    <div class="text-2xl font-black text-white">#1,402</div>
                </div>
                <i data-lucide="award" class="w-10 h-10 text-indigo-500 opacity-50"></i>
            </div>
            <table class="w-full text-left">
                <thead><tr class="text-xs text-slate-500 uppercase"><th class="pb-3">Rank</th><th class="pb-3">Trader</th><th class="pb-3">Payout</th><th class="pb-3 text-right">Win Rate</th></tr></thead>
                <tbody class="text-slate-300">
                    <tr class="border-t border-slate-800"><td class="py-4 font-bold text-amber-500">1</td><td class="py-4 flex items-center gap-2"><img src="https://i.pravatar.cc/150?u=1" class="w-6 h-6 rounded-full"> Alex R.</td><td class="py-4 font-mono text-emerald-400">₹142,500</td><td class="py-4 text-right">82%</td></tr>
                    <tr class="border-t border-slate-800"><td class="py-4 font-bold text-slate-300">2</td><td class="py-4 flex items-center gap-2"><img src="https://i.pravatar.cc/150?u=2" class="w-6 h-6 rounded-full"> Sarah M.</td><td class="py-4 font-mono text-emerald-400">₹98,200</td><td class="py-4 text-right">79%</td></tr>
                    <tr class="border-t border-slate-800"><td class="py-4 font-bold text-amber-700">3</td><td class="py-4 flex items-center gap-2"><img src="https://i.pravatar.cc/150?u=3" class="w-6 h-6 rounded-full"> John D.</td><td class="py-4 font-mono text-emerald-400">₹84₹00</td><td class="py-4 text-right">76%</td></tr>
                </tbody>
            </table>
        </div>'''
    },
    "affiliate": {
        "title": "Affiliate Dashboard",
        "icon": "users",
        "desc": "Earn up to 20% commission on every referral.",
        "widget": '''
        <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                    <div class="text-xs text-slate-400 uppercase">Total Earned</div>
                    <div class="text-2xl font-black text-emerald-400 mt-1">₹0.00</div>
                </div>
                <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                    <div class="text-xs text-slate-400 uppercase">Active Referrals</div>
                    <div class="text-2xl font-black text-white mt-1">0</div>
                </div>
                <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                    <div class="text-xs text-slate-400 uppercase">Conversion Rate</div>
                    <div class="text-2xl font-black text-white mt-1">0%</div>
                </div>
            </div>
            <div class="mb-4 text-sm font-bold text-slate-400">Your Referral Link</div>
            <div class="flex gap-2">
                <input type="text" value="https://myfundeddesk.com/ref/user123" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-300" readonly>
                <button class="bg-primary text-white px-6 py-3 rounded-lg font-bold hover:bg-primary/80 transition-colors">Copy</button>
            </div>
        </div>'''
    },
    "support": {
        "title": "Help & Support",
        "icon": "life-buoy",
        "desc": "24/7 Priority Support for all our traders.",
        "widget": '''
        <div class="h-[500px] flex flex-col" x-data="{ messages: [], newMessage: '', fetchChat() { fetch('/api/chat').then(r=>r.json()).then(d=> { this.messages = d; setTimeout(()=>₹refs.chatbox.scrollTop = ₹refs.chatbox.scrollHeight, 100); }); }, clearChat() { if(confirm('Clear history?')) { fetch('/api/chat/clear', {method:'POST'}).then(()=>this.fetchChat()); } } }" x-init="fetchChat(); setInterval(()=>fetchChat(), 3000);">
            <div class="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
                <div class="font-bold flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div> Live Support</div>
                <div class="flex items-center gap-4">
                    <div class="text-xs text-slate-500">Average response: 3 mins</div>
                    <button @click="clearChat()" title="Clear Chat History" class="text-slate-400 hover:text-rose-500 transition-colors"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
                </div>
            </div>
            <div x-ref="chatbox" class="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-900/50">
                <template x-for="m in messages" :key="m.id">
                    <div class="flex flex-col" :class="m.is_admin ? 'items-start' : 'items-end'">
                        <div class="max-w-[80%] p-3 rounded-2xl" :class="m.is_admin ? 'bg-white dark:bg-slate-800 text-slate-800 dark:text-white rounded-tl-none border border-slate-200 dark:border-slate-700' : 'bg-blue-600 text-white rounded-tr-none shadow-md shadow-blue-500/20'">
                            <div class="text-xs font-bold mb-1 opacity-50" x-text="m.is_admin ? 'Support Agent' : ('User ' + m.user_id)"></div>
                            <p class="text-sm" x-text="m.message"></p>
                        </div>
                        <div class="text-[10px] text-slate-400 mt-1" x-text="new Date(m.created_at).toLocaleTimeString()"></div>
                    </div>
                </template>
                <div x-show="messages.length === 0" class="text-center text-slate-500 text-sm mt-10">Send a message to start chatting with support.</div>
            </div>
            <div class="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <form @submit.prevent="if(newMessage){ let fd = new FormData(); fd.append('message', newMessage); fetch('/api/chat', {method:'POST', body:fd}).then(()=>{ newMessage=''; fetchChat(); }); }">
                    <div class="flex gap-2">
                        <input type="text" x-model="newMessage" placeholder="Type your message..." class="flex-1 bg-slate-100 dark:bg-slate-800 border-none rounded-xl px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-white">
                        <button type="submit" class="bg-blue-600 text-white p-2 rounded-xl hover:bg-blue-500 transition-colors"><i data-lucide="send" class="w-5 h-5"></i></button>
                    </div>
                </form>
            </div>
        </div>
'''
    },
    "coupons": {
        "title": "Coupon Codes",
        "icon": "ticket",
        "desc": "Exclusive discounts and active promotions.",
        "widget": '''
        <div class="p-6 space-y-4">
            <div class="bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 p-6 rounded-2xl flex justify-between items-center">
                <div>
                    <div class="text-amber-500 font-black text-xl mb-1">SUMMER20</div>
                    <div class="text-slate-300 text-sm">Get 20% off all 1-Step Evaluation accounts. Valid until Aug 31.</div>
                </div>
                <button class="bg-amber-600 text-white font-bold py-2 px-6 rounded-lg shadow-lg hover:bg-amber-500">Copy</button>
            </div>
            <div class="bg-slate-800/50 border border-slate-700 p-6 rounded-2xl flex justify-between items-center">
                <div>
                    <div class="text-white font-black text-xl mb-1">RETRY10</div>
                    <div class="text-slate-400 text-sm">10% discount on challenge retries. Always active.</div>
                </div>
                <button class="bg-slate-700 text-white font-bold py-2 px-6 rounded-lg hover:bg-slate-600">Copy</button>
            </div>
        </div>'''
    },
    "giveaway": {
        "title": "FundedFirm Giveaway",
        "icon": "gift",
        "desc": "Participate to win free funded accounts.",
        "widget": '''
        <div class="p-6 text-center max-w-lg mx-auto py-12">
            <h2 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600 mb-4">Win a ₹100k Account</h2>
            <p class="text-slate-400 mb-8">Join our monthly giveaway. Complete social tasks to earn entries!</p>
            <div class="grid grid-cols-3 gap-4 mb-8">
                <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                    <div class="text-2xl font-black text-white">12</div>
                    <div class="text-[10px] text-slate-500 uppercase mt-1">Days</div>
                </div>
                <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                    <div class="text-2xl font-black text-white">08</div>
                    <div class="text-[10px] text-slate-500 uppercase mt-1">Hours</div>
                </div>
                <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                    <div class="text-2xl font-black text-white">45</div>
                    <div class="text-[10px] text-slate-500 uppercase mt-1">Mins</div>
                </div>
            </div>
            <button class="bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-4 px-8 rounded-xl w-full shadow-lg shadow-pink-500/20 hover:scale-105 transition-transform">Enter Giveaway Now</button>
        </div>'''
    },
    "comparison": {
        "title": "Account Comparison",
        "icon": "arrow-left-right",
        "desc": "Compare evaluation models side by side.",
        "widget": '''
        <div class="p-6 overflow-x-auto">
            <table class="w-full text-left">
                <thead><tr class="text-xs text-slate-400 uppercase bg-slate-800/50"><th class="p-4">Feature</th><th class="p-4">1-Step</th><th class="p-4">2-Step</th><th class="p-4">Instant</th></tr></thead>
                <tbody class="text-slate-300 divide-y divide-slate-800">
                    <tr><td class="p-4 font-bold text-white">Profit Target</td><td class="p-4 text-emerald-400 font-mono">10%</td><td class="p-4 text-emerald-400 font-mono">8% / 5%</td><td class="p-4 text-emerald-400 font-mono">10%</td></tr>
                    <tr><td class="p-4 font-bold text-white">Max Daily Loss</td><td class="p-4 text-rose-400 font-mono">4%</td><td class="p-4 text-rose-400 font-mono">5%</td><td class="p-4 text-rose-400 font-mono">5%</td></tr>
                    <tr><td class="p-4 font-bold text-white">Max Total Loss</td><td class="p-4 text-rose-400 font-mono">6%</td><td class="p-4 text-rose-400 font-mono">10%</td><td class="p-4 text-rose-400 font-mono">10%</td></tr>
                    <tr><td class="p-4 font-bold text-white">Time Limit</td><td class="p-4">Infinite</td><td class="p-4">Infinite</td><td class="p-4">Infinite</td></tr>
                    <tr><td class="p-4 font-bold text-white">Profit Split</td><td class="p-4 font-mono">80% - 90%</td><td class="p-4 font-mono">80% - 90%</td><td class="p-4 font-mono">70%</td></tr>
                </tbody>
            </table>
        </div>'''
    },
    "rules": {
        "title": "Trading Rules",
        "icon": "clipboard-list",
        "desc": "Core guidelines to keep your account safe.",
        "widget": '''
        <div class="p-6 space-y-6 text-slate-300">
            <div>
                <h4 class="text-white font-bold mb-2 flex items-center gap-2"><i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-500"></i> Expert Advisors (EAs)</h4>
                <p class="text-sm text-slate-400">You are fully allowed to use EAs, provided they do not use latency arbitrage or high-frequency tick scalping.</p>
            </div>
            <div>
                <h4 class="text-white font-bold mb-2 flex items-center gap-2"><i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-500"></i> News Trading</h4>
                <p class="text-sm text-slate-400">Trading during high-impact news is permitted on all accounts. However, slippage is out of our control.</p>
            </div>
            <div>
                <h4 class="text-white font-bold mb-2 flex items-center gap-2"><i data-lucide="alert-triangle" class="w-4 h-4 text-rose-500"></i> Account Sharing</h4>
                <p class="text-sm text-slate-400">Accessing your account from different countries simultaneously or sharing credentials will result in instant termination.</p>
            </div>
        </div>'''
    },
    "privacy": {
        "title": "Data & Privacy",
        "icon": "lock",
        "desc": "Manage how we handle your personal data.",
        "widget": '''
        <div class="p-6 max-w-2xl">
            <p class="text-slate-400 mb-6">We take your privacy seriously. Your KYC documents and trading data are encrypted using bank-grade AES-256 encryption.</p>
            <div class="space-y-4">
                <label class="flex items-center gap-3 p-4 bg-slate-800/50 rounded-xl border border-slate-700 cursor-pointer">
                    <input type="checkbox" checked class="w-5 h-5 accent-emerald-500">
                    <div>
                        <div class="font-bold text-white">Marketing Emails</div>
                        <div class="text-xs text-slate-400">Receive updates about new features and discounts.</div>
                    </div>
                </label>
                <label class="flex items-center gap-3 p-4 bg-slate-800/50 rounded-xl border border-slate-700 cursor-pointer">
                    <input type="checkbox" checked class="w-5 h-5 accent-emerald-500">
                    <div>
                        <div class="font-bold text-white">Performance Analytics</div>
                        <div class="text-xs text-slate-400">Allow us to anonymously aggregate your trading data for public statistics.</div>
                    </div>
                </label>
            </div>
        </div>'''
    }
}



@router.get("/feature/{name}", response_class=HTMLResponse)
async def view_feature(request: Request, name: str, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    import json
    import os
    
    feature = None
    page_key = f"page_{name}"
    
    # Fetch from pages.json
    db_file = "data/pages.json"
    if os.path.exists(db_file):
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                pages_data = json.load(f)
                if page_key in pages_data:
                    # Map the saved fields to what the template expects
                    saved = pages_data[page_key]
                    feature = {
                        "title": saved.get("title", ""),
                        "desc": saved.get("desc", ""),
                        "icon": saved.get("icon", "box"),
                        "widget": saved.get("html", "")
                    }
        except Exception as e:
            print("Error loading dynamic page:", e)

    # Fallback to hardcoded defaults
    if not feature:
        feature = FEATURE_CONTENT.get(name, {
            "title": name.replace("-", " ").title(),
            "icon": "box",
            "desc": "This feature is currently being provisioned for your account.",
            "widget": "<div class='flex flex-col items-center justify-center h-64 text-slate-500'><i data-lucide='settings' class='w-12 h-12 mb-4 animate-spin-slow opacity-20'></i><p>Check back later.</p></div>"
        })
    
    if name == "leaderboard":
        top_accounts = db.query(TradingAccount).order_by(desc(TradingAccount.current_balance)).limit(10).all()
        
        rows = ""
        for i, acc in enumerate(top_accounts):
            rank = i + 1
            real_user = db.query(User).filter(User.id == acc.user_id).first()
            trader_name = real_user.full_name if real_user else f"Trader {acc.user_id}"
            initials = "".join([n[0] for n in trader_name.split()[:2]]).upper()
            
            # Highlight top 3
            if rank == 1:
                rank_col = f'<td class="py-4 font-bold text-amber-500">{rank}</td>'
            elif rank == 2:
                rank_col = f'<td class="py-4 font-bold text-slate-300">{rank}</td>'
            elif rank == 3:
                rank_col = f'<td class="py-4 font-bold text-amber-700">{rank}</td>'
            else:
                rank_col = f'<td class="py-4 font-bold text-slate-500">{rank}</td>'
                
            rows += f'''
            <tr class="border-t border-slate-800">
                {rank_col}
                <td class="py-4 flex items-center gap-2">
                    <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-white">{initials}</div>
                    {trader_name}
                </td>
                <td class="py-4 font-mono text-emerald-400">₹{acc.current_balance:,.2f}</td>
                <td class="py-4 text-right">Funded</td>
            </tr>
            '''
            
        feature["widget"] = f'''
        <div class="p-6">
            <div class="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4 flex items-center justify-between mb-6">
                <div>
                    <div class="text-indigo-400 font-bold">Your Global Rank</div>
                    <div class="text-2xl font-black text-white">Top 10%</div>
                </div>
                <i data-lucide="award" class="w-10 h-10 text-indigo-500 opacity-50"></i>
            </div>
            <table class="w-full text-left">
                <thead><tr class="text-xs text-slate-500 uppercase"><th class="pb-3">Rank</th><th class="pb-3">Trader</th><th class="pb-3">Balance</th><th class="pb-3 text-right">Status</th></tr></thead>
                <tbody class="text-slate-300">
                    {rows}
                </tbody>
            </table>
        </div>
        '''

    return templates.TemplateResponse(

        request=request,
        name="feature.html",
        context={
            "app_name": APP_NAME,
            "user": user,
            "feature": feature
        }
    )

