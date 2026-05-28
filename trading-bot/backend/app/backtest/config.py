from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class BacktestSettings:
    # 1. Scope and Balance
    symbol: str = "XAUUSD"
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    initial_balance: float = 10000.0
    
    # 2. Risk Management
    risk_mode: str = "fixed_risk_percent"  # fixed_lot, fixed_risk_percent, dynamic_risk_by_grade
    risk_per_trade_pct: float = 0.01
    fixed_lot_size: float = 0.1
    max_trades_per_day: int = 3
    max_daily_loss_pct: float = 0.02
    max_consecutive_losses: int = 2
    cooldown_after_loss_mins: int = 45
    cooldown_same_setup_mins: int = 60
    
    # 3. Execution Simulation
    spread_mode: str = "fixed"  # fixed, session_based, random
    fixed_spread_points: float = 35.0  # For XAUUSD, 35 points = 3.5 pips
    max_spread_allowed: float = 55.0
    slippage_points: float = 5.0
    entry_model: str = "market"  # market, limit, retest
    
    # 4. Indicators and Warmup
    warmup_candles_m1: int = 650
    intracandle_rule: str = "conservative"  # conservative (SL first), aggressive (TP first)
    
    # 5. Features
    ai_filter_enabled: bool = True
    ai_threshold: float = 0.52
    structure_filter_enabled: bool = True
    structure_threshold: float = 0.45
    
    # 6. Strategies and Sessions
    enabled_strategies: List[str] = field(default_factory=lambda: [
        "SMC_VOLUME", "SMC_SWEEP", "SMC_VSA", "SMC_TREND", 
        "SMC_MSS", "SMC_MITIGATION", "SMC_REVERSAL", "SMC_BREAKER"
    ])
    excluded_strategies: Optional[List[str]] = None
    enabled_sessions: List[str] = field(default_factory=lambda: ["LONDON", "NEW_YORK", "OVERLAP"])
    
    # 7. Optimization and Comparison
    apply_recommended_filters: bool = False
    
    # 8. Walk-Forward Validation
    walk_forward_enabled: bool = False
    train_date_from: Optional[datetime] = None
    train_date_to: Optional[datetime] = None
    test_date_from: Optional[datetime] = None
    test_date_to: Optional[datetime] = None
    
    # Rolling Walk-Forward
    rolling_walk_forward_enabled: bool = False
    walk_forward_window_days: int = 30
    walk_forward_test_days: int = 7
    
    # 9. Monte Carlo Robustness
    monte_carlo_enabled: bool = False
    mc_runs: int = 1000
    mc_pnl_noise: float = 0.10
    mc_seed: int = 42
    mc_ruin_dd_pct: float = 0.20
    
    # 10. Output and Debug
    export_folder: str = "backtest_results"
    debug_mode: bool = False
    diagnose_gates: bool = False
    compare_gates: bool = False
    gate_profile: str = "balanced" # strict, balanced, research
    ai_mode: str = "disabled" # disabled, fallback, live_model
    include_rejections_in_report: bool = True
    
    # Phase 2 Cooldown, Clustering, & Health Monitoring Settings
    cooldown_after_losses: int = 2
    cooldown_minutes: int = 60
    per_strategy_cooldown: bool = True
    per_symbol_cooldown: bool = True
    min_candles_between_same_strategy_entries: int = 10
    min_price_distance_atr_multiplier: float = 0.5
    min_rolling_win_rate: float = 40.0
    min_rolling_profit_factor: float = 1.0
