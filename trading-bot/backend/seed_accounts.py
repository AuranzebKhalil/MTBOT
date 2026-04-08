import bcrypt
from sqlalchemy.orm import Session
from app.storage.db import SessionLocal
from app.storage.models import User, BotState

def seed_accounts():
    db = SessionLocal()
    try:
        # 1. Create Super Admin
        admin_email = "admin@alpha.com"
        admin_pass = "admin123"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        if not admin_user:
            hashed = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin_user = User(
                email=admin_email, 
                hashed_password=hashed, 
                role="superadmin",
                username="SuperAdmin"
            )
            db.add(admin_user)
            print(f"✅ Created SuperAdmin: {admin_email} / {admin_pass}")
        else:
            admin_user.role = "superadmin" # Ensure role is correct if user exists
            print(f"ℹ️ Admin user already exists. Role updated to superadmin.")

        # 2. Create Bot User (standard account for strategy signals)
        bot_email = "bot@alpha.com"
        bot_pass = "bot123"
        bot_user = db.query(User).filter(User.email == bot_email).first()
        
        if not bot_user:
            hashed = bcrypt.hashpw(bot_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            bot_user = User(
                email=bot_email, 
                hashed_password=hashed, 
                role="user",
                username="AlphaBot"
            )
            db.add(bot_user)
            print(f"✅ Created Bot User: {bot_email} / {bot_pass}")

        # 3. Initialize Bot State if missing
        state = db.query(BotState).first()
        if not state:
            state = BotState(is_running=False, active_symbols=["XAUUSD", "EURUSD", "GBPUSD"])
            db.add(state)
            print("✅ Initialized Bot State.")

        db.commit()
    except Exception as e:
        print(f"❌ Error seeding accounts: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_accounts()
