from typing import Iterable, List

from sqlalchemy.orm import Session

from app.storage.models import TradeAnnotation
from app.strategy.plotting_models import TradeAnnotationRecord


def persist_trade_annotations(
    db: Session,
    records: Iterable[TradeAnnotationRecord],
) -> None:
    for record in records:
        db_ann = TradeAnnotation(
            id=record.id,
            ticket_id=record.ticket_id,
            symbol=record.symbol,
            concept_type=record.concept_type,
            shape=record.shape.value,
            style=record.style.value,
            time1=record.time1,
            time2=record.time2,
            price1=record.price1,
            price2=record.price2,
            text=record.text,
            layer_priority=record.layer_priority,
            is_active=record.is_active,
            metadata_json=record.metadata,
        )
        db.add(db_ann)
    db.commit()


def load_trade_annotations(
    db: Session,
    ticket_id: int,
) -> List[TradeAnnotation]:
    return (
        db.query(TradeAnnotation)
        .filter(TradeAnnotation.ticket_id == ticket_id)
        .order_by(TradeAnnotation.created_at.asc())
        .all()
    )

