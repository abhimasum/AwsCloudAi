"""Setup OpenSearch domain and create index for vector RAG."""

import os
import json
import logging
from opensearchpy import OpenSearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT", "http://localhost:9200")
OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX", "geography-documents")
OPENSEARCH_USER = os.environ.get("OPENSEARCH_USER", "admin")
OPENSEARCH_PASSWORD = os.environ.get("OPENSEARCH_PASSWORD", "")

def setup_opensearch():
    """Create OpenSearch index with vector field for embeddings."""
    try:
        # Create client
        if OPENSEARCH_PASSWORD:
            client = OpenSearch(
                hosts=[{"host": OPENSEARCH_ENDPOINT.split("//")[1].split(":")[0], 
                        "port": int(OPENSEARCH_ENDPOINT.split(":")[-1] if ":" in OPENSEARCH_ENDPOINT else "443")}],
                http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
                use_ssl=True,
                verify_certs=False
            )
        else:
            client = OpenSearch([OPENSEARCH_ENDPOINT])
        
        # Delete existing index if it exists
        try:
            client.indices.delete(index=OPENSEARCH_INDEX)
            logger.info(f"Deleted existing index: {OPENSEARCH_INDEX}")
        except:
            pass
        
        # Create index with vector field
        index_body = {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "knn": True,
                    "knn.algo_param.ef_construction": 128,
                    "knn.algo_param.m": 24
                }
            },
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "space_type": "l2",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                        }
                    },
                    "metadata": {"type": "object"},
                    "source": {"type": "keyword"}
                }
            }
        }
        
        client.indices.create(index=OPENSEARCH_INDEX, body=index_body)
        logger.info(f"✅ Created OpenSearch index: {OPENSEARCH_INDEX}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error setting up OpenSearch: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = setup_opensearch()
    sys.exit(0 if success else 1)
