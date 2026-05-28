import logging
import threading
import uuid
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from app.backtest.runner import BacktestRunner
from app.backtest.config import BacktestSettings

router = APIRouter()
logger = logging.getLogger(__name__)

class BacktestRunRequest(BaseModel):
    symbol: str = Field(..., examples=["XAUUSD"])
    date_from: datetime
    date_to: datetime
    initial_balance: float = 10000.0
    risk_per_trade: float = 0.01
    spread_points: float = 35.0
    apply_recommended_filters: bool = False
    walk_forward: bool = False
    monte_carlo: bool = False
    ai_threshold: Optional[float] = 0.52
    enabled_strategies: Optional[List[str]] = None
    excluded_strategies: Optional[List[str]] = None
    gate_profile: str = "balanced"
    ai_mode: str = "disabled"
    compare_gates: bool = False
    include_rejections: bool = False

# Global state for backtest progress and results
BACKTEST_STATUS = {"progress": 0, "is_running": False, "job_id": None}
BACKTEST_RESULTS = {}

@router.post("/run")
def run_backtest(req: BacktestRunRequest, background_tasks: BackgroundTasks):
    if BACKTEST_STATUS["is_running"]:
        raise HTTPException(status_code=400, detail="A backtest is already running.")
        
    try:
        job_id = str(uuid.uuid4())
        BACKTEST_STATUS["progress"] = 0
        BACKTEST_STATUS["is_running"] = True
        BACKTEST_STATUS["job_id"] = job_id
        BACKTEST_RESULTS[job_id] = None

        def progress_update(p):
            BACKTEST_STATUS["progress"] = p
            if p % 10 == 0:
                logger.debug(f"[BACKTEST] Progress: {p}%")

        def run_task(config_req, j_id):
            try:
                # Initialize Settings
                cfg = BacktestSettings(
                    symbol=config_req.symbol,
                    date_from=config_req.date_from,
                    date_to=config_req.date_to,
                    initial_balance=config_req.initial_balance,
                    risk_per_trade_pct=config_req.risk_per_trade,
                    fixed_spread_points=config_req.spread_points,
                    apply_recommended_filters=config_req.apply_recommended_filters,
                    walk_forward_enabled=config_req.walk_forward,
                    monte_carlo_enabled=config_req.monte_carlo,
                    ai_threshold=config_req.ai_threshold or 0.52,
                    gate_profile=config_req.gate_profile,
                    ai_mode=config_req.ai_mode,
                    compare_gates=config_req.compare_gates,
                    diagnose_gates=True,
                    include_rejections_in_report=config_req.include_rejections
                )
                
                if config_req.enabled_strategies is not None:
                    cfg.enabled_strategies = config_req.enabled_strategies
                if config_req.excluded_strategies is not None:
                    cfg.excluded_strategies = config_req.excluded_strategies

                runner = BacktestRunner(cfg)
                result = runner.run(progress_callback=progress_update)
                BACKTEST_RESULTS[j_id] = result
                BACKTEST_STATUS["progress"] = 100 # Set 100 ONLY AFTER results are stored
            except Exception as e:
                logger.exception(f"[BACKTEST] Job {j_id} failed")
                BACKTEST_RESULTS[j_id] = {"error": str(e)}
                BACKTEST_STATUS["progress"] = 100 # Also set 100 on error so UI can show error
            finally:
                BACKTEST_STATUS["is_running"] = False

        # Start the backtest in a background thread
        thread = threading.Thread(target=run_task, args=(req, job_id))
        thread.start()
        
        return {"status": "started", "job_id": job_id}
        
    except Exception as e:
        BACKTEST_STATUS["is_running"] = False
        logger.exception("[BACKTEST] Failed to start")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_backtest_status():
    return BACKTEST_STATUS

def make_json_serializable(data):
    """Recursively converts numpy/pandas types to native Python types."""
    if isinstance(data, dict):
        return {k: make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_json_serializable(item) for item in data]
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, (pd.Timestamp, datetime)):
        return data.isoformat()
    elif pd.isna(data):
        return None
    return data

@router.get("/results/{job_id}")
def get_backtest_results(job_id: str):
    if job_id not in BACKTEST_RESULTS:
        raise HTTPException(status_code=404, detail="Job not found")
        
    result = BACKTEST_RESULTS[job_id]
    if result is None:
        raise HTTPException(status_code=202, detail="Backtest still in progress")
        
    if isinstance(result, dict) and "error" in result:
        # If it's a known error from the background thread
        raise HTTPException(status_code=500, detail=result["error"])
        
    try:
        # Deep-clean the results for JSON safety before encoding
        serializable_result = make_json_serializable(result)
        return jsonable_encoder(serializable_result)
    except Exception as e:
        logger.exception(f"[BACKTEST] Failed to serialize results for job {job_id}")
        raise HTTPException(status_code=500, detail=f"Serialization error: {str(e)}")
