"""
LIVE STRATEGY DEBUGGER
======================
Run this to see EXACTLY what the bot analyses every 10 seconds.
Shows every indicator, every gate, and why each decision is made.

Usage: python live_debug.py XAUUSD
       python live_debug.py BTCUSD
"""
import time
import sys
import os
import datetime
import pandas as pd

# ── Path setup ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_layer.mt5_connector import MT5Connector
from strategy import SMCStrategy
from indicators import SMCIndicators

# ── Config ────────────────────────────────────────────────────────────
SYMBOL   = sys.argv[1].upper() if len(sys.argv) > 1 else "XAUUSD"
INTERVAL = 10  # seconds between analysis cycles

def clr(text, code): return f"\033[{code}m{text}\033[0m"
GREEN  = lambda t: clr(t, "92")
RED    = lambda t: clr(t, "91")
YELLOW = lambda t: clr(t, "93")
CYAN   = lambda t: clr(t, "96")
BLUE   = lambda t: clr(t, "94")
GRAY   = lambda t: clr(t, "90")
BOLD   = lambda t: clr(t, "1")
WHITE  = lambda t: clr(t, "97")

def divider(char="─", width=62):
    print(GRAY(char * width))

def header(title):
    print()
    print(CYAN("╔" + "═"*60 + "╗"))
    print(CYAN("║") + BOLD(WHITE(f"  {title:<58}")) + CYAN("║"))
    print(CYAN("╚" + "═"*60 + "╝"))

def gate(num, name, passed, reason=""):
    icon  = GREEN("✅ PASS") if passed else RED("❌ FAIL")
    color = GREEN if passed else RED
    print(f"  {YELLOW(f'GATE {num}')}  {color(name):<30}  {icon}")
    if reason:
        print(f"          {GRAY('→')} {reason}")

def indicator_row(name, value, note=""):
    print(f"  {GRAY('▸')} {name:<28} {CYAN(str(value))}  {GRAY(note)}")

