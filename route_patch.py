with open("app/routers/admin_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

route = """
@router.post('/admin/accounts/{account_id}/edit-capital')
async def edit_capital(account_id: int, request: Request, balance: float = Form(...), equity: float = Form(...), db: Session = Depends(get_db)):
    user = check_admin(request, db)
    if not user:
        return RedirectResponse('/admin/login', status_code=302)
    
    acc = db.query(TradingAccount).filter(TradingAccount.id == account_id).first()
    if acc:
        acc.current_balance = balance
        acc.current_equity = equity
        db.commit()
    
    return RedirectResponse('/admin', status_code=302)
"""

if "def edit_capital(" not in text:
    text += "\n" + route

with open("app/routers/admin_dashboard.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Added edit-capital route.")
