"""Orchestrator agent: public-facing agent that delegates to specialist agents.

Flow:
1. Query comes in
2. SQL agent finds relevant metadata/indices (country, state, district IDs)  
3. Retriever agent uses that context to search OpenSearch RAG knowledge base
4. Combined answer returned to user
"""

import os
import sys
import asyncio
import json
from pathlib import Path
import httpx
import logging
import boto3
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# AWS Configuration
MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")

logger.info(f"Orchestrator Agent initialized with model={MODEL_ID}, region={REGION}")

# Initialize AWS Bedrock client
bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)

# Import the SQL agent from sibling directory (same container/process)
_agents_dir = Path(__file__).parent.parent
sys.path.insert(0, str(_agents_dir))
try:
    from sql_agent.agent import query_database
except ImportError:
    logger.warning("SQL agent not found, will use stub")
    async def query_database(_: str) -> str:
        return "SQL agent not available"

# URL of the retriever_agent service (separate ECS/AppRunner instance)
RETRIEVER_AGENT_URL = os.environ.get("RETRIEVER_URL", os.environ.get("RETRIEVER_AGENT_URL", "http://localhost:8081"))


async def ask_sql_agent(query: str) -> str:
    """Query the SQL agent for geography index metadata (state/country IDs, capitals, lists)."""
    try:
        logger.info(f"Calling SQL agent for: {query[:100]}...")
        result = await query_database(query)
        logger.info(f"SQL agent returned: {len(str(result))} chars")
        return str(result)
    except Exception as e:
        logger.error(f"SQL agent error: {str(e)}", exc_info=True)
        return f"SQL agent error: {str(e)}"


async def ask_retriever_agent(query: str) -> str:
    """Query the retriever agent for detailed RAG-grounded facts from documents."""
    try:
        logger.info(f"Calling retriever agent for: {query[:100]}...")
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{RETRIEVER_AGENT_URL}/run", 
                json={"query": query},
                timeout=180.0
            )
            response.raise_for_status()
            result = response.json().get("response", "No response from retriever agent")
            logger.info(f"Retriever responded: {len(str(result))} chars")
            return result
    except asyncio.TimeoutError:
        logger.error("Retriever agent timed out")
        return "Query took too long. Please try a simpler question."
    except httpx.TimeoutException:
        logger.error("HTTP connection timed out")
        return "Connection timeout. Please try again."
    except Exception as e:
        logger.error(f"Retriever error: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"


async def call_bedrock(prompt: str) -> str:
    """Call AWS Bedrock Claude model."""
    try:
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )
        
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]
    except Exception as e:
        logger.error(f"Bedrock error: {str(e)}", exc_info=True)
        return f"Error calling Bedrock: {str(e)}"


async def process_query(query: str) -> dict:
    """Process a user query through the orchestrator agent using Strands Agent SDK logic."""
    try:
        logger.info(f"Processing query: {query}")
        
        # Step 1: Determine query type
        classification_prompt = f"""Classify this query as one of:
1. GREETING (hi, hello, how are you)
2. LIST_QUERY (list states, get capitals, metadata)
3. DETAILED_QUERY (culture, economy, geography details)

Query: {query}

Respond with just the classification (GREETING/LIST_QUERY/DETAILED_QUERY)."""
        
        classification = await call_bedrock(classification_prompt)
        classification = classification.strip().upper()
        logger.info(f"Query classified as: {classification}")
        
        # Step 2: Route to appropriate agent
        if "GREETING" in classification:
            response = "Hello! I'm a geography Q&A bot for India. Ask me about Indian states, culture, economy, and geography."
        elif "LIST_QUERY" in classification:
            response = await ask_sql_agent(query)
        else:  # DETAILED_QUERY
            response = await ask_retriever_agent(query)
        
        return {
            "response": response,
            "status": "success",
            "classification": classification
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return {
            "response": f"Error: {str(e)}",
            "status": "error"
        }
