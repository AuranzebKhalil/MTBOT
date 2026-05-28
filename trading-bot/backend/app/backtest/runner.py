import logging
import csv
import json
import os
import time
import random
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.ai.predictor import MarketPredictor
from app.core.enums import OrderSide, EntryMode
from app.market_data.mt5_client import MT5Client
from app.risk.manager import RiskManager
from app.strategy.engine import StrategyEngine
from app.strategy.smc import (
    SMCSweepReclaimStrategy, SMCVsaShiftStrategy, SMCContinuationRetestStrategy,
    SMCFirstTouchMitigationStrategy, SMCExhaustionReversalStrategy,
    SMCMSSStrategy, SMCBreakerStrategy, SMCVolumeFlowStrategy
)
from indicators import SMCIndicators
from app.strategy.families.smc import SMCStrategyFamily
from app.core.config import settings
from app.backtest.config import BacktestSettings

logger = logging.getLogger("BacktestRunner")

class BacktestRunner:
    """
    Advanced Backtest Engine v2.7:
    - Candle-by-candle causal simulation (O(N) Optimized)
    - Strategy Diagnostics & Optimization Decision Layer
    - Walk-Forward Validation (Simple & Rolling)
    - Monte Carlo Robustness Analysis (Shuffle, Noise, Ruin, Shocks)
    """

    STRATEGY_ID_MAP = {
        "SMC_VOLUME": "Volume Flow", "SMC_SWEEP": "Sweep Reclaim", "SMC_VSA": "VSA Shift",
        "SMC_TREND": "Continuation", "SMC_MITIGATION": "Mitigation", "SMC_REVERSAL": "Exhaustion",
        "SMC_MSS": "MSS", "SMC_BREAKER": "Breaker Block",
        "HYBRID_REVERSION": "Hybrid Reversion", "HYBRID_SR": "Hybrid S/R",
        "HYBRID_BREAKOUT": "Hybrid Breakout", "HYBRID_MASTER": "Hybrid Master",
        "MAD_TREND_LOOP": "MAD Trend Loop"
    }

    def __init__(self, cfg: BacktestSettings):
        random.seed(42)
        np.random.seed(42)
        self.cfg = cfg
        self.mt5 = MT5Client()
        self.predictor = MarketPredictor()
        self.indicators = SMCIndicators()
        self.smc_family = SMCStrategyFamily(self.indicators)

        from app.strategy.hybrid_strategies import (
            MeanReversionStrategy, SupportResistanceStrategy, BreakoutStrategy,
            HybridSwitcherStrategy, MadTrendLoopStrategy
        )
        
        strategy_map = {
            "SMC_VOLUME": SMCVolumeFlowStrategy, "SMC_SWEEP": SMCSweepReclaimStrategy,
            "SMC_VSA": SMCVsaShiftStrategy, "SMC_TREND": SMCContinuationRetestStrategy,
            "SMC_MITIGATION": SMCFirstTouchMitigationStrategy, "SMC_REVERSAL": SMCExhaustionReversalStrategy,
            "SMC_MSS": SMCMSSStrategy, "SMC_BREAKER": SMCBreakerStrategy,
            "HYBRID_REVERSION": MeanReversionStrategy, "HYBRID_SR": SupportResistanceStrategy,
            "HYBRID_BREAKOUT": BreakoutStrategy, "HYBRID_MASTER": HybridSwitcherStrategy,
            "MAD_TREND_LOOP": MadTrendLoopStrategy
        }

        selected_strategies = [strategy_map[sid](self.indicators) for sid in self.cfg.enabled_strategies if sid in strategy_map]
        self.engine = StrategyEngine(ai_predictor=self.predictor, strategies=selected_strategies)
        self.engine.ai_threshold = self.cfg.ai_threshold
        self.engine.structure_gate_min_score = self.cfg.structure_threshold
        self.engine.diagnose_gates = self.cfg.diagnose_gates
        self.engine.gate_profile = self.cfg.gate_profile
        self.engine.ai_mode = self.cfg.ai_mode
        self.risk = RiskManager()
        self.progress_callback = None

    def run(self, progress_callback=None) -> Dict[str, Any]:
        self.progress_callback = progress_callback
        if self.cfg.monte_carlo_enabled: return self._run_monte_carlo()
        elif self.cfg.walk_forward_enabled: return self._run_walk_forward()
        elif self.cfg.rolling_walk_forward_enabled: return self._run_rolling_walk_forward()
        elif self.cfg.compare_gates: return self._run_comparison_backtest()
        else: return self._run_standard_backtest()

    def _run_standard_backtest(self) -> Dict[str, Any]:
        logger.info(f"[BACKTEST] Starting Standard Backtest: {self.cfg.symbol}")
        baseline = self._run_simulation(self.cfg.date_from, self.cfg.date_to)
        if "error" in baseline: return baseline
        recs = self._generate_recommendations(baseline["diagnostics"])
        self._export_optimization_reports(recs)
        if self.cfg.apply_recommended_filters:
            logger.info("[BACKTEST] Running Optimization Pass...")
            filtered = self._run_simulation(self.cfg.date_from, self.cfg.date_to, opt_rules=recs.get("suggested_config"))
            baseline["comparison"] = self._generate_comparison(baseline, filtered)
            self._export_comparison_report(baseline["comparison"])
        self._export_to_filesystem(baseline["trades"], baseline["rejected_signals"], baseline["summary"], baseline["diagnostics"])
        return baseline

    def _run_monte_carlo(self) -> Dict[str, Any]:
        logger.info(f"[MC] Starting Monte Carlo Analysis ({self.cfg.mc_runs} runs): {self.cfg.symbol}")
        baseline = self._run_simulation(self.cfg.date_from, self.cfg.date_to)
        if "error" in baseline: return baseline
        if not baseline["trades"]: return {"error": "No trades executed in baseline to run Monte Carlo."}
        
        mc_results = self._perform_mc_simulations(baseline["trades"])
        shocks = self._perform_shock_tests(baseline["trades"])
        report = self._generate_mc_report(baseline, mc_results, shocks)
        self._export_mc_reports(report)
        return {"summary": report["classification"]}

    def _perform_mc_simulations(self, trades: List[Dict]) -> Dict:
        random.seed(self.cfg.mc_seed)
        np.random.seed(self.cfg.mc_seed)
        pnl_values = [t["realized_pnl"] for t in trades]
        initial = self.cfg.initial_balance
        ruin_count, ending_balances, max_dds = 0, [], []
        
        for _ in range(self.cfg.mc_runs):
            sim_pnl = list(pnl_values)
            random.shuffle(sim_pnl)
            
            # Add PnL Noise
            if self.cfg.mc_pnl_noise > 0:
                noise = np.random.uniform(1 - self.cfg.mc_pnl_noise, 1 + self.cfg.mc_pnl_noise, len(sim_pnl))
                sim_pnl = [p * n for p, n in zip(sim_pnl, noise)]
            
            balance = initial
            peak = initial
            cur_max_dd = 0.0
            ruined = False
            
            for p in sim_pnl:
                balance += p
                peak = max(peak, balance)
                dd = (peak - balance) / peak if peak > 0 else 0
                cur_max_dd = max(cur_max_dd, dd)
                if dd >= self.cfg.mc_ruin_dd_pct: ruined = True
            
            ending_balances.append(balance)
            max_dds.append(cur_max_dd)
            if ruined: ruin_count += 1

        return {
            "ending_balances": ending_balances, "max_drawdowns": max_dds,
            "prob_profitable": len([b for b in ending_balances if b > initial]) / self.cfg.mc_runs,
            "prob_ruin": ruin_count / self.cfg.mc_runs,
            "median_end_bal": np.median(ending_balances), "worst_end_bal": min(ending_balances), "best_end_bal": max(ending_balances),
            "median_max_dd": np.median(max_dds), "worst_max_dd": max(max_dds),
            "percentiles_bal": {p: np.percentile(ending_balances, p) for p in [5, 25, 50, 75, 95]},
            "percentiles_dd": {p: np.percentile(max_dds, p) for p in [5, 50, 95]},
            "risk_10": len([d for d in max_dds if d >= 0.10]) / self.cfg.mc_runs,
            "risk_20": len([d for d in max_dds if d >= 0.20]) / self.cfg.mc_runs,
            "risk_30": len([d for d in max_dds if d >= 0.30]) / self.cfg.mc_runs
        }

    def _perform_shock_tests(self, trades: List[Dict]) -> Dict:
        # Approximate spread cost based on lot and symbol
        point = 0.01 if "XAU" in self.cfg.symbol.upper() or "GOLD" in self.cfg.symbol.upper() else 0.0001
        contract = 100 if "XAU" in self.cfg.symbol.upper() or "GOLD" in self.cfg.symbol.upper() else 100000
        base_spread = self.cfg.fixed_spread_points
        
        shocks = {}
        for mult in [1.25, 1.50, 2.00]:
            extra_pts = base_spread * (mult - 1)
            cost_per_lot = extra_pts * point * contract
            pnl_shock = sum(t["realized_pnl"] - (t["initial_lot"] * cost_per_lot) for t in trades)
            shocks[f"spread_{mult}x"] = round(pnl_shock, 2)
            
        for pts in [5, 10, 20]:
            cost_per_lot = pts * point * contract
            pnl_shock = sum(t["realized_pnl"] - (t["initial_lot"] * cost_per_lot) for t in trades)
            shocks[f"slippage_{pts}pts"] = round(pnl_shock, 2)
            
        return shocks

    def _generate_mc_report(self, baseline: Dict, mc: Dict, shocks: Dict) -> Dict:
        bp = baseline["summary"]["performance"]
        cls, reason = "ROBUST", "Strategy survived all sequence and noise tests."
        if mc["prob_profitable"] < 0.8 or mc["risk_20"] > 0.05: cls, reason = "MODERATE", "Moderate sensitivity to trade sequencing or noise."
        if mc["prob_profitable"] < 0.6 or mc["risk_20"] > 0.15: cls, reason = "FRAGILE", "High risk of drawdown or loss under noise."
        if mc["median_end_bal"] < self.cfg.initial_balance: cls, reason = "FAILED", "Strategy failed to remain profitable in median simulation."
        
        return {
            "symbol": self.cfg.symbol, "runs": self.cfg.mc_runs, "original": bp, "mc_stats": mc, "shocks": shocks,
            "classification": cls, "reason": reason, "warnings": []
        }

    def _export_mc_reports(self, report: Dict):
        path = os.path.join(os.getcwd(), self.cfg.export_folder)
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "backtest_monte_carlo_report.json"), "w") as f: json.dump(report, f, indent=4)
        with open(os.path.join(path, "backtest_monte_carlo_report.txt"), "w") as f:
            mc = report["mc_stats"]
            f.write(f"MTBOT Monte Carlo Robustness Report\n{'='*35}\n\nSymbol: {report['symbol']}\nRuns: {report['runs']}\n\n")
            f.write(f"Original Result: ${report['original']['net_pnl']} (WR {report['original']['win_rate']}%)\n\n")
            f.write(f"Monte Carlo Summary\n- Median End Balance: ${mc['median_end_bal']:,.2f}\n- Worst End Balance: ${mc['worst_end_bal']:,.2f}\n")
            f.write(f"- Prob. Profitable: {mc['prob_profitable']*100:.1f}%\n- Risk of 20% DD: {mc['risk_20']*100:.1f}%\n\n")
            f.write(f"Robustness Result: {report['classification']}\nReason: {report['reason']}\n")

    def _run_walk_forward(self) -> Dict[str, Any]:
        train = self._run_simulation(self.cfg.train_date_from, self.cfg.train_date_to)
        if "error" in train: return train
        recs = self._generate_recommendations(train["diagnostics"])
        test_b = self._run_simulation(self.cfg.test_date_from, self.cfg.test_date_to)
        test_f = self._run_simulation(self.cfg.test_date_from, self.cfg.test_date_to, opt_rules=recs["suggested_config"])
        report = self._generate_walkforward_report(train, recs, test_b, test_f)
        self._export_walkforward_reports(report)
        return {"summary": report["classification"]}

    def _run_comparison_backtest(self) -> Dict[str, Any]:
        logger.info(f"[COMPARE] Starting Gate Comparison: {self.cfg.symbol}")
        profiles = ["strict", "balanced", "research"]
        results = {}
        
        # Save original settings
        orig_profile = self.cfg.gate_profile
        orig_ai = self.cfg.ai_mode
        
        for profile in profiles:
            logger.info(f"[COMPARE] Running simulation for profile: {profile}")
            self.cfg.gate_profile = profile
            self.engine.gate_profile = profile
            
            # For research mode, we disable AI to see raw potential
            if profile == "research":
                self.cfg.ai_mode = "disabled"
                self.engine.ai_mode = "disabled"
            else:
                self.cfg.ai_mode = orig_ai
                self.engine.ai_mode = orig_ai
                
            res = self._run_simulation(self.cfg.date_from, self.cfg.date_to)
            if "error" not in res:
                results[profile] = res
        
        # Restore original
        self.cfg.gate_profile = orig_profile
        self.engine.gate_profile = orig_profile
        self.cfg.ai_mode = orig_ai
        self.engine.ai_mode = orig_ai
        
        # Print Comparison Table
        print("\n" + "="*85)
        print(f"{'PROFILE':<12} | {'RAW':<5} | {'APP':<5} | {'TRADES':<6} | {'WR%':<6} | {'PNL':<10} | {'PF':<5} | {'MAX_DD':<7} | {'TOP REASON'}")
        print("-" * 85)
        for profile, res in results.items():
            perf = res["summary"]["performance"]
            debug = res["debug_metrics"]
            top_reason = debug["top_rejection_rules"][0][0] if debug["top_rejection_rules"] else "N/A"
            print(f"{profile:<12} | {debug['raw_signals']:<5} | {debug['approved_signals']:<5} | {perf['total_trades']:<6} | {perf['win_rate']:<6} | ${perf['net_pnl']:<9} | {perf['profit_factor']:<5} | {perf['max_drawdown_pct']:<7}% | {top_reason}")
        print("="*85 + "\n")
        
        return results.get("balanced", results.get("strict", {}))

    def _run_rolling_walk_forward(self) -> Dict[str, Any]:
        curr = self.cfg.date_from
        windows = []
        while True:
            tr_end = curr + timedelta(days=self.cfg.walk_forward_window_days)
            ts_end = tr_end + timedelta(days=self.cfg.walk_forward_test_days)
            if ts_end > self.cfg.date_to: break
            tr = self._run_simulation(curr, tr_end)
            recs = self._generate_recommendations(tr["diagnostics"])
            ts = self._run_simulation(tr_end, ts_end, opt_rules=recs["suggested_config"])
            windows.append({"pnl": ts["summary"]["performance"]["net_pnl"]})
            curr += timedelta(days=self.cfg.walk_forward_test_days)
        summary = {"total_windows": len(windows), "avg_pnl": np.mean([w["pnl"] for w in windows]) if windows else 0}
        with open(os.path.join(os.getcwd(), self.cfg.export_folder, "rolling_wf.json"), "w") as f: json.dump(summary, f, indent=4)
        return {"summary": summary}

    def _run_simulation(self, d_from: Optional[datetime], d_to: Optional[datetime], opt_rules: Optional[Dict] = None) -> Dict[str, Any]:
        # 0. Log Inputs
        logger.info(f"[BACKTEST] Initializing Simulation")
        logger.info(f" - Symbol: {self.cfg.symbol}")
        logger.info(f" - Raw From: {d_from}")
        logger.info(f" - Raw To: {d_to}")

        d_f = d_from.replace(tzinfo=None) if d_from else None
        d_t = d_to.replace(tzinfo=None) if d_to else None
        
        logger.info(f" - Parsed UTC From: {d_f}")
        logger.info(f" - Parsed UTC To: {d_t}")

        # Validation: Date Range
        if d_f and d_t and d_t <= d_f:
            logger.error("[BACKTEST] Validation failed: date_to <= date_from")
            return {"error": "Invalid date range: End date must be after start date."}

        # 1. Symbol Resolution
        resolved_symbol = self.mt5.resolve_symbol(self.cfg.symbol)
        if not resolved_symbol:
            logger.error(f"[BACKTEST] Symbol resolution failed for {self.cfg.symbol}")
            return {"error": f"Symbol '{self.cfg.symbol}' could not be resolved. Check broker symbol availability."}
        
        logger.info(f" - Resolved Broker Symbol: {resolved_symbol}")
        
        # 2. MT5 Status Check
        mt5_initialized = self.mt5._connected
        logger.info(f" - MT5 Initialized: {mt5_initialized}")
        
        acc = self.mt5.get_account_info()
        logger.info(f" - MT5 Connected: {acc.get('balance', 0) > 0}")

        # 3. Data Fetching (with Warmup)
        # We need extra history before date_from for indicator warmup
        warmup_days = 5
        warmup_start = d_f - timedelta(days=warmup_days) if d_f else None
        logger.info(f" - Warmup Start Date: {warmup_start}")
        
        logger.info(f"[BACKTEST] Fetching M1 bars for {resolved_symbol} from {warmup_start} to {d_t}...")
        df = self.mt5.get_bars_range(resolved_symbol, "M1", warmup_start, d_t)
        
        if df is None or df.empty:
            last_err = self.mt5.get_last_error()
            logger.error(f"[BACKTEST] Data fetch failed for {resolved_symbol}. MT5 Error: {last_err}")
            return {
                "error": f"No M1 candles found for symbol {resolved_symbol} from {warmup_start} to {d_t}. "
                         f"Check broker symbol, MT5 connection, date range, or history availability.",
                "diagnostics": {
                    "requested_symbol": self.cfg.symbol,
                    "resolved_symbol": resolved_symbol,
                    "requested_from": d_f.isoformat() if d_f else "N/A",
                    "requested_to": d_t.isoformat() if d_t else "N/A",
                    "warmup_from": warmup_start.isoformat() if warmup_start else "N/A",
                    "mt5_error": str(last_err)
                }
            }
            
        df = df.sort_values("time").reset_index(drop=True)
        candle_count = len(df)
        logger.info(f" - Number of M1 candles returned: {candle_count}")
        if candle_count > 0:
            logger.info(f" - First candle: {df.iloc[0]['time']}")
            logger.info(f" - Last candle: {df.iloc[-1]['time']}")

        # Validation: Sufficient Data
        if candle_count < self.cfg.warmup_candles_m1:
            logger.warning(f"[BACKTEST] Data range may be too short ({candle_count} candles).")
        
        # 2. Pre-calculating All Timeframes and Indicators (O(N) Optimization)
        logger.info("[BACKTEST] Pre-calculating indicators (Optimization Layer)...")
        if self.progress_callback: self.progress_callback(5)
        
        # M1 Pre-calculation
        # Add indicators needed by ContextEvaluator
        df['tr'] = np.maximum(df['high'] - df['low'], 
                     np.maximum(abs(df['high'] - df['close'].shift()), 
                                 abs(df['low'] - df['close'].shift())))
        df['atr_m1'] = df['tr'].rolling(14).mean()
        df['body_avg_m1'] = abs(df['close'] - df['open']).rolling(20).mean()
        
        # AI & Hybrid Features Pre-calculation
        df['rsi'] = self.smc_family.indicators.calculate_rsi(df['close'])
        upper, mid, lower = self.smc_family.indicators.calculate_bollinger_bands(df['close'])
        df['bb_upper'] = upper
        df['bb_mid'] = mid
        df['bb_lower'] = lower
        df['adx'] = self.smc_family.indicators.calculate_adx(df)
        
        v_col = 'tick_volume' if 'tick_volume' in df.columns else 'real_volume'
        if v_col in df.columns:
            df['v_avg'] = df[v_col].rolling(20).mean()
            df['rel_activity'] = df[v_col] / df['v_avg']
        df['volatility'] = df['close'].rolling(window=20).std()
        
        m1_full = self.smc_family.preprocess(df)
        
        # MadTrendLoop Pre-calculation
        from app.strategy.custome_indicator import MeanDeviationLoopStrategy
        m1_full = MeanDeviationLoopStrategy.apply_indicator(m1_full)
        
        # Map SMC indicators to AI binary flags
        m1_full['is_sweep'] = np.where(m1_full.get('sweep', 0) != 0, 1, 0)
        m1_full['is_bos'] = np.where(m1_full.get('bos', 0) != 0, 1, 0)
        m1_full['is_fvg'] = np.where(m1_full.get('fvg_bullish', False) | m1_full.get('fvg_bearish', False), 1, 0)
        m1_full['in_ob'] = np.where(m1_full.get('order_block', 0) != 0, 1, 0)
        
        sz = m1_full['supply_zone'] if 'supply_zone' in m1_full.columns else False
        dz = m1_full['demand_zone'] if 'demand_zone' in m1_full.columns else False
        in_sd = (sz == True) | (dz == True) if (isinstance(sz, pd.Series) or isinstance(dz, pd.Series)) else (sz or dz)
        m1_full['in_sd_zone'] = np.where(in_sd, 1, 0)
        
        m1_full['is_2br'] = np.where(m1_full.get('vsa', "") == "TWO_BAR_REVERSAL", 1, 0)
        m1_full['is_nsnd'] = np.where((m1_full.get('vsa', "") == "NO_SUPPLY") | (m1_full.get('vsa', "") == "NO_DEMAND"), 1, 0)
        
        # M5 Pre-calculation
        df5 = df.set_index('time').resample('5min').agg({'open':'first','high':'max','low':'min','close':'last','tick_volume':'sum'}).dropna().reset_index()
        df5['ema20_m5'] = df5['close'].rolling(20).mean()
        df5['adx'] = self.smc_family.indicators.calculate_adx(df5)
        m5_full = self.smc_family.preprocess(df5)
        
        # M15 Pre-calculation
        df15 = df.set_index('time').resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','tick_volume':'sum'}).dropna().reset_index()
        df15['ema50_m15'] = df15['close'].rolling(50).mean()
        # Regime Indicators
        df15['tr'] = np.maximum(df15['high'] - df15['low'], 
                     np.maximum(abs(df15['high'] - df15['close'].shift()), 
                                 abs(df15['low'] - df15['close'].shift())))
        df15['atr_m15'] = df15['tr'].rolling(14).mean()
        df15['atr_sma_m15'] = df15['atr_m15'].rolling(50).mean()
        df15['ema20_m15'] = df15['close'].rolling(20).mean()
        df15['adx'] = self.smc_family.indicators.calculate_adx(df15)
        m15_full = self.smc_family.preprocess(df15)
        
        if self.progress_callback: self.progress_callback(15)

        # 3. Setup Loop Parameters
        # Ensure date_from is naive for comparison with MT5 data
        search_from = d_f if d_f else self.cfg.date_from
        if hasattr(search_from, 'tzinfo') and search_from.tzinfo is not None:
            search_from = search_from.replace(tzinfo=None)
            
        idx = df['time'].searchsorted(search_from)
        idx = max(idx, self.cfg.warmup_candles_m1)
        
        if idx >= len(df):
            logger.warning(f"[BACKTEST] Start date {search_from} is after last available candle {df['time'].iloc[-1]}. Falling back to start.")
            idx = self.cfg.warmup_candles_m1
            
        balance, peak, max_dd = self.cfg.initial_balance, self.cfg.initial_balance, 0.0
        trades, active, rejected = [], [], []
        daily = {}
        
        # Diagnostics tracking
        rejection_counts = {
            "strategy_filter": 0, "structure_gate": 0, "ai_gate": 0,
            "risk_manager": 0, "entry_model": 0, "daily_protection": 0,
            "opt": 0, "spread_guard": 0
        }
        rejection_rules = {}
        rejection_reasons = {}
        
        # Expose to _log_rejection to avoid double-counting and capture all rejections
        self._rejection_counts = rejection_counts
        self._rejection_rules = rejection_rules
        self._rejection_reasons = rejection_reasons
        
        approved_signals_count = 0
        daily_protection_skipped = 0
        point = 0.01 if "XAU" in self.cfg.symbol.upper() or "GOLD" in self.cfg.symbol.upper() or "JPY" in self.cfg.symbol.upper() else 0.0001
        size = 100 if "XAU" in self.cfg.symbol.upper() or "GOLD" in self.cfg.symbol.upper() else 100000

        total_iterations = len(df) - idx
        last_progress_update = 0

        # 4. Simulation Loop
        logger.info(f"[BACKTEST] Starting simulation loop ({total_iterations} candles)...")
        # Aggressive suppression of verbose logs during backtest to boost performance
        loggers_to_silence = ["StrategyEngine", "SMCStrategy", "AIConfidencePredictor", "RiskManager", "SMC_VOLUME", "SMC_MSS"]
        # Also silence any app.* loggers
        for name in logging.root.manager.loggerDict:
            if name.startswith("app."): loggers_to_silence.append(name)
        
        old_levels = {}
        for name in loggers_to_silence:
            l = logging.getLogger(name)
            old_levels[name] = l.level
            l.setLevel(logging.WARNING)
        
        try:
            for i in range(idx, len(df)):
                c = df.iloc[i]
                t = c['time']
                t_naive = t.to_pydatetime().replace(tzinfo=None) if hasattr(t, 'to_pydatetime') else t.replace(tzinfo=None)
                ds = t.strftime("%Y-%m-%d")
            
                # Progress Update
                if i % 500 == 0 or i == len(df) - 1:
                    progress = 15 + int((i - idx) / total_iterations * 80)
                    if progress > last_progress_update:
                        if self.progress_callback: self.progress_callback(progress)
                        last_progress_update = progress
    
                if ds not in daily: daily[ds] = {"trades": 0, "pnl": 0.0, "consecutive_losses": 0, "start": balance, "locked": False}
                
                # Trade Management
                if active:
                    res = self._advance_trade(active[0], c, point, size, self._get_spread(t))
                    if res:
                        balance += res['realized_pnl']
                        peak = max(peak, balance)
                        max_dd = max(max_dd, (peak - balance) / peak if peak > 0 else 0)
                        trades.append(res)
                        active = []
                        daily[ds]["pnl"] += res['realized_pnl']
                        if res['realized_pnl'] < 0: daily[ds]["consecutive_losses"] += 1
                        else: daily[ds]["consecutive_losses"] = 0
                
                # Strategy Evaluation (Causal Slicing from Pre-calculated Data)
                if not active:
                    d = daily[ds]
                    if d["locked"]:
                        daily_protection_skipped += 1
                        continue
    
                    max_t = opt_rules.get("max_trades_per_day", self.cfg.max_trades_per_day) if opt_rules else self.cfg.max_trades_per_day
                    if d["trades"] >= max_t:
                        self._log_rejection(rejected, t, None, stage="daily_protection", rule="MAX_TRADES_PER_DAY", reason="Daily trade limit reached")
                        d["locked"] = True
                        continue
                    if (d["start"] - balance) > (self.cfg.max_daily_loss_pct * self.cfg.initial_balance):
                        self._log_rejection(rejected, t, None, stage="daily_protection", rule="MAX_DAILY_LOSS", reason="Daily loss limit exceeded")
                        d["locked"] = True
                        continue
                    if d["consecutive_losses"] >= self.cfg.max_consecutive_losses:
                        self._log_rejection(rejected, t, None, stage="daily_protection", rule="MAX_CONSECUTIVE_LOSSES", reason="Max consecutive losses reached")
                        d["locked"] = True
                        continue
                    
                    # Optimized Slicing: Only take bars that were closed BEFORE or AT current time t
                    m1_slice = m1_full.iloc[:i+1]
                    
                    # Optimized search for M5/M15 latest closed candles
                    # We find the index of the latest bar where bar_time + duration <= current_time
                    m5_idx = m5_full['time'].searchsorted(t_naive - pd.Timedelta('5min'), side='right')
                    m5_slice = m5_full.iloc[:m5_idx]
                    
                    m15_idx = m15_full['time'].searchsorted(t_naive - pd.Timedelta('15min'), side='right')
                    m15_slice = m15_full.iloc[:m15_idx]
                    
                    if m5_slice.empty or m15_slice.empty: continue
    
                    data = {"M1": m1_slice, "M5": m5_slice, "M15": m15_slice}
                    if self.cfg.diagnose_gates:
                        self.engine._gate_diagnostics["funnel"]["raw_signals"] += 1
                        
                    app, rej, _ = self.engine.evaluate(self.cfg.symbol, data)
                    
                    for r in rej:
                        self._log_rejection(rejected, t, r)
                    
                    if app:
                        sig = app[0]
                        if opt_rules and not self._apply_opt_filters(sig, t, opt_rules):
                            self._log_rejection(rejected, t, sig, stage="opt", reason="Filtered")
                            continue
                            
                        # Phase 4: Risk Manager Validation in Backtest
                        acc_info = {"balance": balance, "equity": balance}
                        current_tick = {"ask": c['close'] + 5*point, "bid": c['close'], "time": int(t_naive.timestamp())}
                        sig.metadata["current_tick"] = current_tick
                        
                        # Compute regime metrics, bias, ATR, and session to align with live trading validation
                        m15_regime = self.engine.context_eval.regime_detector.identify(m15_slice)
                        m15_bias = m15_regime.metrics.get("market_bias", "NEUTRAL")
                        m15_atr = m15_regime.metrics.get("atr", 0.0)
                        
                        risk_context = {
                            "is_backtest": True,
                            "tick_time": int(t_naive.timestamp()),
                            "eval_id": f"BT_{i}",
                            "active_cooldowns": [],
                            "blocked_zones": [],
                            "active_news_event": None,
                            "current_session": self.engine.context_eval.session_manager.get_current_session(t),
                            "nearest_level": self._find_nearest_structural_level(self.cfg.symbol, m15_slice, sig.side),
                            "market_bias": m15_bias,
                            "atr": m15_atr,
                            "market_regime": m15_regime.regime.name,
                            "closed_trades": trades,
                            "per_symbol_cooldown": getattr(self.cfg, "per_symbol_cooldown", True)
                        }
                        
                        # Build merged symbol_settings from self.cfg values so RiskManager gets them:
                        sim_settings = {
                            "max_spread_points": self.cfg.max_spread_allowed,
                            "cooldown_after_losses": getattr(self.cfg, "cooldown_after_losses", 2),
                            "cooldown_minutes": getattr(self.cfg, "cooldown_minutes", 60),
                            "per_strategy_cooldown": getattr(self.cfg, "per_strategy_cooldown", True),
                            "per_symbol_cooldown": getattr(self.cfg, "per_symbol_cooldown", True),
                            "min_candles_between_same_strategy_entries": getattr(self.cfg, "min_candles_between_same_strategy_entries", 10),
                            "min_price_distance_atr_multiplier": getattr(self.cfg, "min_price_distance_atr_multiplier", 0.5),
                            "min_rolling_win_rate": getattr(self.cfg, "min_rolling_win_rate", 40.0),
                            "min_rolling_profit_factor": getattr(self.cfg, "min_rolling_profit_factor", 1.0),
                        }
                        if opt_rules:
                            sim_settings.update(opt_rules)

                        risk_dec = self.risk.validate_signal(
                            sig, acc_info, active, daily[ds]["pnl"], 
                            symbol_settings=sim_settings,
                            symbol_spec={"point": point, "contract_size": size},
                            context=risk_context,
                            gate_profile=self.cfg.gate_profile
                        )
                        
                        if not risk_dec.is_approved:
                            self._log_rejection(rejected, t, sig, 
                                stage=risk_dec.metadata.get("rejection_stage", "risk_manager") if risk_dec.metadata else "risk_manager",
                                rule=risk_dec.metadata.get("rejection_rule", "RISK_REJECT") if risk_dec.metadata else "RISK_REJECT",
                                reason=risk_dec.reason,
                                current_value=risk_dec.metadata.get("current_value") if risk_dec.metadata else None,
                                required_value=risk_dec.metadata.get("required_value") if risk_dec.metadata else None
                            )
                            continue
     
                        self.engine._update_strategy_funnel(sig.metadata.get("strategy_id", "UNKNOWN"), "after_risk_manager")
                        
                        # Phase 5: Entry Model (Spread Guard already in risk manager or here)
                        # For backtest simplicity, we assume risk manager handled it.
                        self.engine._update_strategy_funnel(sig.metadata.get("strategy_id", "UNKNOWN"), "after_entry_model")
     
                        approved_signals_count += 1
                        lot = risk_dec.lot_size if risk_dec.lot_size > 0 else self._calculate_lot_size(balance, sig, size)
                        en = (c['close'] + 5 * point) if sig.side == OrderSide.BUY else (c['close'] - 5 * point)
                        
                        # Capture full metadata at entry
                        m = sig.metadata or {}
                        dist = abs(en - sig.structural_sl)
                        rr_val = round(abs(sig.targets[0] - en) / dist, 2) if dist > 0 else 0
                        
                        self.engine._update_strategy_funnel(sig.metadata.get("strategy_id", "UNKNOWN"), "executed")
                        
                        active.append({
                            "id": len(trades)+1, 
                            "symbol": self.cfg.symbol,
                            "resolved_symbol": resolved_symbol,
                            "strategy": m.get("strategy_id", sig.strategy_name),
                            "setup": m.get("setup_type", "N/A"),
                            "side": sig.side.name, 
                            "direction": sig.side.name,
                            "entry_time": t.isoformat(), 
                            "entry_price": en,
                            "stop_loss": sig.structural_sl, 
                            "take_profit": sig.targets[0], 
                            "sl": sig.structural_sl, # legacy support
                            "tp": sig.targets[0], # legacy support
                            "initial_lot": lot, 
                            "realized_pnl": 0.0, 
                            "current_lot": lot,
                            "grade": m.get("trade_grade", "—"),
                            "ai_conf": round(float(sig.ai_confidence or 0), 3) if self.engine.ai_mode != "disabled" else "disabled",
                            "structure": round(float(m.get("current_structure_score", 0)), 3),
                            "rr": rr_val,
                            "session": str(getattr(sig, "session", "N/A")),
                            "market_bias": m.get("market_bias", "N/A"),
                            "market_regime": m15_regime.regime.name
                        })
                        d["trades"] += 1
        
        finally:
            # Restore logging levels
            for name, level in old_levels.items():
                logging.getLogger(name).setLevel(level)
            
        summary = self._generate_report(trades, rejected, balance, max_dd, daily_protection_skipped)
        diag = self._run_strategy_diagnostics(trades, rejected)
        
        # Add Debug Metrics for Frontend Diagnostic Box
        debug_metrics = {
            "requested_symbol": self.cfg.symbol,
            "resolved_symbol": resolved_symbol,
            "m1_candles_loaded": len(df),
            "candles_skipped_warmup": idx,
            "candles_evaluated": len(df) - idx,
            "raw_signals": len(trades) + len(rejected),
            "approved_signals": approved_signals_count,
            "executed_trades": len(trades),
            "rejected_signals_count": len(rejected),
            "rejection_stage_counts": rejection_counts,
            "top_rejection_reasons": sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_rejection_rules": sorted(rejection_rules.items(), key=lambda x: x[1], reverse=True)[:5],
            "daily_protection_skipped": daily_protection_skipped,
            "mt5_error": None
        }

        self._export_strategy_reports(diag)

        # Progress 100% will be set by the API layer after results are stored
            
        # Limit rejections to prevent network/memory issues with massive payloads
        output_rejections = []
        if self.cfg.include_rejections_in_report:
            output_rejections = rejected[-2000:] # Cap at 2000 most recent
            if len(rejected) > 2000:
                logger.info(f"[BACKTEST] Truncating rejections for payload safety: {len(rejected)} -> 2000")

        return {
            "summary": summary,
            "diagnostics": diag,
            "trades": self._validate_trade_data(trades),
            "rejected_signals": output_rejections,
            "equity_curve": self._build_equity_curve(trades),
            "debug_metrics": debug_metrics
        }

    def _build_equity_curve(self, trades: List[Dict]) -> List[Dict]:
        curve = [{"timestamp": "Start", "balance": self.cfg.initial_balance, "drawdown": 0}]
        bal = self.cfg.initial_balance
        peak = bal
        for t in trades:
            bal += t.get("net_pnl", 0)
            peak = max(peak, bal)
            dd = (peak - bal) / peak if peak > 0 else 0
            curve.append({
                "timestamp": t.get("exit_time", t.get("entry_time", "N/A")),
                "balance": round(bal, 2),
                "drawdown": round(dd, 6)
            })
        return curve

    def _validate_trade_data(self, trades: List[Dict]) -> List[Dict]:
        required = ["symbol", "strategy", "entry_price", "exit_price", "net_pnl", "rr"]
        for t in trades:
            missing = [f for f in required if f not in t]
            if missing:
                logger.warning(f"[BACKTEST] Trade {t.get('id')} missing fields: {missing}")
        return trades

    def _apply_opt_filters(self, sig, ts, rules) -> bool:
        n = self.STRATEGY_ID_MAP.get(sig.strategy_name, sig.strategy_name)
        if n in rules.get("disabled_strategies", []): return False
        if sig.session.name not in rules.get("allowed_sessions", []): return False
        if ts.hour in rules.get("blocked_hours", []): return False
        if sig.ai_confidence < rules.get("min_ai_score", 0): return False
        return True

    def _generate_recommendations(self, diag) -> Dict:
        config = {"enabled_strategies": [], "disabled_strategies": [], "allowed_sessions": ["LONDON", "NEW_YORK"], "min_ai_score": 0.55}
        for n, p in diag["strategy_performance"].items():
            rec = p.get("recommendation") or p.get("label")
            if rec == "KEEP": config["enabled_strategies"].append(n)
            elif rec == "DISABLE": config["disabled_strategies"].append(n)
        return {"suggested_config": config}

    def _generate_comparison(self, b, f) -> Dict:
        return {"baseline": b["summary"], "filtered": f["summary"]}

    def _generate_report(self, trades, rejected, bal, dd, skipped) -> Dict:
        df = pd.DataFrame(trades)
        
        # Calculate rejection counts
        rejected_by_regime = 0
        rejected_by_score = 0
        rejected_by_low_volatility = 0
        rejected_by_choppiness = 0
        rejected_by_missing_fvg = 0
        rejected_by_missing_sweep = 0
        rejected_by_cooldown = 0
        rejected_by_clustering = 0
        rejected_by_strategy_health = 0
        
        for r in rejected:
            reason = str(r.get("reason", "")).lower()
            rule = str(r.get("rule", "")).lower()
            stage = str(r.get("stage", "")).lower()
            
            if "regime" in reason or "non_trending" in reason or "ranging" in reason or "regime" in rule:
                rejected_by_regime += 1
            if "score" in reason:
                rejected_by_score += 1
            if "volatility" in reason or "low_vol" in reason:
                rejected_by_low_volatility += 1
            if "choppy" in reason or "chop" in reason:
                rejected_by_choppiness += 1
            if "fvg" in reason:
                rejected_by_missing_fvg += 1
            if "sweep" in reason or "liquidity" in reason:
                rejected_by_missing_sweep += 1
            if "cooldown" in stage or "cooldown" in reason:
                rejected_by_cooldown += 1
            elif "clustering" in stage or "clustering" in reason:
                rejected_by_clustering += 1
            elif "strategy_health" in stage or "strategy_health" in reason or "health" in stage or "health" in reason:
                rejected_by_strategy_health += 1

        rejections_summary = {
            "rejected_by_regime": rejected_by_regime,
            "rejected_by_score": rejected_by_score,
            "rejected_by_low_volatility": rejected_by_low_volatility,
            "rejected_by_choppiness": rejected_by_choppiness,
            "rejected_by_missing_fvg": rejected_by_missing_fvg,
            "rejected_by_missing_sweep": rejected_by_missing_sweep,
            "rejected_by_cooldown": rejected_by_cooldown,
            "rejected_by_clustering": rejected_by_clustering,
            "rejected_by_strategy_health": rejected_by_strategy_health,
            "strategy_degraded_count": getattr(self.risk, "strategy_degraded_count", 0),
            "strategy_recovered_count": getattr(self.risk, "strategy_recovered_count", 0)
        }
        
        if df.empty:
            res = {
                "total_trades": 0, "net_pnl": 0, "win_rate": 0, 
                "profit_factor": 0, "max_drawdown": 0, "return_pct": 0,
                "average_rr": 0, "best_setup_type": "N/A",
                "daily_protection_skipped": skipped
            }
            res.update(rejections_summary)
            return res
        
        wins, losses = df[df["realized_pnl"] > 0], df[df["realized_pnl"] <= 0]
        pnl = df["realized_pnl"].sum()
        
        # Calculate Best Setup
        best_setup = "N/A"
        if not df.empty:
            setup_pnl = df.groupby("setup")["realized_pnl"].sum()
            if not setup_pnl.empty:
                best_setup = setup_pnl.idxmax()
        
        res = {
            "total_trades": len(df),
            "net_pnl": round(pnl, 2),
            "win_rate": round(len(wins)/len(df)*100, 2),
            "profit_factor": round(wins["realized_pnl"].sum()/abs(losses["realized_pnl"].sum()), 2) if not losses.empty else 10.0,
            "max_drawdown": round(dd*100, 2),
            "return_pct": round(pnl/self.cfg.initial_balance*100, 2),
            "average_rr": round(df["rr"].mean(), 2) if "rr" in df.columns else 0,
            "best_setup_type": best_setup,
            "daily_protection_skipped": skipped
        }
        res.update(rejections_summary)
        return res

    def _advance_trade(self, tr, c, pt, sz, spr) -> Optional[Dict]:
        is_buy, h, l, en = tr["side"] == "BUY", float(c['high']), float(c['low']), tr["entry_price"]
        sl_hit = (is_buy and l <= tr["sl"]) or (not is_buy and (h + spr*pt) >= tr["sl"])
        tp_hit = (is_buy and h >= tr["tp"]) or (not is_buy and (l + spr*pt) <= tr["tp"])
        if sl_hit: tr["exit_price"], tr["exit_reason"] = tr["sl"], "SL"
        elif tp_hit: tr["exit_price"], tr["exit_reason"] = tr["tp"], "TP"
        else: return None
        p = (tr["exit_price"] - tr["entry_price"]) if is_buy else (tr["entry_price"] - tr["exit_price"])
        tr["realized_pnl"] += (p * tr["current_lot"] * sz) - (tr["current_lot"] * 7.0)
        tr["exit_time"] = c['time'].isoformat()
        tr["net_pnl"] = round(tr["realized_pnl"], 2)
        tr["pnl"] = tr["net_pnl"] # alias for frontend
        tr["result"] = "WIN" if tr["net_pnl"] > 0 else "LOSS"
        return tr

    def _calculate_lot_size(self, bal, sig, sz) -> float:
        risk = bal * self.cfg.risk_per_trade_pct
        dist = abs(sig.entry_price - sig.structural_sl)
        return round(max(0.01, min(10.0, risk / (dist * sz) if dist > 0 else 0.01)), 2)

    def _get_spread(self, ts) -> float:
        return self.cfg.fixed_spread_points if 8 <= ts.hour < 18 else self.cfg.fixed_spread_points * 1.5

    def _resample_causal(self, df, tf, ts) -> pd.DataFrame:
        df = df.set_index('time')
        res = df.resample(tf).agg({'open':'first','high':'max','low':'min','close':'last','tick_volume':'sum'}).dropna().reset_index()
        return res[res['time'].dt.tz_localize(None) + pd.Timedelta(tf) <= ts.replace(tzinfo=None)]

    def _log_rejection(self, log, ts, sig, **kwargs):
        entry = {
            "time": ts.isoformat(),
            "symbol": self.cfg.symbol,
            "strategy": "System",
            "setup": "N/A",
            "direction": "N/A",
            "grade": "—",
            "ai_conf": 0.0,
            "structure": 0.0,
            "stage": kwargs.get("stage", "unknown"),
            "rule": kwargs.get("rule", "unknown"),
            "reason": kwargs.get("reason", "unknown"),
            "current_value": kwargs.get("current_value"),
            "required_value": kwargs.get("required_value")
        }
        
        if sig:
            m = sig.metadata or {}
            entry["strategy"] = m.get("strategy_id", getattr(sig, "strategy_name", "N/A"))
            entry.update({
                "setup": m.get("setup_type", "N/A"),
                "direction": sig.side.name if hasattr(sig.side, "name") else str(sig.side),
                "grade": m.get("trade_grade", "—"),
                "ai_conf": round(float(sig.ai_confidence or 0), 3),
                "structure": round(float(m.get("current_structure_score", 0)), 3),
                "stage": m.get("rejection_stage") or entry["stage"],
                "rule": m.get("rejection_rule") or entry["rule"],
                "reason": m.get("rejection_reason") or entry["reason"],
                "current_value": m.get("current_value") if m.get("current_value") is not None else entry["current_value"],
                "required_value": m.get("required_value") if m.get("required_value") is not None else entry["required_value"]
            })
            
        log.append(entry)
        
        # Centralized tracking updates
        stage = entry.get("stage", "unknown")
        rule = entry.get("rule", "unknown")
        reason = entry.get("reason", "unknown")
        
        if hasattr(self, "_rejection_counts"):
            self._rejection_counts[stage] = self._rejection_counts.get(stage, 0) + 1
        if hasattr(self, "_rejection_rules"):
            self._rejection_rules[rule] = self._rejection_rules.get(rule, 0) + 1
        if hasattr(self, "_rejection_reasons"):
            self._rejection_reasons[reason] = self._rejection_reasons.get(reason, 0) + 1

    def _run_strategy_diagnostics(self, trades: List[Dict], rejected: List[Dict]) -> Dict:
        """
        Builds per-strategy funnel and performance metrics.
        """
        funnels = self.engine._gate_diagnostics["strategy_funnels"]
        tdf = pd.DataFrame(trades)
        rdf = pd.DataFrame(rejected)
        
        all_strategies = list(self.STRATEGY_ID_MAP.keys())
        results = {
            "active": [],
            "blocked": [],
            "silent": [],
            "strategy_performance": {},
            "strategy_funnels": funnels,
            "rejection_summary": {},
            "session_performance": {},
            "traced_signals": []
        }
        
        # Populate traced signals with some detailed rejections for the report
        if not rdf.empty:
            # Convert rejected signals to the format expected by _export_strategy_reports
            for _, r in rdf.head(10).iterrows():
                results["traced_signals"].append({
                    "type": r.get("rule", "REJECT"),
                    "timestamp": r.get("time"),
                    "strategy": r.get("strategy"),
                    "score": r.get("structure", 0),
                    "required": 0.5, # Placeholder or from settings
                    "breakdown": {},
                    "failing": r.get("reason"),
                    "confidence": r.get("ai_conf", 0),
                    "reason": r.get("reason"),
                    "weak": ""
                })

        for sid in all_strategies:
            s_trades = tdf[tdf["strategy"] == sid] if not tdf.empty else pd.DataFrame()
            s_rej = rdf[rdf["strategy"] == sid] if not rdf.empty else pd.DataFrame()
            s_funnel = funnels.get(sid, {
                "raw_signals": 0, "after_strategy_filter": 0, "after_structure_gate": 0,
                "after_ai_gate": 0, "after_trade_grading": 0, "after_risk_manager": 0,
                "after_entry_model": 0, "executed": 0
            })
            
            total_t = len(s_trades)
            raw_s = s_funnel["raw_signals"]
            
            # 1. Determine Status
            status = "NO_SIGNALS"
            if total_t > 0:
                status = "ACTIVE"
                results["active"].append(sid)
            elif raw_s > 0:
                status = "BLOCKED_BY_FILTERS"
                results["blocked"].append(sid)
            else:
                results["silent"].append(sid)

            # 2. Calculate Metrics
            wins = s_trades[s_trades["realized_pnl"] > 0] if not s_trades.empty else pd.DataFrame()
            losses = s_trades[s_trades["realized_pnl"] <= 0] if not s_trades.empty else pd.DataFrame()
            net_pnl = s_trades["realized_pnl"].sum() if not s_trades.empty else 0
            win_rate = (len(wins) / total_t * 100) if total_t > 0 else 0
            pf = (wins["realized_pnl"].sum() / abs(losses["realized_pnl"].sum())) if not losses.empty else (10.0 if total_t > 0 else 0)
            avg_rr = s_trades["rr"].mean() if not s_trades.empty else 0
            
            if status == "ACTIVE" and total_t >= 30:
                if pf < 1.0: status = "WEAK_PERFORMANCE"
            elif status == "ACTIVE" and total_t < 30:
                status = "NEEDS_MORE_DATA"
            
            # 3. Recommendation
            rec = "NO_ACTION"
            if raw_s == 0: rec = "NO_ACTION"
            elif total_t < 30: rec = "NEEDS_MORE_DATA"
            else:
                if pf > 1.3: rec = "KEEP"
                elif pf >= 1.0: rec = "TUNE"
                else: rec = "DISABLE"
                
            # 4. Rejection Breakdown
            top_rule = "N/A"
            top_reason = "N/A"
            if not s_rej.empty:
                rule_counts = s_rej["rule"].value_counts()
                top_rule = rule_counts.index[0]
                top_reason = s_rej[s_rej["rule"] == top_rule]["reason"].iloc[0]

            results["strategy_performance"][sid] = {
                "name": self.STRATEGY_ID_MAP.get(sid, sid),
                "status": status,
                "recommendation": rec,
                "label": rec,
                "raw_signals": raw_s,
                "executed_trades": total_t,
                "rejected_signals": len(s_rej),
                "win_rate": round(win_rate, 2),
                "net_pnl": round(net_pnl, 2),
                "profit_factor": round(pf, 2),
                "avg_rr": round(avg_rr, 2),
                "top_rejection_rule": top_rule,
                "top_rejection_reason": top_reason,
                "funnel": s_funnel
            }
            
        return results


    def _export_strategy_reports(self, diag: Dict):
        """Generates the .json and .txt diagnostic files."""
        base_path = "app/backtest/reports"
        os.makedirs(base_path, exist_ok=True)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = f"{base_path}/strategy_diagnostics_{ts}.json"
        txt_path = f"{base_path}/strategy_diagnostics_{ts}.txt"
        
        with open(json_path, 'w') as f:
            json.dump(diag, f, indent=4)
            
        with open(txt_path, 'w') as f:
            f.write("MTBOT Strategy Funnel & Performance Report\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Active Strategies:    {', '.join(diag['active']) or 'None'}\n")
            f.write(f"Blocked Strategies:   {', '.join(diag['blocked']) or 'None'}\n")
            f.write(f"Silent Strategies:    {', '.join(diag['silent']) or 'None'}\n\n")
            
            f.write("Strategy Details\n")
            f.write("-" * 60 + "\n")
            for sid, p in diag["strategy_performance"].items():
                f.write(f"Strategy:       {sid} ({p['name']})\n")
                f.write(f"Status:         {p['status']}\n")
                f.write(f"Recommendation: {p['recommendation']}\n")
                f.write(f"Raw Signals:    {p['raw_signals']}\n")
                f.write(f"Executed:       {p['executed_trades']}\n")
                f.write(f"Profit Factor:  {p['profit_factor']}\n")
                f.write(f"Win Rate:       {p['win_rate']}%\n")
                f.write(f"Top Rejection:  {p['top_rejection_rule']}\n")
                f.write(f"Funnel:         {p['funnel']}\n")
                f.write("-" * 30 + "\n")
                
        logger.info(f"[BACKTEST] Diagnostic reports exported to {base_path}")
            
        print("\nTRACED REJECTIONS (First 2)")
        for sig in diag["traced_signals"][:2]:
            print(f"\nType: {sig['type']} | {sig['timestamp']} | {sig['strategy']}")
            if sig['type'] == "STRUCTURE_REJECT":
                print(f"Score: {sig['score']:.2f} (Req: {sig['required']:.2f})")
                print(f"Factors: {json.dumps(sig['breakdown'], indent=2)}")
                print(f"Failing: {sig['failing']}")
            else:
                print(f"Confidence: {sig['confidence']:.2f} (Req: {sig['required']:.2f})")
                print(f"Reason: {sig['reason']}")
                print(f"Weak: {sig['weak']}")
        print("="*60 + "\n")



    def _export_to_filesystem(self, trades, rejections, summary, diag):
        path = os.path.join(os.getcwd(), self.cfg.export_folder)
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "summary.json"), "w") as f: json.dump(summary, f, indent=4)

    def _export_optimization_reports(self, recs):
        pass

    def _export_comparison_report(self, comp):
        pass

    def _generate_walkforward_report(self, tr, recs, tb, tf):
        return {"classification": "PASSED"} # Placeholder

    def _export_walkforward_reports(self, report):
        pass

    def _find_nearest_structural_level(self, symbol: str, m15_df: pd.DataFrame, direction: OrderSide) -> Optional[Dict[str, Any]]:
        """Finds the nearest swing high/low that might act as immediate resistance."""
        if m15_df.empty:
            return None
        latest_price = m15_df['close'].iloc[-1]
        if direction == OrderSide.BUY:
            highs = m15_df[m15_df['swing_high'] == True].tail(10) if 'swing_high' in m15_df.columns else pd.DataFrame()
            if highs.empty:
                return None
            above = highs[highs['high'] > latest_price]
            if not above.empty:
                level = float(above['high'].min())
                return {"price": level, "type": "Swing High", "tf": "M15"}
            return None
        else:
            lows = m15_df[m15_df['swing_low'] == True].tail(10) if 'swing_low' in m15_df.columns else pd.DataFrame()
            if lows.empty:
                return None
            below = lows[lows['low'] < latest_price]
            if not below.empty:
                level = float(below['low'].max())
                return {"price": level, "type": "Swing Low", "tf": "M15"}
            return None
