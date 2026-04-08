import sqlite3
import os

db_path = "trading_bot.db"

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 TARGETING DATABASE UPGRADE...")
    
    # 1. Upgrade Users Table
    new_user_cols = [
        ("role", "VARCHAR DEFAULT 'user'"),
        ("is_breached", "BOOLEAN DEFAULT 0"),
        ("username", "VARCHAR"),
        ("total_profit", "FLOAT DEFAULT 0.0"),
        ("current_balance", "FLOAT DEFAULT 0.0")
    ]
    
    for col_name, col_type in new_user_cols:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"✅ Users column added: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"⏩ Users column exists: {col_name}")
            else:
                print(f"❌ Users column failed: {col_name} - {e}")

    # 2. Create Support Tables
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject VARCHAR,
            status VARCHAR DEFAULT 'open',
            priority VARCHAR DEFAULT 'normal',
            assigned_to INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            user_id INTEGER,
            FOREIGN KEY(assigned_to) REFERENCES users(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        print("✅ Table created: support_tickets")
    except Exception as e:
        print(f"❌ Table failed: support_tickets - {e}")

    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at DATETIME,
            ticket_id INTEGER,
            sender_id INTEGER,
            FOREIGN KEY(ticket_id) REFERENCES support_tickets(id),
            FOREIGN KEY(sender_id) REFERENCES users(id)
        )""")
        print("✅ Table created: support_messages")
    except Exception as e:
        print(f"❌ Table failed: support_messages - {e}")

    print("\n🛡️ SEEDING SUPERADMIN...")
    try:
        import bcrypt
        hashed = bcrypt.hashpw("Alertli@2026".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("SELECT id FROM users WHERE email='admin@alertli.ai'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (email, username, hashed_password, role, is_active) VALUES (?, ?, ?, ?, ?)",
                         ("admin@alertli.ai", "Superadmin", hashed, "superadmin", 1))
            print("🚀 SEED: Superadmin admin@alertli.ai created.")
        else:
            print("⏩ SEED: Superadmin already exists.")
    except Exception as e:
        print(f"❌ Seed failed: {e}")

    conn.commit()
    conn.close()
    print("\n✨ UPGRADE COMPLETE. Relaunch your bot and login.")
