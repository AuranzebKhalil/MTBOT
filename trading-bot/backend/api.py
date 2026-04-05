from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uvicorn
import threading
import datetime
from typing import List, Optional
from datetime import timedelta

from fastapi.middleware.cors import CORSMiddleware
from database import engine, get_db, Base
import models
import auth

# Initialize Database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Alertli Forex Trading Bot API")

# Enable CORS for institutional frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Pydantic Models ---
class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Trade(BaseModel):
    id: int
    symbol: str
    type: str
    volume: float
    entry_price: float
    sl: float
    tp: float
    pnl: float
    status: str
    rationale: Optional[str] = "Institutional Quant Analysis"

class BotStatus(BaseModel):
    is_running: bool
    balance: float
    equity: float
    daily_pnl: float
    active_trades: int
    win_rate: Optional[float] = 0
    profit_factor: Optional[float] = 0
    total_growth: Optional[float] = 0
    symbol: Optional[str] = "GOLD"
    timeframe: Optional[str] = "M1"
    market_open: Optional[bool] = True
    logs: Optional[List[str]] = []

class SettingsUpdate(BaseModel):
    symbol: Optional[str] = None
    active_symbols: Optional[List[str]] = None # List of active pairs for multi-chart
    timeframe: Optional[str] = None
    preferred_session: Optional[str] = None # ALL, LONDON, NEW YORK, ASIAN

class RiskUpdate(BaseModel):
    risk_per_trade: Optional[float] = None
    max_trades: Optional[int] = None
    max_daily_trades: Optional[int] = None
    daily_loss_limit: Optional[float] = None

class CustomStrategyCreate(BaseModel):
    name: str
    type: str
    description: str
    logic: str
    color: Optional[str] = "#00ffbd"

class CustomStrategyResponse(BaseModel):
    id: int
    name: str
    type: str
    description: str
    logic: str
    color: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- In-Memory State (For Real-time Sync) ---
BOT_DATA = {
    "status": {
        "is_running": False, 
        "balance": 0.0, 
        "equity": 0.0, 
        "daily_pnl": 0.0, 
        "active_trades": 0,
        "symbol": "GOLD",
        "active_symbols": ["GOLD"], # Multi-chart support
        "timeframe": "M1",
        "preferred_session": "ALL",
        "market_open": True,
        "session": "IDLE",
        "is_institutional_session": False,
        "logs": ["[SYS] Initializing Quant Engine..."]
    },
    "risk": {
        "risk_per_trade": 0.01,
        "max_trades": 2,
        "max_daily_trades": 20,
        "daily_loss_limit": 0.10
    },
    "trades": [],
    "history": [],
    "depth": {"bids": [], "asks": []},
    "manual_order": None,
    "symbols": {
        "GOLD": {
            "chart": [],
            "overlays": {
                "fvg_zones":          [],
                "order_blocks":       [],
                "sweeps":             [],
                "bos_markers":        [],
                "support_resistance": []
            },
            "last_decision": {
                "direction": "WAIT",
                "strategy": "Initializing",
                "reason": "Syncing market structure...",
                "score": 0,
                "flow": ["Connecting to MT5", "Loading AI Brain"]
            }
        }
    },
    "rationales": {},
    "news": []
}

# --- Auth Dependencies ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except auth.JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# --- Auth Endpoints ---
@app.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pass = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pass)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = auth.create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Initialize global BOT_DATA with user persistent settings
    BOT_DATA["status"]["symbol"] = user.preferred_symbol
    active_list = (user.active_symbols or "GOLD").split(",")
    BOT_DATA["status"]["active_symbols"] = active_list
    
    # Initialize dictionary structure for all active symbols
    for sym in active_list:
        if sym not in BOT_DATA["symbols"]:
            BOT_DATA["symbols"][sym] = {
                "chart": [], 
                "overlays": {"fvg_zones":[], "order_blocks":[], "sweeps":[], "bos_markers":[], "support_resistance":[]},
                "last_decision": {"direction": "WAIT", "strategy": "Monitoring", "reason": "Cold sync...", "score": 0, "flow": []}
            }
            
    BOT_DATA["status"]["timeframe"] = user.preferred_timeframe
    BOT_DATA["status"]["preferred_session"] = user.preferred_session
    BOT_DATA["risk"]["risk_per_trade"] = user.risk_per_trade
    BOT_DATA["risk"]["max_trades"] = user.max_trades
    BOT_DATA["risk"]["daily_loss_limit"] = user.daily_loss_limit
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Bot Endpoints ---
@app.get("/status", response_model=BotStatus)
async def get_status(current_user: models.User = Depends(get_current_user)):
    return BOT_DATA["status"]

