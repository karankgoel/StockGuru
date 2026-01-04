from fastmcp import FastMCP
import yfinance as yf
import ta
import pandas as pd
from ddgs import DDGS

# Initialize FastMCP server
mcp = FastMCP("stock_data")

@mcp.tool()
def search_web(query: str, max_results: int = 5) -> str:
    """
    Performs a web search using DuckDuckGo.
    Useful for finding popular funds, investor portfolios, or recent news not covered by stock APIs.
    
    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).
    """
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        
        formatted = []
        for r in results:
            formatted.append(f"- {r['title']}: {r['href']}\n  {r['body']}")
        
        return "\n".join(formatted)
    except Exception as e:
        return f"Search failed: {e}"

@mcp.tool()
def get_etf_info(symbol: str) -> str:
    """
    Fetches detailed information for an ETF, including top holdings and expense ratio.
    
    Args:
        symbol: The ETF ticker symbol.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Extract ETF specific data
        name = info.get('longName', symbol)
        category = info.get('category', 'N/A')
        expense_ratio = info.get('annualReportExpenseRatio', 'N/A')
        total_assets = info.get('totalAssets', 'N/A')
        summary = info.get('longBusinessSummary', 'No description.')
        
        # Holdings are tricky in yfinance, often in 'holdings' or 'topHoldings' keys, 
        # but sometimes not available. We'll try to get what we can.
        # Note: yfinance support for holdings varies. We return basic info + summary.
        
        return (
            f"ETF Report for {name} ({symbol}):\n"
            f"Category: {category}\n"
            f"Expense Ratio: {expense_ratio}\n"
            f"Total Assets: {total_assets}\n"
            f"Summary: {summary}\n"
        )
    except Exception as e:
        return f"Error fetching ETF info for {symbol}: {e}"

@mcp.tool()
def get_stock_history(symbol: str, period: str = "1mo") -> str:
    """
    Fetches historical stock data for a given symbol.
    
    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL').
        period: The period to fetch data for (e.g., '1d', '5d', '1mo', '3mo', '1y').
    """
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)
        if history.empty:
            return f"No history found for {symbol}."
        return f"History for {symbol} ({period}):\n{history.to_string()}"
    except Exception as e:
        return f"Error fetching history for {symbol}: {e}"

@mcp.tool()
def get_stock_news(symbol: str) -> str:
    """
    Fetches the latest news for a given stock symbol.
    
    Args:
        symbol: The stock ticker symbol.
    """
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if not news:
            return f"No news found for {symbol}."
        
        formatted_news = []
        for item in news[:5]: # Limit to top 5 news items
            title = item.get('title', 'No Title')
            link = item.get('link', 'No Link')
            formatted_news.append(f"- {title} ({link})")
            
        return f"Latest news for {symbol}:\n" + "\n".join(formatted_news)
    except Exception as e:
        return f"Error fetching news for {symbol}: {e}"

@mcp.tool()
def get_stock_profile(symbol: str) -> str:
    """
    Fetches the company profile for a given stock symbol.
    
    Args:
        symbol: The stock ticker symbol.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        summary = info.get('longBusinessSummary', 'No description available.')
        
        return f"Profile for {symbol}:\nSector: {sector}\nIndustry: {industry}\nSummary: {summary}"
    except Exception as e:
        return f"Error fetching profile for {symbol}: {e}"

@mcp.tool()
def get_technical_summary(symbol: str) -> str:
    """
    Performs a comprehensive technical analysis using the 'ta' library.
    Calculates RSI, MACD, Bollinger Bands, and SMA.
    
    Args:
        symbol: The stock ticker symbol.
    """
    try:
        # Fetch data (need enough data for indicators, e.g., 6 months)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        
        if df.empty:
            return f"No history found for {symbol}."
            
        # Clean data
        df = ta.utils.dropna(df)
        
        # Add indicators
        
        # RSI
        rsi_indicator = ta.momentum.RSIIndicator(close=df["Close"], window=14)
        df["rsi"] = rsi_indicator.rsi()
        
        # MACD
        macd_indicator = ta.trend.MACD(close=df["Close"])
        df["macd"] = macd_indicator.macd()
        df["macd_signal"] = macd_indicator.macd_signal()
        df["macd_diff"] = macd_indicator.macd_diff()
        
        # Bollinger Bands
        bb_indicator = ta.volatility.BollingerBands(close=df["Close"], window=20, window_dev=2)
        df["bb_high"] = bb_indicator.bollinger_hband()
        df["bb_low"] = bb_indicator.bollinger_lband()
        
        # SMA
        df["sma_20"] = ta.trend.SMAIndicator(close=df["Close"], window=20).sma_indicator()
        df["sma_50"] = ta.trend.SMAIndicator(close=df["Close"], window=50).sma_indicator()
        
        # Get latest values
        latest = df.iloc[-1]
        
        summary = [
            f"Technical Analysis Summary for {symbol} (as of {latest.name.date()}):",
            f"Current Price: {latest['Close']:.2f}",
            "",
            "Momentum:",
            f"- RSI (14): {latest['rsi']:.2f} " + ("(Overbought)" if latest['rsi'] > 70 else "(Oversold)" if latest['rsi'] < 30 else "(Neutral)"),
            "",
            "Trend:",
            f"- MACD: {latest['macd']:.2f}",
            f"- MACD Signal: {latest['macd_signal']:.2f}",
            f"- MACD Diff: {latest['macd_diff']:.2f} " + ("(Bullish)" if latest['macd_diff'] > 0 else "(Bearish)"),
            f"- SMA 20: {latest['sma_20']:.2f}",
            f"- SMA 50: {latest['sma_50']:.2f} " + ("(Price above SMA50)" if latest['Close'] > latest['sma_50'] else "(Price below SMA50)"),
            "",
            "Volatility:",
            f"- Bollinger High: {latest['bb_high']:.2f}",
            f"- Bollinger Low: {latest['bb_low']:.2f}",
            f"- Band Width: {latest['bb_high'] - latest['bb_low']:.2f}"
        ]
        
        return "\n".join(summary)
        
    except Exception as e:
        return f"Error performing technical analysis for {symbol}: {e}"

if __name__ == "__main__":
    mcp.run()
