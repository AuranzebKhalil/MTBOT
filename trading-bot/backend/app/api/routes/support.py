from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.storage.db import get_db
from app.storage.models import User, SupportTicket, SupportMessage
from app.api.dependencies import get_current_user
from app.api.routes.sockets import manager
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter()

class CreateTicket(BaseModel):
    subject: str
    content: str
    priority: str = "normal"

class SupportTicketRes(BaseModel):
    id: int
    subject: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

class SupportMessageRes(BaseModel):
    id: int
    content: str
    sender_id: int
    sender_email: str
    created_at: datetime

@router.post("/tickets", response_model=SupportTicketRes)
async def create_ticket(data: CreateTicket, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = SupportTicket(
        subject=data.subject,
        priority=data.priority,
        user_id=current_user.id
    )
    db.add(ticket)
    db.flush() # Get Ticket ID
    
    first_message = SupportMessage(
        content=data.content,
        ticket_id=ticket.id,
        sender_id=current_user.id
    )
    db.add(first_message)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/tickets", response_model=List[SupportTicketRes])
async def get_my_tickets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SupportTicket).filter(SupportTicket.user_id == current_user.id).order_by(SupportTicket.updated_at.desc()).all()

@router.get("/tickets/{ticket_id}/messages", response_model=List[SupportMessageRes])
async def get_ticket_messages(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if the user owns the ticket OR is admin
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not enough privileges to view this ticket")
        
    messages = db.query(SupportMessage).filter(SupportMessage.ticket_id == ticket_id).order_by(SupportMessage.created_at.asc()).all()
    res = []
    for m in messages:
        res.append(SupportMessageRes(
            id=m.id,
            content=m.content,
            sender_id=m.sender_id,
            sender_email=m.sender.email,
            created_at=m.created_at
        ))
    return res

@router.post("/tickets/{ticket_id}/messages")
async def send_message(ticket_id: int, content: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not enough privileges to view this ticket")

    message = SupportMessage(
        content=content,
        ticket_id=ticket_id,
        sender_id=current_user.id
    )
    db.add(message)
    ticket.updated_at = datetime.now(timezone.utc)
    # If users replies and status is "closed", we reopen it
    if ticket.status == "closed":
        ticket.status = "open"
        
    db.commit()
    
    # Real-time relay: Notify the recipient
    recipient_id = ticket.user_id if current_user.role in ["admin", "superadmin"] else ticket.assigned_to
    if recipient_id:
        await manager.send_to_user(recipient_id, {
            "type": "NEW_SUPPORT_MESSAGE",
            "ticket_id": ticket_id,
            "sender_email": current_user.email,
            "content": content[:100]
        })
    elif current_user.role == "user":
        # If user replies and no one is assigned, notify all admins (broadcast or specific role broadcast)
        # For now, just a general 'manager broadcast' or we can add an admin specific list
        pass

    return {"message": "Message sent successfully"}
