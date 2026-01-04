import os
import yfinance as yf
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import timedelta

from api.models import Token, UserCreate, ChatMessage
from agent.orchestrator import AdvisorAgent
from api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user
)

# In-memory DB for demo purposes
# In production, use SQLite/PostgreSQL
users_db = {} 
watchlist_db = {} # {username: [symbol1, symbol2]}

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/")
async def read_root():
    return FileResponse('web/index.html')

@app.post("/auth/register")
async def register(user: UserCreate):
    try:
        if user.username in users_db:
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_password = get_password_hash(user.password)
        users_db[user.username] = {
            "username": user.username,
            "password_hash": hashed_password
        }
        return {"message": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user_dict["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_dict["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/market/indexes")
async def get_market_indexes(country: str = "US"):
    """Fetch top indexes based on country."""
    indexes = {
        "US": ["^GSPC", "^DJI", "^IXIC", "^RUT"], # S&P 500, Dow 30, Nasdaq, Russell 2000
        "UK": ["^FTSE", "^GSPC"], # FTSE 100
        "IN": ["^BSESN", "^NSEI"], # Sensex, Nifty 50
        "JP": ["^N225"], # Nikkei 225
    }
    
    symbols = indexes.get(country, indexes["US"])
    data = []
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.history(period="2d")
            if len(info) >= 2:
                current = info["Close"].iloc[-1]
                prev = info["Close"].iloc[-2]
                change = current - prev
                percent = (change / prev) * 100
                data.append({
                    "symbol": symbol,
                    "price": round(current, 2),
                    "change": round(change, 2),
                    "percent": round(percent, 2),
                    "name": symbol # yfinance sometimes doesn't give shortName for indexes reliably
                })
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            
    return data

@app.get("/market/chart/{symbol}")
async def get_chart_data(symbol: str, period: str = "1mo"):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(row["Close"], 2)
            })
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail="Symbol not found")

# Initialize Agent Lazily
agent = None

def get_agent():
    global agent
    if agent is None:
        try:
            print("Initializing AdvisorAgent...")
            agent = AdvisorAgent()
            print("AdvisorAgent initialized.")
        except Exception as e:
            print(f"Error initializing agent: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return agent

@app.post("/agent/chat")
def chat_agent(chat: ChatMessage, current_user: str = Depends(get_current_user)):
    """Chat with the AI Agent. Runs synchronously in threadpool."""
    agent_instance = get_agent()
    try:
        response = agent_instance.run(chat.message)
        return {"response": response}
    except Exception as e:
        return {"response": f"Error: {e}"}


@app.get("/watchlist")
async def get_watchlist(current_user: str = Depends(get_current_user)):
    return watchlist_db.get(current_user, [])

@app.post("/watchlist")
async def add_to_watchlist(symbol: str, current_user: str = Depends(get_current_user)):
    if current_user not in watchlist_db:
        watchlist_db[current_user] = []
    if symbol not in watchlist_db[current_user]:
        watchlist_db[current_user].append(symbol)
    return {"message": "Symbol added"}
