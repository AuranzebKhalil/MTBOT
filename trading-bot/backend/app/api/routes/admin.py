from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.storage.db import get_db
from app.storage.models import User, Trade, SupportTicket, SupportMessage
from app.api.dependencies import get_current_admin, get_super_admin
from app.api.routes.sockets import manager
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter()

class UserStats(BaseModel):
    id: int
    email: str
    username: Optional[str]
    role: str
    is_active: bool
    is_breached: bool
    total_profit: float
    current_balance: float
    trade_count: int

@router.get("/users", response_model=List[UserStats])
async def get_all_users(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    users = db.query(User).all()
    res = []
    for u in users:
        trade_count = db.query(Trade).filter(Trade.user_id == u.id).count()
        res.append(UserStats(
            id=u.id,
            email=u.email,
            username=u.username,
            role=u.role,
            is_active=u.is_active,
            is_breached=u.is_breached,
            total_profit=u.total_profit,
            current_balance=u.current_balance,
            trade_count=trade_count
        ))
    return res

@router.post("/users/{user_id}/breach")
async def breach_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_super_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_breached = True
    user.is_active = False # Optionally lock them out
    db.commit()
    
    # Trigger real-time pop-up notification
    await manager.send_to_user(user_id, {
        "type": "ACCOUNT_BREACH",
        "message": "Your account has been suspended. Please contact support for further assistance."
    })
    
    return {"message": f"Account {user.email} marked as breached and locked."}

@router.post("/users/{user_id}/unbreach")
async def unbreach_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_super_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_breached = False
    user.is_active = True
    db.commit()

    # Trigger real-time restoration notification
    await manager.send_to_user(user_id, {
        "type": "ACCOUNT_RESTORED",
        "message": "Your account access has been restored."
    })
    
    return {"message": f"Account {user.email} restored."}

@router.get("/tickets", response_model=List[dict])
async def get_all_tickets(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    tickets = db.query(SupportTicket).order_by(SupportTicket.updated_at.desc()).all()
    res = []
    for t in tickets:
        res.append({
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "priority": t.priority,
            "user_email": t.owner.email,
            "created_at": t.created_at,
            "updated_at": t.updated_at
        })
    return res

@router.post("/tickets/{ticket_id}/close")
async def close_ticket(ticket_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.status = "closed"
    db.commit()
    return {"message": "Ticket closed successfully"}
