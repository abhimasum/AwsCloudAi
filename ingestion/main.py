"""Ingestion service main entry point."""

import os
import sys
import logging
from ingest import ingest_documents_from_local, ingest_documents_from_s3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run ingestion."""
    logger.info("Starting document ingestion service...")
    
    # Try S3 first if configured
    s3_bucket = os.environ.get("S3_BUCKET")
    if s3_bucket and s3_bucket != "geography-docs":
        logger.info("Attempting S3 ingestion...")
        success = ingest_documents_from_s3()
    else:
        logger.info("Using local document ingestion...")
        success = ingest_documents_from_local("data/sample_docs")
    
    if success:
        logger.info("✅ Ingestion completed successfully")
        return 0
    else:
        logger.error("❌ Ingestion failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