@app.get("/trades", response_model=List[Trade])
async def get_trades(current_user: models.User = Depends(get_current_user)):
    return BOT_DATA["trades"]

@app.get("/overlays")
async def get_overlays(symbol: str = "GOLD", current_user: models.User = Depends(get_current_user)):
    """Returns detected SMC levels for chart drawing: FVGs, OBs, Sweeps, BOS, S/R."""
    symbol = symbol.upper()
    return BOT_DATA["symbols"].get(symbol, {}).get("overlays", {
        "fvg_zones": [], "order_blocks": [], "sweeps": [], "bos_markers": [], "support_resistance": []
    })

@app.get("/decision")
async def get_decision(symbol: str = "GOLD", current_user: models.User = Depends(get_current_user)):
    """Returns the latest strategy decision and flow explanation."""
    symbol = symbol.upper()
    return BOT_DATA["symbols"].get(symbol, {}).get("last_decision", {
        "direction": "WAIT", "strategy": "Monitoring", "reason": "Syncing structure...", "score": 0, "flow": []
    })

@app.get("/history")
async def get_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Auto-sync MT5 history into DB
    for mt_trade in BOT_DATA["history"]:
        ticket = mt_trade.get("id")
        if ticket:
            exists = db.query(models.Trade).filter(models.Trade.ticket_id == ticket).first()
            if not exists:
                new_trade = models.Trade(
                    ticket_id=ticket,
                    symbol=mt_trade.get("symbol"),
                    type=mt_trade.get("type"),
                    volume=mt_trade.get("volume"),
                    entry_price=mt_trade.get("entry_price"),
                    profit=mt_trade.get("profit"),
                    sl=mt_trade.get("sl", 0),
                    tp=mt_trade.get("tp", 0),
                    status="CLOSED",
                    rationale=BOT_DATA["rationales"].get(ticket, "Institutional Analysis"),
                    user_id=current_user.id
                )
                db.add(new_trade)
    db.commit()
    
    return db.query(models.Trade).filter(models.Trade.user_id == current_user.id).order_by(models.Trade.time.desc()).all()

@app.get("/depth")
async def get_depth():
    return BOT_DATA["depth"]

@app.get("/chart")
async def get_chart(symbol: str = "GOLD"):
    symbol = symbol.upper()
    return BOT_DATA["symbols"].get(symbol, {}).get("chart", [])

@app.get("/news")
async def get_news():
    """Returns detected high-impact news events for frontend visualization."""
    return BOT_DATA["news"]

@app.post("/start")
async def start_bot(current_user: models.User = Depends(get_current_user)):
    BOT_DATA["status"]["is_running"] = True
    return {"message": "Quant Engine Engaged"}

@app.post("/stop")
async def stop_bot(current_user: models.User = Depends(get_current_user)):
    BOT_DATA["status"]["is_running"] = False
    return {"message": "Quant Engine Halted"}

