import os
import sys
import time
import subprocess
import logging

# Configure Startup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - MTBOT: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Starter")

def run_api(env):
    """Starts the FastAPI Backend."""
    logger.info("Initializing API Layer (FastAPI)...")
    # Using 'python -m uvicorn' to ensure the correct environment and 'app.main:app' path.
    # --reload is enabled for development persistence.
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ]
    return subprocess.Popen(cmd, env=env)

def run_worker(env):
    """Starts the Trading Bot Worker."""
    logger.info("Initializing Strategy Worker (BotWorker)...")
    # run_worker.py handles the MT5 connection and loop
    cmd = [sys.executable, "run_worker.py"]
    return subprocess.Popen(cmd, env=env)

def main():
    logger.info("==========================================")
    logger.info("🛡️  ALPHA QUANTITATIVE | TRADING ENGINE")
    logger.info("==========================================")
    
    # Ensure current directory is in PYTHONPATH for consistent imports
    root_path = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env["PYTHONPATH"] = root_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    # Pass the env to run functions
    api_process = run_api(env)
    time.sleep(3) # Give API time to initialize the database/models
    
    worker_process = run_worker(env)

    logger.info("✅ System synchronized. Services are now active.")
    logger.info("   API: http://localhost:8000")
    logger.info("   Worker: Scanning configurations...")
    
    try:
        while True:
            # Monitor process health
            if api_process.poll() is not None:
                logger.error("⚠️ API process terminated unexpectedly. Restarting in 5s...")
                time.sleep(5)
                api_process = run_api()
            
            if worker_process.poll() is not None:
                logger.error("⚠️ Worker process terminated unexpectedly. Restarting in 5s...")
                time.sleep(5)
                worker_process = run_worker()
                
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutdown command received. Terminating processes...")
        api_process.terminate()
        worker_process.terminate()
        
        # Wait for clean exit
        try:
            api_process.wait(timeout=5)
            worker_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Force killing hung processes...")
            api_process.kill()
            worker_process.kill()
            
        logger.info("MTBOT safely powered down.")

if __name__ == "__main__":
    main()
