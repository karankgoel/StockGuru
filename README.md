# Multi-Agent Stock Advisor

A powerful stock analysis tool that leverages a multi-agent system powered by Google's Gemini models to provide comprehensive stock recommendations. This tool fetches financial data and performs technical analysis to give you informed insights.

## Features

- **Multi-Agent Analysis**: Uses specialized agents to analyze stocks from different perspectives.
- **Dual Interfaces**:
  - **CLI**: Interactive command-line interface for quick queries.
  - **REST API**: FastAPI-based server for integration with other applications.
- **Real-time Data**: Fetches up-to-date market data using `yfinance`.
- **Technical Analysis**: Performs technical indicators analysis using the `ta` library.

## Prerequisites

- Python 3.8+
- A Google Cloud Project with the Gemini API enabled.
- An API key for Google Gemini.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**
    You must set the `GOOGLE_API_KEY` environment variable for the agent to function.
    
    You can create a `.env` file in the root directory:
    ```bash
    cp .env.example .env
    # Edit .env and add your API Key
    ```
    
    Or export it directly:
    ```bash
    export GOOGLE_API_KEY="your_api_key_here"
    ```

## Usage

### Command Line Interface (CLI)

To investigate stocks interactively in your terminal:

```bash
python main.py
```

The application will prompt you to enter a stock symbol (e.g., AAPL, GOOGL) or a query.

### REST API

To run the API server, you can use the provided helper script:

```bash
./run_app.sh
```

Or run `uvicorn` directly:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.
- **Docs**: `http://localhost:8000/docs`
- **Analyze Endpoint**: `POST /analyze`
  - Body: `{"symbol": "AAPL"}`

## Project Structure

- `agent/`: Contains the core agent logic and orchestrator.
- `api/`: FastAPI application code.
- `main.py`: Entry point for the CLI.
- `requirements.txt`: Project dependencies.
- `run_app.sh`: Script to launch the API server.
