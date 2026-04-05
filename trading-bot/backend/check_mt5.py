
import MetaTrader5 as mt5
import os

def check_mt5_status():
    if not mt5.initialize():
        print(f"Failed to initialize MT5, error: {mt5.last_error()}")
        return

    print("--- MT5 ACCOUNT INFO ---")
    account_info = mt5.account_info()
    if account_info:
        print(f"Balance: {account_info.balance}")
        print(f"Equity: {account_info.equity}")
        print(f"Profit: {account_info.profit}")
    else:
        print("Failed to get account info")

    print("\n--- OPEN POSITIONS ---")
    positions = mt5.positions_get()
    if positions:
        for p in positions:
            print(f"Ticket: {p.ticket}, Symbol: {p.symbol}, Type: {'BUY' if p.type == 0 else 'SELL'}, Volume: {p.volume}, Profit: {p.profit}")
    else:
        print("No open positions")

    print("\n--- LAST ERROR ---")
    print(mt5.last_error())

    mt5.shutdown()

if __name__ == "__main__":
    check_mt5_status()
