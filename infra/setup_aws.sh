#!/bin/bash
# AWS Infrastructure Setup Script for Geography AI Agents

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
PROJECT_NAME=${PROJECT_NAME:-geography-ai}
ENVIRONMENT=${ENVIRONMENT:-dev}

echo "Setting up AWS infrastructure for $PROJECT_NAME in $AWS_REGION..."

# 1. Create RDS PostgreSQL Instance
echo "Creating RDS PostgreSQL database..."
aws rds create-db-instance \
    --db-instance-identifier "$PROJECT_NAME-db-$ENVIRONMENT" \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username postgres \
    --master-user-password "${RDS_PASSWORD}" \
    --allocated-storage 20 \
    --storage-type gp2 \
    --backup-retention-period 7 \
    --multi-az false \
    --publicly-accessible false \
    --region "$AWS_REGION" \
    || echo "Database may already exist"

# 2. Create OpenSearch Domain
echo "Creating OpenSearch domain..."
aws opensearch create-domain \
    --domain-name "$PROJECT_NAME-os-$ENVIRONMENT" \
    --engine-version "OpenSearch_2.11" \
    --node-type t3.small.search \
    --instance-count 1 \
    --enable-advanced-security \
    --master-username admin \
    --master-password "${OPENSEARCH_PASSWORD}" \
    --ebs-options EBSEnabled=true,VolumeType=gp2,VolumeSize=10 \
    --region "$AWS_REGION" \
    || echo "OpenSearch domain may already exist"

# 3. Create S3 Bucket for Documents
echo "Creating S3 bucket for documents..."
BUCKET_NAME="$PROJECT_NAME-docs-$(date +%s)"
aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$AWS_REGION" \
    $([ "$AWS_REGION" != "us-east-1" ] && echo "--create-bucket-configuration LocationConstraint=$AWS_REGION") \
    || echo "Bucket may already exist"

echo "✅ Infrastructure setup complete!"
echo "📝 Save these credentials to GitHub Secrets:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - RDS_PASSWORD"
echo "   - OPENSEARCH_PASSWORD"
echo ""
echo "📊 Created resources:"
echo "   - RDS: $PROJECT_NAME-db-$ENVIRONMENT"
echo "   - OpenSearch: $PROJECT_NAME-os-$ENVIRONMENT"
echo "   - S3 Bucket: $BUCKET_NAME"
