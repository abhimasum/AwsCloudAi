"""FastAPI server for orchestrator agent with web UI."""

import os
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from agent import process_query

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AWS Geography Agent")

# Mount static files (web UI)
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve web UI."""
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    return "<h1>Geography Q&A Bot</h1><p>UI not found</p>"


@app.post("/run")
async def run_query(request: Request):
    """Process a query through the orchestrator agent."""
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            return JSONResponse({"error": "No query provided"}, status_code=400)
        
        logger.info(f"Received query: {query}")
        result = await process_query(query)
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"Error in /run endpoint: {str(e)}", exc_info=True)
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "orchestrator-agent"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8002"))
    logger.info(f"Starting orchestrator agent on port {port}")
    
    # Run with 300 second keep-alive timeout
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        timeout_keep_alive=300
    )
