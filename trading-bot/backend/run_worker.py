import logging
import signal
import sys
from app.worker.bot_worker import BotWorker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("WorkerEntry")

def main():
    worker = BotWorker()
    
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        worker.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Alertli Bot Worker...")
    worker.start()
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        worker.stop()

if __name__ == "__main__":
    main()
