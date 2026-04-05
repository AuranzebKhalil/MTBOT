from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import datetime
from app.core.datatypes import OrderSide

@dataclass
class BrokerTick:
    symbol: str
    bid: float
    ask: float
    timestamp: datetime
    volume: float

@dataclass
class BrokerPosition:
    ticket: int
    symbol: str
    side: OrderSide
    volume: float
    open_price: float
    sl: float
    tp: float
    profit: float

@dataclass
class BrokerOrderResult:
    success: bool
    ticket: Optional[int]
    filled_price: Optional[float]
    slippage: Optional[float]
    comment: str
    raw_response: dict

@dataclass
class SymbolTradingRules:
    min_lot: float
    lot_step: float
    min_stop_distance_points: int
    freeze_level_points: int
    digits: int
    point_size: float

class IBrokerAdapter(ABC):
    @abstractmethod
    def get_positions(self) -> Dict[int, BrokerPosition]: pass
    @abstractmethod
    def get_latest_tick(self, symbol: str) -> Optional[BrokerTick]: pass
    @abstractmethod
    def get_symbol_rules(self, symbol: str) -> SymbolTradingRules: pass
    @abstractmethod
    def place_order(self, symbol: str, side: OrderSide, volume: float, price: float, sl: float, tp: float, deviation: int) -> BrokerOrderResult: pass
    @abstractmethod
    def modify_order(self, ticket: int, new_sl: float, new_tp: float) -> BrokerOrderResult: pass
    @abstractmethod
    def close_position(self, ticket: int, volume: float) -> BrokerOrderResult: pass
