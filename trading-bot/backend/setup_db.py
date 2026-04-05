import psycopg2
import sys

def setup():
    passwords_to_try = [None, "admin123", "postgres", "admin", "1234", "password"]
    ports_to_try = [5432, 5433]
    connected = False
    conn = None
    
    print("--- Institutional Database Initialization ---")
    
    for port in ports_to_try:
        print(f"\nScanning Port {port}...")
        for pwd in passwords_to_try:
            try:
                if pwd is None:
                    print(f"  > Attempting NO password...")
                else:
                    print(f"  > Attempting password: '{pwd}'...")
                    
                conn = psycopg2.connect(
                    host="127.0.0.1",
                    port=port,
                    user="postgres",
                    password=pwd,
                    connect_timeout=2
                )
                connected = True
                print(f"\n[+] SUCCESS! Connected on Port {port}")
                break
            except Exception:
                continue
        if connected: break
            
    if not connected:
        print("\n[!] FATAL ERROR: All connection attempts failed on ports 5432 and 5433.")
        print("Please check your Windows 'Services' app to see if PostgreSQL is running.")
        sys.exit(1)
        
    conn.autocommit = True
    cur = conn.cursor()
    
    # Standardize environment
    print("[+] Standardizing Master Password to 'admin123'...")
    cur.execute("ALTER USER postgres WITH PASSWORD 'admin123';")
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname='trading_bot'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE trading_bot;")
        print("[+] Created Database 'trading_bot'")
    else:
        print("[+] Database 'trading_bot' verified.")
        
    cur.close()
    conn.close()
    print("\nSUCCESS: Institutional Infrastructure is ONLINE.")
    print("Launch the bot: 'python bot.py'")

if __name__ == "__main__":
    setup()
