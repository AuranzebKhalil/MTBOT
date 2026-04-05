from datetime import datetime
from typing import List, Optional

from app.core.datatypes import RawSetup, TradeSignal, OrderSide
from app.strategy.plotting_models import StrategyOutput, ZoneRegistry
from app.strategy.annotations import (
    zone_to_record,
    build_entry_annotation,
    build_sl_annotation,
    build_tp_annotation,
    build_bos_annotation,
    build_choch_annotation,
    build_sweep_annotation,
)


def _to_unix(dt: datetime) -> int:
    return int(dt.timestamp())


def build_strategy_output_from_setup(
    setup: RawSetup,
    signal: Optional[TradeSignal],
    zones: ZoneRegistry,
) -> StrategyOutput:
    symbol = setup.symbol
    signal_id = signal.idempotency_key if signal else None

    involved_zone_ids: List[str] = []
    zone_ids_from_anchors: List[str] = setup.anchors.get("zone_ids", []) or []
    for zid in zone_ids_from_anchors:
        if zones.get_zone(zid):
            involved_zone_ids.append(zid)

    annotations = []
    for zid in involved_zone_ids:
        zone = zones.get_zone(zid)
        if not zone:
            continue
        annotations.append(zone_to_record(zone, signal_id=signal_id, trade_id=None))

    setup_time_unix = _to_unix(setup.setup_candle_timestamp)

    annotations.append(
        build_entry_annotation(
            symbol=symbol,
            time=setup_time_unix,
            price=setup.entry_price,
            side=setup.direction,
            signal_id=signal_id,
            trade_id=None,
        )
    )

    annotations.append(
        build_sl_annotation(
            symbol=symbol,
            time=setup_time_unix,
            price=setup.stop_loss,
            side=setup.direction,
            signal_id=signal_id,
            trade_id=None,
        )
    )

    for idx, tp in enumerate(setup.targets, start=1):
        annotations.append(
            build_tp_annotation(
                symbol=symbol,
                time=setup_time_unix,
                price=tp,
                side=setup.direction,
                index=idx,
                signal_id=signal_id,
                trade_id=None,
            )
        )

    bos_anchor = setup.anchors.get("bos")
    if bos_anchor:
        annotations.append(
            build_bos_annotation(
                symbol=symbol,
                time=bos_anchor["time"],
                price=bos_anchor["price"],
                direction=OrderSide(bos_anchor["direction"]),
                signal_id=signal_id,
                trade_id=None,
            )
        )

    choch_anchor = setup.anchors.get("choch")
    if choch_anchor:
        annotations.append(
            build_choch_annotation(
                symbol=symbol,
                time=choch_anchor["time"],
                price=choch_anchor["price"],
                direction=OrderSide(choch_anchor["direction"]),
                signal_id=signal_id,
                trade_id=None,
            )
        )

    sweep_anchor = setup.anchors.get("sweep")
    if sweep_anchor:
        annotations.append(
            build_sweep_annotation(
                symbol=symbol,
                time=sweep_anchor["time"],
                price=sweep_anchor["price"],
                direction=OrderSide(sweep_anchor["direction"]),
                signal_id=signal_id,
                trade_id=None,
            )
        )

    context_summary = {
        "family": setup.family.value,
        "direction": setup.direction.value,
        "score": setup.metadata.get("score"),
        "anchors": setup.anchors,
    }

    return StrategyOutput(
        signal=signal,
        involved_zone_ids=involved_zone_ids,
        annotations=annotations,
        context_summary=context_summary,
    )

