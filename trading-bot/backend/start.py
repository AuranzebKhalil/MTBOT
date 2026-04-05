import uvicorn
import multiprocessing
import os
import sys

# Add the current directory to sys.path so 'app' can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_api():
    # NOTE: reload=True can terminate sibling processes (worker) during code reloads.
    # Run API without reload when using the combined runner.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

def run_worker():
    import run_worker
    run_worker.main()

if __name__ == "__main__":
    # Ensure DB is initialized and migrated before spawning processes
    from app.storage.db import init_db
    print("🔄 Synchronizing Intelligence Database Schema...")
    init_db()
    
    # In a real production environment, these would be separate services/containers
    # For local development, we can run them in separate processes
    api_process = multiprocessing.Process(target=run_api)
    worker_process = multiprocessing.Process(target=run_worker)
    
    api_process.start()
    worker_process.start()

    try:
        api_process.join()
        worker_process.join()
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C (Windows-friendly)
        for p in (api_process, worker_process):
            try:
                if p.is_alive():
                    p.terminate()
            except Exception:
                pass
        for p in (api_process, worker_process):
            try:
                p.join(timeout=5)
            except Exception:
                pass
