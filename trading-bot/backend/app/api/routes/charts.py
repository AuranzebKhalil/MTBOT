from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.storage.db import get_db
from app.storage.models import TradeAnnotation, Trade, TradeEvent
from app.core.annotations import TradeChartPayload, ChartAnnotation
from pydantic import BaseModel


router = APIRouter()


class ChartLevels(BaseModel):
    entry: float | None = None
    sl: float | None = None
    tp: float | None = None


class TradeChartEnvelope(BaseModel):
    signal_id: str | None
    trade_id: int
    symbol: str
    timeframe: str
    annotations: List[ChartAnnotation]
    levels: ChartLevels
    context_summary: Dict[str, Any]
    versions: Dict[str, int]


class ReplayEvent(BaseModel):
    timestamp: int
    event_type: str
    old_value: float | None = None
    new_value: float | None = None


class ReplayPayload(BaseModel):
    trade_id: int
    symbol: str
    annotations: List[ChartAnnotation]
    events: List[ReplayEvent]
    context_summary: Dict[str, Any]
    versions: Dict[str, int]


@router.get("/trades/{ticket_id}", response_model=TradeChartPayload)
def get_trade_chart_data(ticket_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.ticket_id == ticket_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    db_annotations = db.query(TradeAnnotation).filter(TradeAnnotation.ticket_id == ticket_id).all()

    annotations: List[ChartAnnotation] = []
    for ann in db_annotations:
        annotations.append(
            ChartAnnotation(
                id=ann.id,
                concept_type=ann.concept_type,
                shape=ann.shape,
                style=ann.style,
                time1=ann.time1,
                time2=ann.time2,
                price1=ann.price1,
                price2=ann.price2,
                text=ann.text,
                layer_priority=ann.layer_priority,
                is_active=ann.is_active,
                metadata_fields=ann.metadata_json or {},
            )
        )

    start_time = min([a.time1 for a in annotations]) if annotations else int(trade.time.timestamp()) - 3600
    end_time = max([a.time2 or a.time1 for a in annotations]) if annotations else int(trade.time.timestamp()) + 3600

    return TradeChartPayload(
        ticket_id=ticket_id,
        symbol=trade.symbol,
        timeframe="M1",
        bars_start_time=start_time,
        bars_end_time=end_time,
        annotations=annotations,
    )


@router.get("/trades/{ticket_id}/envelope", response_model=TradeChartEnvelope)
def get_trade_chart_envelope(ticket_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.ticket_id == ticket_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    db_annotations = db.query(TradeAnnotation).filter(TradeAnnotation.ticket_id == ticket_id).all()

    annotations: List[ChartAnnotation] = []
    for ann in db_annotations:
        annotations.append(
            ChartAnnotation(
                id=ann.id,
                concept_type=ann.concept_type,
                shape=ann.shape,
                style=ann.style,
                time1=ann.time1,
                time2=ann.time2,
                price1=ann.price1,
                price2=ann.price2,
                text=ann.text,
                layer_priority=ann.layer_priority,
                is_active=ann.is_active,
                metadata_fields=ann.metadata_json or {},
            )
        )

    levels = ChartLevels(entry=trade.entry_price, sl=trade.sl, tp=trade.tp)

    context_summary: Dict[str, Any] = {
        "strategy_name": trade.strategy_name,
        "opened_at": trade.time.isoformat() if isinstance(trade.time, datetime) else None,
        "status": trade.status,
    }

    versions = {
        "annotations": 1,
        "payload": 1,
    }

    return TradeChartEnvelope(
        signal_id=None,
        trade_id=trade.id,
        symbol=trade.symbol,
        timeframe="M1",
        annotations=annotations,
        levels=levels,
        context_summary=context_summary,
        versions=versions,
    )


@router.get("/trades/{ticket_id}/replay", response_model=ReplayPayload)
def get_trade_replay(ticket_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.ticket_id == ticket_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    db_annotations = db.query(TradeAnnotation).filter(TradeAnnotation.ticket_id == ticket_id).all()
    db_events = (
        db.query(TradeEvent)
        .filter(TradeEvent.ticket_id == ticket_id)
        .order_by(TradeEvent.timestamp.asc())
        .all()
    )

    annotations: List[ChartAnnotation] = []
    for ann in db_annotations:
        annotations.append(
            ChartAnnotation(
                id=ann.id,
                concept_type=ann.concept_type,
                shape=ann.shape,
                style=ann.style,
                time1=ann.time1,
                time2=ann.time2,
                price1=ann.price1,
                price2=ann.price2,
                text=ann.text,
                layer_priority=ann.layer_priority,
                is_active=ann.is_active,
                metadata_fields=ann.metadata_json or {},
            )
        )

    events: List[ReplayEvent] = []
    for ev in db_events:
        events.append(
            ReplayEvent(
                timestamp=int(ev.timestamp.timestamp()),
                event_type=ev.event_type,
                old_value=ev.old_value,
                new_value=ev.new_value,
            )
        )

    context_summary: Dict[str, Any] = {
        "strategy_name": trade.strategy_name,
        "opened_at": trade.time.isoformat() if isinstance(trade.time, datetime) else None,
        "status": trade.status,
    }

    versions = {
        "annotations": 1,
        "replay": 1,
    }

    return ReplayPayload(
        trade_id=trade.id,
        symbol=trade.symbol,
        annotations=annotations,
        events=events,
        context_summary=context_summary,
        versions=versions,
    )