# ══════════════════════════════════════════════════════════════════════
def run_cycle(mt5: MT5Connector, strategy: SMCStrategy, indicators: SMCIndicators):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    header(f"LIVE ANALYSIS  ·  {SYMBOL}  ·  {now}")

    # ── Fetch Data ────────────────────────────────────────────────────
    print(f"\n{BLUE('📡 Fetching 10,000 M1 / M5 / M15 bars ...')}")
    dm1  = mt5.get_market_data(SYMBOL, "M1",  10000)
    dm5  = mt5.get_market_data(SYMBOL, "M5",  500)
    dm15 = mt5.get_market_data(SYMBOL, "M15", 500)

    if dm1 is None or dm5 is None or dm15 is None:
        print(RED("  ✖ Data fetch failed — is MT5 open and logged in?"))
        return

    price   = dm1['close'].iloc[-1]
    p_open  = dm1['open'].iloc[-1]
    p_high  = dm1['high'].iloc[-1]
    p_low   = dm1['low'].iloc[-1]

    divider()
    print(f"  {WHITE('Current Price')}  {GREEN(f'{price:.5f}')}")
    print(f"  O:{GRAY(f'{p_open:.5f}')}  H:{GREEN(f'{p_high:.5f}')}  L:{RED(f'{p_low:.5f}')}  C:{WHITE(f'{price:.5f}')}")
    print(f"  Candles: M1={len(dm1):,}  M5={len(dm5):,}  M15={len(dm15):,}")

    # ── GATE 1: MACRO BIAS  (M15) ─────────────────────────────────────
    divider()
    print(f"\n{BOLD(YELLOW('🔭 GATE 1 — MACRO BIAS (M15)'))}")

    ema50_m15 = dm15['close'].rolling(50).mean().iloc[-1]
    close_m15 = dm15['close'].iloc[-1]
    hh = dm15['high'].iloc[-20:].max() >= dm15['high'].iloc[-40:-20].max()
    ll = dm15['low'].iloc[-20:].min()  <= dm15['low'].iloc[-40:-20].min()

    indicator_row("M15 EMA50",        f"{ema50_m15:.5f}")
    indicator_row("M15 Current Close",f"{close_m15:.5f}")
    indicator_row("Making Higher Highs", str(hh))
    indicator_row("Making Lower Lows",   str(ll))

    if close_m15 > ema50_m15 and hh:
        bias = 1
        gate(1, "Macro Bias", True, f"BULLISH — Price above EMA50, Higher Highs confirmed")
    elif close_m15 < ema50_m15 and ll:
        bias = -1
        gate(1, "Macro Bias", True, f"BEARISH — Price below EMA50, Lower Lows confirmed")
    else:
        bias = 0
        gate(1, "Macro Bias", False, "NEUTRAL — No clear HTF trend. Bot says WAIT.")
        print(f"\n  {RED('⛔ ANALYSIS STOPPED — No macro trend to trade with.')}")
        return

    # ── GATE 2: STRUCTURAL ALIGNMENT (M5) ────────────────────────────
    divider()
    print(f"\n{BOLD(YELLOW('🏗️  GATE 2 — M5 STRUCTURE ALIGNMENT'))}")

    ema20_m5   = dm5['close'].rolling(20).mean().iloc[-1]
    close_m5   = dm5['close'].iloc[-1]
    m5_structure = 1 if close_m5 > ema20_m5 else -1

    indicator_row("M5 EMA20",          f"{ema20_m5:.5f}")
    indicator_row("M5 Current Close",  f"{close_m5:.5f}")
    m5_label = "BULLISH" if m5_structure == 1 else "BEARISH"
    m15_label = "BULLISH" if bias == 1 else "BEARISH"
    indicator_row("M5 Structure",      m5_label)
    indicator_row("M15 Bias",          m15_label)

    aligned = m5_structure == bias
    gate(2, "M5/M15 Alignment", aligned,
         f"Both {m15_label}" if aligned else f"MISMATCH: M15={m15_label} vs M5={m5_label}")

    if not aligned:
        print(f"\n  {RED('⛔ ANALYSIS STOPPED — Multi-timeframe structure mismatch.')}")
        return

    # ── RUN INDICATORS ON M1 ─────────────────────────────────────────
    divider()
    print(f"\n{BOLD(YELLOW('🔬 RUNNING SMC INDICATORS ON M1 (10,000 bars)'))}")

    df = dm1.copy()
    df = indicators.detect_liquidity_sweeps(df)
    df = indicators.detect_bos_choch(df)
    df = indicators.detect_fvg(df)
    df = indicators.detect_order_blocks(df)
    df = indicators.detect_supply_demand(df)

    latest = df.iloc[-2]
    recent_8 = df.iloc[-10:-2]

    # Sweep stats
    sweeps_bull = (df['sweep'] == 1).sum()
    sweeps_bear = (df['sweep'] == -1).sum()
    recent_sweep_bull = (recent_8['sweep'] == 1).any()
    recent_sweep_bear = (recent_8['sweep'] == -1).any()

    indicator_row("Bullish Sweeps (all)",   f"{sweeps_bull}")
    indicator_row("Bearish Sweeps (all)",   f"{sweeps_bear}")
    indicator_row("Sweep in last 8 bars ↑", str(recent_sweep_bull), "← SRR trigger")
    indicator_row("Sweep in last 8 bars ↓", str(recent_sweep_bear), "← SRR trigger")
    indicator_row("BOS on last candle",     str(latest['bos']),      "← CR trigger")
    indicator_row("FVG Bullish (last bar)", str(latest['fvg_bullish']))
    indicator_row("FVG Bearish (last bar)", str(latest['fvg_bearish']))
    indicator_row("Order Block (last bar)", str(latest['order_block']), "(1=Bull, -1=Bear)")
    indicator_row("Demand Zone (last bar)", str(latest['demand_zone']))
    indicator_row("Supply Zone (last bar)", str(latest['supply_zone']))

    # Tick activity
    v_latest = df['tick_volume'].iloc[-1]
    v_avg    = df['tick_volume'].rolling(20).mean().iloc[-1]
    v_ratio  = v_latest / v_avg if v_avg > 0 else 0
    activity_ok = 0.5 <= v_ratio <= 4.0
    indicator_row("Tick Volume (latest)",   f"{v_latest:.0f}")
    indicator_row("Tick Volume (20-avg)",   f"{v_avg:.1f}")
    indicator_row("Relative Activity",      f"{v_ratio:.2f}x", "✅ OK" if activity_ok else "❌ BLOCKED (< 0.5x or > 4.0x)")

    # ── MCS SCORE ────────────────────────────────────────────────────
    divider()
    print(f"\n{BOLD(YELLOW('🎯 MACRO CONFLUENCE SCORE (MCS)'))}")

    score = 0
    mcs_items = [
        ("Sweep present",          latest['sweep'] != 0),
        ("BOS on candle",          latest['bos']),
        ("FVG present",            latest['fvg_bullish'] or latest['fvg_bearish']),
        ("Order Block present",    latest['order_block'] != 0),
        ("S/D Zone present",       latest['demand_zone'] or latest['supply_zone']),
        ("High Relative Activity", v_ratio > 1.5),
    ]
    for label, hit in mcs_items:
        marker = GREEN("  ✓ +1") if hit else GRAY("  ✗ +0")
        print(f"  {marker}  {label}")
        if hit: score += 1

    score_color = GREEN if score >= 2 else RED
    print(f"\n  {BOLD(WHITE('MCS Total Score:'))} {score_color(f'{score}/6')}  {GRAY('(need ≥ 2 to qualify)')}")

    # ── STRATEGY FAMILIES ────────────────────────────────────────────
    divider()
    print(f"\n{BOLD(YELLOW('📋 STRATEGY FAMILY EVALUATION'))}")

    families = [
        ("SRR", "Sweep Reclaim Reversal",  _check_srr(recent_8, latest, bias)),
        ("CR",  "Continuation Retest",     _check_cr(latest, bias)),
        ("MR",  "Manipulation Reversal",   _check_mr(df, latest, bias)),
        ("FTM", "First Touch Mitigation",  _check_ftm(latest, bias)),
        ("ER",  "Exhaustion Reversal",     _check_er(df, latest, bias, v_latest, v_avg)),
    ]

    signal = "WAIT"
    triggered_family = None
    for code, name, sig in families:
        icon  = GREEN(f"✅ SIGNAL: {sig}") if sig != "WAIT" else GRAY("⬜ No setup")
        print(f"  {YELLOW(code):<6} {name:<30} {icon}")
        if sig != "WAIT" and signal == "WAIT":
            signal = sig
            triggered_family = name

    # ── FINAL VERDICT ─────────────────────────────────────────────────
    divider()
    print(f"\n{BOLD(YELLOW('🏁 FINAL VERDICT'))}")

    if signal == "WAIT":
        print(f"  {GRAY('⏸️  WAIT')} — No strategy family triggered on this cycle.")
    elif not activity_ok:
        print(f"  {RED('⛔ BLOCKED')} — {triggered_family} fired {signal} but Relative Activity = {v_ratio:.2f}x (invalid range)")
    elif score < 2:
        print(f"  {RED('⛔ BLOCKED')} — {triggered_family} fired {signal} but MCS Score = {score}/6 (below threshold 2)")
    else:
        color = GREEN if signal == "BUY" else RED
        print(f"  {color(f'🚀 {signal} SIGNAL')} — {triggered_family}")
        print(f"  {WHITE('→ Would now go to AI Gate for confirmation...')}")
        print(f"  {WHITE('→ If AI agrees → Risk Gate → MT5 Order')}")

    print()

