"""FastAPI server for retriever agent."""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from agent import answer_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AWS Retriever Agent")


@app.post("/run")
async def run_query(request: Request):
    """Process a retriever query."""
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            return JSONResponse({"error": "No query provided"}, status_code=400)
        
        logger.info(f"Retriever received query: {query}")
        result = await answer_query(query)
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"Error in /run endpoint: {str(e)}", exc_info=True)
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "retriever-agent"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8081"))
    logger.info(f"Starting retriever agent on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        timeout_keep_alive=300
    )