@app.post("/settings")
async def update_settings(settings: SettingsUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if settings.symbol:
        sym = settings.symbol.upper()
        BOT_DATA["status"]["symbol"] = sym
        current_user.preferred_symbol = sym
        if sym not in BOT_DATA["symbols"]:
            BOT_DATA["symbols"][sym] = {
                "chart": [], 
                "overlays": {"fvg_zones":[], "order_blocks":[], "sweeps":[], "bos_markers":[], "support_resistance":[]},
                "last_decision": {"direction": "WAIT", "strategy": "Monitoring", "reason": "Initializing...", "score": 0, "flow": []}
            }
            
    if settings.active_symbols:
        active = [s.upper() for s in settings.active_symbols]
        BOT_DATA["status"]["active_symbols"] = active
        current_user.active_symbols = ",".join(active)
        # Ensure all active symbols exist in the data structure
        for sym in active:
            if sym not in BOT_DATA["symbols"]:
                BOT_DATA["symbols"][sym] = {
                    "chart": [], 
                    "overlays": {"fvg_zones":[], "order_blocks":[], "sweeps":[], "bos_markers":[], "support_resistance":[]},
                    "last_decision": {"direction": "WAIT", "strategy": "Monitoring", "reason": "Initializing...", "score": 0, "flow": []}
                }

    if settings.timeframe:
        tf = settings.timeframe.upper()
        BOT_DATA["status"]["timeframe"] = tf
        current_user.preferred_timeframe = tf
    if settings.preferred_session:
        sess = settings.preferred_session.upper()
        BOT_DATA["status"]["preferred_session"] = sess
        current_user.preferred_session = sess
    
    db.commit()
    return {"status": "Persistent settings updated", "data": BOT_DATA["status"]}

@app.get("/multi-status")
async def get_multi_status(current_user: models.User = Depends(get_current_user)):
    """Batch status for all active symbols."""
    return {
        "status": BOT_DATA["status"],
        "symbols": {sym: BOT_DATA["symbols"].get(sym) for sym in BOT_DATA["status"]["active_symbols"]}
    }

@app.post("/risk")
async def update_risk(risk: RiskUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if risk.risk_per_trade is not None:
        BOT_DATA["risk"]["risk_per_trade"] = risk.risk_per_trade
        current_user.risk_per_trade = risk.risk_per_trade
    if risk.max_trades is not None:
        BOT_DATA["risk"]["max_trades"] = risk.max_trades
        current_user.max_trades = risk.max_trades
    if risk.max_daily_trades is not None:
        BOT_DATA["risk"]["max_daily_trades"] = risk.max_daily_trades
    if risk.daily_loss_limit is not None:
        BOT_DATA["risk"]["daily_loss_limit"] = risk.daily_loss_limit
        current_user.daily_loss_limit = risk.daily_loss_limit
    
    db.commit()
    return {"status": "Institutional risk profile synchronized", "data": BOT_DATA["risk"]}

@app.get("/risk")
async def get_risk(current_user: models.User = Depends(get_current_user)):
    """Fetches the active risk parameters for the current institutional profile."""
    return {
        "risk_per_trade": current_user.risk_per_trade,
        "max_trades": current_user.max_trades,
        "max_daily_trades": BOT_DATA["risk"].get("max_daily_trades", 20),
        "daily_loss_limit": current_user.daily_loss_limit
    }

# --- Custom Strategy Endpoints ---
@app.post("/strategies", response_model=CustomStrategyResponse)
async def create_strategy(strategy: CustomStrategyCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_strat = models.CustomStrategy(
        name=strategy.name,
        type=strategy.type,
        description=strategy.description,
        logic=strategy.logic,
        color=strategy.color,
        user_id=current_user.id
    )
    db.add(new_strat)
    db.commit()
    db.refresh(new_strat)
    return new_strat

@app.get("/strategies", response_model=List[CustomStrategyResponse])
async def list_strategies(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.CustomStrategy).filter(models.CustomStrategy.user_id == current_user.id).all()

@app.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    strat = db.query(models.CustomStrategy).filter(
        models.CustomStrategy.id == strategy_id, 
        models.CustomStrategy.user_id == current_user.id
    ).first()
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")
    db.delete(strat)
    db.commit()
    return {"message": "Success"}

# --- Reset Endpoints ---
@app.post("/reset/history")
async def reset_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Wipes all historical trade records for the user from database and memory."""
    db.query(models.Trade).filter(models.Trade.user_id == current_user.id).delete()
    BOT_DATA["history"] = []
    db.commit()
    return {"message": "Trade analytics purged successfully"}

class SymbolSettingsUpdate(BaseModel):
    symbol: str
    manual_volume: Optional[float] = None

@app.post("/settings/symbol")
async def update_symbol_settings(update: SymbolSettingsUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Updates manual volume override for a specific symbol."""
    settings_dict = dict(current_user.symbol_settings or {})
    if update.manual_volume is not None:
        if update.symbol not in settings_dict:
            settings_dict[update.symbol] = {}
        settings_dict[update.symbol]["manual_volume"] = update.manual_volume
    else:
        # If None, remove the override
        if update.symbol in settings_dict:
            settings_dict[update.symbol].pop("manual_volume", None)
            
    current_user.symbol_settings = settings_dict
    db.commit()
    return {"message": f"Updated settings for {update.symbol}", "settings": settings_dict[update.symbol] if update.symbol in settings_dict else {}}

@app.get("/symbols/engine-config")
async def get_symbol_engine_config(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Returns symbol specifications (min volume, price) collected by the worker."""
    state = db.query(models.BotState).first()
    if not state or not state.current_metrics:
        return {}
    
    specs = state.current_metrics.get("symbol_specs", {})
    user_settings = current_user.symbol_settings or {}
    
    # Combine specs with user settings
    response = {}
    for symbol, spec in specs.items():
        response[symbol] = {
            **spec,
            "manual_volume": user_settings.get(symbol, {}).get("manual_volume")
        }
    return response

@app.post("/reset/risk")
async def reset_risk(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Resets the risk management engine to strict institutional defaults."""
    defaults = {
        "risk_per_trade": 0.01,
        "max_trades": 2,
        "max_daily_trades": 5,
        "daily_loss_limit": 0.05
    }
    BOT_DATA["risk"].update(defaults)
    current_user.risk_per_trade = defaults["risk_per_trade"]
    current_user.max_trades = defaults["max_trades"]
    current_user.daily_loss_limit = defaults["daily_loss_limit"]
    db.commit()
    return {"message": "Institutional risk safeguards restored", "data": BOT_DATA["risk"]}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)
