from typing import Optional, List, Dict
from uuid import uuid4

from app.core.annotations import AnnotationShape, AnnotationStyle
from app.core.datatypes import OrderSide, RawSetup, SetupFamily
from app.strategy.plotting_models import (
    SMCZone,
    TradeAnnotationRecord,
)


def _direction_style(direction: OrderSide) -> AnnotationStyle:
    if direction == OrderSide.BUY:
        return AnnotationStyle.BULLISH
    if direction == OrderSide.SELL:
        return AnnotationStyle.BEARISH
    return AnnotationStyle.NEUTRAL


def zone_to_record(
    zone: SMCZone,
    signal_id: Optional[str],
    trade_id: Optional[int],
) -> TradeAnnotationRecord:
    return TradeAnnotationRecord(
        id=str(uuid4()),
        symbol=zone.symbol,
        ticket_id=trade_id,
        signal_id=signal_id,
        concept_type=zone.concept_type,
        shape=AnnotationShape.ZONE_RECTANGLE,
        style=_direction_style(zone.direction),
        time1=zone.time_start,
        price1=zone.price_low,
        time2=zone.time_end,
        price2=zone.price_high,
        text=zone.concept_type.replace("_", " ").title(),
        layer_priority=1,
        is_active=True,
        metadata={
            "timeframe": zone.timeframe,
            "zone_id": zone.id,
            **(zone.metadata or {}),
        },
    )


def build_entry_annotation(
    symbol: str,
    time: int,
    price: float,
    side: OrderSide,
    signal_id: Optional[str],
    trade_id: Optional[int],
) -> TradeAnnotationRecord:
    return TradeAnnotationRecord(
        id=str(uuid4()),
        symbol=symbol,
        ticket_id=trade_id,
        signal_id=signal_id,
        concept_type="ENTRY",
        shape=AnnotationShape.HORIZONTAL_LINE,
        style=AnnotationStyle.NEUTRAL,
        time1=time,
        price1=price,
        time2=None,
        price2=None,
        text="ENTRY",
        layer_priority=5,
        is_active=True,
        metadata={
            "side": side.value,
        },
    )


def build_sl_annotation(
    symbol: str,
    time: int,
    price: float,
    side: OrderSide,
    signal_id: Optional[str],
    trade_id: Optional[int],
) -> TradeAnnotationRecord:
    return TradeAnnotationRecord(
        id=str(uuid4()),
        symbol=symbol,
        ticket_id=trade_id,
        signal_id=signal_id,
        concept_type="STOP_LOSS",
        shape=AnnotationShape.HORIZONTAL_LINE,
        style=AnnotationStyle.RISK_STOP,
        time1=time,
        price1=price,
        time2=None,
        price2=None,
        text="SL",
        layer_priority=6,
        is_active=True,
        metadata={
            "side": side.value,
        },
    )


def build_tp_annotation(
    symbol: str,
    time: int,
    price: float,
    side: OrderSide,
    index: int,
    signal_id: Optional[str],
    trade_id: Optional[int],
) -> TradeAnnotationRecord:
    return TradeAnnotationRecord(
        id=str(uuid4()),
        symbol=symbol,
        ticket_id=trade_id,
        signal_id=signal_id,
        concept_type="TAKE_PROFIT",
        shape=AnnotationShape.HORIZONTAL_LINE,
        style=AnnotationStyle.TARGET_PROFIT,
        time1=time,
        price1=price,
        time2=None,
        price2=None,
        text=f"TP{index}",
        layer_priority=4,
        is_active=True,
        metadata={
            "side": side.value,
            "target_index": index,
        },
    )


def build_label_annotation(
    symbol: str,
    time: int,
    price: float,
    text: str,
    style: AnnotationStyle,
    concept_type: str,
    signal_id: Optional[str],
    trade_id: Optional[int],
) -> TradeAnnotationRecord:
    return TradeAnnotationRecord(
        id=str(uuid4()),
        symbol=symbol,
        ticket_id=trade_id,
        signal_id=signal_id,
        concept_type=concept_type,
        shape=AnnotationShape.LABEL,
        style=style,
        time1=time,
        price1=price,
        time2=None,
        price2=None,
        text=text,
        layer_priority=7,
        is_active=True,
        metadata={},
    )


def build_bos_annotation(
    symbol: str,
    time: int,
    price: float,
    direction: OrderSide,
    signal_id: Optional[str],
    trade_id: Optional[int],
) -> TradeAnnotationRecord:
    return TradeAnnotationRecord(
        id=str(uuid4()),
        symbol=symbol,
        ticket_id=trade_id,
        signal_id=signal_id,
        concept_type="BOS",
        shape=AnnotationShape.HORIZONTAL_LINE,
        style=_direction_style(direction),
        time1=time,
        price1=price,
        time2=None,
        price2=None,
        text="BOS",
        layer_priority=2,
        is_active=True,
        metadata={
            "direction": direction.value,
        },
    )


