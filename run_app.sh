#!/bin/bash
echo "Stopping any existing server on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "Starting Agentic Bot Web App..."
echo "Open http://localhost:8000 in your browser."

# Run Uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