# ── Mini strategy checkers (mirrors strategy.py logic exactly) ────────

def _check_srr(recent8, latest, bias):
    if (recent8['sweep'] == 1).any() and bias == 1:
        if latest['fvg_bullish'] or latest['order_block'] == 1:
            return "BUY"
    if (recent8['sweep'] == -1).any() and bias == -1:
        if latest['fvg_bearish'] or latest['order_block'] == -1:
            return "SELL"
    return "WAIT"

def _check_cr(latest, bias):
    if latest['bos']:
        if bias == 1 and latest['close'] > latest['open']:  return "BUY"
        if bias == -1 and latest['close'] < latest['open']: return "SELL"
    return "WAIT"

def _check_mr(df, latest, bias):
    avg_sp = (df['high'] - df['low']).rolling(20).mean().iloc[-1]
    prev   = df.iloc[-3]
    if (prev['high'] - prev['low']) > avg_sp * 2.0:
        if bias == 1 and latest['close'] > prev['high']:  return "BUY"
        if bias == -1 and latest['close'] < prev['low']:  return "SELL"
    return "WAIT"

def _check_ftm(latest, bias):
    if bias == 1 and latest['demand_zone'] and latest['close'] > latest['open']:  return "BUY"
    if bias == -1 and latest['supply_zone'] and latest['close'] < latest['open']: return "SELL"
    return "WAIT"

def _check_er(df, latest, bias, v_latest, v_avg):
    if v_latest > v_avg * 2.5:
        if bias == 1 and latest['close'] > latest['open'] and latest['low'] < df['low'].iloc[-10:].min():
            return "BUY"
        if bias == -1 and latest['close'] < latest['open'] and latest['high'] > df['high'].iloc[-10:].max():
            return "SELL"
    return "WAIT"

# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(CYAN(f"""
╔══════════════════════════════════════════════════════════════╗
║         ALERTLI QUANT — LIVE STRATEGY DEBUGGER              ║
║         Symbol: {SYMBOL:<8}  Refresh: every {INTERVAL}s              ║
║         Press CTRL+C to stop                                 ║
╚══════════════════════════════════════════════════════════════╝"""))

    mt5 = MT5Connector()
    if not mt5.connect():
        print(RED("❌ Cannot connect to MT5. Is the terminal open?"))
        sys.exit(1)

    ind = SMCIndicators()
    strat = SMCStrategy()

    print(GREEN(f"\n  ✅ Connected to MT5. Starting live analysis for {SYMBOL}...\n"))

    try:
        while True:
            run_cycle(mt5, strat, ind)
            print(GRAY(f"  Next scan in {INTERVAL} seconds... (Ctrl+C to stop)"))
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print(YELLOW("\n\n  ⏹️  Debugger stopped by user."))
        mt5.disconnect()
