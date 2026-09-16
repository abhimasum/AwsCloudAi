"""Document ingestion service: uploads documents to OpenSearch with embeddings."""

import os
import logging
import json
from pathlib import Path
from datetime import datetime
import boto3
from opensearchpy import OpenSearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET", "geography-docs")
S3_PREFIX = os.environ.get("S3_PREFIX", "documents/")

# OpenSearch Configuration
OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT", "http://localhost:9200")
OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX", "geography-documents")
OPENSEARCH_USER = os.environ.get("OPENSEARCH_USER", "admin")
OPENSEARCH_PASSWORD = os.environ.get("OPENSEARCH_PASSWORD", "")

# Bedrock Configuration
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")

# Initialize clients
s3_client = boto3.client("s3", region_name=AWS_REGION)
bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def get_opensearch_client():
    """Create OpenSearch client."""
    if OPENSEARCH_PASSWORD:
        return OpenSearch(
            hosts=[OPENSEARCH_ENDPOINT],
            http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
            use_ssl=True,
            verify_certs=False
        )
    else:
        return OpenSearch([OPENSEARCH_ENDPOINT])


def get_embedding(text: str) -> list:
    """Get embedding for text using Bedrock Titan embeddings."""
    try:
        response = bedrock_client.invoke_model(
            modelId=EMBEDDING_MODEL,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({"inputText": text})
        )
        
        result = json.loads(response["body"].read())
        return result.get("embedding", [])
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        return []


def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
    """Split text into chunks with overlap."""
    chunks = []
    for i in range(0, len(text), chunk_size - chunk_overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def ingest_documents_from_s3():
    """Download documents from S3 and ingest into OpenSearch."""
    try:
        client = get_opensearch_client()
        
        # List documents in S3
        logger.info(f"Fetching documents from s3://{S3_BUCKET}/{S3_PREFIX}")
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
        
        if "Contents" not in response:
            logger.warning("No documents found in S3")
            return
        
        doc_count = 0
        chunk_count = 0
        
        for obj in response["Contents"]:
            if obj["Key"].endswith((".txt", ".md")):
                try:
                    # Download document
                    response = s3_client.get_object(Bucket=S3_BUCKET, Key=obj["Key"])
                    content = response["Body"].read().decode("utf-8")
                    
                    logger.info(f"Processing: {obj['Key']}")
                    
                    # Split into chunks
                    chunks = split_text(content)
                    
                    # Generate embeddings and index
                    for i, chunk in enumerate(chunks):
                        embedding = get_embedding(chunk)
                        
                        if not embedding:
                            logger.warning(f"Failed to get embedding for chunk {i}")
                            continue
                        
                        doc_body = {
                            "text": chunk,
                            "embedding": embedding,
                            "source": obj["Key"],
                            "chunk": i,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        client.index(
                            index=OPENSEARCH_INDEX,
                            body=doc_body
                        )
                        chunk_count += 1
                    
                    doc_count += 1
                    logger.info(f"Indexed {len(chunks)} chunks from {obj['Key']}")
                
                except Exception as e:
                    logger.error(f"Error processing {obj['Key']}: {e}")
        
        logger.info(f"✅ Ingestion complete: {doc_count} documents, {chunk_count} chunks indexed")
        return True
    
    except Exception as e:
        logger.error(f"Error in ingestion: {e}")
        return False


def ingest_documents_from_local(doc_dir: str = "data/sample_docs"):
    """Ingest documents from local directory."""
    try:
        client = get_opensearch_client()
        
        doc_count = 0
        chunk_count = 0
        
        for file_path in Path(doc_dir).glob("*.md"):
            try:
                logger.info(f"Processing: {file_path}")
                
                # Read file
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Split into chunks
                chunks = split_text(content)
                
                # Generate embeddings and index
                for i, chunk in enumerate(chunks):
                    embedding = get_embedding(chunk)
                    
                    if not embedding:
                        logger.warning(f"Failed to get embedding for chunk {i}")
                        continue
                    
                    doc_body = {
                        "text": chunk,
                        "embedding": embedding,
                        "source": file_path.name,
                        "chunk": i,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    client.index(
                        index=OPENSEARCH_INDEX,
                        body=doc_body
                    )
                    chunk_count += 1
                
                doc_count += 1
                logger.info(f"Indexed {len(chunks)} chunks from {file_path.name}")
            
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"✅ Ingestion complete: {doc_count} documents, {chunk_count} chunks indexed")
        return True
    
    except Exception as e:
        logger.error(f"Error in local ingestion: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    # Try S3 first, fall back to local
    if S3_BUCKET and S3_BUCKET != "geography-docs":
        success = ingest_documents_from_s3()
    else:
        success = ingest_documents_from_local()
    
    sys.exit(0 if success else 1)
