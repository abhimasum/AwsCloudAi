"""Retriever agent: RAG specialist using OpenSearch for vector search over documents."""

import os
import logging
import json
import boto3
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# AWS Configuration
MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")
OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT", "http://localhost:9200")
OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX", "geography-documents")

logger.info(f"Retriever Agent initialized with model={MODEL_ID}, region={REGION}")

# Initialize AWS Bedrock client
bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)

# Initialize OpenSearch client
try:
    from opensearchpy import OpenSearch
    
    opensearch_client = OpenSearch(
        hosts=[OPENSEARCH_ENDPOINT],
        use_ssl=False,
        verify_certs=False,
        http_auth=None
    )
    logger.info("OpenSearch client initialized")
except Exception as e:
    logger.error(f"Error initializing OpenSearch: {e}")
    opensearch_client = None


def search_documents(query: str, top_k: int = 5) -> list:
    """Search OpenSearch for relevant documents using keyword search."""
    try:
        if not opensearch_client:
            return []
        
        logger.info(f"Searching for: {query}")
        
        # Use keyword search (simple text search without embeddings)
        search_body = {
            "size": top_k,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["text", "source"]
                }
            }
        }
        
        results = opensearch_client.search(index=OPENSEARCH_INDEX, body=search_body)
        
        documents = []
        for hit in results["hits"]["hits"]:
            documents.append({
                "content": hit["_source"].get("text", ""),
                "score": hit["_score"],
                "source": hit["_source"].get("source", "unknown")
            })
        
        logger.info(f"Found {len(documents)} documents")
        return documents
    
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}", exc_info=True)
        return []


def generate_answer(query: str, documents: list) -> str:
    """Use Bedrock Claude to generate an answer based on retrieved documents."""
    try:
        # Format documents for the prompt
        doc_context = "\n".join([
            f"Source: {doc['source']}\nContent: {doc['content'][:500]}"
            for doc in documents
        ])
        
        prompt = f"""Based on the following documents, answer the user's query.

Documents:
{doc_context}

User Query: {query}

Provide a clear, concise answer based on the documents. If the documents don't contain relevant information, say so."""
        
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
        answer = result["content"][0]["text"]
        logger.info(f"Generated answer: {len(answer)} chars")
        return answer
    
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"


async def answer_query(query: str) -> dict:
    """Answer a query using RAG with OpenSearch and Bedrock."""
    try:
        logger.info(f"Processing RAG query: {query}")
        
        # Step 1: Search documents
        documents = search_documents(query)
        
        if not documents:
            return {
                "response": "No relevant documents found for this query.",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 2: Generate answer using Bedrock
        answer = generate_answer(query, documents)
        
        return {
            "response": answer,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "documents_used": len(documents)
        }
    except Exception as e:
        logger.error(f"Error processing RAG query: {str(e)}", exc_info=True)
        return {
            "response": f"Error: {str(e)}",
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }
