import logging
import time
from app.worker.bot_worker import BotWorker
from app.storage.db import DatabaseContext
from app.storage.models import BotState, User

# Configure logging to console for demo visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DEMO_LAUNCH")

def launch():
    worker = BotWorker()
    logger.info("🚀 INITIALIZING DEMO WORKER...")
    
    # Force Demo State in DB
    with DatabaseContext() as db:
        state = db.query(BotState).first()
        if state:
            state.is_running = True
            state.active_symbols = ["XAUUSD"]
            db.commit()

    # Start the worker loop
    logger.info("⚙️ Starting BotWorker loop...")
    try:
        # The worker will print its own config on the first cycle
        worker.start()
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Stop signal received.")
        worker.stop()
    except Exception as e:
        logger.error(f"💥 Worker crashed: {e}")
        worker.stop()

if __name__ == "__main__":
    launch()