class AnnotationBuilder:
    """
    Legacy-compatible facade used by StrategyEngine.

    Returns lightweight dicts so existing TradeSignal.chart_annotations
    and persistence logic keep working without architectural changes.
    """

    def build(self, setup: RawSetup) -> List[Dict]:
        if setup.family == SetupFamily.SWEEP_RECLAIM:
            return self._build_sweep_reclaim(setup)
        if setup.family == SetupFamily.VSA_SHIFT:
            return self._build_vsa_shift(setup)
        if setup.family in (SetupFamily.CONTINUATION, SetupFamily.MITIGATION, SetupFamily.EXHAUSTION):
            return self._build_structure(setup)
        return []

    def _build_sweep_reclaim(self, setup: RawSetup) -> List[Dict]:
        anns: List[Dict] = []

        sweep_time = setup.anchors.get("sweep_time")
        sweep_price = setup.anchors.get("sweep_price")
        if sweep_time and sweep_price:
            sweep = build_sweep_annotation(
                symbol=setup.symbol,
                time=sweep_time,
                price=sweep_price,
                direction=setup.direction,
                signal_id=None,
                trade_id=None,
            )
            anns.append(self._to_dict(sweep))

        entry = build_entry_annotation(
            symbol=setup.symbol,
            time=int(setup.setup_candle_timestamp.timestamp()),
            price=setup.entry_price,
            side=setup.direction,
            signal_id=None,
            trade_id=None,
        )
        anns.append(self._to_dict(entry))
        return anns

    def _build_vsa_shift(self, setup: RawSetup) -> List[Dict]:
        label = build_label_annotation(
            symbol=setup.symbol,
            time=int(setup.setup_candle_timestamp.timestamp()),
            price=setup.entry_price,
            text="VSA SHIFT",
            style=AnnotationStyle.INFO,
            concept_type="VSA_SHIFT",
            signal_id=None,
            trade_id=None,
        )
        return [self._to_dict(label)]

    def _build_structure(self, setup: RawSetup) -> List[Dict]:
        anns: List[Dict] = []

        zone_rect = setup.anchors.get("zone_rect")
        if zone_rect and len(zone_rect) == 4:
            t1, p1, t2, p2 = zone_rect
            # Encode as a generic ORDER_BLOCK / FVG-style rectangle
            anns.append(
                {
                    "id": str(uuid4()),
                    "concept_type": setup.family.value,
                    "shape": AnnotationShape.ZONE_RECTANGLE.value,
                    "style": (
                        AnnotationStyle.BULLISH.value
                        if setup.direction == OrderSide.BUY
                        else AnnotationStyle.BEARISH.value
                    ),
                    "time1": t1,
                    "price1": p1,
                    "time2": t2,
                    "price2": p2,
                    "text": setup.family.value,
                    "layer_priority": 1,
                    "is_active": True,
                    "metadata_fields": {},
                }
            )

        entry = build_entry_annotation(
            symbol=setup.symbol,
            time=int(setup.setup_candle_timestamp.timestamp()),
            price=setup.entry_price,
            side=setup.direction,
            signal_id=None,
            trade_id=None,
        )
        anns.append(self._to_dict(entry))

        sl = build_sl_annotation(
            symbol=setup.symbol,
            time=int(setup.setup_candle_timestamp.timestamp()),
            price=setup.stop_loss,
            side=setup.direction,
            signal_id=None,
            trade_id=None,
        )
        anns.append(self._to_dict(sl))

        for idx, tp in enumerate(setup.targets, start=1):
            tp_ann = build_tp_annotation(
                symbol=setup.symbol,
                time=int(setup.setup_candle_timestamp.timestamp()),
                price=tp,
                side=setup.direction,
                index=idx,
                signal_id=None,
                trade_id=None,
            )
            anns.append(self._to_dict(tp_ann))

        return anns

    @staticmethod
    def _to_dict(record: TradeAnnotationRecord) -> Dict:
        return {
            "id": record.id,
            "concept_type": record.concept_type,
            "shape": record.shape.value,
            "style": record.style.value,
            "time1": record.time1,
            "time2": record.time2,
            "price1": record.price1,
            "price2": record.price2,
            "text": record.text,
            "layer_priority": record.layer_priority,
            "is_active": record.is_active,
            "metadata_fields": record.metadata,
        }


def build_choch_annotation(
    symbol: str,
    time: int,
    price: float,
    direction: OrderSide,
    signal_id: Optional[str],
    trade_id: Optional[int],
) -> TradeAnnotationRecord:
    return TradeAnnotationRecord(
        id=str(uuid4()),
        symbol=symbol,
        ticket_id=trade_id,
        signal_id=signal_id,
        concept_type="CHOCH",
        shape=AnnotationShape.HORIZONTAL_LINE,
        style=_direction_style(direction),
        time1=time,
        price1=price,
        time2=None,
        price2=None,
        text="CHOCH",
        layer_priority=2,
        is_active=True,
        metadata={
            "direction": direction.value,
        },
    )


def build_sweep_annotation(
    symbol: str,
    time: int,
    price: float,
    direction: OrderSide,
    signal_id: Optional[str],
    trade_id: Optional[int],
) -> TradeAnnotationRecord:
    marker_shape = (
        AnnotationShape.MARKER_UP if direction == OrderSide.BUY else AnnotationShape.MARKER_DOWN
    )
    return TradeAnnotationRecord(
        id=str(uuid4()),
        symbol=symbol,
        ticket_id=trade_id,
        signal_id=signal_id,
        concept_type="SWEEP",
        shape=marker_shape,
        style=_direction_style(direction),
        time1=time,
        price1=price,
        time2=None,
        price2=None,
        text="SWEEP",
        layer_priority=8,
        is_active=True,
        metadata={
            "direction": direction.value,
        },
    )

