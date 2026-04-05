import MetaTrader5 as mt5

def check_mt5():
    if not mt5.initialize():
        print(f"MT5 Init Failed. Error: {mt5.last_error()}")
        return
    
    acc = mt5.account_info()
    if acc:
        print(f"Connected to Account: {acc.login}")
        print(f"Server: {acc.server}")
        print(f"Balance: {acc.balance}")
    else:
        print("Could not get account info. Terminal might not be logged in.")
        print(f"Last Error: {mt5.last_error()}")

    mt5.shutdown()

if __name__ == "__main__":
    check_mt5()
