import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.orchestrator import AdvisorAgent

app = FastAPI(title="Multi-Agent Stock Advisor API")

# Initialize the agent
# Note: Ensure GOOGLE_API_KEY is set in the environment
if "GOOGLE_API_KEY" not in os.environ:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")

advisor = AdvisorAgent()

class StockRequest(BaseModel):
    symbol: str

class StockResponse(BaseModel):
    symbol: str
    report: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Multi-Agent Stock Advisor API. Use POST /analyze to get a recommendation."}

@app.post("/analyze", response_model=StockResponse)
def analyze_stock(request: StockRequest):
    """
    Analyzes a stock symbol using the multi-agent system.
    """
    try:
        symbol = request.symbol.upper()
        # The prompt can be adjusted to ensure the agent understands the context
        prompt = f"Analyze {symbol} and provide a comprehensive recommendation."
        report = advisor.run(prompt)
        return StockResponse(symbol=symbol, report=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
