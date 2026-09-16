"""SQL agent: handles queries against RDS PostgreSQL geography index."""

import os
import logging
import asyncio
import json
import boto3
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Constants
DB_UNAVAILABLE_MESSAGE = "Database unavailable"

# Database configuration
DB_HOST = os.environ.get("RDS_ENDPOINT", "localhost")
DB_PORT = int(os.environ.get("RDS_PORT", "5432"))
DB_NAME = os.environ.get("RDS_DB_NAME", "geography_db")
DB_USER = os.environ.get("RDS_USER", "postgres")
DB_PASSWORD = os.environ.get("RDS_PASSWORD", "postgres")

# AWS Configuration
MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")

logger.info(f"SQL Agent initialized with DB={DB_HOST}:{DB_PORT}/{DB_NAME}")

# Initialize AWS Bedrock client
bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)


def get_db_connection():
    """Create database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        return None


def list_all_states() -> str:
    """Get list of all Indian states and union territories."""
    try:
        conn = get_db_connection()
        if not conn:
            return DB_UNAVAILABLE_MESSAGE
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT name, capital FROM states ORDER BY name")
            states = cur.fetchall()
        
        conn.close()
        
        if not states:
            return "No states found"
        
        result = "Indian States and Union Territories:\n"
        for state in states:
            result += f"- {state['name']} (Capital: {state['capital']})\n"
        
        return result
    except Exception as e:
        logger.error(f"Error listing states: {e}")
        return f"Error: {str(e)}"


def get_state_info(state_name: str) -> str:
    """Get detailed information about a specific state."""
    try:
        conn = get_db_connection()
        if not conn:
            return DB_UNAVAILABLE_MESSAGE
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM states WHERE name ILIKE %s",
                (f"%{state_name}%",)
            )
            state = cur.fetchone()
        
        conn.close()
        
        if not state:
            return f"State '{state_name}' not found"
        
        result = f"**{state['name']}**\n"
        result += f"Capital: {state['capital']}\n"
        if state.get('area_sq_km'):
            result += f"Area: {state['area_sq_km']} sq km\n"
        if state.get('region'):
            result += f"Region: {state['region']}\n"
        
        return result
    except Exception as e:
        logger.error(f"Error getting state info: {e}")
        return f"Error: {str(e)}"


def search_districts(state_name: Optional[str] = None) -> str:
    """Search for districts, optionally filtered by state."""
    try:
        conn = get_db_connection()
        if not conn:
            return DB_UNAVAILABLE_MESSAGE
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if state_name:
                cur.execute(
                    "SELECT d.name, s.name as state_name FROM districts d "
                    "JOIN states s ON d.state_id = s.id "
                    "WHERE s.name ILIKE %s ORDER BY d.name",
                    (f"%{state_name}%",)
                )
            else:
                cur.execute("SELECT name FROM districts ORDER BY name LIMIT 20")
            
            districts = cur.fetchall()
        
        conn.close()
        
        if not districts:
            return "No districts found"
        
        result = "Districts:\n"
        for district in districts:
            state_info = f" ({district.get('state_name')})" if district.get('state_name') else ""
            result += f"- {district['name']}{state_info}\n"
        
        return result
    except Exception as e:
        logger.error(f"Error searching districts: {e}")
        return f"Error: {str(e)}"


async def query_database(query: str) -> str:
    """Process a query against the SQL agent using Strands-like logic."""
    try:
        logger.info(f"SQL Agent query: {query}")
        
        # Determine which database function to call
        query_lower = query.lower()
        
        if "list" in query_lower and "state" in query_lower:
            return list_all_states()
        elif "capital" in query_lower:
            return await query_bedrock_for_intent(query, "capitals")
        elif "district" in query_lower:
            return search_districts(extract_state_name(query))
        else:
            # Use Bedrock to extract intent and call appropriate function
            return await query_bedrock_for_intent(query, "general")
    
    except Exception as e:
        logger.error(f"Error in SQL agent: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"


async def query_bedrock_for_intent(query: str, intent_type: str) -> str:
    """Use Bedrock to understand query intent and route to appropriate DB function."""
    try:
        prompt = f"""Given this query about Indian geography, extract the state name if mentioned.
        
Query: {query}
Intent: {intent_type}

If a state is mentioned, respond with just the state name.
If multiple states, respond with comma-separated list.
If no state, respond with 'GENERAL'.
"""
        
        import json
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )
        
        result = json.loads(response["body"].read())
        state_name = result["content"][0]["text"].strip()
        
        if intent_type == "capitals" and state_name != "GENERAL":
            return get_state_info(state_name)
        else:
            return list_all_states()
    
    except Exception as e:
        logger.error(f"Bedrock intent error: {e}")
        return list_all_states()


def extract_state_name(query: str) -> Optional[str]:
    """Extract state name from query (simple regex-based)."""
    import re
    # Common state names
    states = ["Maharashtra", "Karnataka", "Tamil Nadu", "Uttar Pradesh", "West Bengal", 
              "Telangana", "Rajasthan", "Gujarat", "Andhra Pradesh", "Madhya Pradesh"]
    
    query_lower = query.lower()
    for state in states:
        if state.lower() in query_lower:
            return state
    
    return None
